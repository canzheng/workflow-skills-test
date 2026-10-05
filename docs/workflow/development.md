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

Commit the reviewed adoption, including all three shared `.agents/skills/` directories,
risk references and the schema-3 provenance manifest. A fresh checkout has the skills
without network access, environment injection or global installation.

```sh
python3 tools/workflow/workflow.py check --repo . --run-local --json
python3 tools/workflow/workflow.py doctor --repo . --json
```

Both hosts and consumer CI verify the same committed snapshot and exact source pin.
Repeat verification is read-only; `bootstrap --apply` is also verification-only for
existing callers. Missing tracked files are errors, not permission to fetch/recreate
skills during startup. See [operations](operations.md) for one-time adoption, explicit
ignored-to-tracked migration and conflicts. Actual initial Cloud/Ubuntu catalog/use
and enforcement remain separate acceptance from Git/file/hash checks.
