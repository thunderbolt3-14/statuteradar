# Phase 4 reviewer handoff

Prepared 2026-11-28. This is a source and workflow checklist, not legal advice, an annotation, or a gold-label proposal. Do not copy it into either annotator packet as an independent annotation.

## Current packet state

- `data/golden/cases.jsonl` contains 10 structurally valid draft cases. All labels are null and all scenario dates are null.
- `data/golden/annotations/annotator_a.csv` and `annotator_b.csv` each contain 10 rows. Labels and rationales are blank in both packets.
- Both packets currently show `2026-11-28` as the scenario date, while the canonical cases file leaves the date null. The reviewers should agree on and freeze the date; after that, update the canonical file to match before finalization.
- The project has 1,554 processed provision chunks. The DPDP Act and Rules PDFs have been restored under `data/raw/dpdp/` and their SHA-256 hashes match `data/raw/dpdp/SOURCES.md`.
- The GDPR and California source snapshots are not present under `data/raw/`. Their official URLs and hashes are recorded in `data/raw/gdpr/SOURCES.md` and `data/raw/ccpa/SOURCES.md`. The official sites did not return downloadable content through this environment; reviewers can use the linked official sources directly.

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

The processed chunks preserve source hashes, but the project should restore or otherwise make the original GDPR and California source snapshots available to the reviewers. The DPDP source documents are the Gazette of India notifications for the Act and the 2025 Rules. The commencement schedule in those notifications must be checked against any later Gazette notice before labels are finalized.

Official reference links:

- [GDPR, EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng/)
- [DPDP Act commencement notification, G.S.R. 843(E)](https://www.meity.gov.in/static/uploads/2025/11/c56ceae6c383460ca69577428d36828b.pdf)
- [DPDP Rules notification, G.S.R. 846(E)](https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf)
- [California Civil Code, official Legislature site](https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?lawCode=CIV&division=3.&title=1.81.5.&part=4.&chapter=&article=)
- [CCPA threshold update, California Privacy Protection Agency](https://cppa.ca.gov/regulations/cpi_adjustment.html)

## After review

1. Confirm and freeze the scenario date and predicate schema with both annotators.
2. Supply the missing scenario facts or remove cases that cannot be made determinate.
3. Have both annotators independently complete their existing packets without sharing labels.
4. Compare labels, adjudicate each disagreement, and preserve the original packets.
5. Build and validate a new reviewed candidate with `scripts/finalize_golden_annotations.py` and `scripts/validate_golden_dataset.py`.
6. Keep unresolved cases out of scored evaluation and expand toward the 30–40 reviewed cases in `docs/golden_dataset_labeling_guide.md`.
