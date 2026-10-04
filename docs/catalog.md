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

Catalog files use UTF-8 JSON, independent of process locale, mapping nonempty
case-sensitive ingredient IDs to nonnegative integer grams.
CLI identifier arguments use UTF-8; raw argument bytes are recovered through the
OS filesystem encoding before decoding as text, including under an ASCII locale.
Invalid UTF-8 identifiers fail without changing data. Direct Python calls accept text.
Zero is valid; booleans/floats/negative values, duplicate IDs and malformed data fail.
Excessively nested JSON is rejected with flat-schema guidance and no traceback;
show/add leave that invalid file unchanged. Schema validation rejects arrays and
nested ingredient amounts even on Python versions whose JSON decoder accepts deep nesting.
CLI input/type errors exit 2; data/path/operation errors exit 1 with an actionable
stderr explanation. Show and successful add print the complete sorted JSON object.
Validation and pre-replacement storage failures leave the original bytes unchanged.
The successful replacement commits the data before result output. If stdout fails
(for example a closed pipe), add may exit nonzero after committing; use show to
check the catalog before retrying rather than assuming rollback.
Writes use a same-directory staged
file and atomic replacement; existing file mode is preserved, new files use private
temporary-file permissions. Permission and replacement errors are surfaced, with
best-effort staging cleanup. If permissions prevent cleanup, the error reports both
the original failure and cleanup failure, including the staged path. After restoring
permissions, inspect the catalog and remove that reported `.pantry-*` residue;
do not treat it as committed data. There is no concurrent-writer lock or crash-durable directory fsync;
this bounded single-writer pilot is not a multi-user database.

Run configured local verification:
`python3 tools/workflow/workflow.py check --repo . --run-local --json`.
On the required Ubuntu environment, also run `check --repo . --run-integration --json`
and record actual OS/Python/branch/SHA. CI runs local application tests plus workflow
integrity; it does not establish merge protection or automatic host skill discovery.
