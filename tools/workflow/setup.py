"""Repository-scoped install/update/uninstall with preflight and rollback."""
import json
import os
import pathlib
import re
import shutil
import stat
import tempfile

from core import (Conflict, Invalid, START, END, SKILLS, CI_ASSETS, IGNORE_START, IGNORE_END,
                  SOURCE_URL, REQUIRED_ASSETS, block, config, digest, git, ignore_block, load, manifest,
                  owned, repository, safe, shared, shared_files, source_url, effective_ignore_policy, valid_bundle_version,
                  dependency_policy)


def source_bundle(source, revision):
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise Invalid('source revision must be a full 40-character commit SHA')
    source = repository(source)
    resolved = git(source, '--no-replace-objects', 'rev-parse', '--verify', revision + '^{commit}').decode().strip()
    if resolved != revision:
        raise Invalid('source revision must identify the commit itself, not an annotated tag object')
    spec = load(safe(source, '.workflow/bundle.json'))
    if not isinstance(spec, dict) or type(spec.get('schema_version')) is not int or spec.get('schema_version') != 1 or not valid_bundle_version(spec.get('bundle_version')) or not isinstance(spec.get('assets'), dict):
        raise Invalid('Unsupported source bundle schema')
    assets = spec['assets']
    if any(not isinstance(dest, str) for dest in assets.values()):
        raise Invalid('Source asset destinations must be repository-relative strings')
    if not REQUIRED_ASSETS <= set(assets.values()):
        raise Conflict('Incomplete production bundle: required consumer assets omitted: ' + ', '.join(sorted(REQUIRED_ASSETS - set(assets.values()))))
    paths = {'.workflow/bundle.json', *assets.keys()}
    result = {}
    for name in sorted(paths):
        p = safe(source, name)
        if not p.is_file():
            raise Conflict('Missing source asset: ' + name)
        data = git(source, '--no-replace-objects', 'show', revision + ':' + name)
        if p.read_bytes() != data:
            raise Conflict('Source bytes differ from pinned revision: ' + name)
        if name in assets:
            dest = assets[name]
            if not owned(dest) or dest in result:
                raise Invalid('Unsafe or duplicate bundle destination: ' + str(dest))
            result[dest] = data
    return spec['bundle_version'], result


def preflight_destinations(root, names):
    for name in names:
        p = safe(root, name)
        if p.exists() and not p.is_file():
            raise Conflict('Owned file destination is not a file: ' + name)
        for parent in p.parents:
            if parent == root:
                break
            if parent.exists() and not parent.is_dir():
                raise Conflict('Destination parent is not a directory: ' + str(parent))
        staged = p.with_name(p.name + '.wf2-staged')
        if staged.exists() or staged.is_symlink():
            raise Conflict('Staging collision: ' + str(staged))


def transaction(root, changes, fail_after=None):
    """Restore only our unchanged writes; retain backups for conflicting rollback."""
    if not changes:
        return
    preflight_destinations(root, changes)
    created_dirs = {}
    originals = {}
    def directory_name(path):
        return path.relative_to(root).as_posix() if path != root and path.is_relative_to(root) else str(path)
    def directory_metadata(path):
        # Optional skill-only targets may start with missing root/ancestors.
        # Revalidate their full path too; never follow a replaced parent symlink.
        for part in (path, *path.parents):
            if part.is_symlink():
                raise Invalid('Symlink directory during rollback: ' + str(part))
        return path.lstat()
    with tempfile.TemporaryDirectory(prefix='wf2-stage-') as td:
        stage = pathlib.Path(td)
        for i, (name, data) in enumerate(changes.items()):
            p = safe(root, name)
            originals[name] = (p.read_bytes(), p.stat().st_mode) if p.exists() else None
            if originals[name] is not None:
                (stage / ('backup-' + str(i))).write_bytes(originals[name][0])
            if data is not None:
                (stage / str(i)).write_bytes(data)
        recovery_index = {name: {'backup': 'backup-' + str(i) if originals[name] is not None else None,
                                 'mode': originals[name][1] if originals[name] is not None else None}
                          for i, name in enumerate(changes)}
        (stage / 'recovery-index.json').write_text(json.dumps(recovery_index, indent=2))
        applied = {}
        try:
            for i, (name, data) in enumerate(changes.items()):
                p = safe(root, name)
                now = (p.read_bytes(), p.stat().st_mode) if p.exists() else None
                if now != originals[name]:
                    raise Conflict('Concurrent local edit detected: ' + name)
                parents = []
                for parent in p.parents:
                    if parent.exists():
                        break
                    parents.append(parent)
                for parent in reversed(parents):
                    directory_metadata(parent.parent)
                    parent.mkdir()
                    metadata = directory_metadata(parent)
                    created_dirs[parent] = (metadata.st_mode, metadata.st_dev, metadata.st_ino)
                    recovery_index[directory_name(parent)] = {
                        'kind': 'directory', 'backup': None, 'mode': None,
                        'created_mode': metadata.st_mode, 'created_device': metadata.st_dev,
                        'created_inode': metadata.st_ino}
                if data is None:
                    p.unlink(missing_ok=True)
                    applied[name] = None
                else:
                    # Per-file replacement is atomic; the multi-file operation is not.
                    tmp = p.with_name(p.name + '.wf2-staged')
                    if tmp.exists() or tmp.is_symlink():
                        raise Conflict('Staging collision: ' + str(tmp))
                    try:
                        shutil.copyfile(stage / str(i), tmp)
                        if originals[name]:
                            os.chmod(tmp, originals[name][1])
                        installed = tmp.stat()
                        os.replace(tmp, p)
                        # Capture our staged inode before replacement, rather than
                        # accepting another process's subsequent edit as ours.
                        applied[name] = (data, installed.st_mode, installed.st_dev, installed.st_ino)
                    finally:
                        safe(root, name + '.wf2-staged').unlink(missing_ok=True)
                if fail_after is not None and len(applied) == fail_after:
                    raise OSError('Injected apply failure')
        except Exception as exc:
            residuals = []
            for name in reversed(applied):
                try:
                    p = safe(root, name)
                    current = None
                    if p.exists():
                        metadata = p.lstat()
                        if not stat.S_ISREG(metadata.st_mode):
                            raise Conflict('Rollback destination is not a regular file: ' + name)
                        current = (p.read_bytes(), metadata.st_mode, metadata.st_dev, metadata.st_ino)
                    if current != applied[name]:
                        raise Conflict('Concurrent edit during rollback: ' + name)
                    original = originals[name]
                    if original is None:
                        p.unlink(missing_ok=True)
                    else:
                        p.write_bytes(original[0])
                        os.chmod(p, original[1])
                except (OSError, Invalid, Conflict):
                    residuals.append(name)
            for p in sorted(created_dirs, key=lambda p: len(p.parts), reverse=True):
                name = directory_name(p)
                try:
                    metadata = directory_metadata(p)
                    if not stat.S_ISDIR(metadata.st_mode) or (metadata.st_mode, metadata.st_dev, metadata.st_ino) != created_dirs[p]:
                        raise Conflict('Concurrent directory change during rollback: ' + name)
                    p.rmdir()
                except FileNotFoundError:
                    pass  # already absent; never recreate a concurrent deletion
                except (OSError, Invalid, Conflict):
                    residuals.append(name)
            if residuals:
                (stage / 'recovery-index.json').write_text(json.dumps(recovery_index, indent=2))
                recovery = pathlib.Path(tempfile.mkdtemp(prefix='wf2-recovery-'))
                shutil.copytree(stage, recovery, dirs_exist_ok=True)
                raise Conflict('Rollback residuals: ' + ', '.join(residuals) + '; recoverable originals: ' + str(recovery)) from exc
            raise Conflict('Apply failed; original files restored: ' + str(exc)) from exc


def setup(args):
    root = repository(args.target)
    old = manifest(root)
    agents = safe(root, 'AGENTS.md')
    text = agents.read_text() if agents.exists() else ''
    current = block(text)
    ignore_path = safe(root, '.gitignore')
    ignore_text = ignore_path.read_text(encoding='utf-8') if ignore_path.exists() else ''
    current_ignore = ignore_block(ignore_text)
    if not args.uninstall and ('<!-- Beginning of Workflow Section -->' in text or
                               'bash install.sh' in text or 'must invoke `start-task`' in text):
        raise Conflict('Active legacy instruction routing; inspect migration and perform a bounded cutover first')
    if not old and current:
        raise Conflict('Unmanaged workflow-v2 block; resolve ownership first')
    changes, residuals = {}, []
    if args.uninstall:
        if not old:
            return [], []
        remaining = {}
        for name, h in old['files'].items():
            p = safe(root, name)
            if p.exists() and digest(p.read_bytes()) != h:
                residuals.append(name)
                remaining[name] = h
            elif p.exists():
                changes[name] = None
        if current and digest(current.encode()) == old['agents_block_hash']:
            changes['AGENTS.md'] = text.replace(current, '', 1).encode()
        elif current:
            residuals.append('AGENTS.md managed block')
        if old['schema_version'] in (2, 4) and current_ignore:
            if digest(current_ignore.encode()) != old['gitignore_block_hash']:
                residuals.append('.gitignore managed block')
            elif not any(shared(name) for name in remaining):
                changes['.gitignore'] = ignore_text.replace(current_ignore + ('\n' if current_ignore + '\n' in ignore_text else ''), '', 1).encode()
        mpath = '.workflow/install-manifest.json'
        if residuals:
            updated = {**old, 'files': remaining}
            changes[mpath] = (json.dumps(updated, indent=2) + '\n').encode()
        else:
            changes[mpath] = None
    else:
        if not args.source or not args.revision:
            raise Invalid('setup requires --source and --revision')
        version, assets = source_bundle(args.source, args.revision)
        url = source_url(getattr(args, 'source_url', SOURCE_URL))
        for name in shared_files(root):
            safe(root, name)
            if name not in assets and (not old or name not in old['files']):
                raise Conflict('Unmanaged shared dependency asset: ' + name)
        if current_ignore and (not old or old['schema_version'] not in (2, 4)):
            raise Conflict('Unmanaged shared-dependency gitignore block; resolve ownership first')
        if old and old['schema_version'] in (2, 4) and (not current_ignore or digest(current_ignore.encode()) != old['gitignore_block_hash']):
            raise Conflict('Managed shared-dependency ignore block modified or missing')
        # Existing configuration is user owned and must remain valid.
        cp = safe(root, '.workflow/config.json')
        if cp.exists():
            config(root)
        if old:
            if not current or digest(current.encode()) != old['agents_block_hash']:
                raise Conflict('Managed AGENTS block modified or missing')
            if old['schema_version'] == 4:
                dependency_policy(root, old)
            for name, h in old['files'].items():
                p = safe(root, name)
                if shared(name) and old['schema_version'] in (2, 4) and not p.exists():
                    continue  # Legacy ignored dependencies may be absent in fresh clones.
                if not p.is_file() or digest(p.read_bytes()) != h:
                    raise Conflict('Modified/missing managed file: ' + name)
                if name not in assets:
                    changes[name] = None
        for name, data in assets.items():
            p = safe(root, name)
            if p.exists() and (not old or name not in old['files']):
                raise Conflict('Unmanaged target collision: ' + name)
            if not p.exists() or p.read_bytes() != data:
                changes[name] = data
        ignored_dependency = args.skill_storage == 'ignored'
        entry = (START + '\nUse the repo-local workflow-skills v2 in .agents/skills/. Read\n'
                 'docs/workflow/contract.md and docs/workflow/README.md.\n'
                 'Run pinned bootstrap before Codex starts; then verify with\n'
                 'python3 tools/workflow/workflow.py check --repo .\n'
                 'Historical planning directories do not select v1. Never use obsolete\n'
                 'repository wrappers or global installation here. Preserve unrelated rules.\n' + END)
        new_text = text.replace(current, entry, 1) if current else text + ('\n' if text and not text.endswith('\n') else '') + entry + '\n'
        if new_text != text:
            changes['AGENTS.md'] = new_text.encode()
        # Only the verified schema-2 owned block is removed on explicit update.
        # Other root/nested/global ignores are preserved and checked for conflicts.
        new_ignore = ignore_text.replace(current_ignore + ('\n' if current_ignore + '\n' in ignore_text else ''), '', 1) if current_ignore else ignore_text
        if ignored_dependency:
            dependency_ignore = (IGNORE_START + '\n' + '\n'.join('/.agents/skills/' + s + '/' for s in SKILLS) + '\n' + IGNORE_END)
            new_ignore += ('\n' if new_ignore and not new_ignore.endswith('\n') else '') + dependency_ignore + '\n'
        effective_ignore_policy(root, assets, proposed=new_ignore, ignored_shared=ignored_dependency)
        if new_ignore != ignore_text:
            changes['.gitignore'] = new_ignore.encode()
        if not cp.exists():
            if not args.repository or not re.fullmatch(r'[\w.-]+/[\w.-]+', args.repository):
                raise Invalid('Fresh setup requires --repository owner/name')
            c = dict(schema_version=1, workflow='github-v2', repository=args.repository,
                     docs_index='docs/workflow/README.md', contract='docs/workflow/contract.md',
                     openspec='on-demand', verification={'local': [['python3', 'tools/workflow/workflow.py', 'check', '--repo', '.']], 'integration': []})
            changes['.workflow/config.json'] = (json.dumps(c, indent=2) + '\n').encode()
        m = dict(schema_version=4 if ignored_dependency else 3, skill_storage=args.skill_storage, bundle_version=version, source_revision=args.revision, source_url=url,
                 files={name: digest(data) for name, data in assets.items()}, agents_block_hash=digest(entry.encode()))
        if ignored_dependency:
            m['gitignore_block_hash'] = digest(dependency_ignore.encode())
        data = (json.dumps(m, indent=2) + '\n').encode()
        p = safe(root, '.workflow/install-manifest.json')
        if not p.exists() or p.read_bytes() != data:
            changes['.workflow/install-manifest.json'] = data
    preflight_destinations(root, changes)
    if args.apply:
        transaction(root, changes)
    return list(changes), residuals


def install_skills(args):
    """Explicit optional global installation; never change project policy/auth/config."""
    root = pathlib.Path(args.target).absolute()
    if not pathlib.Path(args.target).is_absolute():
        raise Invalid('Global/custom skill target must be an explicit absolute path')
    for p in (root, *root.parents):
        if p.is_symlink():
            raise Invalid('Global skill target contains a symlink')
        if p.exists() and not p.is_dir():
            raise Invalid('Global skill target is not a directory')
    pin_name = '.workflow-skills-install.json'
    pin = safe(root, pin_name)
    old = load(pin) if pin.exists() else None
    if old is not None:
        if (not isinstance(old, dict) or type(old.get('schema_version')) is not int or
                old['schema_version'] != 1 or not isinstance(old.get('files'), dict) or
                not re.fullmatch(r'[0-9a-f]{40}', str(old.get('source_revision', ''))) or
                not valid_bundle_version(old.get('bundle_version'))):
            raise Invalid('Invalid shared-skills installation provenance')
        source_url(old.get('source_url'))
        for name, h in old['files'].items():
            if (not any(name.startswith(s + '/') for s in SKILLS) or
                    not isinstance(h, str) or not re.fullmatch(r'[0-9a-f]{64}', h)):
                raise Invalid('Unsafe shared-skills provenance path/hash')
            safe(root, name)
    changes, residuals = {}, []
    if args.uninstall:
        if not old:
            return [], []
        remaining = {}
        for name, h in old['files'].items():
            p = safe(root, name)
            if p.exists() and (not p.is_file() or digest(p.read_bytes()) != h):
                residuals.append(name); remaining[name] = h
            elif p.exists():
                changes[name] = None
        changes[pin_name] = (json.dumps({**old, 'files': remaining}, indent=2) + '\n').encode() if residuals else None
    else:
        if not args.source or not args.revision:
            raise Invalid('install-skills requires --source and --revision')
        version, assets = source_bundle(args.source, args.revision)
        prefix = '.agents/skills/'
        skills = {name[len(prefix):]: data for name, data in assets.items() if shared(name)}
        for s in SKILLS:
            folder = safe(root, s)
            if folder.exists() and not folder.is_dir():
                raise Conflict('Shared skill destination is not a directory: ' + s)
            for p in folder.rglob('*') if folder.exists() else ():
                name = p.relative_to(root).as_posix(); safe(root, name)
                if p.is_file() and (not old or name not in old['files']):
                    raise Conflict('Unmanaged global shared-skill collision: ' + name)
        if old:
            for name, h in old['files'].items():
                p = safe(root, name)
                if not p.is_file() or digest(p.read_bytes()) != h:
                    raise Conflict('Modified/missing global skill preserved: ' + name)
                if name not in skills:
                    changes[name] = None
        for name, data in skills.items():
            p = safe(root, name)
            if p.exists() and (not old or name not in old['files']):
                raise Conflict('Unmanaged global shared-skill collision: ' + name)
            if not p.exists() or p.read_bytes() != data:
                changes[name] = data
        m = dict(schema_version=1, bundle_version=version, source_revision=args.revision,
                 source_url=source_url(args.source_url), files={n: digest(d) for n, d in skills.items()})
        data = (json.dumps(m, indent=2) + '\n').encode()
        if not pin.exists() or pin.read_bytes() != data:
            changes[pin_name] = data
    preflight_destinations(root, changes)
    if args.apply:
        transaction(root, changes)
    return list(changes), residuals
