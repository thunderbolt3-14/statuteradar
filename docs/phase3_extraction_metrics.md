# Phase 3 extraction benchmark

Run date: 2026-11-12  
Sample: 16 provisions across GDPR, DPDP, DPDP Rules, and CCPA  
Split: 8 development cases and 8 held-out diagnostic cases  
Historical annotation status for this original benchmark: single-pass assistant-drafted labels.  
Models: local Ollama `qwen2.5:3b` and `llama3.2:3b`

This section records the original assistant-labeled benchmark. It is retained for history only;
do not treat it as the current adjudicated score. The test cases were inspected, so they are no
longer a fresh held-out test set.

## Overall results

| Metric | Qwen 2.5 3B | Llama 3.2 3B |
|---|---:|---:|
| Schema-valid rate | 1.000 | 1.000 |
| Evidence-grounding rate among schema-valid | 0.813 | 0.938 |
| Pipeline acceptance rate | 0.438 | 0.563 |
| Outcome accuracy among schema-valid | 0.750 | 0.938 |
| Exact obligation precision | 0.074 | 0.049 |
| Exact obligation recall | 0.100 | 0.100 |
| Exact obligation F1 | 0.085 | 0.066 |

## Held-out results (8 cases)

| Metric | Qwen 2.5 3B | Llama 3.2 3B |
|---|---:|---:|
| Schema-valid rate | 1.000 | 1.000 |
| Evidence-grounding rate among schema-valid | 0.875 | 0.875 |
| Pipeline acceptance rate | 0.375 | 0.625 |
| Outcome accuracy among schema-valid | 0.750 | 1.000 |
| Exact obligation precision | 0.000 | 0.000 |
| Exact obligation recall | 0.000 | 0.000 |
| Exact obligation F1 | 0.000 | 0.000 |
| Action token-overlap F1 | 0.523 | 0.570 |
| Condition token-overlap F1 | 0.000 | 0.017 |
| Constraint token-overlap F1 | 0.000 | 0.000 |
| Exception token-overlap F1 | 0.000 | 0.000 |

Token overlap is a diagnostic for partial wording overlap, not semantic correctness. It does not
replace exact field metrics or human legal review. Both models failed to produce an exact
obligation record on this held-out sample; the token overlap on action text does not change that
finding.

## Field exact F1 on held-out cases

| Field | Qwen 2.5 3B | Llama 3.2 3B |
|---|---:|---:|
| Modality | 0.609 | 0.643 |
| Actor | 0.636 | 0.741 |
| Action | 0.000 | 0.000 |
| Data category | 0.737 | 0.857 |
| Condition | 0.000 | 0.000 |
| Constraint | 0.000 | 0.000 |
| Exceptions | 0.000 | 0.000 |
| Qualifier kind/text | 0.000 | 0.000 |

## What failed

- Both models returned schema-valid JSON for all 16 cases, but schema validity was not a reliable
  signal of accurate legal extraction.
- Llama had better pipeline acceptance and outcome accuracy on the held-out split; neither model
  matched any complete gold obligation there. Llama also produced many extra records, lowering
  exact precision.
- Action record boundaries and wording were the main scoring failure. Each model had nonzero
  token overlap, but zero exact action-field F1 on the held-out cases.
- Neither model recovered the labeled constraints or exceptions on held-out cases. Qwen emitted
  one unmatched qualifier; neither model matched the gold qualifier record.
- Qwen's held-out errors included missed operative effects, missed explicit actors, ungrounded
  evidence, and modality conflicts. Llama's included a modality conflict on a right, an
  ungrounded quote, and actor mismatch on a CCPA transfer clause.
- Reported model confidence is not calibrated and must not be used as a quality threshold.

## Development/test discipline

The split is fixed by provision and intentionally small. The development split can guide future
prompt or validator work; changes made after reviewing the held-out results require a fresh,
independently labeled held-out set before a new test score is reported. Current labels need
independent review and adjudication first. Annotation instructions are in
`docs/phase3_annotation_guidelines.md`.

## Artifacts and reproduction

- Labels and splits: `data/extraction_eval.json`
- Evaluator: `scripts/evaluate_extraction.py`
- Qwen 16-case predictions/report: `data/extraction_eval_predictions_qwen_16.json`,
  `data/extraction_eval_report_qwen_16.json`
- Llama 16-case predictions/report: `data/extraction_eval_predictions_llama32_16.json`,
  `data/extraction_eval_report_llama32_16.json`

Both models were run locally with the same evaluator, schema, and 16 cases. The reports include
overall, development, held-out, per-field, and per-provision results. These outcomes do not
support downstream legal obligation use. Anthropic/API comparison was not run because no API
key or spending approval was provided.

## Adjudicated human-label development run

Two annotators independently labeled the same 16 cases and adjudicated their disagreements. The
structured labels are in `data/extraction_eval_adjudicated.json`. Existing saved Qwen and Llama
predictions were rescored against these labels; this did not call either model again.

| Model | Sample | Exact obligation F1 | Pipeline acceptance | Notes |
|---|---:|---:|---:|---|
| Qwen 2.5 3B | 16 | 0.085 | 0.438 | Full adjudicated diagnostic set |
| Llama 3.2 3B | 16 | 0.098 | 0.563 | Full adjudicated diagnostic set |
| Qwen 2.5 3B | 8 dev | 0.200 | 0.875 | Fresh generation against adjudicated dev labels |
| Llama 3.2 3B | 8 dev | 0.121 | 0.750 | Fresh generation against adjudicated dev labels |

The Qwen development run returned schema-valid output for all eight cases and passed pipeline
validation for seven. It had exact obligation counts TP=2, FP=9, FN=7 (F1=0.200). Exact action
F1 was 0.300; condition, constraint, exception, and qualifier-text F1 were 0.000. One output was
rejected because its second CCPA deletion-notice evidence quote was not present in the source
chunk. These are extraction quality errors, not command/runtime failures.

Llama's development run had exact obligation counts TP=2, FP=22, FN=7 (F1=0.121), showing
substantial over-extraction despite 100% quote grounding. Its exact action F1 was 0.182; condition,
constraint, exception, and qualifier-text F1 were 0.000. Two cases were rejected: a GDPR Art. 17(3)
carve-out was treated as a prohibition, and one CCPA quote was ungrounded. Neither model's results
are a quality pass. The current eight-case test split has already been inspected; the fresh test
results below are the current diagnostic evaluation.

Fresh development artifacts: `data/extraction_eval_predictions_qwen_dev.json`,
`data/extraction_eval_report_qwen_dev.json`, `data/extraction_eval_predictions_llama32_dev.json`,
and `data/extraction_eval_report_llama32_dev.json`.

## Remaining resources and known file issue

- The two completed annotation packets cover the same 16 cases only. The other 1,538 rows in
  `data/annotation_packet.csv` remain blank.
- The fresh 16-case targeted held-out packet has been completed, independently annotated,
  adjudicated, and evaluated once per model. It must not be reused for prompt or validator tuning.
- This 16-case sample is suitable only for a small diagnostic check, not a precise or
  corpus-representative accuracy estimate. Agree with the project guide on a larger final sample
  and pass criteria before making a completion claim.
- `data/annotations/structured_adjudicated_eval.json` is a legacy flat list of 56 disagreement
  rows, not evaluator-ready gold JSON. Do not pass it to the evaluator. Use
  `data/extraction_eval_adjudicated.json` instead.
- `scripts/parse_adjudicated_to_structured.py` was based on obsolete column names and has been
  disabled with instructions. The supported converter is
  `scripts/build_adjudicated_eval.py`; it now checks field list lengths, modalities, and evidence
  quotes against the provision text.
- Both local models are installed. No local model package is missing. A paid API comparison is
  optional and would require credentials and approval for spending.

## Fresh adjudicated held-out test

Two annotators independently labeled and adjudicated a new 16-case targeted sample, with four
cases from each of GDPR, DPDP, DPDP Rules, and CCPA. The cases exclude the earlier evaluation set.
Both local models were evaluated once against the same adjudicated labels. This is a small
diagnostic sample, not a representative estimate of corpus-wide accuracy.

| Metric | Qwen 2.5 3B | Llama 3.2 3B |
|---|---:|---:|
| Sample size | 16 | 16 |
| Schema-valid rate | 1.000 | 1.000 |
| Evidence-grounding rate | 0.9375 | 0.9375 |
| Pipeline acceptance rate | 0.875 | 0.625 |
| Outcome accuracy among schema-valid | 0.5625 | 0.8125 |
| Exact obligation precision | 0.000 | 0.000 |
| Exact obligation recall | 0.000 | 0.000 |
| Exact obligation F1 | 0.000 | 0.000 |
| Exact action F1 | 0.000 | 0.0476 |
| Exact actor F1 | 0.5455 | 0.4878 |
| Exact data-category F1 | 0.6400 | 0.3784 |
| Exact condition F1 | 0.000 | 0.000 |
| Exact constraint F1 | 0.000 | 0.000 |
| Exact exception F1 | 0.000 | 0.000 |
| Exact qualifier-text F1 | 0.000 | 0.000 |

Both models produced schema-valid output for every case, yet neither matched any complete gold
obligation record. Qwen's exact obligation counts were TP=0, FP=13, FN=21; Llama's were TP=0,
FP=21, FN=21. Qwen had a higher pipeline acceptance rate, while Llama had higher outcome
accuracy. These measures do not offset the zero exact obligation score. The models are not ready
for downstream legal-obligation use.

The evaluator reported Qwen rejections for one missing explicit actor and one ungrounded quote.
Llama had three missing-explicit-actor rejections, two non-operative-effect rejections, and one
ungrounded-quote rejection. Action token-overlap F1 was 0.3180 for Qwen and 0.3195 for Llama; this
is only a wording-overlap diagnostic, not evidence of semantic correctness.

Artifacts:

- Adjudicated labels: `data/extraction_eval_fresh_holdout.json`
- Qwen predictions/report: `data/extraction_eval_predictions_qwen_fresh_test.json`,
  `data/extraction_eval_report_qwen_fresh_test.json`
- Llama predictions/report: `data/extraction_eval_predictions_llama32_fresh_test.json`,
  `data/extraction_eval_report_llama32_fresh_test.json`

These results consume the fresh holdout. Any prompt or validator changes made after reviewing
them require a new independently labeled held-out set before another final test score is claimed.
