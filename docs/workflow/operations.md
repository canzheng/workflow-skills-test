# Operations

## One-time adoption and explicit updates

Use the source checkout at an exact full commit, explicit consumer Git root and
owner/name. Preview before apply:

```sh
python3 /pinned/source/tools/workflow/workflow.py setup --source /pinned/source --revision FULL_40_CHAR_SHA --target /absolute/consumer --repository owner/repo --json
```

Repeat with `--apply` for authorized adoption/update. Setup installs tracked project
policy/config/docs/CI/templates and materializes shared skills plus the Python
runtime as ignored dependencies. Schema-5 .workflow/install-manifest.json tracks
the full source commit, credential-free URL, asset hashes and owned ignore-block hash.
It is provenance, not task state. Only these anchored root rules are added:

```gitignore
# workflow-v2-dependency:start
/.agents/skills/workflow-design-to-backlog/
/.agents/skills/workflow-deliver-issue/
/.agents/skills/workflow-risk-review/
/.agents/tools/workflow/
# workflow-v2-dependency:end
```

Project skills/tools remain trackable. Never ignore all of .agents or force-add shared
files around this policy. Existing unrelated rules/config/skills are preserved.
Modified managed bytes or instruction/ignore blocks, unmanaged collisions, unsafe
paths and symlinks conflict before writes. Initial adoption also rejects destinations
owned by the Git index or HEAD, including deleted working copies and deleted policy
files and file/gitlink ancestors of every destination; it never recreates an
unrelated deletion or repurposes a deleted indexed file as a directory. Multi-file apply stages backups and
restores only unchanged installer writes on failure. Concurrent edits, deletions,
permission changes or symlink replacements are preserved and reported as recoverable
residuals with original backups. Newly created directories are removed only when
their inode/mode still match and they remain empty; changed directories are retained
and reported with creation metadata in recovery-index.json. Staging files are created exclusively, with writes/permissions bound to the opened
file descriptor. A symlink introduced at creation is rejected without writing its
external target. Cleanup removes only unchanged installer staging files; changed
bytes/modes/replacements or symlinks remain residuals with staging creation metadata.
Replacement and rollback use Linux renameat2: existing entries are exchanged
with staged files so the actual displaced bytes/mode/inode can be checked;
absent destinations require atomic no-replace. Rollback stages originals instead
of opening/truncating a live destination. Deletion first captures the actual entry
under a reserved .wf2-removed name, validates it and restores a mismatched entry
when the destination remains absent. Concurrent entries remain at their original
path or are reported as recovery residuals. Unsupported atomic operations fail;
there is no ordinary overwrite fallback. .wf2-staged, .wf2-restore and .wf2-removed
collisions require manual review. A displaced inode edited during cleanup is copied
to a concurrent_backup with concurrent_mode in recovery-index.json; inspect these
alongside original backups before retrying. This is best-effort recovery, not a
multi-process lock or an atomic multi-file transaction. Review residuals before retrying. Setup never stages/commits or changes repository administration.

Fresh ignored adoption rejects shared namespaces present in the Git index, including
deleted working copies and indexed files at a namespace root, before preview/apply.
An existing schema-4/5 update preflights dependency/index policy before any writes.
Force-tracked shared files, incomplete project staging or invalid staged policy are
conflicts preserving files/manifest/raw index. Resolve the reviewed index conflict
explicitly; setup never untracks a file for you. Schema-3 migration below remains
an explicit storage change, distinct from updating an already ignored adoption.

Plain-text diagnostics escape characters unsupported by the output encoding rather
than raising a traceback. JSON keeps its standard escaped representation. This also
applies to malformed/untrusted PR links; neither output mode executes PR content.

## Migrate a tracked adoption

Existing schema-3 snapshots remain verifiable. Use the new source's setup preview
and explicit apply to migrate to schema 5, preserving the index. Then review and
untrack only the dependency namespaces without deleting working files:

```sh
git rm --cached -r --ignore-unmatch -- .agents/skills/workflow-design-to-backlog .agents/skills/workflow-deliver-issue .agents/skills/workflow-risk-review .agents/tools/workflow
```

This is a caller-authorized Git change, not an installer side effect. Stage reviewed
project/provenance/.gitignore changes and commit. Older schema-3/4 consumers with
the runtime in tools/workflow instead review the installer's removal of those
owned files, stage those deletions, untrack any remaining shared skills, and
update only workflow CLI references in project-owned config/docs to the new path.
The command tolerates dependency paths already untracked or absent from older
layouts. Stage the owned legacy runtime deletions as well; an indexed old shared
Python file cannot pass a new-layout commit check. The seven canonical legacy
filenames are reserved in the new-layout index, while unrelated project tools
remain untouched. Bundles and provenance cannot mix old/new canonical runtimes. Then commit. Until untracking/staging is complete,
checks can fail because the working adoption and staged commit are inconsistent.
Old schema-1/2 consumers also require explicit reviewed setup; startup does not migrate.
`--dependency-storage tracked` (legacy alias `--skill-storage tracked`) preserves schema-3 behavior for compatibility, not the default.

All non-dependency manifest assets, provenance/config, AGENTS and .gitignore must remain
indexed after any adoption is staged/committed. Removing provenance cannot bypass
verification. Canonical staged hashes, schemas, configured docs and instruction/ignore
blocks must agree with regular files/no merge stages; good working bytes cannot hide
broken staged content. Applicable nested ignore rules and new project-skill paths
come from the same index snapshot, never from restored/missing working-tree copies.
Valid differing project rules are preserved. Shared files must be absent from the index. Checks preserve
both snapshots and never repair/stage. Newly staged policy/config or newly introduced managed routing/ignore blocks
count as adoption and require the complete commit candidate. Pre-existing human
policy alone does not. Initial completely unstaged adoption is
reviewable only with trackable project files; commit it before host acceptance.

## Bootstrap before Ubuntu Codex startup

From the exact consumer Git root, before starting a fresh agent:

```sh
python3 .agents/tools/workflow/workflow.py bootstrap --repo . --apply --json
python3 .agents/tools/workflow/workflow.py check --repo . --run-local --json
python3 .agents/tools/workflow/workflow.py doctor --repo . --json
git --no-optional-locks status --short --untracked-files=all
```

A fresh clone lacks both dependency directories. Fetch the tracked source URL/full
SHA and run its source-owned environment-setup.sh as documented in the source
README before running the commands above; never expect an absent consumer CLI to
bootstrap itself. The source entrypoint preserves existing pins and tracked files,
materializes missing dependency files, then runs the installed checker/doctor.

Bootstrap fetches only the manifest's full commit when ignored files are missing,
verifies canonical pinned skill bytes/hashes and writes only missing shared skill/runtime files.
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

The source-owned tools/workflow/environment-setup.sh can adopt a new Git root
without existing tools/first commit. Resolve its README and Ubuntu handoff from
the tracked manifest source_url/source_revision, never an implicit latest branch.
Cloud is optional/deferred for this release.

Doctor reports an unreadable/undecodable discovery file as a per-file warning and
continues scanning other entries, including duplicate-name checks. It preserves
the file; this filesystem scan does not prove native host discovery. Invalid UTF-8
project text is a structured invalid-input error, not permission to rewrite it.


Schema-5 ignored dependencies require the runtime at `.agents/tools/workflow/`.
Ignored setup from an old runtime-layout bundle fails before writes; existing
schema-3/4 pins remain supported and tracked legacy setup stays explicit. CI
selects consumer provenance before any unrelated `.workflow/bundle.json`, fetches
that exact pin, and verification chooses the runtime recorded in its manifest.
PR metadata makes the same selection from the trusted base checkout only.

Existing parent and ancestor directory identities are recorded before apply and
revalidated before writes and rollback. Apply deletion, staging/replacement/cleanup,
restoration and created-directory operations use verified directory descriptors
and relative names. Component-by-component no-follow opening binds each operation
to the recorded parent inode even if its pathname is swapped during the call.
A replaced namespace is reported as a recoverable residual; human files in its
replacement directory are preserved. This requires the supported POSIX/Ubuntu
directory-descriptor and no-follow operations. A missing deleted file is restored only
through its unchanged parent chain; replaced, missing or symlinked parents remain
recoverable residuals. Recovery records include expected parent directory devices
and inodes beside original file bytes/modes. Permission changes on the same parent
are preserved; created-directory cleanup retains its separate inode/mode checks.

After replacement, the destination bytes/mode/device/inode must match the staged
file identity. A swapped staging entry or a changed/missing destination is a
recoverable conflict, not successful setup. Foreign destination content is retained
and original bytes/mode are backed up for explicit recovery.
