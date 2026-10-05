# workflow-skills-test
test repo for workflow-skills


## Consumer workflow pilot
[Project design](docs/design.md) is the intent source. The pinned workflow bundle
is repository-local; read [its contract](docs/workflow/contract.md) and
[consumer guidance](docs/workflow/README.md). GitHub owns live Issue status.
Initial setup/CI proves workflow integrity; application verification is added with
the ingredient-catalog implementation PR. No global skill install or Conda needed.

The three shared skill directories/references are ignored pinned dependencies.
Project policy/config/helpers/CI/docs/project skills and schema-4 provenance are
tracked in Git. Source pin: `b444021557d1a67f2a2e04deb6bc4d87f2772bd5`. Source-authored skills remain tracked.
[Setup instructions](https://github.com/canzheng/workflow-skills/blob/b444021557d1a67f2a2e04deb6bc4d87f2772bd5/README.md)
distinguish first adoption, explicit updates and repeatable bootstrap. Only shared
workflow directories are ignored; pantry-project remains tracked. Setup never stages,
commits or silently migrates a tracked installation.

For Ubuntu, bootstrap before starting Codex from this repository root:

```sh
python3 tools/workflow/workflow.py bootstrap --repo . --apply --json
python3 tools/workflow/workflow.py check --repo . --run-local --json
python3 tools/workflow/workflow.py doctor --repo . --json
git --no-optional-locks status --short --untracked-files=all
codex
```

Bootstrap materializes only missing ignored skills from the exact pin; complete
matching reruns are offline/no-op, preserving project files/pin/index. Modified,
extra or symlinked dependency bytes conflict without overwrite or latest fallback.
Python >=3.10 and Git are required. This workflow-only branch has no application
implementation; workflow checks do not establish application acceptance.

Ubuntu fresh native discovery and actual skill use are separate evidence gates.
Cloud environment/discovery investigation is deferred by user approval. Optional
explicit shared-skills-only global install is source-owned; it is never performed
implicitly here. Test global and repo-local discovery separately to avoid duplicates.
See [operations](docs/workflow/operations.md) for migration/conflicts and the
[original Ubuntu workstation evidence](https://github.com/canzheng/workflow-skills/blob/b444021557d1a67f2a2e04deb6bc4d87f2772bd5/docs/validation/ubuntu-workstation-session.md).
No merge, completed Issue closure, administration or global changes occur here.

The original workstation session verified startup discovery and actual v2 use at
consumer9bd23d72/sourcea75c3f2. This reviewed runtime repair leaves all four shared
file hashes unchanged. Current exact update/CI/review evidence belongs to Issue #7
and PR #8; original evidence retains its original revisions. Existing schema-4 setup
updates now refuse invalid dependency/index policy before writes, and staged nested
ignore rules/project skills are validated from the index snapshot.

Rollback restores only unchanged installer writes. Concurrent edits, deletions,
permission changes and symlink replacements remain recoverable residuals with
original backups. See the operations recovery guidance; this is best-effort recovery.
