# Golden dataset: drafting and labeling guide

## Purpose and status

This dataset records small, reviewable scenarios for evaluating whether obligations in two jurisdictions can be satisfied together for a defined data flow. A difference between laws, a stricter rule, or permission in one law does not by itself establish a conflict.

`data/golden/cases.jsonl` is the canonical working file. Its ten initial records are **draft cases**, not gold labels. `label` and `gold_predicates` stay empty until the annotators have reviewed the cited provisions and the team has frozen the predicate schema. Do not use draft cases to report model accuracy.

The earlier `data/golden/conflicts_golden.json` contains one unreviewed hypothesis. In particular, a rule that permits a transfer subject to conditions does not, by itself, require that transfer or prove joint unsatisfiability. Keep it out of scored evaluation until independently reviewed and adjudicated.

## Label definitions

- `CONFLICT`: For the exact profile and the same processing operation, both obligations apply and no permitted operational choice satisfies both. The annotators must identify the incompatible requirements and explain why apparent exceptions, safeguards, or alternative choices do not resolve them.
- `COMPATIBLE`: Both obligations apply to the same operation, and at least one concrete operating choice satisfies both. State that choice and any conditions it depends on.
- `INDEPENDENT`: The cited rules do not constrain the same actor, data, purpose, operation, or time period in this profile, so the pair creates no joint constraint to solve. Do not use this label merely because no conflict was found; use `COMPATIBLE` when both obligations apply and can coexist.

If facts or legal interpretation are missing, mark the annotation `NEEDS_REVIEW`, record the missing fact, and do not force one of the three labels. These are research labels for a student prototype, not legal advice.

## Annotation workflow

1. Freeze and record the profile fields and predicate schema with Persons A and B before adding structured predicates.
2. For each case, independently read every cited provision in `data/processed/chunks.jsonl` and verify the citation with `python scripts/show.py "<citation>"`.
3. Each annotator records a label, a short rationale, the obligations that apply, exceptions or conditions considered, and any missing fact. Do this independently before discussing cases.
4. Compare labels only after both passes are saved. Preserve the original labels; record adjudicated label and rationale separately.
5. Compute Cohen's kappa on the original independent labels, report the number of cases and the label distribution, and explain that a small or imbalanced sample makes the estimate uncertain.
6. Split by `case_id` into development and test sets before tuning. Keep test labels hidden from anyone changing prompts, rules, or thresholds. With only ten seed cases, treat both splits as drafting material, not a reliable benchmark.
7. Expand toward 30–40 cases, aiming for about 40% non-conflict cases overall. Record the actual distribution rather than forcing labels to match a target.

## Case record format

One JSON object per line. Keep fields stable so evaluation code can consume the file later:

```json
{
  "case_id": "case-001",
  "status": "draft",
  "split": null,
  "scenario": "A concrete data-flow scenario with actor, data, purpose, and time.",
  "profile": {
    "organization_established_in": "IN",
    "data_subject_locations": ["EU"],
    "data_categories": ["account data"],
    "storage_locations": ["IN"],
    "transfers": [],
    "children_data": false,
    "sale_or_sharing": false
  },
  "category": "erasure_retention",
  "cited_provisions": [
    {"instrument": "GDPR", "citation": "GDPR Art. 17(1)"},
    {"instrument": "DPDP", "citation": "DPDP s.8(7)"}
  ],
  "gold_predicates": [],
  "label": null,
  "annotator_labels": [],
  "adjudicated_label": null,
  "rationale": "",
  "missing_facts": []
}
```

Allowed final labels are `CONFLICT`, `COMPATIBLE`, and `INDEPENDENT`. Draft status and null labels are intentional. Do not populate gold predicates until their agreed field names and meanings are stable.

## Seed cases

The ten records are starting scenarios selected from the project scope. They are not pre-labeled. At least one independent reviewer should check every case and its citations before it is considered usable; revise or discard cases whose facts do not support a clear annotation.
