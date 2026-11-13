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

Labels remain single-pass assistant-drafted annotations, without independent review or
adjudication. On the held-out eight cases, Qwen 2.5 3B and Llama 3.2 3B both had zero exact
obligation F1. Pipeline acceptance was 0.375 for Qwen and 0.625 for Llama. Action token-overlap
F1 was 0.523 and 0.570 respectively, but exact action F1, condition/constraint F1, and exception
F1 were all zero. These metrics indicate serious extraction errors and are not a validated
general accuracy estimate. Full scores and per-provision errors are in
`docs/phase3_extraction_metrics.md` and the JSON reports under `data/`.

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
  the adjudication notes. Do not call the current annotations gold.
- Build a larger, stratified, independently labeled set with a new held-out split. The present
  test cases have already been inspected diagnostically and should not be reused for future
  tuning claims.
- Improve atomic action boundaries, exception/scope extraction, conditions, constraints, and
  permission/prohibition polarity on development data, then evaluate once on the fresh held-out
  set.
- Do not pass these model outputs into applicability or constraint decisions, or present them as
  legal determinations.
- An Anthropic model comparison requires a configured API key and explicit approval for any
  API spending; it was not run in this work.

Phase 3 is implemented as a research prototype. It is not quality-closed for downstream use.
