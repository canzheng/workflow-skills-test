# Workflow documentation

Read [the contract](contract.md), [development](development.md) and
[operations](operations.md). This repository's own design, current specs and
architecture remain user-owned. GitHub owns delivery records; historical
planning directories cannot activate obsolete wrappers.

For a new project, supply the existing design and say "Create the initial backlog
from this design" or "Create the MVP backlog from the current design". The design
skill prepares the whole selected release as one coherent Issue batch, with design
section links and explicit dependencies. Approve the batch once to make eligible
work Ready; readiness approval alone never starts implementation. Ask to execute
separately. Keep later scope and unresolved choices bounded; no per-capability calls,
engineering-task Issue explosion or duplicate backlog document is required.

Project policy/config, CI/templates, docs/specs and project-specific skills remain
tracked. The three shared workflow skills are ignored repo-local dependencies;
`.workflow/install-manifest.json` tracks their exact source revision and hashes.
Run the [pinned bootstrap](operations.md) during environment preparation before
agent discovery. Cloud and Ubuntu use the same tracked pin; the environment is not
a separate version source.
