---
name: workflow-deliver-issue
description: Implement or resume an authorized GitHub Issue or bounded approved bootstrap feature, verify behavior, complete documentation and prepare a reviewable branch or PR. Use for ordinary features and small bugs without extra wrappers.
---

Read [the delivery contract](../../../docs/workflow/contract.md), which owns
scope, documentation, evidence and completion rules. Resolve exact assignment,
repository, checkout, branch/SHA, user authorization and relevant dependencies.
A missing/ambiguous worktree or branch is a blocker for that item, never permission
to choose the current directory. Preserve unrelated/uncommitted work. Read linked
design/specs, current architecture and relevant implementation before edits.

Inspect competing execution and record branch/session ownership when remote access
allows; re-read before starting. Comments/labels are not atomic locks. Stop only
conflicting work. No mandatory feature file, task lifecycle, per-task plan or
subagent pipeline. Persist a plan only for continuation; use a single OpenSpec-owned
plan for substantial behavior/migration/security/expensive ambiguity. A small clear
bug needs no new change directory. Keep existing specs accurate regardless.

Assess documentation at start: observable behavior/API/data -> current specs and
user guidance; component/data flow -> architecture; config/setup/recovery ->
development/operations and executable examples. Implement the smallest complete
approved outcome with meaningful tests, including denied/missing/interrupted paths
where relevant. Select workflow-risk-review for material risk and load only relevant
methods. Preserve original acceptance and strong fixtures; do not broaden expected
outputs or disable failures to pass. Raise actual contract changes explicitly.

Read .workflow/config.json and use its docs_index/contract and declared verification
argv arrays. Run applicable local commands with `check --run-local` or native argv
execution (no shell interpretation), and required integration commands only in the
intended environment. Run relevant checks on actual content. Record full revision, environment, command,
exit/result and passed/failed/skipped/pending requirements. Commit tested content
or bind dirty-tree evidence to a patch/content digest, then verify the final revision.
Material code/config changes invalidate affected evidence. Cloud local results
cannot certify required Ubuntu checks. Report required missing docs or verification
as unfinished, even when a PR exists.

Reassess final diff against docs: check defaults, errors, examples, limits and target
versus current wording. An internal repair may state no impact only when explanations
remain accurate. A random Markdown edit does not prove semantic consistency.
Prepare PR sections Assignment, Changes, Evidence, Documentation and Remaining,
including acceptance mapping, meaningful design deviations and exact next action.
When publication is available, open/update a draft PR for continuous deterministic
checks. After implementation, self-verification and final docs assessment, resolve
known blockers to review and mark the canonical PR Ready for Review, then update the
linked Issue to wf:review while preserving unrelated labels. Record the PR link.
Keep a draft PR's Issue wf:in-progress; conversion back to draft restores that phase.
Formal independent semantic/code review belongs on the Ready PR, with fixes and
required reruns there. Targeted risk methods during implementation are not another
mandatory independent pre-PR reviewer pipeline. Pending required environment evidence
remains explicit and can block delivery without blocking a useful review.
A significant multi-PR change has a closing owner; partial PRs neither archive
pending scope nor close the parent. Final archive/current specs accompany delivery.

Remote writes use native tools/gh within authorization. Search open/closed source
identities before creation, reconcile timeouts before retry, preserve human prose
and unrelated labels with read/compare/update. No write access: continue authorized
implementation and leave committed reviewable branch plus exact candidate body and
handoff; branch-only wf:review is a fallback when PR publication is unavailable.
Never invent Issue numbers, publication or remote phase changes.
Handoff: repository, assignment, branch/full SHA, dirty state, plan/spec/docs paths,
passed/failed/pending checks, prerequisites/blockers and exact next action.

Distinguish implemented, locally verified, integration pending, ready for review,
merged and delivered. Only the full contract permits delivered or completed closure.
Never merge/release/change protections/delete remote branches/change global settings
without separate authority. Required review authorship/independence is reported honestly.
