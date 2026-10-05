# Workflow operations

## Adoption and updates

Use an explicit workflow-skills checkout, full commit SHA and target Git root.
Preview `setup --source /pinned/source --revision FULL_SHA --target . --repository owner/repo`;
`--apply` performs the bounded adoption/update. The source-owned environment entrypoint
can adopt a fresh repository without existing tools or a first commit. See the source
README for its exact pinned fetch-and-run command. It is not copied into the consumer.

Setup installs all three shared skills and risk references as commit-ready files in
`.agents/skills/`, alongside utilities, policy/config, CI/templates and docs. Review
and commit these files and `.workflow/install-manifest.json`. Schema 3 records
`skill_storage: tracked`, source URL/full SHA, bundle version and managed hashes;
this is provenance, not task state. Shared and project-specific skills must be
trackable. No shared-skill ignore entries are added. Setup never stages or commits.

Repeated identical setup is a no-op. Explicit updates require unmodified managed
bytes/instruction blocks, verify canonical source objects and change the source pin
only in the reviewed diff. Configuration remains project-owned. Modified files,
unmanaged collisions, symlinks and unsafe targets fail before writes. Failed apply
restores originals or reports recoverable residuals. No main/latest/global fallback.

## Migrate an ignored-skill adoption

Use the new source's setup dry-run/apply, not the old installed helper. For schema 2,
setup verifies the old owned ignore-block hash and removes only that block, preserving
other rules, project skills/config and the index. Missing ignored assets may be
installed during this explicit update; modified assets or ignore blocks conflict.
Broader/nested/global/info excludes that still hide any shared/project skills also
conflict before writes. Resolve those rules deliberately; never force-add around them.
Schema-1 tracked adopters can update without untracking their skills.

Review the migration, stage the three shared directories and all owned adoption
changes, then commit. Startup/check/doctor cannot certify an indexed manifest with
untracked shared assets. Initial unstaged adoption is reviewable before staging,
but cannot establish a committed checkout or initial host discovery.

## Repeatable environment verification

An adopted consumer carries its skills in Git. A fresh clone must contain them before
an agent starts; environment setup does not inject them. From the consumer root:

```sh
python3 tools/workflow/workflow.py check --repo . --run-local --json
python3 tools/workflow/workflow.py doctor --repo . --json
git --no-optional-locks status --short --untracked-files=all
```

These commands need no workflow-source fetch. Existing `bootstrap --apply` callers
are supported as read-only verification of schema-3 shared assets; it never downloads,
repairs, updates the pin or changes the index. Optional `--source /pinned/source`
compares canonical source bytes offline. Missing/modified/extra/symlinked/untracked
assets fail: restore the reviewed Git checkout or perform an explicit setup/update.
Old schema-1/2 adoptions require reviewed setup before using new startup verification.
The source-owned environment entrypoint also rejects missing config/wrong identity
before writes and retains the installed pin on repeat, even with a newer entrypoint.

Require exit0/ok:true; do not equate this with application acceptance or host discovery.
The default config checks workflow integrity only. Add actual application commands
when code exists. Consumer CI checks the committed skills directly after checkout,
then runs declared local commands and mechanical checks. No bootstrap fetch is needed.

For Cloud/Ubuntu, confirm selected branch/SHA, committed manifest/skill bytes and
actual initial host catalog. A skill's disk presence, explicit file read or a green
CI job does not prove automatic discovery. Capture configured host cwd/project root
separately from shell cwd; do not move skills outside the repo or install globally.

Uninstall removes only unmodified managed assets/instruction blocks and retains
modified residuals and project config. It never changes the index or repository
administration. Doctor reports absent optional tools and unprobed capabilities honestly.
