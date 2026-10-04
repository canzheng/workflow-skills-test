"""Small shared validation and filesystem primitives; no task state."""
import hashlib
import json
import pathlib
import re
import subprocess
import tempfile

START = '<!-- workflow-v2:start -->'
END = '<!-- workflow-v2:end -->'
IGNORE_START = '# workflow-v2-dependency:start'
IGNORE_END = '# workflow-v2-dependency:end'
SOURCE_URL = 'https://github.com/canzheng/workflow-skills.git'
SKILLS = ('workflow-design-to-backlog', 'workflow-deliver-issue', 'workflow-risk-review')
CI_ASSETS = ('.github/workflows/workflow-v2-verify.yml',
             '.github/workflows/workflow-v2-pr-metadata.yml')
RUNTIME_ASSETS = tuple('tools/workflow/' + p for p in
                      ('workflow.py', 'core.py', 'setup.py', 'bootstrap.py', 'checks.py', 'records.py', 'migration.py'))
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


def shared(name):
    return any(name.startswith('.agents/skills/' + s + '/') for s in SKILLS)


def ignore_block(text):
    a, b = text.count(IGNORE_START), text.count(IGNORE_END)
    if (a, b) == (0, 0):
        return None
    if (a, b) != (1, 1) or text.index(IGNORE_START) >= text.index(IGNORE_END):
        raise Conflict('Malformed shared-dependency gitignore markers')
    return text[text.index(IGNORE_START):text.index(IGNORE_END) + len(IGNORE_END)]


def source_url(value):
    if not isinstance(value, str) or not re.fullmatch(r'https://github\.com/[\w.-]+/[\w.-]+', value):
        raise Invalid('Dependency source URL must be an explicit HTTPS GitHub repository without credentials')
    return value


def shared_files(root):
    result = set()
    for skill in SKILLS:
        folder = safe(root, '.agents/skills/' + skill)
        if folder.exists() and not folder.is_dir():
            raise Conflict('Shared skill directory is not a directory: ' + str(folder))
        for p in folder.rglob('*') if folder.exists() else ():
            if p.is_file() or p.is_symlink():
                result.add(p.relative_to(root).as_posix())
    return result


def dependency_policy(root, m):
    """Require ignored, untracked canonical namespaces; never edit the Git index."""
    if m['schema_version'] != 2:
        raise Conflict('This pin predates dependency bootstrap; perform explicit adoption/update first')
    p = safe(root, '.gitignore')
    b = ignore_block(p.read_text(encoding='utf-8') if p.exists() else '')
    if not b or digest(b.encode()) != m['gitignore_block_hash']:
        raise Conflict('Shared-dependency ignore block modified/missing; restore reviewed project policy')
    prefixes = ['.agents/skills/' + s for s in SKILLS]
    if git(root, 'ls-files', '-z', '--', *prefixes):
        raise Conflict('Shared workflow skills are tracked; review and untrack only the three canonical skill directories before adoption/bootstrap')
    for name in shared_files(root):
        safe(root, name)
        if name not in m['files']:
            raise Conflict('Unmanaged shared dependency asset: ' + name)
    effective_ignore_policy(root, m['files'])


def effective_ignore_policy(root, names, proposed=None):
    """Read Git's effective policy, including nested/global/info rules, before writes."""
    skills_root = safe(root, '.agents/skills')
    projects = {'.agents/skills/workflow-project-trackability-probe/SKILL.md'}
    for p in skills_root.rglob('*') if skills_root.exists() else ():
        name = p.relative_to(root).as_posix()
        if shared(name) or shared(name + '/'):
            continue
        safe(root, name)
        if p.is_file():
            projects.add(name)
        elif p.is_dir():
            projects.add(name + '/workflow-project-trackability-probe.md')
    required = {name for name in names if shared(name)}
    candidates = sorted(required | projects)

    def inspect(worktree):
        command = ['git', '-C', str(root)]
        if worktree is not None:
            command += ['--work-tree=' + str(worktree)]
            # Relative repository excludes must continue to resolve at the real root.
            exclude = subprocess.run(['git', '-C', str(root), 'config', '--path', '--get', 'core.excludesFile'], capture_output=True, check=False)
            if exclude.returncode not in (0, 1):
                raise Invalid('Cannot inspect repository exclude configuration')
            if exclude.returncode == 0:
                path = pathlib.Path(exclude.stdout.decode().strip())
                command += ['-c', 'core.excludesFile=' + str(path if path.is_absolute() else root / path)]
        result = subprocess.run(command + ['check-ignore', '--no-index', '-z', '--stdin'],
                                input=('\0'.join(candidates) + '\0').encode(), capture_output=True, check=False)
        if result.returncode not in (0, 1):
            raise Invalid('Cannot inspect effective shared/project skill ignore policy')
        ignored = set(result.stdout.decode().split('\0')) - {''}
        if required - ignored:
            raise Conflict('Shared dependency path is not ignored: ' + sorted(required - ignored)[0])
        if projects & ignored:
            raise Conflict('Project-specific skill path is ignored; narrow project ignore policy: ' + sorted(projects & ignored)[0])

    if proposed is None:
        inspect(None)
    else:
        # Preview the proposed root policy without touching project files or index.
        with tempfile.TemporaryDirectory(prefix='wf2-ignore-preview-') as directory:
            preview = pathlib.Path(directory)
            (preview / '.gitignore').write_text(proposed, encoding='utf-8')
            agents = safe(root, '.agents')
            for p in agents.rglob('.gitignore') if agents.exists() else ():
                name = p.relative_to(root).as_posix()
                safe(root, name)
                dest = preview / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(p.read_bytes())
            for name in candidates:
                (preview / name).parent.mkdir(parents=True, exist_ok=True)
            inspect(preview)


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
    if not isinstance(m, dict) or type(m.get('schema_version')) is not int or m.get('schema_version') not in (1, 2) or not isinstance(m.get('files'), dict) or not re.fullmatch(r'[0-9a-f]{40}', str(m.get('source_revision', ''))) or not isinstance(m.get('bundle_version'), str):
        raise Invalid('Invalid installation manifest')
    if m['schema_version'] == 2:
        source_url(m.get('source_url'))
        if not re.fullmatch(r'[0-9a-f]{64}', str(m.get('gitignore_block_hash', ''))):
            raise Invalid('Invalid shared-dependency ignore hash')
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
    m = manifest(root)
    dependency_modified = False
    if m and m['schema_version'] == 2:
        actual_shared = shared_files(root)
        names.update(actual_shared)
        dependency_modified = bool(actual_shared - m['files'].keys())
        for name, expected in m['files'].items():
            if shared(name):
                names.add(name)
                p = safe(root, name)
                dependency_modified |= not p.is_file() or digest(p.read_bytes()) != expected
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
                dirty=bool(git(root, 'status', '--porcelain')) or dependency_modified,
                dependency_modified=dependency_modified, content_digest=h.hexdigest())
