# Phase 4 reviewer handoff

Prepared 2026-11-28. This is a source and workflow checklist, not legal advice, an annotation, or a gold-label proposal. Do not copy it into either annotator packet as an independent annotation.

## Current packet state

- `data/golden/cases.jsonl` contains 10 structurally valid draft cases. All labels and canonical scenario dates are null by design until the date is frozen.
- `data/golden/annotations/annotator_a.csv` and `annotator_b.csv` each contain 10 rows. Labels and rationales are blank in both packets.
- Both blank packets currently carry `2026-11-28` as a provisional working date, while the canonical cases file keeps dates unset. This preserves the draft workflow. The reviewer and both annotators must ratify/freeze the date before finalization; if they choose another date, update the canonical file and both packet contexts together.
- The project has 1,554 processed provision chunks. The DPDP Act and Rules PDFs have been restored under `data/raw/dpdp/` and their SHA-256 hashes match `data/raw/dpdp/SOURCES.md`.
- The original GDPR and California LegInfo HTML snapshots are not present under `data/raw/`. The official GDPR URL and original hash are recorded in `data/raw/gdpr/SOURCES.md`. A current California statute PDF, effective 2026-01-01, has been restored from the California Privacy Protection Agency site; its SHA-256 is recorded in `data/raw/ccpa/SOURCES.md`. Reviewers should use that current statute and separately verify current regulations.

## Case review questions

Resolve these facts before either annotator assigns a substantive label. If a fact cannot be supplied, record the case as unresolved in the review workflow or remove it from the scored set.

| Case | Facts/questions for the reviewer |
|---|---|
| case-001 | Does GDPR Article 3 apply to this Indian company and processing? Which Article 17(1) ground is established? Confirm the DPDP provision's commencement on the selected scenario date. |
| case-002 | Name the retention law, record, purpose, and duration. Does the GDPR Article 17(3)(b) exception cover that exact record and purpose? Confirm GDPR scope and DPDP commencement. |
| case-003 | Which Article 17(1) erasure ground applies after the service purpose ends? Confirm GDPR scope and DPDP commencement. |
| case-004 | Name and source the retention obligation, and define the data and duration it covers. Confirm GDPR scope and DPDP commencement. |
| case-005 | Establish GDPR scope and CCPA business coverage using the facts and threshold effective on the scenario date. Confirm both laws cover the same actor, record, purpose, and operation. |
| case-006 | Establish GDPR scope, the actual exporter and recipient roles, and the transfer mechanism. Confirm the DPDP Rules' commencement and whether a restriction applies to this destination. |
| case-007 | Identify the exporter and controller/processor roles. Determine whether the described movement is a GDPR Chapter V transfer and which transfer mechanism applies. |
| case-008 | Specify the government restriction, destination, data, actor, and required operation. Confirm the applicable GDPR safeguard and whether both laws require the same transfer decision. |
| case-009 | Supply the child's age, the relevant Member State threshold, the service context, and GDPR territorial-scope facts. Confirm DPDP section 9 commencement. |
| case-010 | Establish CCPA business coverage and GDPR territorial scope. State whether the same actor, person, data, purpose, and operation are constrained by both laws. |

## Citation/source check

The citations resolve to text in `data/processed/chunks.jsonl`, with one citation-granularity exception: cases 002 and 004 cite `GDPR Art. 17(3)(b)`, while the corpus chunk is labeled `GDPR Art. 17(3)` and contains the full paragraph. Review the text of that parent chunk and confirm the subparagraph citation before locking the annotation context.

The processed chunks preserve source hashes. The original GDPR HTML snapshot is still missing; reviewers can use the official EUR-Lex text. The current California statute PDF is available locally, but its implementing regulations must be checked separately. The DPDP source documents are the Gazette of India notifications for the Act and the 2025 Rules. Their commencement schedule must be checked against any later Gazette notice before labels are finalized.

## Source-backed legal review flags

These points identify what the reviewers should verify; they are not case labels or a legal opinion.

- The 13 November 2025 DPDP commencement notification schedules sections 7–10 and 11–17 eighteen months after publication. The Rules notification schedules rules 5–16 on the same timetable. On the current provisional date, 2026-11-28, those provisions are not yet at their scheduled commencement under these notices. Verify the Gazette for any later notification before treating this as final.
- GDPR Article 3 requires an EU establishment or, for a non-EU controller/processor, processing related to offering goods/services to people in the Union or monitoring their behavior there. EU residence alone does not resolve scope.
- GDPR Article 17(3)(b) refers to a legal obligation under Union or Member State law to which the controller is subject. Cases 002 and 004 need the retention law's jurisdiction, the exact record and purpose, and a check of necessity. The processed corpus stores the enclosing text as `GDPR Art. 17(3)`; the cited letter (b) is within that paragraph.
- GDPR Articles 44 and 46 concern an actual transfer to a third country and the conditions/safeguards for it. Cases 006–008 need the exporter, processing roles, data flow, and actual mechanism or restriction; a safeguard does not itself require a transfer.
- GDPR Article 8 applies in the specific context of an information society service offered directly to a child when consent is the basis. It sets a default age of 16, with Member States able to lower it no further than 13. Case 009 needs the child's age, country, service facts, and consent basis.
- The current California statute PDF is the CPPA's version effective 2026-01-01. Sections 1798.105 and 1798.120 address deletion and opt-out rights, with statutory scope and exceptions that need checking against the exact operation. The CPPA lists a $26,625,000 gross-revenue threshold effective 2025-01-01; the statutory definition also has consumer-volume and revenue-from-sale/sharing alternatives. Check all definition elements and the entity's facts; a California consumer alone is insufficient.

Official reference links:

- [GDPR, EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng/)
- [DPDP Act commencement notification, G.S.R. 843(E)](https://www.meity.gov.in/static/uploads/2025/11/c56ceae6c383460ca69577428d36828b.pdf)
- [DPDP Rules notification, G.S.R. 846(E)](https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf)
- [California Civil Code, official Legislature site](https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?lawCode=CIV&division=3.&title=1.81.5.&part=4.&chapter=&article=)
- [California Consumer Privacy Act statute effective 2026-01-01, CPPA](https://cppa.ca.gov/pdf/20260101_ccpa_statute.pdf)
- [CPPA laws and regulations, including regulations effective 2026-01-01](https://cppa.ca.gov/regulations/)
- [CCPA threshold update, California Privacy Protection Agency](https://cppa.ca.gov/regulations/cpi_adjustment.html)

## After review

1. Confirm and freeze the scenario date and predicate schema with both annotators.
2. Supply the missing scenario facts or remove cases that cannot be made determinate.
3. Have both annotators independently complete their existing packets without sharing labels.
4. Compare labels, adjudicate each disagreement, and preserve the original packets.
5. Build and validate a new reviewed candidate with `scripts/finalize_golden_annotations.py` and `scripts/validate_golden_dataset.py`.
6. Keep unresolved cases out of scored evaluation and expand toward the 30–40 reviewed cases in `docs/golden_dataset_labeling_guide.md`.
