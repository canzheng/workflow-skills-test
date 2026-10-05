---
name: workflow-design-to-backlog
description: Create the initial or MVP GitHub backlog in one batch from one or more high-level or detailed design documents, or safely refine existing candidate Issues as the design evolves. Use for "Create the initial backlog from this design"; not for an already-ready small implementation request.
---

Read [the delivery contract](../../../docs/workflow/contract.md). It owns workflow
rules; this skill translates intent into delivery outcomes, not execution authority.

## Default: design to initial backlog in one run
Read all supplied design documents, repository instructions/.workflow/config.json,
current implementation/specs if any, and the explicit first-release/MVP boundary.
An empty implementation is valid. The existing design is the durable intent source;
reuse it, preserve section anchors and record only consequential agreed decisions.
For a detailed design, translate its already explicit outcomes/acceptance/dependencies;
do not brainstorm them again. Shape a high-level design only enough to derive usable
acceptance/dependencies. Surface product choices instead of inventing them.

Derive a capability/dependency decomposition internally across the selected release.
Do not require a separate capability map, plan or persisted intermediate artifact.
Produce the smallest coherent batch of independently useful/verifiable outcomes,
preferably vertical slices. Enabling work needs a real dependency/outcome. Never
create engineering-task Issues such as "create class", "add migration" or "write tests".
A large design does not imply a large first backlog: materialize the authorized MVP
slice; leave later candidates in the design unless deliberately requested as backlog.
No repeated invocation per capability/Issue or repeated approval per batch item.

Each Issue body includes outcome, in/out scope, concrete success/failure acceptance,
relevant design sections/current specs, explicit dependency links, risk/environment,
documentation impact and a stable logical source identity. Link design sections instead
of copying long prose. Use the dependency convention in
[the contract](../../../docs/workflow/contract.md#backlog-batches-and-dependencies).
Keep direct prerequisites explicit, including [] for independently dispatchable work;
link decisions too. Separate items with no mutual prerequisite can proceed in parallel
once otherwise Ready, subject to scope/ownership. Cycles, missing references or
contradictory design/human acceptance block affected readiness and need reconciliation.

An unresolved decision becomes a bounded discovery/blocking Issue; record the exact
question, affected outcomes and next action. Unknowns block only dependent items,
not the whole backlog. Keep excluded enhancements excluded. Select OpenSpec only
for substantial contracts/risk/ambiguity; use one plan home if needed.

## Approval, publication and readiness are separate
"Create the initial backlog" authorizes candidate publication when access exists,
not implementation or implicit product approval. Present the coherent batch once
for approval when it was not already approved. Before approval candidates remain
wf:backlog. After a single batch approval, sufficiently specified, approved-release
Issues with available prerequisites become wf:ready; unresolved/unsatisfied items
remain wf:backlog + wf:blocked with their reason/next action. Intentionally deferred
later items remain wf:backlog (wf:deferred only for an explicit deferral).
An actionable discovery Issue can become Ready when its investigation is authorized;
never mark the dependent product commitment Ready without its resolved decision.

Batch approval permits readiness, not execution. Do not claim/start an Issue, create
an implementation branch/PR, or edit application code unless the user separately
asked to execute that scope. An already authorized batch needs no repeat approval.

## Safe batch creation and reruns
Resolve exact repository and stable identities across the whole batch. Prefer existing
design/Issue IDs; never derive identity from changing titles, section numbers or a
content hash. Search open AND closed Issues, paginate: zero permits creation, one
reuses even when closed (inspect disposition; do not silently reopen), multiple block
that mutation. Evolved designs add only genuinely new outcomes. A contradiction is
reported for resolution, not overwritten or used to recreate an Issue.

When publication is authorized, create/reuse the batch using native host tools/gh,
then fill dependency links with confirmed Issue URLs/IDs. Until links are resolved,
keep affected Issues backlog/blocked; never fabricate numbers. Preserve human prose,
acceptance edits and unrelated labels. Re-read before bounded managed-section updates;
reconcile changed snapshots, and stop only conflicting mutation. After timeout or
partial publication, reconcile confirmed identities before retrying. No write access:
return exact candidate bodies/references and unresolved publication without an outbox,
state store or claim of remote creation.

Return one batch summary: confirmed/candidate references, Ready versus backlog/blocked
reasons, dependency/parallel groups, exclusions, exact decisions and any publication
failures. Traceability is design section → Issue → eventual PR through normal references;
a link-only design index is optional, never a second editable backlog/status mirror.
Stop after backlog preparation unless execution was explicitly requested.
