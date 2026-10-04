# Risk-specific proof methods

## Numerical and data meaning
Name units, precision, rounding and invariants. Compute an expectation independently:
10000 cents with 25% discount is 7500 cents, not 9975. Use values where plausible
wrong formulas diverge; a zero-only fixture is weak. Exercise boundaries and rejected
inputs; use a separate trusted reference when arithmetic is not hand-computable.

## Producer/consumer contracts — retained L-001
Schema/parser/emitter coverage alone does not prove use. Trace an emitted field into
an actual downstream action and break the consumer deliberately. Example: EUR cents
must format EUR 6.97; a parser that stores currency while formatting USD is broken.
Source regression: tests/v2/test_risk.py and test_delivery.py in workflow-skills.
The original lesson/evidence remains reachable at the recorded pre-rewrite SHA;
do not carry lesson retrieval counters or dormant runtime fields into v2.

## Filesystem and targets — retained L-002
Test missing AND ambiguous target as well as success/dirty target. Reject symlink
escapes, unexpected root, stale revision and modified owned files. A missing worktree
never chooses cwd. Inject failure after some replacements, prove restoration or
precise recoverable residuals and rerun. Source proof: test_setup.py and
revision-target tests added with handoffs. Global duplicates need explicit discovery
resolution, never automated global deletion.

## Migration/persistence
Use realistic known-format records: active/done/deferred/duplicate/missing change.
Describe interruption and rollback limits. Snapshot before/after; no guessed state
or recreation of Done history. Establish one authority per migrated item, carrying
remaining acceptance/evidence/blockers and old/new IDs. Rollback preserves remote history.

## Permissions and secrets
Resolve allowed principal/resource/action. Test allowed and denied paths separately;
authentication alone proves neither reads nor writes. Never emit tokens in diagnostics.
Host permissions do not authorize merge/admin/global operations outside the assignment.

## Remote mutations
Search open/closed source markers, reconcile unknown creation outcomes before retry,
re-read and compare before bounded updates, retain human edits/unrelated labels.
Test permission loss midway and duplicate/multiple matches. Native operations do
not promise distributed locks or atomic remote transactions. Missing access does
not block independent local implementation or certify remote success.

## Contract-changing repair
Inspect original acceptance and discriminating cases. A proposed repair accepting
498 instead of documented 697 is rejected unless the behavior change was approved.
Record reviewer authorship; primary-author inspection is not independent review.
