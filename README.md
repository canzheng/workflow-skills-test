# workflow-skills-test
test repo for workflow-skills


## Consumer workflow pilot
[Project design](docs/design.md) is the intent source. The pinned workflow bundle
is repository-local; read [its contract](docs/workflow/contract.md) and
[consumer guidance](docs/workflow/README.md). GitHub owns live Issue status.
Initial setup/CI proves workflow integrity; application verification is added with
the ingredient-catalog implementation PR. No global skill install or Conda needed.

Cloud environment preparation/task-start verification:
```sh
python3 --version
git --version
python3 tools/workflow/workflow.py check --repo . --run-local --json
```
Requires Python >=3.10 and Git. No Node/OpenSpec needed for this bounded CLI pilot.
Actual skill discovery requires a fresh Codex Cloud task, not merely these checks.
