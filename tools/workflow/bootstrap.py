"""Materialize missing ignored skills from an exact pin; preserve project files/index."""
import pathlib
import tempfile

from core import (Conflict, REQUIRED_ASSETS, block, dependency_policy, digest, git,
                  manifest, repository, safe, shared)
from setup import source_bundle, transaction


def bootstrap(args):
    root = repository(args.repo)
    m = manifest(root)
    if not m:
        raise Conflict('Installation provenance missing; perform one-time adoption first')
    if not REQUIRED_ASSETS <= m['files'].keys():
        raise Conflict('Incomplete installed manifest; restore reviewed complete adoption')
    dependency_policy(root, m)
    expected = {name: h for name, h in m['files'].items() if shared(name)}
    # Reject project/managed edits before any fetch or dependency writes.
    for name, h in m['files'].items():
        if not shared(name):
            p = safe(root, name)
            if not p.is_file() or digest(p.read_bytes()) != h:
                raise Conflict('Missing/modified project asset preserved: ' + name)
    instructions = safe(root, 'AGENTS.md')
    current = block(instructions.read_text()) if instructions.is_file() else None
    if not current or digest(current.encode()) != m['agents_block_hash']:
        raise Conflict('Managed AGENTS block modified or missing')
    missing = []
    for name, h in expected.items():
        p = safe(root, name)
        if not p.exists() and m['schema_version'] == 4:
            missing.append(name)
        elif not p.is_file() or digest(p.read_bytes()) != h:
            raise Conflict('Missing/modified skill preserved: ' + name +
                           '; restore reviewed bytes or perform explicit setup/update')

    def resolve(source):
        version, assets = source_bundle(source, m['source_revision'])
        skills = {name: digest(data) for name, data in assets.items() if shared(name)}
        if version != m['bundle_version'] or skills != expected:
            raise Conflict('Pinned source skill bytes differ from provenance hashes')
        return {name: assets[name] for name in missing}

    if args.source:
        changes = resolve(args.source)
    elif missing:
        with tempfile.TemporaryDirectory(prefix='wf2-pinned-source-') as folder:
            source = pathlib.Path(folder)
            git(source, 'init', '--quiet')
            git(source, 'fetch', '--no-tags', '--depth=1', m['source_url'], m['source_revision'])
            git(source, 'checkout', '--detach', '--quiet', m['source_revision'])
            changes = resolve(source)
    else:
        changes = {}  # Complete matching installations are offline no-ops.
    if args.apply:
        transaction(root, changes)
    return list(changes)
