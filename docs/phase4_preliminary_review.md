# Phase 4 preliminary case review

Review date and provisional scenario date: **2026-11-28**.

This is a preparation memo, not an independent annotation or legal opinion. It records why the ten seed cases are not ready to receive substantive gold labels. The annotator packets remain blank; no labels or agreement scores have been invented. A qualified reviewer must verify current law and case facts before final adjudication.

## Time-sensitive commencement check

India's 13 November 2025 commencement notification schedules DPDP Act sections 3–17, including sections 8, 9, and 16, for eighteen months after Gazette publication. The 2025 Rules schedule rules 3, 5–16, 22, and 23 on the same timetable. On the selected 28 November 2026 date, those provisions are scheduled to commence on 13 May 2027. Verify that no later notification changed the schedule before using the dataset. Sources: [MeitY commencement notification G.S.R. 843(E)](https://www.meity.gov.in/static/uploads/2025/11/c56ceae6c383460ca69577428d36828b.pdf) and [MeitY DPDP Rules 2025 G.S.R. 846(E)](https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf?v=20261027115856).

GDPR applicability cannot be inferred from an EU resident's location alone. For these non-EU organizations, annotators must inspect the specific Article 3 facts (establishment, offering goods or services to people in the Union, or monitoring their behavior) and identify the responsible controller/processor. Transfers also require a covered exporter and an actual Chapter V transfer. Use the [official EUR-Lex GDPR text](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng/).

CCPA coverage requires facts about the business, California activity, and current statutory thresholds; do not infer coverage from a California consumer alone. Start with the [California Privacy Protection Agency FAQ](https://cppa.ca.gov/faq) and verify the threshold effective for the selected date.

## Case-by-case blockers

| Case | Required review before a substantive label |
| --- | --- |
| case-001 | Establish GDPR Article 3 scope and the Article 17 erasure ground; the cited DPDP section 8(7) is not yet in force on the selected date. |
| case-002 | Identify the actual retention law, record, purpose, and duration; establish GDPR scope and whether Article 17(3)(b) applies. DPDP section 8(7) is not yet in force. |
| case-003 | Verify GDPR scope and the relevant Article 17(1) ground. The DPDP erasure provision is not yet in force on the selected date. |
| case-004 | Name and verify the retention obligation and its exact coverage; establish GDPR scope. The DPDP provision is not yet in force. |
| case-005 | Verify GDPR scope, CCPA business coverage and threshold, and that both laws govern the same record and operation. |
| case-006 | DPDP Rule 15 is not yet in force on the selected date. Establish GDPR territorial scope, exporter/controller roles, and the applicable transfer mechanism. |
| case-007 | Identify the actual exporter and roles, establish GDPR Article 3 scope, and determine whether the movement is a Chapter V transfer. |
| case-008 | DPDP section 16 and Rule 15 are not yet in force on the selected date. The hypothetical restriction and available GDPR safeguard do not alone establish contradictory duties; establish applicability and whether the same transfer is required. |
| case-009 | DPDP section 9 is not yet in force on the selected date. Provide the child's age and relevant Member State threshold, and establish GDPR Article 3 and Article 8 conditions. |
| case-010 | Establish CCPA and GDPR coverage and whether the same actor, data, purpose, and operation are actually constrained. The current scenario does not establish this overlap. |

The conservative provisional disposition is **unresolved / NEEDS_REVIEW for all ten cases** until the listed facts and legal questions are addressed. This disposition is not written into either annotator packet and is not a gold label. The project must not calculate model accuracy from these cases in this state.

## Completion gate

1. A legal reviewer confirms the selected as-of date and each cited provision's status and scope.
2. The team supplies missing scenario facts or removes cases that cannot be made determinate.
3. Two annotators independently complete the dated packets. They must not copy this memo as if it were an independent annotation.
4. The team freezes the predicate schema, compares labels, adjudicates every disagreement, and builds a new reviewed candidate with `scripts/finalize_golden_annotations.py`.
5. Keep `NEEDS_REVIEW` rows out of scored splits. Expand the reviewed dataset toward the 30–40 cases specified in the labeling guide, split by case ID, then evaluate only after labels and the schema are frozen.
