# Workflow development

Python >=3.10 and Git run the installed utilities without Conda or global skills.
Run `python3 tools/workflow/workflow.py check --repo .` for bundle/config/link
checks, and the application verification commands declared in .workflow/config.json.
The generated default checks only the workflow bundle; add real application test
commands before accepting application delivery. Arguments are arrays, never shell
strings. Node/OpenSpec are optional until a relevant spec check is required.

Setup also installs workflow-v2-verify.yml and workflow-v2-pr-metadata.yml under
.github/workflows/. Verification runs on push/PR head changes, bootstraps the pinned shared skills, then uses the declared
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

## Ubuntu preparation

Commit project policy/config/helpers/CI/docs/project skills and schema-4 provenance.
The three shared directories/references are ignored, not committed. Bootstrap their
exact source pin before starting Codex from the repository root:

```sh
python3 tools/workflow/workflow.py bootstrap --repo . --apply --json
python3 tools/workflow/workflow.py check --repo . --run-local --json
python3 tools/workflow/workflow.py doctor --repo . --json
```

Fresh clones require source read access for missing dependency bytes; complete reruns
are offline/no-op and preserve project files/index. Consumer CI bootstraps that same
pin before verification. Modified dependencies fail without overwrite. See
[operations](operations.md) for explicit migration, conflicts and optional global
shared-skills-only installation. Capture initial native catalog separately from
actual use; files/hash checks do not prove either. Required Ubuntu discovery/use and
GitHub enforcement remain separate acceptance. Cloud discovery is deferred for this
first release; no published Cloud environment is needed for workstation use.
