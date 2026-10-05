"""Verify tracked shared skills; environment startup never installs or repairs them."""
from core import Conflict, REQUIRED_ASSETS, dependency_policy, digest, manifest, repository, safe, shared
from setup import source_bundle


def bootstrap(args):
    root = repository(args.repo)
    m = manifest(root)
    if not m:
        raise Conflict('Installation provenance missing; perform one-time adoption first')
    if not REQUIRED_ASSETS <= m['files'].keys():
        raise Conflict('Incomplete installed manifest; restore reviewed complete adoption')
    dependency_policy(root, m)
    expected = {name: h for name, h in m['files'].items() if shared(name)}
    for name, h in expected.items():
        p = safe(root, name)
        if not p.is_file() or digest(p.read_bytes()) != h:
            raise Conflict('Missing/modified tracked skill preserved: ' + name +
                           '; restore the reviewed Git checkout or perform explicit setup/update')
    if args.source:
        version, assets = source_bundle(args.source, m['source_revision'])
        skills = {name: digest(data) for name, data in assets.items() if shared(name)}
        if version != m['bundle_version'] or skills != expected:
            raise Conflict('Pinned source skill bytes differ from tracked provenance hashes')
    # --apply remains accepted for existing callers, but never writes or fetches.
    return []
