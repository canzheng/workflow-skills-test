"""Mechanical checks only; documentation semantics require human/agent review."""
import json
import os
import pathlib
import re
import shutil
import subprocess
from urllib.parse import unquote, urlsplit

from core import (Invalid, SKILLS, CI_ASSETS, START, block, config, digest, finding, git, load,
                  manifest, owned, relative, safe)
from records import issue_findings

SECTIONS = ('Assignment', 'Changes', 'Evidence', 'Documentation', 'Remaining')


def strip_code(text):
    return re.sub(r'(```|~~~).*?\1', '', text, flags=re.S)


def anchors(text):
    result, counts = set(), {}
    for name in re.findall(r'^#{1,6}\s+(.+?)\s*#*$', strip_code(text), re.M):
        slug = re.sub(r'[^\w\- ]', '', name.strip().lower()).replace(' ', '-')
        n = counts.get(slug, 0)
        counts[slug] = n + 1
        result.add(slug + ('-' + str(n) if n else ''))
    result.update(re.findall(r'<a\s+(?:name|id)=[\"\']([^\"\']+)', text))
    return result


def links(root, text, origin, reader=None):
    findings = []
    for target in re.findall(r'!?\[[^\]]*\]\(([^\n]+?)\)', strip_code(text)):
        target = target.strip()
        if target.startswith('<') and target.endswith('>'):
            target = target[1:-1]
        # Optional Markdown title; spaces in paths should use angle brackets.
        if ' "' in target:
            target = target.split(' "', 1)[0]
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc:
            continue
        path = unquote(parsed.path)
        fragment = unquote(parsed.fragment)
        candidate = pathlib.Path(origin).parent / path if path else pathlib.Path(origin)
        normalized = os.path.normpath(candidate.as_posix())
        try:
            relative(normalized)
            p = safe(root, normalized)
            if reader:
                data = reader(normalized)
            elif p.is_file():
                data = p.read_bytes()
            else:
                raise FileNotFoundError(normalized)
            if fragment and normalized.endswith('.md') and fragment not in anchors(data.decode()):
                findings.append(finding('links.anchor', origin, 'Missing local anchor: ' + target, 'Correct the link or heading'))
        except (Invalid, OSError, UnicodeError):
            findings.append(finding('links.path', origin, 'Missing or unsafe local link: ' + target, 'Reference an existing repository-relative file'))
    return findings


def pr_contract(root, snapshot):
    c = config(root)
    if not isinstance(snapshot, dict):
        raise Invalid('PR snapshot must be an object')
    reader = None
    if 'pull_request' in snapshot:
        pr = snapshot['pull_request']
        repo = snapshot.get('repository', {}).get('full_name')
        if pr.get('base', {}).get('repo', {}).get('full_name') != c['repository']:
            raise Invalid('PR base repository differs from configured repository')
        sha = pr.get('head', {}).get('sha', '')
        if not re.fullmatch(r'[0-9a-f]{40}', sha):
            raise Invalid('PR head must be a full commit SHA')
        # Read untrusted head content as Git blobs, never check out or execute it.
        if subprocess.run(['git', '-C', str(root), 'cat-file', '-e', sha + '^{commit}'], capture_output=True, check=False).returncode:
            git(root, 'fetch', '--no-tags', 'origin', sha)
        def reader(name):
            r = subprocess.run(['git', '-C', str(root), 'show', sha + ':' + name], capture_output=True, check=False)
            if r.returncode:
                raise FileNotFoundError(name)
            return r.stdout
        body = pr.get('body') or ''
    else:
        repo, body = snapshot.get('repository'), snapshot.get('body')
    if repo != c['repository'] or not isinstance(body, str):
        raise Invalid('PR snapshot requires matching repository and text body')
    findings = []
    parts = list(re.finditer(r'^##\s+(.+?)\s*$', strip_code(body), re.M))
    sections = {m.group(1): strip_code(body)[m.end():parts[i + 1].start() if i + 1 < len(parts) else len(strip_code(body))].strip() for i, m in enumerate(parts)}
    for name in SECTIONS:
        if not sections.get(name):
            findings.append(finding('pr.section', 'PR body', 'Missing or empty ' + name + ' section', 'Complete the PR evidence contract'))
    if len(parts) != len({m.group(1) for m in parts}):
        findings.append(finding('pr.duplicate', 'PR body', 'Duplicate section headings', 'Use one authoritative section per concern'))
    findings.extend(links(root, body, 'PR.md', reader))
    return findings


def check(root, args):
    c = config(root)
    findings = []
    if args.pr_json:
        findings.extend(pr_contract(root, load(pathlib.Path(args.pr_json))))
    if getattr(args, 'metadata_only', False):
        if not args.pr_json:
            raise Invalid('--metadata-only requires --pr-json')
        if args.run_local or args.run_integration or args.specs or args.issues_json:
            raise Invalid('--metadata-only cannot execute code/spec/integration checks')
        return findings
    for key in ('docs_index', 'contract'):
        if not safe(root, c[key]).is_file():
            findings.append(finding('config.path', c[key], 'Configured document is missing', 'Restore or correct configured path'))
    m = manifest(root)
    if m:
        for name, h in m['files'].items():
            p = safe(root, name)
            if not p.is_file() or digest(p.read_bytes()) != h:
                findings.append(finding('bundle.modified', name, 'Owned bytes differ or are missing', 'Review edits; do not silently overwrite'))
        text = safe(root, 'AGENTS.md').read_text() if safe(root, 'AGENTS.md').exists() else ''
        b = block(text)
        if not b or digest(b.encode()) != m['agents_block_hash']:
            findings.append(finding('instructions.modified', 'AGENTS.md', 'Managed instruction block differs', 'Resolve ownership'))
    else:
        spec = load(safe(root, '.workflow/bundle.json'))
        if not isinstance(spec, dict) or type(spec.get('schema_version')) is not int or spec.get('schema_version') != 1 or not isinstance(spec.get('bundle_version'), str) or not isinstance(spec.get('assets'), dict):
            raise Invalid('Invalid source bundle schema')
        destinations = set()
        for source, dest in spec['assets'].items():
            if not owned(dest) or dest in destinations:
                raise Invalid('Unsafe or duplicate bundle destination')
            destinations.add(dest)
            if not safe(root, source).is_file():
                findings.append(finding('bundle.missing', source, 'Production asset missing', 'Assemble complete bundle before installation'))
        required = {'.agents/skills/' + s + '/SKILL.md' for s in SKILLS} | set(CI_ASSETS)
        if not required <= destinations:
            findings.append(finding('bundle.incomplete', '.workflow/bundle.json', 'Required skill or consumer workflow omitted', 'Include all three canonical skills and both consumer workflows'))
    for s in SKILLS:
        p = safe(root, '.agents/skills/' + s + '/SKILL.md')
        if not p.is_file():
            findings.append(finding('skill.missing', p, 'Required skill is absent', 'Restore canonical source'))
        elif not re.match(r'\A---\nname: ' + re.escape(s) + r'\ndescription: .+\n---\n', p.read_text()):
            findings.append(finding('skill.header', p, 'Invalid skill frontmatter', 'Provide canonical name and focused description'))
    docs = [root / x for x in ('README.md', 'AGENTS.md', 'CLAUDE.md') if (root / x).is_file()]
    docs += list((root / 'docs').rglob('*.md')) + list((root / '.agents/skills').rglob('*.md'))
    docs += list((root / 'openspec/specs').rglob('*.md'))
    docs += list((root / 'openspec/changes/workflow-v2-rewrite').rglob('*.md'))
    for p in docs:
        name = p.relative_to(root).as_posix()
        if name.startswith(('docs/planning/', 'docs/lessons/', 'docs/history/')):
            continue
        findings.extend(links(root, p.read_text(), name))
    if args.issues_json:
        snapshot = load(pathlib.Path(args.issues_json))
        if not isinstance(snapshot, dict) or snapshot.get('repository') != c['repository'] or not isinstance(snapshot.get('issues'), list):
            raise Invalid('Issue audit snapshot requires matching repository and issues array')
        for item in snapshot['issues']:
            for problem in issue_findings(item):
                findings.append(finding('issue.inconsistent', str(item.get('number', 'unknown')), problem, 'Re-read native Issue/PR acceptance and delivery evidence'))
    if args.specs:
        cli = root / 'node_modules/.bin/openspec'
        if not cli.is_file():
            exe = shutil.which('openspec')
            cli = pathlib.Path(exe) if exe else cli
        if not cli.is_file():
            findings.append(finding('specs.unavailable', 'OpenSpec', 'Selected required spec check cannot run', 'Install pinned OpenSpec 1.14.0 with npm ci'))
        else:
            env = {**os.environ, 'OPENSPEC_TELEMETRY': '0', 'DO_NOT_TRACK': '1'}
            version = subprocess.run([str(cli), '--version'], capture_output=True, text=True, env=env, check=False)
            if version.returncode or version.stdout.strip() != '1.14.0':
                findings.append(finding('specs.version', cli, 'OpenSpec version differs from pinned 1.14.0', 'Use repository-pinned CLI'))
            else:
                r = subprocess.run([str(cli), 'validate', '--all', '--strict', '--no-interactive'], cwd=root, capture_output=True, text=True, env=env, check=False)
                if r.returncode:
                    findings.append(finding('specs.invalid', 'openspec', (r.stdout + r.stderr).strip(), 'Fix actual spec/delta errors; do not skip validation'))
    for category, requested in [('local', args.run_local), ('integration', args.run_integration)]:
        if not requested:
            continue
        commands = c['verification'][category]
        if not commands:
            findings.append(finding('verification.empty', '.workflow/config.json', category + ' has no declared commands; no pass claimed', 'Define required commands or record environmental acceptance separately', 'warning'))
        for index, command in enumerate(commands, 1):
            try:
                result = subprocess.run(command, cwd=root, shell=False, capture_output=True, check=False)
                passed = result.returncode == 0
                findings.append(finding('verification.passed' if passed else 'verification.failed', '.workflow/config.json',
                                        category + ' command ' + str(index) + ' exited ' + str(result.returncode),
                                        'Record revision/environment; inspect the declared command for details', 'info' if passed else 'error'))
            except OSError:
                findings.append(finding('verification.unavailable', '.workflow/config.json', category + ' command ' + str(index) + ' could not launch', 'Install the declared runtime; never silently choose another interpreter'))
    return findings
