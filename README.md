# workflow-skills-test
test repo for workflow-skills


## Consumer workflow pilot
[Project design](docs/design.md) is the intent source. The pinned workflow bundle
is repository-local; read [its contract](docs/workflow/contract.md) and
[consumer guidance](docs/workflow/README.md). GitHub owns live Issue status.
Initial setup/CI proves workflow integrity; application verification is added with
the ingredient-catalog implementation PR. No global skill install or Conda needed.

The shared skills and risk references are committed with schema-3 provenance in
`.workflow/install-manifest.json`, pinning source
`a4eb9f1303d80cc18f83b5bbd734063cac03b9c3`. Initial adoption or explicit update uses
that pinned source's [setup procedure](https://github.com/canzheng/workflow-skills/blob/a4eb9f1303d80cc18f83b5bbd734063cac03b9c3/README.md).
Review and commit generated skill/project files; setup never stages or commits.
Shared skills and pantry-project remain tracked and are not ignored. No source-owned
setup entrypoint is copied here.

For this already adopted consumer, Cloud's Install field and Ubuntu setup verify the
checkout directly, with no workflow-source fetch or skill injection:

```sh
set -eu
cd /workspace/workflow-skills-test
python3 tools/workflow/workflow.py check --repo . --run-local --json
python3 tools/workflow/workflow.py doctor --repo . --json
git --no-optional-locks status --short --untracked-files=all
```

Python >=3.10 and Git are required. Missing/modified/untracked skills fail rather than
being repaired at startup. This workflow-only branch has no application implementation:
integrity checks do not establish application acceptance. A fresh task must select the
reviewed consumer revision before initial discovery; older main does not test this
migration. Capture the host catalog before explicit skill reads. Fresh Cloud/Ubuntu
agent-host discovery remains a separate observed gate.

Published-environment creation currently exposes repository selection only in this
pilot's UI; no branch selector is documented for that flow. Fresh diagnostics on
older main found intact shared skills but no workflow entries in exposed catalogs,
including after environment recreation. That is a discovery blocker, not an installer
failure or proof that merging would fix it. Reading repo-local skill files explicitly
is available as a fallback; it does not pass automatic discovery acceptance. See
[operations](docs/workflow/operations.md) for explicit migration/conflict recovery.
No merge, Issue completion or administrative action is authorized.
