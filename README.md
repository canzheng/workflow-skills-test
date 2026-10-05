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
tracked in Git. Source pin: `a75c3f20e5f4032568b1d1a5cb17d001fc781918`. Source-authored skills remain tracked.
[Setup instructions](https://github.com/canzheng/workflow-skills/blob/a75c3f20e5f4032568b1d1a5cb17d001fc781918/README.md)
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
[source Ubuntu handoff](https://github.com/canzheng/workflow-skills/blob/rewrite/workflow-skills-v2/docs/validation/ubuntu-workstation-handoff.md).
No merge, completed Issue closure, administration or global changes occur here.
