# Ingredient catalog

This implements the [ingredient-catalog design](design.md#ingredient-catalog) only.
Recipes/planning/shopping export and the dietary-policy decision remain separate Issues.
Runtime: Python >=3.10, standard library; no network, Conda, Node or global skills.

```sh
python3 -m app.catalog --file /tmp/pantry-example.json add oats 500
python3 -m app.catalog --file /tmp/pantry-example.json add lentils 300
python3 -m app.catalog --file /tmp/pantry-example.json show
```

For a fresh example file the last command prints `{"lentils": 300, "oats": 500}`.
Use a new file for each rerun: add rejects existing IDs rather than updating them.
`--file` defaults to pantry.json in the current directory. Relative and absolute
paths are supported; the parent must exist and symlink targets are rejected.
Show on a missing file returns {} without creating it. A valid empty object is allowed.

Catalog JSON maps nonempty case-sensitive ingredient IDs to nonnegative integer grams.
Zero is valid; booleans/floats/negative values, duplicate IDs and malformed data fail.
CLI input/type errors exit 2; data/path/operation errors exit 1 with an actionable
stderr explanation. Show and successful add print the complete sorted JSON object.
A failed add leaves the original bytes unchanged. Writes use a same-directory staged
file and atomic replacement; existing file mode is preserved, new files use private
temporary-file permissions. Permission and replacement errors are surfaced, with
staging cleaned. There is no concurrent-writer lock or crash-durable directory fsync;
this bounded single-writer pilot is not a multi-user database.

Run configured local verification:
`python3 tools/workflow/workflow.py check --repo . --run-local --json`.
On the required Ubuntu environment, also run `check --repo . --run-integration --json`
and record actual OS/Python/branch/SHA. CI runs local application tests plus workflow
integrity; it does not establish merge protection or automatic host skill discovery.
