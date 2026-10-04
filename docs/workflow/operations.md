# Workflow operations

Use a pinned workflow-skills source checkout and its setup command with explicit
source, full revision, target and repository. Dry-run first, `--apply` performs
installation/update. Modified managed files conflict; configuration is user-owned.
Doctor is read-only: `python3 tools/workflow/workflow.py doctor --repo . --json`.
Uninstall: `python3 tools/workflow/workflow.py setup --target . --uninstall --apply`.
Only unmodified files/block are removed; modified residuals and config remain.
Partial apply restores originals or identifies recoverable residuals. Never use
missing-target fallback or silently overwrite human modifications.

## Pinned shared-skill bootstrap

One-time adoption writes project-owned config, utilities, CI/templates, the managed
AGENTS block and a tracked schema-2 `.workflow/install-manifest.json`. That manifest
is the dependency pin: full source SHA, credential-free HTTPS GitHub source URL and
asset hashes. Shared skills remain tracked in the workflow-skills source repository;
consumers materialize them locally and ignore exactly these directories:

```gitignore
/.agents/skills/workflow-design-to-backlog/
/.agents/skills/workflow-deliver-issue/
/.agents/skills/workflow-risk-review/
```

Project-specific skills stay trackable. Setup adds/owns this delimited ignore block,
preserving other rules, and materializes the dependency initially. Repeating setup
with the same inputs returns no changes. It does not silently configure GitHub
administration or edit the Git index. Fork adoption may explicitly supply
`--source-url https://github.com/OWNER/REPO.git`; the default source is
`https://github.com/canzheng/workflow-skills.git`.

For an existing adoption with tracked shared skills, review their managed hashes and
any human changes first, then explicitly untrack only these paths, preserving bytes:

```sh
git rm --cached -r -- .agents/skills/workflow-design-to-backlog .agents/skills/workflow-deliver-issue .agents/skills/workflow-risk-review
```

Run the new pinned setup dry-run/apply and commit the reviewed migration. An ignore
rule alone cannot untrack files. Setup refuses tracked shared skills, unmanaged
collisions and modified managed bytes rather than silently discarding them.

Repeatable Cloud/Ubuntu environment preparation, from the consumer root:

```sh
python3 tools/workflow/workflow.py bootstrap --repo . --apply --json
python3 tools/workflow/workflow.py check --repo . --run-local --json
python3 tools/workflow/workflow.py doctor --repo . --json
```

Bootstrap reads the tracked pin; no source version belongs in environment settings.
If files already match it, rerunning needs no network and returns `changes: []`.
Otherwise Python >=3.10, Git and Git HTTPS read access to the pinned source are
required. It fetches the full commit into a temporary checkout, verifies source and
skill hashes, then materializes only those ignored namespaces. `--source /exact/pinned/checkout`
provides an explicit offline source; omitting `--apply` previews missing assets.
It never changes config, docs, policy, pin or index. Modified/extra/symlinked shared
assets, missing ignore policy, source/hash mismatch and denied fetch fail safely;
resolve the reported conflict deliberately before retrying. Downloaded source code
is not executed. Only explicit setup/update changes the pin; bootstrap never upgrades.

Configure the host's preparation/maintenance hook to run these commands after the
consumer checkout and before agent skill discovery. Publishing a setup script or
running it from an already-started agent does not prove fresh host discovery. Recheck
after branch/pin changes and record consumer/source SHAs and the actual tested host
profile. Uninstall removes the owned ignore block only when unchanged and no modified
shared asset remains; retained modifications remain ignored and reported as residuals.

Effective Git ignore policy is checked before adoption/update writes and during
bootstrap/check/doctor, including nested/global/info excludes. Broad project-skill
ignores or negations exposing shared dependencies conflict even with an unchanged
managed block. Narrow the offending rule deliberately; unrelated rules are preserved.

Missing installed runtime modules fail bundle preflight. Extra ignored shared assets
also mark dependency identity dirty, even when ordinary Git status is clean.
