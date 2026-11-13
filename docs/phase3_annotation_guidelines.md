# Phase 3 extraction annotation guidelines

These instructions define the target labels for `data/extraction_eval.json`. The current labels
are assistant-drafted and require independent human review before they can be treated as gold.
Annotators should use the cited source text, not model output or assumptions about what a law
normally requires.

## Unit and record boundaries

- Use one evaluation case per source chunk. Read its full provision and any lead-in text supplied
  with it.
- Create one obligation record for each distinct actor/action/legal effect. Keep separate duties
  separate when their actors, actions, conditions, or legal effects differ. Do not duplicate a
  record just because the same duty is restated.
- A clause that only defines a term, grants an exception, or sets a scope condition is not by
  itself an obligation. Label it as a qualifier where appropriate.
- If a provision contains both a duty and an exception, annotate the duty and the exception
  separately, linking the exception to the duty it limits.

## Obligation fields

- `modality`: `MUST` for a required act, `MUST_NOT` for a prohibited act, and `MAY` for an
  express permission or right. Preserve the source's polarity; do not turn a permission into a
  duty or an exception into a prohibition.
- `actor`: the person or entity legally assigned the action. Copy the named role when the text
  names one. Use `null` only when the provision does not identify an actor; do not infer one from
  general knowledge.
- `action`: a concise verb phrase describing the legally operative act or omission. Keep the
  action span grounded in the source, but avoid copying an entire paragraph when a shorter phrase
  captures the effect.
- `data_category`: the affected personal-data category when the text states it; otherwise
  `null`. Do not invent categories from context elsewhere in the Act.
- `condition`: a trigger or circumstance that must hold for the obligation or permission to
  apply. Use `null` if none is stated.
- `constraint`: a limit, deadline, procedure, or standard governing performance. Use `null` if
  none is stated.
- `exceptions`: reserve for exception text directly attached to this obligation. Prefer the
  structured qualifier record below when the exception has its own scope or condition and should
  be independently measured.
- `evidence_quote`: the shortest exact source span that supports this record. Preserve wording;
  whitespace normalization is allowed by the evaluator, paraphrase is not.
- `extraction_confidence`: record the model's reported score only; it is not a human correctness
  judgment and must not be treated as calibrated probability.

## Qualifiers

Create a `qualifiers` record for each distinct `exception` or `scope` effect:

- `kind`: `exception` when text removes or limits an otherwise applicable duty/right; `scope`
  when text states who, what, or which processing/activity is covered.
- `text`: a concise, faithful description of the effect.
- `applies_to`: the obligation identifier or short description this qualifier limits. Use `null`
  when it applies to the provision generally or the target cannot be determined from the text.
- `condition`: the stated condition or trigger for the qualifier, otherwise `null`.
- `evidence_quote`: exact text supporting the qualifier.
- `confidence`: model confidence on its reported 0–100 scale; it is not calibrated.

## Outcome and disagreement handling

- Choose `obligations` if the chunk contains at least one operative obligation, prohibition, or
  express permission/right. Include any qualifiers alongside those records.
- Choose `no_obligation` when no such operative effect appears. A qualifier-only chunk can still
  be `no_obligation` and should retain its qualifier records.
- Do not label a passage `no_obligation` merely because the duty is conditional or phrased as a
  right/permission.
- Annotators should label independently before comparing outputs. Resolve disagreements by
  citing the exact clause and recording the adjudicated decision plus a short rationale. Track
  agreement separately for outcome, obligation boundaries, and each field; do not report a single
  agreement score without defining its unit and statistic.

## Split discipline

The existing eight `dev` and eight `test` cases are a small, fixed diagnostic split, not a
statistically representative sample. Do not use `test` cases to tune prompts or validators. If
the implementation changes after inspecting test errors, create a fresh held-out test set before
reporting a new test score.
