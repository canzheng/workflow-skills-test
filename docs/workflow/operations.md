# Workflow operations

## One-time adoption and explicit updates

Use the source checkout at an exact full commit, explicit consumer Git root and
owner/name. Preview before apply:

```sh
python3 /pinned/source/tools/workflow/workflow.py setup --source /pinned/source --revision FULL_40_CHAR_SHA --target /absolute/consumer --repository owner/repo --json
```

Repeat with `--apply` for authorized adoption/update. Setup installs tracked project
policy/config/helpers/docs/CI/templates and materializes the three shared skill
directories as ignored dependencies. Schema-4 .workflow/install-manifest.json tracks
the full source commit, credential-free URL, asset hashes and owned ignore-block hash.
It is provenance, not task state. Only these anchored root rules are added:

```gitignore
# workflow-v2-dependency:start
/.agents/skills/workflow-design-to-backlog/
/.agents/skills/workflow-deliver-issue/
/.agents/skills/workflow-risk-review/
# workflow-v2-dependency:end
```

Project skills remain trackable. Never ignore all of .agents or force-add shared
files around this policy. Existing unrelated rules/config/skills are preserved.
Modified managed bytes or instruction/ignore blocks, unmanaged collisions, unsafe
paths and symlinks conflict before writes. Multi-file apply stages backups and
restores only unchanged installer writes on failure. Concurrent edits, deletions,
permission changes or symlink replacements are preserved and reported as recoverable
residuals with original backups. Newly created directories are removed only when
their inode/mode still match and they remain empty; changed directories are retained
and reported with creation metadata in recovery-index.json. Staging files are created exclusively, with writes/permissions bound to the opened
file descriptor. A symlink introduced at creation is rejected without writing its
external target. Cleanup removes only unchanged installer staging files; changed
bytes/modes/replacements or symlinks remain residuals with staging creation metadata.
This is best-effort
recovery, not a multi-process
lock or an atomic multi-file transaction. Review residuals before retrying. Setup never stages/commits or changes repository administration.

Fresh ignored adoption rejects shared namespaces present in the Git index, including
deleted working copies and indexed files at a namespace root, before preview/apply.
An existing schema-4 update preflights dependency/index policy before any writes.
Force-tracked shared files, incomplete project staging or invalid staged policy are
conflicts preserving files/manifest/raw index. Resolve the reviewed index conflict
explicitly; setup never untracks a file for you. Schema-3 migration below remains
an explicit storage change, distinct from updating an already ignored adoption.

Plain-text diagnostics escape characters unsupported by the output encoding rather
than raising a traceback. JSON keeps its standard escaped representation. This also
applies to malformed/untrusted PR links; neither output mode executes PR content.

## Migrate a tracked adoption

Existing schema-3 snapshots remain verifiable. Use the new source's setup preview
and explicit apply to migrate to schema 4, preserving the index. Then review and
untrack only the shared directories without deleting working files:

```sh
git rm --cached -r -- .agents/skills/workflow-design-to-backlog .agents/skills/workflow-deliver-issue .agents/skills/workflow-risk-review
```

This is a caller-authorized Git change, not an installer side effect. Stage reviewed
project/provenance/.gitignore changes and commit. Until untracking/staging is complete,
checks can fail because the working adoption and staged commit are inconsistent.
Old schema-1/2 consumers also require explicit reviewed setup; startup does not migrate.
`--skill-storage tracked` preserves schema-3 behavior for compatibility, not the default.

All non-shared manifest assets, provenance/config, AGENTS and .gitignore must remain
indexed after any adoption is staged/committed. Removing provenance cannot bypass
verification. Canonical staged hashes, schemas, configured docs and instruction/ignore
blocks must agree with regular files/no merge stages; good working bytes cannot hide
broken staged content. Applicable nested ignore rules and new project-skill paths
come from the same index snapshot, never from restored/missing working-tree copies.
Valid differing project rules are preserved. Shared files must be absent from the index. Checks preserve
both snapshots and never repair/stage. Initial completely unstaged adoption is
reviewable only with trackable project files; commit it before host acceptance.

## Bootstrap before Ubuntu Codex startup

From the exact consumer Git root, before starting a fresh agent:

```sh
python3 tools/workflow/workflow.py bootstrap --repo . --apply --json
python3 tools/workflow/workflow.py check --repo . --run-local --json
python3 tools/workflow/workflow.py doctor --repo . --json
git --no-optional-locks status --short --untracked-files=all
```

Bootstrap fetches only the manifest's full commit when ignored files are missing,
verifies canonical pinned skill bytes/hashes and writes only missing shared files.
`--source /pinned/source` permits offline materialization. Omit --apply to preview;
preview may fetch source into a temporary directory but does not change the consumer.
A complete matching rerun is offline and returns changes:[]. Modified/extra/symlinked
skills, policy/project edits, wrong source or unavailable pins fail without overwrite
or main/latest fallback. Project files/pin/index remain unchanged. Schema-3 compatibility
bootstrap verifies only and never recreates missing tracked files.

Require exit0/ok:true; default local config proves workflow integrity, not application
acceptance. Application argv arrays run with shell disabled; required integration
commands run only in their intended environment. Empty integration arrays are not
an environmental pass. Missing runtimes fail without selecting another interpreter.

Consumer verification CI performs the same exact-pin bootstrap before configured
local commands/mechanical checks. Trusted-base metadata treats PR content as data;
base adoption and observed required-check enforcement remain separate from YAML
installation. Setup never configures protections or performs merge/Issue closure.

## Optional global shared-skills installation

Explicit source-owned `install-skills` defaults to ~/.agents/skills; --target chooses
an absolute alternate skills root. It installs only three skills/references plus
.workflow-skills-install.json provenance, never AGENTS/project config/helpers.
Preview, then repeat with --apply:

```sh
python3 /pinned/source/tools/workflow/workflow.py install-skills --source /pinned/source --revision FULL_40_CHAR_SHA --json
```

Reruns are no-ops; updates preserve edited/unmanaged skills and unrelated names.
`install-skills --uninstall --apply` removes only unmodified owned files and reports
modified residuals. No repository setup/bootstrap implicitly writes global skills.
Use one active discovery location per name; doctor reports duplicates rather than
assuming repo-local precedence. A global skill resolves documents/policy from the
selected project, not a global docs tree. Global installation alone does not adopt
project policy or satisfy the repo-local dependency checks; test its host catalog/use
separately in a project without local shared copies. Do not change authentication.

## Recovery and evidence

Uninstall via setup --target /absolute/consumer --uninstall --apply removes only
unmodified owned assets/blocks and preserves project config and modified residuals.
It never changes the index. Rollback residuals include a recovery-index.json mapping
original paths to backup bytes/modes (null means newly created). Resolve deliberately.
Return codes: 0 success, 1 conflict/failed check, 2 invalid invocation/configuration.
Doctor is read-only; inaccessible host catalogs and unperformed remote capabilities
remain unprobed. Record consumer/source SHAs, OS/runtime, initial catalog and actual
skill use independently. A file/hash check, explicit file reading or green CI alone
cannot establish automatic discovery, semantic review, merge or delivery.

Doctor reports an unreadable/undecodable discovery file as a per-file warning and
continues scanning other entries, including duplicate-name checks. It preserves
the file; this filesystem scan does not prove native host discovery. Invalid UTF-8
project text is a structured invalid-input error, not permission to rewrite it.
