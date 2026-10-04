# Workflow development

Python >=3.10 and Git run the installed utilities without Conda or global skills.
Run `python3 tools/workflow/workflow.py check --repo .` for bundle/config/link
checks, and the application verification commands declared in .workflow/config.json.
The generated default checks only the workflow bundle; add real application test
commands before accepting application delivery. Arguments are arrays, never shell
strings. Node/OpenSpec are optional until a relevant spec check is required.

Setup also installs workflow-v2-verify.yml and workflow-v2-pr-metadata.yml under
.github/workflows/. Verification runs on push/PR head changes, using the declared
local argv commands and mechanical checks. Python 3.12 runs workflow utilities;
project runtimes/dependency preparation belong in reviewed application commands
(e.g. a repository script invoked by an argv array), or an explicitly reviewed
workflow customization. Missing prerequisites fail rather than selecting another
runtime. Default config proves only workflow integrity, not application acceptance.
Required integration commands are run separately in their intended environment;
they are not assumed safe for the generic Ubuntu job.

Trusted-base PR metadata runs on body/head changes with read-only permissions and
never executes head code or config commands. It becomes active only after adoption
onto the base branch. Setup installs files but does not enable Actions, change rulesets
or configure branch protection. An authorized administrator must observe check
contexts and require v2 verification/v2 PR contract where appropriate, then read back
settings and observe blocking. Merge protection and skill discovery remain separate
acceptance. Existing workflow name collisions are conflicts; modified owned workflows
are preserved on update/uninstall. No closure/phase bot is installed.

## Cloud and Ubuntu preparation

From the checked-out consumer root, run before the agent starts/discovers skills:

```sh
python3 tools/workflow/workflow.py bootstrap --repo . --apply --json
python3 tools/workflow/workflow.py check --repo . --run-local --json
python3 tools/workflow/workflow.py doctor --repo . --json
```

Use the tracked manifest's exact source pin on both hosts. Repeated bootstrap is a
no-op when bytes match, preserves project-owned tracked files, and never fetches
main/latest or installs globally. Preparation/maintenance hook ordering and fresh
host discovery require real host evidence; a start-of-task instruction alone does
not establish pre-discovery installation. See [operations](operations.md) for scoped
ignores, offline bootstrap, old tracked-file migration and safe conflict recovery.
The generic CI job bootstraps the same pin before verification. Trusted-base metadata
continues to read PR data without executing head code or requiring head skill files.
