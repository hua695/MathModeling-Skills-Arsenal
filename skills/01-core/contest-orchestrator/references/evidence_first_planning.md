# Evidence-first content planning

`content_budget_plan.yaml` is the only manual planning input for page capacity.
It describes what each subproblem must prove; it does not contain fabricated
results and it never authorizes filler text. `scripts/build_evidence_index.py`
creates a derived `.contest/evidence_index.json` from existing contracts, run
manifests, and registries. The derived index is a report, not a second results
database and must not be hand-edited.

## Planning contract

New plans may declare:

```yaml
planning_contract: evidence_first
evidence_policy:
  source_of_truth: ".contest/evidence_index.json"
  required_sources: [model_contract, derivation_registry, modeling_solution_contract, run_manifest]
  anti_padding: [no_repeated_formula, no_unexplained_figure, no_manual_page_break]
```

Each subproblem may add `capability_profile` (for example,
`data_prediction` or `simulation_dynamics`), `validation_scope` (`local`,
`global`, or `both`), and a list of `visual_evidence` entries. A visual entry
records why a figure is needed and its source; it does not impose a global
figure count. Mixed questions can use different profiles, while the shared
budget remains one plan.

## Execution semantics

- At `blueprint`, validate the declared plan and capacity before writing.
- At `solution`, require a generated evidence index and completed per-question
  evidence; missing source artifacts route back to modeling or execution.
- At `delivery`, reuse the index for diagnosis, while authoritative gates still
  validate each source directly.
- A short paper is a review state, not an automatic writing instruction. A
  long paper is not rescued by a budget plan if it contains repeated formulas,
  empty figure pages, or untraceable claims.
