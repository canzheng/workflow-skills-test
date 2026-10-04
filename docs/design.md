# Pantry Planner project design

This is the disposable F14 consumer project in canzheng/workflow-skills-test.
Logical design identity: pantry-planner. The repository is fresh: no application code
or current application specs. Existing workflow/config are inspected, not replaced.

## MVP boundary
An offline CLI helps a household record available ingredients and recipes, produce
a feasible meal plan, and list missing ingredients. Public quantities use integer
grams; no accounts, network or personal-profile persistence in this release.
Scope approval applies to the following outcome batch once, not to implementation.
The user authorizes this F14 evaluation batch and the real execution of one bounded
pilot Issue: ingredient catalog. Candidate/readiness preparation of the batch does
not dispatch the other product outcomes. Later capabilities and the dietary decision
are not silently authorized for implementation. The remaining real merge/completion
and administrative configuration steps require separate authorization.

## Ingredient catalog
Stable outcome ID: pantry-planner:ingredients.
Store/retrieve named ingredient entries and nonnegative integer grams in the local
project data file. Reject duplicate IDs, negative/noninteger grams and malformed data
with an actionable error; a failed input leaves previous data unchanged. An empty
catalog is valid. Example: oats=500g, lentils=300g round-trip unchanged.
Acceptance and dependencies are explicit; do not reshape these into coding tasks.
No dependencies on meal planning or recipes. Document file schema, errors and examples.

## Recipe catalog
Stable outcome ID: pantry-planner:recipes.
Import/retrieve recipe IDs, servings and named ingredient amounts in integer grams.
Reject duplicate IDs, nonpositive/noninteger servings, empty ingredient lists and
negative/noninteger grams, preserving existing data on failure. Recipes may name
ingredients not in the pantry. Example: soup needs lentils200g/carrot100g for2servings.
Independent of the ingredient catalog: use names, not a shared persistent database.
Document accepted data format, error cases and an import/retrieve example.

## Dietary policy decision
Stable outcome ID: pantry-planner:dietary-policy.
Unresolved product choice: must the MVP exclude specified allergens, or is recipe
selection solely an explicit user choice? The owner must choose before plan delivery.
Record the decision here, affected acceptance and what information it requires.
Discovery currently waits for that owner input; do not invent a default policy or
claim the product is safe for allergy use. This does not block either catalog.

## Meal planning
Stable outcome ID: pantry-planner:meal-plan.
Given catalog data and selected recipe/serving count, output deterministic required
and missing ingredient grams. Soup above from pantry lentils300g/carrot0g yields
required lentils200g/carrot100g, missing carrot100g. Reject invalid servings and unknown
recipe IDs; consume the actual ingredient/recipe catalogs. Dietary-policy acceptance
must be added after the explicit decision. Depends on both catalogs and that decision;
the unresolved acceptance keeps this outcome backlog/blocked.
Document units, planning example, denied inputs and actual dietary limitations.

## Shopping list export
Stable outcome ID: pantry-planner:shopping-list.
Export the actual missing-ingredient output to sorted CSV, one ingredient per row,
integer grams and no zero-quantity entries. The soup example produces carrot,100.
Reject malformed plan output and avoid partial output overwrites. Depends on meal-plan.
Document CSV schema, consumer linkage, failures and the independently checked example.

## Later scope and exclusions
Cloud sync, accounts, shared household access, nutrition analytics and mobile UI are
later candidates, not initial backlog Issues. No schema migration/class/test/CI task
Issues; those are implementation decisions within delivery-level outcomes.
