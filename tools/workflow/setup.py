"""Repository-scoped install/update/uninstall with preflight and rollback."""
import json
import os
import pathlib
import re
import shutil
import tempfile

from core import (Conflict, Invalid, START, END, SKILLS, CI_ASSETS, IGNORE_START, IGNORE_END,
                  SOURCE_URL, REQUIRED_ASSETS, block, config, digest, git, ignore_block, load, manifest,
                  owned, repository, safe, shared, shared_files, source_url, effective_ignore_policy)


def source_bundle(source, revision):
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise Invalid('source revision must be a full 40-character commit SHA')
    source = repository(source)
    git(source, 'cat-file', '-e', revision + '^{commit}')
    spec = load(safe(source, '.workflow/bundle.json'))
    if not isinstance(spec, dict) or type(spec.get('schema_version')) is not int or spec.get('schema_version') != 1 or not isinstance(spec.get('bundle_version'), str) or not isinstance(spec.get('assets'), dict) or not re.fullmatch(r'2\.\d+\.\d+', spec['bundle_version']):
        raise Invalid('Unsupported source bundle schema')
    assets = spec['assets']
    if not REQUIRED_ASSETS <= set(assets.values()):
        raise Conflict('Incomplete production bundle: required consumer assets omitted: ' + ', '.join(sorted(REQUIRED_ASSETS - set(assets.values()))))
    paths = {'.workflow/bundle.json', *assets.keys()}
    result = {}
    for name in sorted(paths):
        p = safe(source, name)
        if not p.is_file():
            raise Conflict('Missing source asset: ' + name)
        data = git(source, 'show', revision + ':' + name)
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
    """Stage all bytes and backups first; restore content/modes on apply failure."""
    if not changes:
        return
    preflight_destinations(root, changes)
    created_dirs = set()
    originals = {}
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
        applied = []
        try:
            for i, (name, data) in enumerate(changes.items()):
                p = safe(root, name)
                now = (p.read_bytes(), p.stat().st_mode) if p.exists() else None
                if now != originals[name]:
                    raise Conflict('Concurrent local edit detected: ' + name)
                for parent in p.parents:
                    if parent == root:
                        break
                    if not parent.exists():
                        created_dirs.add(parent)
                p.parent.mkdir(parents=True, exist_ok=True)
                applied.append(name)
                if data is None:
                    p.unlink(missing_ok=True)
                else:
                    # Per-file replacement is atomic; the multi-file operation is not.
                    tmp = p.with_name(p.name + '.wf2-staged')
                    if tmp.exists() or tmp.is_symlink():
                        raise Conflict('Staging collision: ' + str(tmp))
                    try:
                        shutil.copyfile(stage / str(i), tmp)
                        if originals[name]:
                            os.chmod(tmp, originals[name][1])
                        os.replace(tmp, p)
                    finally:
                        tmp.unlink(missing_ok=True)
                if fail_after is not None and len(applied) == fail_after:
                    raise OSError('Injected apply failure')
        except Exception as exc:
            residuals = []
            for name in reversed(applied):
                p = root / name
                try:
                    original = originals[name]
                    if original is None:
                        p.unlink(missing_ok=True)
                    else:
                        p.write_bytes(original[0])
                        os.chmod(p, original[1])
                except OSError:
                    residuals.append(name)
            for p in sorted(created_dirs, key=lambda p: len(p.parts), reverse=True):
                try:
                    p.rmdir()
                except OSError:
                    pass
            if residuals:
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
        if old['schema_version'] == 2 and current_ignore:
            if digest(current_ignore.encode()) != old['gitignore_block_hash']:
                residuals.append('.gitignore managed block')
            elif not any(shared(name) for name in remaining):
                changes['.gitignore'] = ignore_text.replace(current_ignore, '', 1).encode()
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
        if git(root, 'ls-files', '-z', '--', *['.agents/skills/' + s for s in SKILLS]):
            raise Conflict('Shared workflow skills are tracked; review and untrack only the three canonical skill directories before dependency adoption')
        for name in shared_files(root):
            safe(root, name)
            if name not in assets and (not old or name not in old['files']):
                raise Conflict('Unmanaged shared dependency asset: ' + name)
        if current_ignore and (not old or old['schema_version'] != 2):
            raise Conflict('Unmanaged shared-dependency gitignore block; resolve ownership first')
        if old and old['schema_version'] == 2 and (not current_ignore or digest(current_ignore.encode()) != old['gitignore_block_hash']):
            raise Conflict('Managed shared-dependency ignore block modified or missing')
        # Existing configuration is user owned and must remain valid.
        cp = safe(root, '.workflow/config.json')
        if cp.exists():
            config(root)
        if old:
            if not current or digest(current.encode()) != old['agents_block_hash']:
                raise Conflict('Managed AGENTS block modified or missing')
            for name, h in old['files'].items():
                p = safe(root, name)
                if shared(name) and old['schema_version'] == 2 and not p.exists():
                    continue  # Fresh clones have not materialized ignored dependencies yet.
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
        entry = (START + '\nBootstrap the pinned shared skills before starting the agent:\n'
                 'python3 tools/workflow/workflow.py bootstrap --repo . --apply --json\n'
                 'Use workflow-skills v2 from .agents/skills/. Read\n'
                 'docs/workflow/contract.md and docs/workflow/README.md.\n'
                 'Historical planning directories do not select v1. Never use obsolete\n'
                 'repository wrappers or global installation here. Preserve unrelated rules.\n' + END)
        new_text = text.replace(current, entry, 1) if current else text + ('\n' if text and not text.endswith('\n') else '') + entry + '\n'
        if new_text != text:
            changes['AGENTS.md'] = new_text.encode()
        ignores = IGNORE_START + '\n' + '\n'.join('/.agents/skills/' + s + '/' for s in SKILLS) + '\n' + IGNORE_END
        new_ignore = ignore_text.replace(current_ignore, ignores, 1) if current_ignore else ignore_text + ('\n' if ignore_text and not ignore_text.endswith('\n') else '') + ignores + '\n'
        effective_ignore_policy(root, assets, proposed=new_ignore)
        if new_ignore != ignore_text:
            changes['.gitignore'] = new_ignore.encode()
        if not cp.exists():
            if not args.repository or not re.fullmatch(r'[\w.-]+/[\w.-]+', args.repository):
                raise Invalid('Fresh setup requires --repository owner/name')
            c = dict(schema_version=1, workflow='github-v2', repository=args.repository,
                     docs_index='docs/workflow/README.md', contract='docs/workflow/contract.md',
                     openspec='on-demand', verification={'local': [['python3', 'tools/workflow/workflow.py', 'check', '--repo', '.']], 'integration': []})
            changes['.workflow/config.json'] = (json.dumps(c, indent=2) + '\n').encode()
        m = dict(schema_version=2, bundle_version=version, source_revision=args.revision, source_url=url,
                 files={name: digest(data) for name, data in assets.items()}, agents_block_hash=digest(entry.encode()),
                 gitignore_block_hash=digest(ignores.encode()))
        data = (json.dumps(m, indent=2) + '\n').encode()
        p = safe(root, '.workflow/install-manifest.json')
        if not p.exists() or p.read_bytes() != data:
            changes['.workflow/install-manifest.json'] = data
    preflight_destinations(root, changes)
    if args.apply:
        transaction(root, changes)
    return list(changes), residuals
