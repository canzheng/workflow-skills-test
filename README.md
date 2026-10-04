# workflow-skills-test
test repo for workflow-skills


## Consumer workflow pilot
[Project design](docs/design.md) is the intent source. The pinned workflow bundle
is repository-local; read [its contract](docs/workflow/contract.md) and
[consumer guidance](docs/workflow/README.md). GitHub owns live Issue status.
Initial setup/CI proves workflow integrity; application verification is added with
the ingredient-catalog implementation PR. No global skill install or Conda needed.

Cloud environment setup/preparation (and maintenance, if the host offers it):
copy the complete command below into the environment configuration. It handles a
new Git repository without tools by fetching an exact seed/adopting once; an existing
tracked pin takes only bootstrap. For another project, set the explicit root and
owner/name inputs. Review/commit generated adoption files after the first run.

The same project-owned script is tracked as [.workflow/cloud-setup.sh](.workflow/cloud-setup.sh).
An adopted checkout can run `bash .workflow/cloud-setup.sh`; a brand-new repo must
paste the full command since it does not yet contain that file or tools/workflow.

```sh
set -eu
WF2_CONSUMER_ROOT=${WF2_CONSUMER_ROOT:-/workspace/workflow-skills-test}
WF2_CONSUMER_REPOSITORY=${WF2_CONSUMER_REPOSITORY:-canzheng/workflow-skills-test}
cd "$WF2_CONSUMER_ROOT"
python3 -c 'import sys; assert sys.version_info >= (3, 10), "Python >=3.10 is required"; print(sys.version.split()[0])'
git --version
if [ ! -f .workflow/install-manifest.json ]; then
    WF2_SOURCE_SHA=7e71186ec8146b682f4c4cf40c8da5ecb6d3f608
    WF2_SOURCE_DIR=$(mktemp -d)
    trap 'rm -rf -- "$WF2_SOURCE_DIR"' EXIT
    git -C "$WF2_SOURCE_DIR" init --quiet
    git -C "$WF2_SOURCE_DIR" fetch --no-tags --depth=1 https://github.com/canzheng/workflow-skills.git "$WF2_SOURCE_SHA"
    git -C "$WF2_SOURCE_DIR" checkout --detach --quiet "$WF2_SOURCE_SHA"
    python3 "$WF2_SOURCE_DIR/tools/workflow/workflow.py" setup --source "$WF2_SOURCE_DIR" --revision "$WF2_SOURCE_SHA" --target "$PWD" --repository "$WF2_CONSUMER_REPOSITORY" --json
    python3 "$WF2_SOURCE_DIR/tools/workflow/workflow.py" setup --source "$WF2_SOURCE_DIR" --revision "$WF2_SOURCE_SHA" --target "$PWD" --repository "$WF2_CONSUMER_REPOSITORY" --apply --json
fi
python3 -c 'import json, pathlib, sys; m=json.loads(pathlib.Path(".workflow/install-manifest.json").read_text(encoding="utf-8")); sys.exit(0 if m.get("schema_version")==2 else "Existing adoption needs reviewed dependency migration; do not overwrite it during environment setup")'
python3 tools/workflow/workflow.py bootstrap --repo . --apply --json
python3 tools/workflow/workflow.py check --repo . --run-local --json
python3 tools/workflow/workflow.py doctor --repo . --json
git status --short --untracked-files=all
```

Only the three shared skill directories are ignored; project skills remain tracked.
The first-adoption seed never overrides an existing tracked manifest's source pin.
No commits/index updates, merges or administrative changes occur during setup.
See [operations](docs/workflow/operations.md) for tracked-skill migration/conflicts.
Python >=3.10 and Git are required; no Node/OpenSpec/Conda/global installation is
needed for this workflow-only branch. It has no application implementation: default
verification proves workflow integrity, not application acceptance. Actual pre-agent
skill discovery and setup persistence/order require a fresh published Cloud task;
local/script checks alone do not certify them.
