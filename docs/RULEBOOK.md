# Prototype rulebook — `student_support_lite` v1.0.0

> **Provisional.** These rules illustrate the mechanism and are **not** official AICTE requirements. Before production, a named policy reviewer must attach a source citation and effective date to each rule.

| ID | Category | Severity | Check |
|---|---|---|---|
| CMP-001 | completeness | high | Applicant signature detected on the application form |
| CMP-002 | completeness | high | Application form, authorization letter and enrolment proof all present |
| CMP-003 | completeness | medium | Form has applicant name, institution, institution ID, date, programme, total |
| CMP-004 | completeness | medium | Declaration ticked |
| CMP-005 | completeness | medium | Proof has student name, enrolment number, institution |
| FMT-001 | compliance | medium | Institution ID matches `^\d-\d{9,10}$` |
| FMT-002 | compliance | low | Phone is a valid 10-digit Indian mobile number |
| DAT-001 | compliance | medium | Application date not in the future |
| DAT-002 | compliance | high | Authorization letter still valid on the application date |
| ARI-001 | compliance | medium | Tuition + hostel + exam fee = total claimed (±0.01) |
| CON-001 | consistency | medium | Institution name matches across documents (similarity ≥ 90) |
| CON-002 | consistency | high | Student name matches across documents (similarity ≥ 88) |
| CON-003 | consistency | medium | Institution ID matches between form and letter |
| SIG-001 | document_signal | medium | Identical file submitted earlier (review signal) |
| SIG-002 | document_signal | low | PDF/image metadata shows later edits or editing software |
| SIG-003 | document_signal | low | Page read by OCR / low confidence / blur / low resolution |
| SIG-004 | document_signal | low | No seal detected on the authorization letter |

Document signals are never high severity and never decide a case.

## Adding a rule

1. Add an entry to `backend/app/rules/rulesets/student_support_lite.v1.yaml` using an existing operator (`required_doc_types`, `required_fields`, `field_equals`, `regex`, `date_not_future`, `date_order`, `arithmetic_sum`, `cross_doc_match`, `duplicate_hash`, `metadata_notes`, `scan_quality`).
2. Bump the ruleset `version` if behaviour changes.
3. Add a passing and a failing test in `backend/tests/test_rules.py`.
4. New logic → new operator in `backend/app/rules/operators.py` with the `@operator("name")` decorator.
