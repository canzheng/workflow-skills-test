# Workflow operations

Use a pinned workflow-skills source checkout and its setup command with explicit
source, full revision, target and repository. Dry-run first, `--apply` performs
installation/update. Modified managed files conflict; configuration is user-owned.
Doctor is read-only: `python3 tools/workflow/workflow.py doctor --repo . --json`.
Uninstall: `python3 tools/workflow/workflow.py setup --target . --uninstall --apply`.
Only unmodified files/block are removed; modified residuals and config remain.
Partial apply restores originals or identifies recoverable residuals. Never use
missing-target fallback or silently overwrite human modifications.
