"""Small shared validation and filesystem primitives; no task state."""
import hashlib
import json
import os
import pathlib
import re
import subprocess
import tempfile

START = '<!-- workflow-v2:start -->'
END = '<!-- workflow-v2:end -->'
IGNORE_START = '# workflow-v2-dependency:start'
IGNORE_END = '# workflow-v2-dependency:end'
SOURCE_URL = 'https://github.com/canzheng/workflow-skills.git'
PROJECT_FILES = frozenset(('AGENTS.md', '.workflow/config.json', '.workflow/install-manifest.json'))
SKILLS = ('workflow-design-to-backlog', 'workflow-deliver-issue', 'workflow-risk-review')
CI_ASSETS = ('.github/workflows/workflow-v2-verify.yml',
             '.github/workflows/workflow-v2-pr-metadata.yml')
RUNTIME_ASSETS = tuple('tools/workflow/' + p for p in
                      ('workflow.py', 'core.py', 'setup.py', 'bootstrap.py', 'checks.py', 'records.py', 'migration.py'))
REQUIRED_ASSETS = (frozenset('.agents/skills/' + s + '/SKILL.md' for s in SKILLS) |
                   frozenset(CI_ASSETS) | frozenset(RUNTIME_ASSETS) | frozenset((
                       'docs/workflow/contract.md', 'docs/workflow/README.md',
                       'docs/workflow/development.md', 'docs/workflow/operations.md',
                       '.github/ISSUE_TEMPLATE/feature.yml', '.github/ISSUE_TEMPLATE/bug.yml',
                       '.github/pull_request_template.md',
                       '.agents/skills/workflow-risk-review/references/methods.md')))
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
    p = subprocess.run(['git', '--no-optional-locks', '-C', str(root), *args], capture_output=True, check=False)
    if p.returncode:
        raise Invalid('Git command failed; confirm repository and revision: ' + ' '.join(args))
    return p.stdout


def relative(value):
    if not isinstance(value, str) or not value or '\\' in value or '\0' in value:
        raise Invalid('Expected a nonempty repository-relative POSIX path without NULs')
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
    top = pathlib.Path(os.fsdecode(git(path, 'rev-parse', '--show-toplevel')).strip()).resolve()
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
    return validate_config(root, c)


def validate_config(root, c):
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
    """Validate project tracking and declared dependency storage without index writes."""
    if m['schema_version'] not in (3, 4):
        raise Conflict('Existing adoption needs reviewed setup/update (schema 3 or 4)')
    ignored_dependency = m['schema_version'] == 4
    if ignored_dependency:
        policy = safe(root, '.gitignore')
        current = ignore_block(policy.read_text()) if policy.is_file() else None
        if not current or digest(current.encode()) != m['gitignore_block_hash']:
            raise Conflict('Managed shared-dependency ignore block modified or missing')
    for name in shared_files(root):
        safe(root, name)
        if name not in m['files']:
            raise Conflict('Unmanaged shared dependency asset: ' + name)
    effective_ignore_policy(root, m['files'], ignored_shared=ignored_dependency)
    tracked = set(os.fsdecode(git(root, 'ls-files', '-z')).split('\0')) - {''}
    committed = (set(os.fsdecode(git(root, 'ls-tree', '-r', '--name-only', '-z', 'HEAD')).split('\0')) - {''}
                 if head_revision(root) else set())
    required = {name for name in m['files'] if not ignored_dependency or not shared(name)} | PROJECT_FILES
    if ignored_dependency:
        required.add('.gitignore')
        if any(shared(name) for name in tracked):
            raise Conflict('Shared dependency remains tracked; review git rm --cached for only the three shared directories')
    # A completely unstaged initial adoption is reviewable. Indexed/committed
    # managed assets identify adoption even when provenance was removed from the
    # index. Existing project-owned AGENTS/config alone are not that sentinel.
    adoption = {name for name in m['files'] if not ignored_dependency or not shared(name)} | {'.workflow/install-manifest.json'}
    if adoption & (tracked | committed) and required - tracked:
        raise Conflict('Workflow installation path is not tracked: ' + sorted(required - tracked)[0] +
                       '; review and commit the complete adoption')
    if adoption & (tracked | committed):
        staged_installation(root)


def staged_installation(root):
    """Validate the commit candidate independently; never refresh/write the index."""
    entries = {}
    for record in git(root, 'ls-files', '--stage', '-z').split(b'\0'):
        if not record:
            continue
        metadata, name = record.split(b'\t', 1)
        mode, oid, stage = metadata.decode().split()
        entries.setdefault(os.fsdecode(name), []).append((mode, oid, stage))

    def read(name):
        staged = entries.get(name, [])
        if len(staged) != 1 or staged[0][0] not in ('100644', '100755') or staged[0][2] != '0':
            raise Conflict('Required path is missing, unmerged or not a regular file: ' + name)
        return git(root, '--no-replace-objects', 'cat-file', 'blob', staged[0][1])

    try:
        m = validate_manifest(root, json.loads(read('.workflow/install-manifest.json')))
        # An explicit schema-1 update may leave a coherent old tracked snapshot
        # in the index until the caller stages the migration; setup owns no index.
        if m['schema_version'] not in (1, 3, 4) or not REQUIRED_ASSETS <= m['files'].keys():
            raise Conflict('Provenance must describe a complete adoption')
        if m['schema_version'] == 4:
            if any(shared(name) for name in entries):
                raise Conflict('Shared dependency must not be staged/tracked')
            policy = ignore_block(read('.gitignore').decode())
            if not policy or digest(policy.encode()) != m['gitignore_block_hash']:
                raise Conflict('Managed ignore block differs from staged provenance')
            effective_ignore_policy(root, m['files'], proposed=read('.gitignore').decode(),
                                    ignored_shared=True, staged_paths=entries, read_staged=read)
        c = validate_config(root, json.loads(read('.workflow/config.json')))
        for key in ('docs_index', 'contract'):
            read(c[key])
        for name, expected in m['files'].items():
            if m['schema_version'] == 4 and shared(name):
                continue  # Pinned dependency bytes are validated in the working tree/bootstrap.
            if digest(read(name)) != expected:
                raise Conflict('Owned bytes differ from staged provenance: ' + name)
        b = block(read('AGENTS.md').decode())
        if not b or digest(b.encode()) != m['agents_block_hash']:
            raise Conflict('Managed AGENTS block differs from staged provenance')
    except ValueError as exc:
        raise Conflict('Staged workflow installation invalid: ' + str(exc)) from exc


def effective_ignore_policy(root, names, proposed=None, ignored_shared=False,
                            staged_paths=None, read_staged=None):
    """Read Git's effective policy, including nested/global/info rules, before writes."""
    skills_root = safe(root, '.agents/skills')
    projects = {'.agents/skills/workflow-project-trackability-probe/SKILL.md'}
    if staged_paths is None:
        for p in skills_root.rglob('*') if skills_root.exists() else ():
            name = p.relative_to(root).as_posix()
            if shared(name) or shared(name + '/'):
                continue
            safe(root, name)
            if p.is_file():
                projects.add(name)
            elif p.is_dir():
                projects.add(name + '/workflow-project-trackability-probe.md')
    else:
        for name in staged_paths:
            if name.startswith('.agents/skills/') and not shared(name):
                relative(name)
                projects.add(name)
                for parent in pathlib.PurePosixPath(name).parents:
                    if str(parent) == '.agents/skills':
                        break
                    projects.add((parent / 'workflow-project-trackability-probe.md').as_posix())
    dependency = {name for name in names if shared(name)} if ignored_shared else set()
    required = (set(names) - dependency) | PROJECT_FILES
    if ignored_shared:
        required.add('.gitignore')
    candidates = sorted(required | dependency | projects)

    def inspect(worktree):
        command = ['git', '-C', str(root)]
        if worktree is not None:
            command += ['--work-tree=' + str(worktree)]
            # Relative repository excludes must continue to resolve at the real root.
            exclude = subprocess.run(['git', '-C', str(root), 'config', '--path', '--get', 'core.excludesFile'], capture_output=True, check=False)
            if exclude.returncode not in (0, 1):
                raise Invalid('Cannot inspect repository exclude configuration')
            if exclude.returncode == 0:
                path = pathlib.Path(os.fsdecode(exclude.stdout).strip())
                command += ['-c', 'core.excludesFile=' + str(path if path.is_absolute() else root / path)]
        result = subprocess.run(command + ['check-ignore', '--no-index', '-z', '--stdin'],
                                input=os.fsencode('\0'.join(candidates) + '\0'), capture_output=True, check=False)
        if result.returncode not in (0, 1):
            raise Invalid('Cannot inspect effective shared/project skill ignore policy')
        ignored = set(os.fsdecode(result.stdout).split('\0')) - {''}
        if required & ignored:
            raise Conflict('Workflow installation path is ignored; remove the conflicting rule: ' + sorted(required & ignored)[0])
        if dependency - ignored:
            raise Conflict('Shared dependency is not ignored: ' + sorted(dependency - ignored)[0])
        if projects & ignored:
            raise Conflict('Project-specific skill path is ignored; narrow project ignore policy: ' + sorted(projects & ignored)[0])

    if proposed is None:
        inspect(None)
    else:
        # Preview the proposed root policy without touching project files or index.
        with tempfile.TemporaryDirectory(prefix='wf2-ignore-preview-') as directory:
            preview = pathlib.Path(directory)
            (preview / '.gitignore').write_text(proposed, encoding='utf-8')
            policies = set()
            for name in candidates:
                for parent in pathlib.PurePosixPath(name).parents:
                    if str(parent) == '.':
                        continue
                    ignore_name = (parent / '.gitignore').as_posix()
                    policies.add(ignore_name)
                (preview / name).parent.mkdir(parents=True, exist_ok=True)
            for name in sorted(policies):
                if staged_paths is None:
                    p = safe(root, name)
                    data = p.read_bytes() if p.is_file() else None
                else:
                    data = read_staged(name) if name in staged_paths else None
                if data is not None:
                    dest = preview / name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(data)
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


def valid_bundle_version(value):
    return isinstance(value, str) and re.fullmatch(r'2\.\d+\.\d+', value) is not None


def manifest(root):
    p = safe(root, '.workflow/install-manifest.json')
    if not p.exists():
        return None
    m = load(p)
    return validate_manifest(root, m)


def validate_manifest(root, m):
    if not isinstance(m, dict) or type(m.get('schema_version')) is not int or m.get('schema_version') not in (1, 2, 3, 4) or not isinstance(m.get('files'), dict) or not re.fullmatch(r'[0-9a-f]{40}', str(m.get('source_revision', ''))) or not valid_bundle_version(m.get('bundle_version')):
        raise Invalid('Invalid installation manifest')
    if m['schema_version'] in (2, 3, 4):
        source_url(m.get('source_url'))
    if m['schema_version'] == 3 and m.get('skill_storage') != 'tracked':
        raise Invalid('Schema-3 adoption requires tracked skill storage')
    if m['schema_version'] == 4 and m.get('skill_storage') != 'ignored':
        raise Invalid('Schema-4 adoption requires ignored skill storage')
    if m['schema_version'] in (2, 4):
        if not re.fullmatch(r'[0-9a-f]{64}', str(m.get('gitignore_block_hash', ''))):
            raise Invalid('Invalid shared-dependency ignore hash')
    for name, h in m['files'].items():
        if not owned(name) or not isinstance(h, str) or not re.fullmatch(r'[0-9a-f]{64}', h):
            raise Invalid('Unsafe manifest path/hash: ' + name)
        safe(root, name)
    if not re.fullmatch(r'[0-9a-f]{64}', str(m.get('agents_block_hash', ''))):
        raise Invalid('Invalid managed instruction hash')
    return m


def head_revision(root):
    """Resolve a real commit or a verified unborn branch without inventing history."""
    resolved = subprocess.run(['git', '-C', str(root), 'rev-parse', '--verify', '--quiet', 'HEAD^{commit}'], capture_output=True, check=False)
    if resolved.returncode == 0:
        revision = resolved.stdout.decode().strip()
    else:
        ref = git(root, 'symbolic-ref', '--quiet', 'HEAD').decode().strip()
        exists = subprocess.run(['git', '-C', str(root), 'show-ref', '--verify', '--quiet', ref], capture_output=True, check=False)
        if not ref.startswith('refs/heads/') or exists.returncode != 1:
            raise Invalid('Cannot resolve repository commit; inspect Git integrity')
        revision = None  # An unborn branch has content, but no tested commit to invent.
    return revision


def content_identity(root):
    """Bind diagnostics/evidence to actual tracked and nonignored untracked bytes."""
    names = set(os.fsdecode(git(root, 'ls-files', '-z', '--cached', '--others', '--exclude-standard')).split('\0')) - {''}
    m = manifest(root)
    dependency_modified = False
    if m and m['schema_version'] in (2, 3, 4):
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
            data = os.fsencode('symlink:' + p.readlink().as_posix())
        elif not p.exists():
            data = b'missing'
        elif p.is_file():
            data = p.read_bytes()
        else:
            data = b'non-file'
        h.update(os.fsencode(name) + b'\0' + digest(data).encode() + b'\0')
    revision = head_revision(root)
    return dict(revision=revision,
                branch=git(root, 'branch', '--show-current').decode().strip(),
                dirty=revision is None or bool(git(root, 'status', '--porcelain')) or dependency_modified,
                dependency_modified=dependency_modified, content_digest=h.hexdigest())
