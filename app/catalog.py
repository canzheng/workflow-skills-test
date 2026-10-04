"""Store and retrieve validated integer-gram ingredient entries."""
import argparse
import json
import os
import pathlib
import tempfile


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate ingredient IDs in catalog')
        result[key] = value
    return result


def validate(catalog):
    if not isinstance(catalog, dict):
        raise ValueError('Catalog must be a JSON object')
    for identifier, grams in catalog.items():
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError('Ingredient ID must be nonempty text')
        if type(grams) is not int or grams < 0:
            raise ValueError('Ingredient grams must be a nonnegative integer')
    return catalog


def target_path(value):
    path = pathlib.Path(value).absolute()
    if any(p.is_symlink() for p in [path, *path.parents]):
        raise ValueError('Symlink catalog targets are not supported')
    if not path.parent.is_dir():
        raise ValueError('Catalog parent directory is missing')
    return path


def load(path):
    if not path.exists():
        return {}
    return validate(json.loads(path.read_text(), object_pairs_hook=unique_object))


def add(path, identifier, grams):
    validate({identifier: grams})
    catalog = load(path)
    if identifier in catalog:
        raise ValueError('Ingredient ID already exists')
    catalog[identifier] = grams
    staged = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, prefix='.pantry-', delete=False) as stream:
            staged = pathlib.Path(stream.name)
            stream.write(json.dumps(catalog, sort_keys=True) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            os.chmod(staged, path.stat().st_mode)
        os.replace(staged, path)
    except BaseException as error:
        if staged is not None:
            try:
                staged.unlink(missing_ok=True)
            except OSError as cleanup_error:
                raise OSError(f'{error}; staging cleanup failed for {staged}: {cleanup_error}') from error
        raise
    return catalog


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file', default='pantry.json', help='Catalog path (default pantry.json)')
    commands = parser.add_subparsers(dest='operation', required=True)
    commands.add_parser('show', help='Retrieve the complete catalog')
    create = commands.add_parser('add', help='Add a unique ingredient ID')
    create.add_argument('identifier')
    create.add_argument('grams', type=int)
    args = parser.parse_args(argv)
    try:
        path = target_path(args.file)
        catalog = add(path, args.identifier, args.grams) if args.operation == 'add' else load(path)
        print(json.dumps(catalog, sort_keys=True), flush=True)
        return 0
    except (ValueError, OSError) as exc:
        parser.exit(1, 'Error: ' + str(exc) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
