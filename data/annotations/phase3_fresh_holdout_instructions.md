# Instructions for the fresh Phase 3 held-out packets

Files:

- `phase3_holdout_annotator_a.csv`
- `phase3_holdout_annotator_b.csv`
- Case IDs and citation manifest: `phase3_fresh_holdout_manifest.json`

These are 16 new cases, four from each of GDPR, DPDP, DPDP Rules, and CCPA. They exclude all
cases in the existing Phase 3 evaluation. This is a targeted diagnostic sample, not a random or
representative sample of every provision in the corpus.

## For each annotator

1. Work only in your own CSV. Do not open the other person's packet, model predictions, or
   `data/extraction_eval_adjudicated.json` until both packets are complete and returned.
2. Read the whole source provision and follow `docs/phase3_annotation_guidelines.md`.
3. Use one JSON value per cell. `modality`, `actor`, `action`, `data_category`, and
   `evidence_quote` are JSON arrays with one element per obligation. Use JSON `null` inside an
   array for a field that is not specified; do not substitute an empty string.
4. In `condition_constraint_exception`, use an array of objects aligned with the obligations.
   Each object has `condition`, `constraint`, and `exceptions`; use `null` for absent scalar
   values and `[]` for no exceptions.
5. In `scope_qualifier`, use a JSON array of objects. Each object must include `kind`, `text`,
   `applies_to`, `condition`, and `evidence_quote`. Use `[]` if no separate qualifier applies.
6. Evidence quotes must be exact continuous substrings from `source_text`. Do not paraphrase.
7. Save as CSV in UTF-8 and return your own completed copy without changing the source text or
   `chunk_id`.

## After both copies return

From Git Bash, compare the returned packets and write a fresh disagreement report:

```bash
cd /c/Projects/statuteradar
python scripts/compare_annotations.py \
  --packet-a data/annotations/phase3_holdout_annotator_a.csv \
  --packet-b data/annotations/phase3_holdout_annotator_b.csv \
  --manifest data/annotations/phase3_fresh_holdout_manifest.json \
  --disagreements data/annotations/phase3_holdout_disagreements.csv \
  --summary data/annotations/phase3_holdout_agreement.json
```

Copy the disagreement file before adjudicating so the comparison output remains intact:

```bash
cp data/annotations/phase3_holdout_disagreements.csv \
  data/annotations/phase3_holdout_adjudication.csv
```

In the adjudication copy, fill `adjudicated_value` and `adjudication_note` for every row.
For fields without disagreement, the converter uses Annotator A's value, which must match
Annotator B after whitespace/case normalization. Resolve disagreements against the text and
retain the rationale.

Build the structured held-out labels:

```bash
python scripts/build_adjudicated_eval.py \
  --packet-a data/annotations/phase3_holdout_annotator_a.csv \
  --packet-b data/annotations/phase3_holdout_annotator_b.csv \
  --adjudication data/annotations/phase3_holdout_adjudication.csv \
  --master data/annotation_packet.csv \
  --manifest data/annotations/phase3_fresh_holdout_manifest.json \
  --output data/extraction_eval_fresh_holdout.json
```

Only after the prompt, validator, and agreed acceptance criteria are frozen should you run the
fresh test once. Use a different prediction/report name per model:

```bash
LLM_PROVIDER=ollama OLLAMA_EXTRACTION_MODEL=qwen2.5:3b \
  python scripts/evaluate_extraction.py \
  --gold data/extraction_eval_fresh_holdout.json --split test \
  --predictions data/extraction_eval_predictions_qwen_fresh_test.json \
  --report data/extraction_eval_report_qwen_fresh_test.json
```

For Llama, change the model to `llama3.2:3b` and use filenames beginning with
`extraction_eval_predictions_llama32_fresh_test` and
`extraction_eval_report_llama32_fresh_test`. Do not tune against these held-out results and
continue calling this same set a test set.
