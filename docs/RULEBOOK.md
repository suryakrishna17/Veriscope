# VeriScope Rulebook & Ruleset Architecture

VeriScope uses a deterministic, pure YAML-configured rule engine designed for automated regulatory and institutional compliance audits.

The engine evaluates application dossiers against formal rulesets without database or network I/O, generating structured outcomes and findings with source citations and recommended next actions.

---

## 1. Ruleset Foundation & Registry

VeriScope maintains two distinct rulesets in `backend/app/rules/rulesets/`:

1. **`aicte_eoa_chapter2.v1.yaml` (AICTE EoA Regulatory Catalogue)**:
   - **Status**: `is_verified: true`, `verification_status: "VERIFIED_OFFICIAL"`.
   - **Scope**: AICTE Approval Process Handbook (APH 2024-25 to 2026-27), Chapter II (*Grant of Extension of Approval for Existing Institutions*), Annexure-2, and Appendix 6.
   - **Contents**: 24 deterministic rules covering Completeness, Statutory Committees, Safety Certifications, Format Norms, Cross-Document Consistency, and Document Signals.
   - **Detailed Documentation**: See [docs/AICTE_EOA_RULE_CATALOGUE.md](AICTE_EOA_RULE_CATALOGUE.md).

2. **`student_support_lite.v1.yaml` (Prototype Student Support Ruleset)**:
   - **Status**: `is_verified: false`, `verification_status: "ILLUSTRATIVE"`.
   - **Scope**: Prototype student fee waiver and identity proof verification.
   - **Purpose**: Illustrates verification mechanisms; clearly marked as illustrative prototype rules.

---

## 2. Evaluation Model & Four Outcomes

The ruleset foundation evaluates dossiers using `evaluate_ruleset(ruleset, ctx) -> list[RuleEvaluation]`.

Each rule evaluation produces exactly one of four canonical outcomes (`RuleOutcome`):

| Outcome | Description | When Generated |
|---|---|---|
| **`PASS`** | The condition or statutory check was evaluated and met successfully. | All required documents/fields present; date ordering holds; values match within tolerance. |
| **`FAIL`** | An unambiguous violation or missing requirement was detected. | Missing mandatory document (e.g. affiliation order for affiliated institution); invalid AICTE ID format; declaration unchecked. |
| **`REVIEW_REQUIRED`** | Discrepancy detected, but official handbook rules require human adjudication. | Safety certificate expired but institution may have submitted renewal receipt/challan (`EOA-DAT-002`, `EOA-DAT-003`); structural engineer fitness inspection (`EOA-INF-001`); document signal (`EOA-SIG-001`, `EOA-SIG-002`). |
| **`NOT_APPLICABLE`** | The rule does not apply to this specific institution type or dossier. | Rule is explicitly disabled (`enabled: false`) or prerequisite condition not met (e.g. document not uploaded or specific field condition false). |

### Backward Compatibility: Active Findings

For downstream case processing pipelines expecting active anomalies (`RuleResult`), `evaluate(ruleset, ctx) -> list[RuleResult]` filters evaluations to non-passing rules (`FAIL` and `REVIEW_REQUIRED`) and returns their detailed findings. Existing consumers remain 100% backward-compatible.

---

## 3. Rule Structure

Every rule in a YAML ruleset is defined with standard fields:

```yaml
  - id: EOA-DAT-002
    category: compliance
    severity: high
    summary: Fire safety certificate validity expired or unverified
    description: >
      Under AICTE APH 2024-27 Chapter II Clause 2.5, Annexure-2, and Appendix 6,
      existing institutions must possess a valid Fire Safety NOC issued by competent authorities.
    clause_citation: "AICTE APH 2024-27 Chapter II, Clause 2.5, Annexure-2, and Appendix 6, p. 28, 93, 115"
    is_verified: true
    verification_status: VERIFIED_OFFICIAL
    outcome_on_pass: PASS
    outcome_on_fail: REVIEW_REQUIRED
    applicable_condition: "Applicable to all technical institutions holding an active campus infrastructure."
    condition:
      doc_present: FIRE_SAFETY_CERTIFICATE
    operator: date_order
    params:
      earlier: {doc_type: EOA_APPLICATION_FORM, field: application_date}
      later: {doc_type: FIRE_SAFETY_CERTIFICATE, field: valid_until}
    next_action: >
      If stated expiration precedes filing, inspect whether a valid renewal receipt or
      temporary fire department extension was uploaded.
```

### Key Properties

- **`id`**: Unique identifier (e.g., `EOA-CMP-001`, `EOA-DAT-002`).
- **`category`**: One of `completeness`, `consistency`, `compliance`, `document_signal`, `issuer_check`.
- **`severity`**: One of `info`, `low`, `medium`, `high`.
- **`summary`**: Short user-facing description of the check.
- **`description`**: Detailed explanation of statutory scope and evaluation logic.
- **`clause_citation`**: Exact chapter, clause, annexure, and page references from official regulations (e.g., AICTE APH 2024–27).
- **`is_verified`**: Boolean indicating whether the rule has been verified against statutory sources.
- **`verification_status`**: `VERIFIED_OFFICIAL` for handbook rules or `ILLUSTRATIVE` for prototypes.
- **`outcome_on_pass`**: Default outcome when rule passes (`PASS`).
- **`outcome_on_fail`**: Outcome when rule condition is violated (`FAIL` or `REVIEW_REQUIRED`).
- **`condition`**: Prerequisite condition for rule applicability (e.g., `doc_present: FIRE_SAFETY_CERTIFICATE`).
- **`applicable_condition`**: Plain-language description of institutional applicability.
- **`operator`**: Evaluator function from `backend/app/rules/operators.py`.
- **`params`**: Operator-specific parameters.
- **`next_action`**: Actionable guidance for the human reviewer when this rule requires review or fails.

---

## 4. How to Add a New Rule

To add a new rule to an existing ruleset:

1. **Verify Statutory Grounding**:
   - Check the official AICTE Approval Process Handbook (or relevant statutory gazette).
   - Identify chapter, clause number, and page.
   - Confirm whether the requirement applies universally or has institutional exceptions (e.g., autonomous vs affiliated).

2. **Choose the Category and Severity**:
   - `completeness`: Document or field presence checks.
   - `compliance`: Format, dates, arithmetic, statutory declarations.
   - `consistency`: Cross-document data reconciliation.
   - `document_signal`: Scanned quality, duplicate file hashes (always `severity: low` or `medium`, outcome `REVIEW_REQUIRED`).

3. **Select or Implement an Operator**:
   - Existing operators in `backend/app/rules/operators.py`:
     - `required_doc_types`: Ensure specified document types are present in dossier.
     - `required_fields`: Ensure specified fields exist on a document.
     - `field_equals`: Verify a field matches an expected value (e.g., `"yes"`).
     - `regex`: Match field against a regular expression pattern.
     - `date_not_future`: Ensure date is on or before current date.
     - `date_order`: Ensure `earlier` date <= `later` date.
     - `arithmetic_sum`: Ensure components sum to a total field within tolerance.
     - `cross_doc_match`: Compare values across documents (fuzzy name or exact).
     - `duplicate_hash`: Check for identical document content across cases.
     - `scan_quality`: Check OCR confidence and DPI flags.
   - If a new evaluation logic is required, add an `@operator("new_operator_name")` in `backend/app/rules/operators.py`.

4. **Add Rule Entry to YAML**:
   - Add the rule block to `backend/app/rules/rulesets/aicte_eoa_chapter2.v1.yaml`.
   - Specify `outcome_on_fail: REVIEW_REQUIRED` if human adjudication is required by regulation, or `outcome_on_fail: FAIL` for clear violations.
   - Ensure trust language guidelines are respected: never use prohibited verdict words (`forged`, `fake`, `fraud`, `genuine`).

5. **Write Unit Tests**:
   - Add targeted test cases in `backend/tests/test_eoa_rules.py`.
   - Test both passing scenario (`outcome == PASS`) and failing scenario (`outcome == FAIL` or `REVIEW_REQUIRED`).
   - If rule has applicability conditions, test `outcome == NOT_APPLICABLE` when condition is unmet.

6. **Verify and Run Tests**:
   ```bash
   python -m pytest tests/test_eoa_rules.py tests/test_rules.py
   python -m ruff check app tests
   ```
