# workflow-skills-test
test repo for workflow-skills


## Consumer workflow pilot
[Project design](docs/design.md) is the intent source. The pinned workflow bundle
is repository-local; read [its contract](docs/workflow/contract.md) and
[consumer guidance](docs/workflow/README.md). GitHub owns live Issue status.
Initial setup/CI proves workflow integrity; application verification is added with
the ingredient-catalog implementation PR. No global skill install or Conda needed.

Cloud and local environment setup use the source-owned fetch-and-run entrypoint in
[workflow-skills README](https://github.com/canzheng/workflow-skills/blob/rewrite/workflow-skills-v2/README.md).
Fetch source `10ff9cc807a54aa0834d24de82e0b685048379de` and run its
`tools/workflow/environment-setup.sh` against
this consumer Git root and `canzheng/workflow-skills-test`. No setup script is copied
into this repository. Existing adoption retains its tracked manifest pin; setup
materializes only the three ignored shared skills and leaves project policy/index
alone. Project-specific skills remain trackable. Review/commit generated policy
when adopting a new repository; no merge or administrative action occurs.

Python >=3.10, Bash, Git and HTTPS source read access are required. This workflow-only
branch has no application implementation: integrity checks do not establish application
acceptance. Fresh pre-agent Cloud/Ubuntu discovery remains a separate observed gate.
See [operations](docs/workflow/operations.md) for migration/conflict recovery.
