# Phase 3 development sample review

Date: 2026-11-12  
Provider: local Ollama, `qwen2.5:3b`  
Sample: four GDPR chunks covering erasure, international transfer, and compatible further processing.

This is a development error review, not legal advice or a measured accuracy evaluation. The sample
is too small and was not independently double-annotated.

| Chunk | Pipeline result | Manual field-level observations |
|---|---|---|
| `gdpr:art17:p1:pta` | Rejected by evidence grounding | The model's evidence quote did not match the source chunk after whitespace normalization. No record was accepted. |
| `gdpr:art17:p3` | Schema and grounding passed | The provision's erasure exceptions were emitted as five `MUST_NOT` obligations, including a duplicate aggregate record. The polarity/action interpretation is wrong for the extraction contract. |
| `gdpr:art46:p1` | Schema and grounding passed | `may transfer` was emitted as `MUST`. The text explicitly names “controller or processor,” but `actor` was null. |
| `gdpr:art6:p4:pta` | Schema and grounding passed | The main duty was identified, but the explicitly named controller was omitted as actor. The evidence quote spans the chunk; this does not by itself validate the extracted fields. |

All returned confidence values were `100`. Treat these as an uncalibrated model score only; they
did not signal the observed polarity and actor errors. The initial 0–1 schema rejected outputs
because this model returned `90`; the extraction field is now defined as an integer from 0 to 100.

## Changes indicated by this sample

- Improve modality instructions and include clear examples distinguishing `MAY` from `MUST`.
- Define how legal exceptions/carve-outs should be represented; do not convert them automatically
  into standalone prohibitions.
- Require extraction of an explicit actor when the sentence names one.
- Keep evidence grounding as a rejection check and add field-level annotation before scoring
  precision, recall, or F1.
- Review output in a larger, stratified sample before using extraction records downstream.

No corpus, evaluation labels, or vector index were modified. These results are not sufficient to
claim Phase 3 extraction accuracy or completion.

## Prompt-refinement rerun

After the initial review, the prompt was revised with explicit modality examples, carve-out
guidance, and instructions to copy named actors. The same four chunks were rerun with the same
local model.

| Chunk | Rerun result | Comparison with initial run |
|---|---|---|
| `gdpr:art17:p1:pta` | Accepted as one `MUST` record, but `actor` remained null even though the evidence quote names the controller. | Evidence grounding now passed; actor omission remains. |
| `gdpr:art17:p3` | Rejected because output contained both obligations and `no_obligation_reason`. | The carve-out was not safely represented; the schema validator rejected the ambiguous outcome. |
| `gdpr:art46:p1` | Rejected for the same both-outcomes validation error. | No accepted record, so the `MAY` vs `MUST` issue remains unresolved. |
| `gdpr:art6:p4:pta` | Accepted as one `MUST` record, but `actor` remained null although the quote names the controller. | Duty recognized; actor omission remains. |

All accepted rerun records again had confidence `100`. The prompt update improved quote grounding
for the first chunk but did not resolve actor extraction, and two of four outputs failed
cross-field validation. At that point the JSON Schema sent to Ollama did not encode the
cross-field rule; the later discriminated-schema change and its results are recorded below.

## Discriminated-schema rerun

The output contract was changed to a discriminated union with `outcome` set to either
`obligations` or `no_obligation`. Each branch has its own required fields and array cardinality;
Pydantic also validates the selected branch after generation. The same four chunks were run again.

| Chunk | Rerun result | Manual review |
|---|---|---|
| `gdpr:art17:p1:pta` | Accepted: one `MUST` record. | Quote grounded, but actor still null despite “controller” appearing as the actor in the quote. |
| `gdpr:art17:p3` | Accepted: `no_obligation`, with empty obligations. | Correctly represented as an exception-only chunk rather than prohibitions. |
| `gdpr:art46:p1` | Rejected by evidence grounding (obligation 4 quote unsupported). | No record accepted; permission modality and actor remain unresolved. |
| `gdpr:art6:p4:pta` | Accepted: one `MUST` record. | Duty and quote grounded, but actor still null despite “controller” appearing as the actor in the quote. |

The two-outcome validation failures did not recur in this run. The schema change improved handling
of the exception-only chunk. The actor omissions persist, and the transfer result still fails quote
grounding. Do not use these outputs as gold labels or downstream legal determinations.

## Stratified development benchmark

The follow-up benchmark now contains eight chunks across GDPR, DPDP, DPDP Rules, and CCPA. The
labels are one-pass assistant-drafted annotations and have not been independently reviewed. The
final prompting/schema revision was run with both local models; metrics and per-chunk predictions
are in `phase3_extraction_metrics.md` and the corresponding JSON artifacts.

Qwen 2.5 3B achieved exact obligation F1 0.211; Llama 3.2 3B achieved 0.160. Both were schema
valid on all eight cases and grounded seven of eight. After fail-closed semantic checks, Qwen
accepted four and Llama accepted five; outcome accuracy among schema-valid outputs was 0.875 for
both. Qwen missed the DPDP s.6(7) permission, made extra or wrong-polarity
records in GDPR Art. 46 and CCPA §1798.120(c), and produced an ungrounded CCPA deletion quote.
Llama misclassified the GDPR Art. 17(3) carve-out and GDPR Art. 46 permission and also failed
grounding on DPDP s.6(7). Neither is ready for downstream legal obligation use.

## Expanded 16-provision benchmark (supersedes the preliminary aggregate above)

The set now has eight `dev` and eight `test` cases, including dedicated qualifier annotations.
Both local models were run against the complete expanded set with separate output files. On the
held-out eight cases, both had zero exact obligation precision/recall/F1. Pipeline acceptance was
0.375 for Qwen and 0.625 for Llama; outcome accuracy among schema-valid cases was 0.750 and
1.000. Both had zero exact action, condition, constraint, and exception F1. Action token overlap
was 0.523 for Qwen and 0.570 for Llama, which indicates some shared wording but does not establish
correct obligation boundaries or legal meaning.

The expanded scores are the current benchmark result. The earlier eight-case scores above are
retained only as historical development results; do not compare them as if they were the same
sample or protocol. Both models still need independent annotations and a fresh held-out set after
any future prompt or validator changes. Full metrics and error details are in
`docs/phase3_extraction_metrics.md`.
