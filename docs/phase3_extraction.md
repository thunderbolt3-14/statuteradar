# Phase 3: obligation extraction

Status: the extraction implementation and diagnostic evaluation are in place on
`feat/phase3-extraction`. The measured quality gate remains open: neither tested local model is
accurate enough for downstream legal-obligation records.

## Implemented

- One-chunk-at-a-time extraction through local Ollama or Anthropic Messages API.
- Clause views that separate sentences and enumerated clauses while repeating lead-in context in
  the prompt. The source chunk remains intact for evidence validation.
- Discriminated JSON output (`obligations` or `no_obligation`) with Pydantic validation.
- Separate exception/scope qualifier records, including for chunks with no standalone
  obligation.
- Trusted citation metadata attached by the application, evidence quote grounding, and
  fail-closed checks for common explicit legal actors and modality conflicts.
- A 16-provision benchmark across four instruments, split into 8 development and 8 held-out
  diagnostic cases; the evaluator reports strict exact-value metrics and token overlap for
  partial text similarity.
- Annotation instructions in `docs/phase3_annotation_guidelines.md`.

## Measured results

The original benchmark labels were assistant-drafted. Two human annotators have since
independently labeled the same 16 cases and adjudicated disagreements. The structured labels are
in `data/extraction_eval_adjudicated.json`; this is still a small diagnostic set, not a fresh
held-out set. Rescoring the saved full-set predictions against adjudicated labels gave exact
obligation F1 of 0.085 for Qwen and 0.098 for Llama.

A fresh Qwen run on the eight adjudicated development cases had exact obligation F1 0.200 and
pipeline acceptance 0.875. Llama had F1 0.121 and pipeline acceptance 0.750. Both outputs were
schema-valid, but action F1 was 0.300 for Qwen and 0.182 for Llama; condition, constraint,
exception, and qualifier-text F1 were 0.000 for both. Qwen had an ungrounded evidence quote;
Llama had one ungrounded quote and treated a GDPR carve-out as a prohibition. The commands
completed; these are extraction quality failures. Current metrics and artifacts are tracked in
`docs/phase3_extraction_metrics.md` and the report JSON files under `data/`.

### Fresh held-out diagnostic

Two annotators independently labeled and adjudicated a new targeted set of 16 cases, four per
instrument, excluding the earlier evaluation cases. Both local models were run once against the
same adjudicated labels. Schema validity was 1.000 and evidence grounding was 0.9375 for each,
but exact obligation F1 was 0.000 for both. Qwen had pipeline acceptance 0.875 and outcome accuracy
0.5625; Llama had pipeline acceptance 0.625 and outcome accuracy 0.8125. Exact condition,
constraint, and exception F1 were 0.000 for both. The targeted sample is diagnostic, not
representative of the corpus, and the results do not support downstream use.

The adjudicated labels, predictions, and reports are saved as
`data/extraction_eval_fresh_holdout.json` and the matching `*_fresh_test.json` files under
`data/`.

## Run and score

From Git Bash, run one model at a time:

```bash
cd /c/Projects/statuteradar
LLM_PROVIDER=ollama OLLAMA_EXTRACTION_MODEL=qwen2.5:3b \
  venv/Scripts/python.exe scripts/evaluate_extraction.py \
  --predictions data/extraction_eval_predictions_qwen_16.json \
  --report data/extraction_eval_report_qwen_16.json
```

Set `OLLAMA_EXTRACTION_MODEL=llama3.2:3b` and use filenames containing `llama32_16` for the
comparison run. Each model call takes roughly a minute on the current laptop. `--reuse` scores an
existing predictions file without calling a model.

## What remains before quality closeout

- Have a second annotator independently label the sample, then resolve disagreements and retain
  the adjudication notes. This is complete for the existing 16 evaluation cases; see the two
  packets and `data/annotations/annotation_adjudication.csv`.
- Build a larger, stratified, independently labeled set with a new held-out split. The fresh
  16-case holdout has now been evaluated and must not be reused for tuning. Use development data
  for prompt or validator changes, then collect a new independently labeled holdout before another
  final evaluation.
- Improve atomic action boundaries, exception/scope extraction, conditions, constraints, and
  permission/prohibition polarity on development data; both models still have zero exact
  obligation F1 on the fresh holdout.
- Do not pass these model outputs into applicability or constraint decisions, or present them as
  legal determinations.
- An Anthropic model comparison requires a configured API key and explicit approval for any
  API spending; it was not run in this work.
- A same-label Llama development run now exists alongside Qwen. No additional model or API is
  required to continue local development.
- The fresh 16-case packet has been independently completed and adjudicated, then evaluated once
  per model. Preserve the raw annotation packets and adjudication worksheet locally; the
  evaluator-ready adjudicated labels and aggregate reports are the shareable artifacts.
- Since both models scored zero exact obligation F1, Phase 3 remains a research prototype and is
  not quality-closed for downstream legal-obligation records.

### Quality holdout v2 status

A provisional pass gate was agreed before selecting the next holdout: schema validity and evidence
grounding must each be at least 0.95, exact obligation F1 must be at least 0.80, and every
field-level exact-value F1 must be at least 0.75. A new targeted 16-case packet, balanced across
GDPR, DPDP, DPDP Rules, and CCPA and excluding both prior evaluation sets, has been prepared.
Its two annotation packets are blank; independent annotation, adjudication, and one run per model
remain outstanding. No quality-gate result is available yet. See
`docs/phase3_extraction_metrics.md` for the criteria and packet paths.

Phase 3 is implemented as a research prototype. It is not quality-closed for downstream use.
