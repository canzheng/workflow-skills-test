"""Read-only inventory for the repository's known v1 Markdown format."""
import pathlib
import re
from core import Invalid, finding, relative, safe

STATES = {'BACKLOG', 'SHAPING', 'READY', 'IN_PROGRESS', 'DONE', 'DEFER'}
META = re.compile(r'^- (Feature ID|OpenSpec Change|Current Task):\s*`([^`]+)`', re.M)


def inspect(root):
    records, findings, ids = [], [], {}
    versions = safe(root, 'docs/planning/versions')
    if not versions.exists():
        return [], dict(records=[], active_count=0, historical_done_count=0)
    for folder in sorted(versions.iterdir()):
        if folder.is_symlink():
            findings.append(finding('migration.symlink', folder, 'Ambiguous version directory', 'Inspect the exact historical directory manually'))
            continue
        ledger = folder / 'BACKLOG.md'
        if not ledger.is_file():
            continue
        ledger_name = ledger.relative_to(root).as_posix()
        text = ledger.read_text()
        headings = list(re.finditer(r'^## \[([^\]]+)\]\s*$|^### (.+)$', text, re.M))
        phase = None
        for index, heading in enumerate(headings):
            if heading.group(1):
                phase = heading.group(1)
                if phase not in STATES:
                    findings.append(finding('migration.state', ledger_name, 'Unknown v1 section ' + phase, 'Resolve state manually; do not guess'))
                continue
            raw = heading.group(2)
            m = re.match(r'`([a-zA-Z0-9]+-[fb]\d+)`\s+', raw)
            if not m or phase not in STATES:
                findings.append(finding('migration.heading', ledger_name, 'Malformed/unowned feature heading: ' + raw, 'Resolve ID and phase manually'))
                continue
            fid = m.group(1)
            if fid in ids:
                findings.append(finding('migration.duplicate', ledger_name, 'Duplicate old ID ' + fid + '; first in ' + ids[fid], 'Reconcile both records before any creation'))
            ids[fid] = ledger_name
            end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
            notes = text[heading.end():end].strip()
            link = re.search(r'\[[^\]]+\]\(([^)]+)\)', raw)
            feature_path, feature_text, metadata, spec_paths = None, '', {}, []
            if link:
                try:
                    relative(link.group(1))
                    feature = safe(root, folder.relative_to(root).as_posix() + '/' + link.group(1))
                    feature_path = feature.relative_to(root).as_posix()
                    feature_text = feature.read_text()
                    metadata = dict(META.findall(feature_text))
                    spec_paths = re.findall(r'^\s+- `(openspec/specs/[^`]+)`', feature_text, re.M)
                    if metadata.get('Feature ID') != fid:
                        findings.append(finding('migration.identity', feature_path, 'Heading and feature metadata ID disagree or metadata is missing', 'Resolve identity explicitly'))
                except (Invalid, OSError):
                    findings.append(finding('migration.feature', ledger_name, 'Missing or unsafe feature target for ' + fid, 'Restore the original record or map manually'))
            elif phase != 'BACKLOG':
                findings.append(finding('migration.feature', ledger_name, 'Promoted item has no feature link: ' + fid, 'Resolve known-format feature record'))
            change = metadata.get('OpenSpec Change')
            change_path = None
            if change:
                try:
                    relative(change)
                    if '/' in change:
                        raise Invalid('Change ID must be one directory name')
                    active = safe(root, 'openspec/changes/' + change)
                    archive = safe(root, 'openspec/changes/archive')
                    archived = [safe(root, p.relative_to(root).as_posix()) for p in archive.glob('*-' + change)]
                    matches = ([active] if active.is_dir() else []) + [p for p in archived if p.is_dir()]
                    if len(matches) == 1:
                        change_path = matches[0].relative_to(root).as_posix()
                    elif phase != 'DONE':
                        findings.append(finding('migration.change', feature_path or ledger_name, 'Missing/ambiguous OpenSpec change for ' + fid, 'Reconcile original change/evidence before migration'))
                except Invalid:
                    findings.append(finding('migration.change', feature_path or ledger_name, 'Unsafe change ID/path for ' + fid, 'Map the original change manually'))
            elif phase not in ('DONE', 'BACKLOG'):
                findings.append(finding('migration.change', feature_path or ledger_name, 'Missing OpenSpec Change metadata for ' + fid, 'Resolve known-format change link'))
            if phase != 'DONE':
                for name in spec_paths:
                    try:
                        if not safe(root, name).is_file():
                            raise OSError('missing')
                    except (Invalid, OSError):
                        findings.append(finding('migration.spec', feature_path, 'Missing referenced active spec: ' + name, 'Restore or deliberately reconcile contract'))
            if phase == 'DONE' and metadata.get('Current Task') not in (None, 'none'):
                findings.append(finding('migration.inconsistent', feature_path or ledger_name, 'Done record has an active task: ' + fid, 'Resolve contradiction; do not invent completion'))
            records.append(dict(old_id=fid, state=phase, ledger=ledger_name,
                                feature_path=feature_path, change_path=change_path,
                                specs=spec_paths, original_record=feature_text or notes,
                                proposed_disposition='retain-history' if phase == 'DONE' else 'defer' if phase == 'DEFER' else 'migrate',
                                requires_authorized_choice=phase != 'DONE'))
    return findings, dict(records=records,
                          active_count=sum(x['state'] != 'DONE' for x in records),
                          historical_done_count=sum(x['state'] == 'DONE' for x in records))
