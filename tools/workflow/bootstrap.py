"""Materialize only the ignored shared skills from the tracked dependency pin."""
import pathlib
import tempfile

from core import Conflict, SKILLS, dependency_policy, digest, git, manifest, repository, safe, shared
from setup import preflight_destinations, source_bundle, transaction


def materialized(root, expected):
    for skill in SKILLS:
        folder = safe(root, '.agents/skills/' + skill)
        if folder.exists() and not folder.is_dir():
            raise Conflict('Shared skill directory is not a directory: ' + str(folder))
        for p in folder.rglob('*') if folder.exists() else ():
            name = p.relative_to(root).as_posix()
            safe(root, name)
            if p.is_file() and name not in expected:
                raise Conflict('Unmanaged shared dependency asset: ' + name)
    missing = []
    for name, expected_hash in expected.items():
        p = safe(root, name)
        if p.exists() and (not p.is_file() or digest(p.read_bytes()) != expected_hash):
            raise Conflict('Modified shared dependency preserved: ' + name)
        if not p.exists():
            missing.append(name)
    preflight_destinations(root, missing)
    return missing


def fetch_source(folder, url, revision):
    git(folder, 'init', '--quiet')
    git(folder, 'fetch', '--no-tags', '--depth=1', url, revision)
    git(folder, 'checkout', '--detach', '--quiet', revision)
    if git(folder, 'rev-parse', 'HEAD').decode().strip() != revision:
        raise Conflict('Fetched dependency revision differs from tracked pin')


def bootstrap(args):
    root = repository(args.repo)
    m = manifest(root)
    if not m:
        raise Conflict('Dependency pin missing; perform one-time adoption first')
    dependency_policy(root, m)
    expected = {name: h for name, h in m['files'].items() if shared(name)}
    required = {'.agents/skills/' + s + '/SKILL.md' for s in SKILLS}
    if not required <= expected.keys():
        raise Conflict('Incomplete shared-skill dependency pin; perform explicit adoption/update')
    missing = materialized(root, expected)
    if not args.source and not missing:
        return []

    def prepare(source):
        version, assets = source_bundle(source, m['source_revision'])
        skills = {name: data for name, data in assets.items() if shared(name)}
        if version != m['bundle_version'] or {name: digest(data) for name, data in skills.items()} != expected:
            raise Conflict('Pinned source skill bytes differ from tracked dependency hashes')
        return {name: skills[name] for name in missing}

    if args.source:
        changes = prepare(args.source)
    else:
        with tempfile.TemporaryDirectory(prefix='wf2-pinned-source-') as directory:
            fetch_source(pathlib.Path(directory), m['source_url'], m['source_revision'])
            changes = prepare(directory)
    # Only these namespaces can be changed; project-owned tracked bytes/index stay intact.
    if args.apply:
        transaction(root, changes)
    return list(changes)
