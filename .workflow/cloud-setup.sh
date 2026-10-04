#!/usr/bin/env bash
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
