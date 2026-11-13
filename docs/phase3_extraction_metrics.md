# Phase 3 extraction benchmark

Run date: 2026-11-12  
Sample: 16 provisions across GDPR, DPDP, DPDP Rules, and CCPA  
Split: 8 development cases and 8 held-out diagnostic cases  
Annotation status: single-pass assistant-drafted labels; no independent second annotator or
adjudication  
Models: local Ollama `qwen2.5:3b` and `llama3.2:3b`

This is a small diagnostic benchmark, not a validated legal gold set. The held-out cases were
scored after the schema/prompt update, but the dataset is too small and unreviewed to support a
general accuracy claim. The test results should not be used to claim a performance improvement.

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
