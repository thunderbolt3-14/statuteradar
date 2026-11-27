# Golden dataset: drafting and labeling guide

## Purpose and status

This dataset records small, reviewable scenarios for evaluating whether obligations in two jurisdictions can be satisfied together for a defined data flow. A difference between laws, a stricter rule, or permission in one law does not by itself establish a conflict.

`data/golden/cases.jsonl` is the canonical working file. Its ten initial records are **draft cases**, not gold labels. `label` and `gold_predicates` stay empty until the annotators have reviewed the cited provisions and the team has frozen the predicate schema. Do not use draft cases to report model accuracy.

Every case must also have a `scenario_as_of_date`. A rule's publication or enactment does not by itself establish that it was in force on the scenario date. The current seed cases leave this field `null`, so none is ready for a final label yet.

### Temporal scope requiring review

The Digital Personal Data Protection Act, 2023 and the Digital Personal Data Protection Rules, 2025 use staged commencement. The commencement notification dated 13 November 2025 schedules sections 3–17 of the Act—including sections 8, 9, and 16—and rules 3, 5–16, 22, and 23 for eighteen months after Gazette publication. Those provisions are not yet in force as of 27 November 2026. Cases citing them must set an explicit scenario date and review the applicable commencement schedule before labeling. See the [official commencement notification](https://egazette.gov.in/WriteReadData/2025/267647.pdf) and [official Rules 2025 notification](https://egazette.gov.in/WriteReadData/2025/267650.pdf).

The seed scenarios also need review for jurisdictional scope facts, such as GDPR territorial scope, California business coverage, applicable actors and processing, and (for the child-consent case) the child's age and relevant Member State threshold. A reviewer must add the facts or mark the case `NEEDS_REVIEW`; annotators must not infer them.

The earlier `data/golden/conflicts_golden.json` contains one unreviewed hypothesis. In particular, a rule that permits a transfer subject to conditions does not, by itself, require that transfer or prove joint unsatisfiability. Keep it out of scored evaluation until independently reviewed and adjudicated.

## Label definitions

- `CONFLICT`: For the exact profile and the same processing operation, both obligations apply and no permitted operational choice satisfies both. The annotators must identify the incompatible requirements and explain why apparent exceptions, safeguards, or alternative choices do not resolve them.
- `COMPATIBLE`: Both obligations apply to the same operation, and at least one concrete operating choice satisfies both. State that choice and any conditions it depends on.
- `INDEPENDENT`: The cited rules do not constrain the same actor, data, purpose, operation, or time period in this profile, so the pair creates no joint constraint to solve. Do not use this label merely because no conflict was found; use `COMPATIBLE` when both obligations apply and can coexist.

If facts or legal interpretation are missing, mark the annotation `NEEDS_REVIEW`, record the missing fact, and do not force one of the three labels. These are research labels for a student prototype, not legal advice.

## Annotation workflow

1. Choose the dataset's legal as-of date and freeze and record the profile fields and predicate schema with Persons A and B before adding structured predicates.
2. For each case, independently read every cited provision in `data/processed/chunks.jsonl` and verify the citation with `python scripts/show.py "<citation>"`.
3. Use separate packets from `python scripts/prepare_golden_annotation_packets.py`. Each annotator records a label, a short rationale, and any missing facts. Do this independently before discussing cases. The predicate column is intentionally withheld until its schema is frozen.
4. After both passes are saved, compare labels with `python scripts/compare_golden_annotations.py`. Preserve the original packets; adjudicate disagreements in the generated template.
5. Report exact label agreement and Cohen's kappa from the generated summary, along with the case count and label distribution. Explain that a small or imbalanced sample makes the estimate uncertain. This comparison does not measure predicate agreement.
6. Split by `case_id` into development and test sets before tuning. Keep test labels hidden from anyone changing prompts, rules, or thresholds. With only ten seed cases, treat both splits as drafting material, not a reliable benchmark.
7. Expand toward 30–40 cases, aiming for about 40% non-conflict cases overall. Record the actual distribution rather than forcing labels to match a target.

The packet columns are `case_id`, `scenario`, `scenario_as_of_date`, `profile_json`, `category`, `cited_provisions_json`, `label`, `rationale`, and `missing_facts_json`. Annotators must not change the first six context columns. Use exactly one label from `CONFLICT`, `COMPATIBLE`, `INDEPENDENT`, or `NEEDS_REVIEW`; rationale is required, and `missing_facts_json` must be a JSON list (use `[]` when none). A `NEEDS_REVIEW` label requires at least one specific missing fact or review question. Add predicate fields only after the predicate schema is jointly frozen.

Example comparison command:

```bash
python scripts/compare_golden_annotations.py \
  --packet-a data/golden/annotations/annotator_a.csv \
  --packet-b data/golden/annotations/annotator_b.csv \
  --summary data/golden/annotations/label_agreement.json \
  --disagreements data/golden/annotations/disagreements.csv \
  --adjudication-template data/golden/annotations/adjudication.csv
```

Review each disagreement and fill `adjudicated_label` and `adjudication_rationale` in the generated template. Do not overwrite either original annotator packet. `scripts/validate_golden_dataset.py` checks the canonical draft file; it does not certify legal correctness or adjudication.

## Case record format

One JSON object per line. Keep fields stable so evaluation code can consume the file later:

```json
{
  "case_id": "case-001",
  "status": "draft",
  "split": null,
  "scenario_as_of_date": null,
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

The ten records are starting scenarios selected from the project scope. They are not pre-labeled. At least one independent reviewer should check every case, its citations, commencement date, and applicability facts before it is considered usable; revise or discard cases whose facts do not support a clear annotation. Run `python scripts/validate_golden_dataset.py` to confirm the file remains structurally valid and draft cases have not been mislabeled as gold.
