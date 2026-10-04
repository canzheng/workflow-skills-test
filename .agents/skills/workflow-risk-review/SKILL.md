---
name: workflow-risk-review
description: Review material numerical, migration, permission, filesystem, remote-write or producer/consumer risks with specific proof and contract preservation. Select relevant methods only; ordinary low-risk work needs no separate review ceremony.
---

Read [the contract](../../../docs/workflow/contract.md) and only the pertinent
sections of [risk methods](references/methods.md). Inputs: approved acceptance,
actual diff, implementation/consumer paths, existing evidence and relevant lessons.

Identify the concrete behavior at risk and what a plausible wrong implementation
would do. Require proof that distinguishes it: independent arithmetic/units,
producer-to-consumer execution, denied authorization, missing/ambiguous target,
interrupted apply/rollback, retry after unknown remote outcome, or human-edit race.
Existing fixtures are not automatically strong; inspect expectations and negative
controls. Parsed/emitted metadata without a real downstream consumer is incomplete.
An absent resource must not choose an unrelated current directory.

Compare repair diff with original contract, assertions, inputs and expected values.
Narrowing cases, accepting broken output or disabling failing checks requires an
explicit approved behavior change; never silently accept test weakening as a fix.
Select only relevant review methods. The author can apply these methods; independence
is required only by an actual task/project rule. Do not invent another reviewer.

Report concrete findings with contract/risk, file/behavior, missing proof and exact
remediation; identify passed/failed/pending checks and residual uncertainty. Separate
fixture-only proof from live integrations and record author/independence honestly.
