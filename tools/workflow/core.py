"""Small shared validation and filesystem primitives; no task state."""
import hashlib
import json
import pathlib
import re
import subprocess

START = '<!-- workflow-v2:start -->'
END = '<!-- workflow-v2:end -->'
SKILLS = ('workflow-design-to-backlog', 'workflow-deliver-issue', 'workflow-risk-review')
CI_ASSETS = ('.github/workflows/workflow-v2-verify.yml',
             '.github/workflows/workflow-v2-pr-metadata.yml')
PHASES = {'wf:backlog', 'wf:ready', 'wf:in-progress', 'wf:review'}
MODIFIERS = {'wf:blocked', 'wf:deferred'}


class Invalid(ValueError):
    pass


class Conflict(ValueError):
    pass


def finding(code, path, message, remediation, severity='error'):
    return dict(code=code, severity=severity, path=str(path), message=message, remediation=remediation)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    p = subprocess.run(['git', '-C', str(root), *args], capture_output=True, check=False)
    if p.returncode:
        raise Invalid('Git command failed; confirm repository and revision: ' + ' '.join(args))
    return p.stdout


def relative(value):
    if not isinstance(value, str) or not value or '\\' in value:
        raise Invalid('Expected a nonempty repository-relative POSIX path')
    p = pathlib.PurePosixPath(value)
    if p.is_absolute() or any(x in ('..', '.', '') for x in value.split('/')) or value.startswith('.git/') or value == '.git':
        raise Invalid('Unsafe repository-relative path: ' + value)
    return p


def safe(root, name):
    relative(name)
    path = root / name
    for part in [path, *path.parents]:
        if part == root.parent:
            break
        if part.is_symlink():
            raise Invalid('Symlink destination is ambiguous: ' + str(part))
    if not path.resolve().is_relative_to(root.resolve()):
        raise Invalid('Path escapes repository: ' + name)
    return path


def repository(value):
    path = pathlib.Path(value).absolute()
    for part in [path, *path.parents]:
        if part.is_symlink():
            raise Invalid('Repository path contains a symlink: ' + str(part))
    if not path.is_dir():
        raise Invalid('Repository target is missing: ' + str(path))
    top = pathlib.Path(git(path, 'rev-parse', '--show-toplevel').decode().strip()).resolve()
    if top != path.resolve():
        raise Invalid('Target must be the explicit Git repository root')
    return top


def load(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise Invalid('Invalid JSON or missing file: ' + str(path)) from exc


def config(root):
    c = load(safe(root, '.workflow/config.json'))
    if not isinstance(c, dict) or type(c.get('schema_version')) is not int or c['schema_version'] != 1 or c.get('workflow') != 'github-v2':
        raise Invalid('Unsupported workflow configuration schema/version')
    if not isinstance(c.get('repository'), str) or not re.fullmatch(r'[\w.-]+/[\w.-]+', c['repository']):
        raise Invalid('repository must be owner/name')
    for key in ('docs_index', 'contract'):
        safe(root, c.get(key))
    if c.get('openspec') not in ('on-demand', 'disabled'):
        raise Invalid('openspec must be on-demand or disabled')
    v = c.get('verification')
    if not isinstance(v, dict) or set(v) != {'local', 'integration'}:
        raise Invalid('verification requires local and integration arrays')
    for commands in v.values():
        if not isinstance(commands, list):
            raise Invalid('verification commands must be arrays')
        for cmd in commands:
            if not isinstance(cmd, list) or not cmd or any(not isinstance(x, str) or not x for x in cmd):
                raise Invalid('Each verification command must be a nonempty argv array')
    if not v['local']:
        raise Invalid('At least one local verification command is required')
    return c


def block(text):
    a, b = text.count(START), text.count(END)
    if (a, b) == (0, 0):
        return None
    if (a, b) != (1, 1) or text.index(START) >= text.index(END):
        raise Conflict('Malformed managed AGENTS markers')
    return text[text.index(START):text.index(END) + len(END)]


def owned(name):
    relative(name)
    return (name.startswith('tools/workflow/') or
            any(name.startswith('.agents/skills/' + s + '/') for s in SKILLS) or
            name in ('docs/workflow/contract.md', 'docs/workflow/README.md',
                     'docs/workflow/development.md', 'docs/workflow/operations.md',
                     '.github/ISSUE_TEMPLATE/feature.yml', '.github/ISSUE_TEMPLATE/bug.yml',
                     '.github/pull_request_template.md',
                     '.github/workflows/workflow-v2-verify.yml',
                     '.github/workflows/workflow-v2-pr-metadata.yml'))


def manifest(root):
    p = safe(root, '.workflow/install-manifest.json')
    if not p.exists():
        return None
    m = load(p)
    if not isinstance(m, dict) or type(m.get('schema_version')) is not int or m.get('schema_version') != 1 or not isinstance(m.get('files'), dict) or not re.fullmatch(r'[0-9a-f]{40}', str(m.get('source_revision', ''))) or not isinstance(m.get('bundle_version'), str):
        raise Invalid('Invalid installation manifest')
    for name, h in m['files'].items():
        if not owned(name) or not isinstance(h, str) or not re.fullmatch(r'[0-9a-f]{64}', h):
            raise Invalid('Unsafe manifest path/hash: ' + name)
        safe(root, name)
    if not re.fullmatch(r'[0-9a-f]{64}', str(m.get('agents_block_hash', ''))):
        raise Invalid('Invalid managed instruction hash')
    return m


def content_identity(root):
    """Bind diagnostics/evidence to actual tracked and nonignored untracked bytes."""
    names = set(git(root, 'ls-files', '-z', '--cached', '--others', '--exclude-standard').decode().split('\0')) - {''}
    h = hashlib.sha256()
    for name in sorted(names):
        relative(name)
        p = root / name
        # A tracked symlink is hashed as its link text, never its destination bytes.
        if p.is_symlink():
            data = ('symlink:' + p.readlink().as_posix()).encode()
        elif not p.exists():
            data = b'missing'
        elif p.is_file():
            data = p.read_bytes()
        else:
            data = b'non-file'
        h.update(name.encode() + b'\0' + digest(data).encode() + b'\0')
    return dict(revision=git(root, 'rev-parse', 'HEAD').decode().strip(),
                branch=git(root, 'branch', '--show-current').decode().strip(),
                dirty=bool(git(root, 'status', '--porcelain')), content_digest=h.hexdigest())
