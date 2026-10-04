<!-- workflow-v2:start -->
Bootstrap the pinned shared skills before starting the agent:
python3 tools/workflow/workflow.py bootstrap --repo . --apply --json
Use workflow-skills v2 from .agents/skills/. Read
docs/workflow/contract.md and docs/workflow/README.md.
Historical planning directories do not select v1. Never use obsolete
repository wrappers or global installation here. Preserve unrelated rules.
<!-- workflow-v2:end -->
