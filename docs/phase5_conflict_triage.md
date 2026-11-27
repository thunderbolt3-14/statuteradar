# Phase 5: conservative conflict triage

## Scope

Phase 5 introduces a small deterministic triage engine that consumes reviewer-structured obligation findings. It does not call an LLM, infer jurisdictional applicability from statute text, or consume the unfinished Phase 4 golden labels. The case and predicate fields are provisional until the Phase 4 reviewers freeze that schema.

The engine returns one of `CONFLICT`, `COMPATIBLE`, `INDEPENDENT`, or `NEEDS_REVIEW`:

- `INDEPENDENT` is returned only when a reviewer explicitly confirms disjoint scope or fewer than two reviewed, applicable rules remain. Multiple applicable rules from only one jurisdiction return `NEEDS_REVIEW`; this engine is limited to cross-jurisdiction triage.
- `COMPATIBLE` is returned only when a reviewer supplies a concrete operating option, rationale, reviewer identity, and evidence references covering every submitted rule.
- `CONFLICT` is returned only for the narrow structured case where two reviewed, applicable obligations have identical actor, action key, target, operation, and condition; opposite `MUST`/`MUST_NOT` modalities; and reviewed empty exception lists. The result still flags human review.
- `NEEDS_REVIEW` is the fail-closed default when scope, applicability, exceptions, or a jointly satisfying option are uncertain, or when the structured predicates do not match the narrow contradiction rule.

The `action_key`, `target_key`, `operation_key`, `condition_key`, and applicability findings are supplied by a human reviewer. The engine does not decide whether two natural-language actions are equivalent. Evidence quotes and source chunk IDs are carried into the result for audit.

## Run

Use the JSON input under `examples/phase5/` only as a synthetic software fixture; it contains fictional rules and is not a legal example.

```bash
python scripts/assess_case.py examples/phase5/synthetic_conflict.json
```

Run core tests with `python -m pytest tests/test_assessment.py -q`.

## Limitations

Phase 4 labels and its predicate schema are not complete. Phase 5 therefore has no measured legal accuracy and must not be used to make legal, compliance, or applicability decisions. `CONFLICT` is a candidate structured contradiction that must be reviewed; `NEEDS_REVIEW` should be used whenever the record is incomplete.
