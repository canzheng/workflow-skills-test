"""Pure snapshot helpers for native GitHub operations; no client or state store."""
import argparse
import json
import pathlib
import re
from core import Conflict, Invalid, MODIFIERS, PHASES


def source_match(items, source_id):
    marker = '<!-- workflow-source: ' + source_id + ' -->'
    matches = [x for x in items if marker in (x.get('body') or '')]
    if len(matches) > 1:
        raise Conflict('Ambiguous source identity: ' + source_id)
    return matches[0] if matches else None


def phase_labels(current, phase=None, modifiers=(), closed=False):
    """Compute bounded label edit from a freshly read snapshot, preserving others."""
    if not closed and phase not in PHASES:
        raise Invalid('An open workflow Issue requires one supported phase')
    if any(x not in MODIFIERS for x in modifiers):
        raise Invalid('Unknown workflow modifier')
    if 'wf:deferred' in modifiers and phase != 'wf:backlog' and not closed:
        raise Invalid('Deferred work must be backlog')
    return sorted((set(current) - PHASES - MODIFIERS) | (set() if closed else {phase, *modifiers}))


def managed_update(expected, fresh, replacement, start, end):
    """Read/compare/update body block. Caller re-reads before native API mutation."""
    if expected != fresh:
        raise Conflict('Remote body changed since read; reconcile human edits before update')
    if fresh.count(start) != 1 or fresh.count(end) != 1 or fresh.index(start) >= fresh.index(end):
        raise Conflict('Missing or ambiguous managed body markers')
    a, b = fresh.index(start) + len(start), fresh.index(end)
    return fresh[:a] + '\n' + replacement.rstrip() + '\n' + fresh[b:]


def issue_findings(item):
    labels = {x['name'] if isinstance(x, dict) else x for x in item.get('labels', [])}
    problems = []
    if item.get('state', '').lower() == 'closed':
        if labels & (PHASES | MODIFIERS):
            problems.append('Closed Issue has stale workflow labels')
        if item.get('state_reason') == 'completed' and not item.get('delivery_evidence'):
            problems.append('Completed claim has no indexed delivery evidence; inspect acceptance and merge manually')
    else:
        if len(labels & PHASES) != 1:
            problems.append('Open workflow Issue must have exactly one phase')
        if 'wf:deferred' in labels and 'wf:backlog' not in labels:
            problems.append('Deferred modifier requires backlog')
    return problems


def render(catalog):
    text = pathlib.Path(catalog).read_text()
    sections = list(re.finditer(r'^### (WF2-F\d{2}) (.+)$', text, re.M))
    result = []
    for i, match in enumerate(sections):
        body = text[match.end():sections[i + 1].start() if i + 1 < len(sections) else text.index('\n## 5. Cross-feature')].strip()
        fid, title = match.groups()
        result.append(dict(source_id=fid, title=fid + ' ' + title,
                           body='<!-- workflow-source: ' + fid + ' -->\n\n' + body + '\n\n'
                           'Approved acceptance source: [feature catalog](https://github.com/canzheng/workflow-skills/blob/rewrite/workflow-skills-v2/docs/v2/v2-feature-list.md).\n'
                           'Dependency implementation may be verified on the same rewrite branch before merge. Use non-closing PR references until complete delivery.\n'))
    if len(result) != 14 or len({x['source_id'] for x in result}) != 14:
        raise Invalid('Catalog must contain all 14 unique approved feature sections')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Render approved WF2 catalog to temporary Issue bodies; no remote writes')
    p.add_argument('--catalog', required=True)
    args = p.parse_args()
    print(json.dumps(render(args.catalog), indent=2))
