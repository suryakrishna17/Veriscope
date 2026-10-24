# AICTE Extension of Approval (EoA) Regulatory Rule Catalogue

**Source Document**: AICTE Approval Process Handbook (APH 2024–25 to 2026–27)  
**Statutory Authority**: All India Council for Technical Education Act, 1987 (Act 52 of 1987)  
**Operational Scope**: Chapter II (*Grant of Extension of Approval for Existing Institutions*) & Annexure-2 (*Documents to be Uploaded / Submitted by Existing Institutions*)  
**Ruleset File**: [`backend/app/rules/rulesets/aicte_eoa_chapter2.v1.yaml`](file:///C:/Users/Navya%20Anubhuti/.gemini/antigravity/scratch/Veriscope/backend/app/rules/rulesets/aicte_eoa_chapter2.v1.yaml)  
**Status**: `is_provisional: true` (Provisional regulatory interpretation; review required prior to production enforcement)

---

## 1. Executive Summary & Regulatory Authority

Under Chapter II of the official AICTE Approval Process Handbook (APH 2024–27), existing technical institutions seeking annual **Extension of Approval (EoA)**, intake variations, or continuation of approved programmes must fulfill rigorous statutory, infrastructural, and academic prerequisites. 

VeriScope models these statutory mandates as **deterministic, source-traceable rules**. Every rule in this catalogue is grounded in specific chapters, clauses, annexures, and published page numbers of the official handbook.

### Trust & Language Boundaries
In strict compliance with VeriScope's high-assurance trust architecture:
* **No Speculative Verdicts**: Rules flag discrepancies, missing records, or unconfirmed declarations; they never assert binary authenticity claims or use speculative labels.
* **Provisional Standing**: Rules remain marked `is_provisional: true` until verified by a named regulatory policy reviewer.
* **Reviewer Gating**: Rule evaluations provide structured evidence citations and recommended next actions, serving as a copilot for human regulatory decision-makers rather than an autonomous judge.

---

## 2. Rule Architecture & Schema Conformance

Each rule in the catalogue implements the standard schema enforced by the VeriScope rule engine ([`app/rules/engine.py`](file:///C:/Users/Navya%20Anubhuti/.gemini/antigravity/scratch/Veriscope/backend/app/rules/engine.py)):

| Schema Field | Type | Description |
|---|---|---|
| `id` | `string` | Unique identifier prefixed with `EOA-` (e.g. `EOA-CMP-001`, `EOA-COM-001`). |
| `category` | `string` | Engine category: `completeness`, `compliance`, `consistency`, or `document_signal`. |
| `severity` | `string` | Risk weighting: `high`, `medium`, `low`, or `info`. |
| `summary` | `string` | Factual, verdict-free summary of the potential compliance issue. |
| `clause_citation` | `string` | Official handbook citation: Chapter, Clause, Annexure, and Page reference. |
| `applicability` | `string` | Scope of institutions subject to the requirement. |
| `limitations` | `string` | Trust boundaries, OCR limits, and what remains subject to human verification. |
| `operator` | `string` | Deterministic evaluator registered in [`app/rules/operators.py`](file:///C:/Users/Navya%20Anubhuti/.gemini/antigravity/scratch/Veriscope/backend/app/rules/operators.py). |
| `params` | `dict` | Operator parameters (document types, field keys, regex patterns, thresholds). |
| `next_action` | `string` | Concrete instruction for the human reviewer to resolve or clarify the discrepancy. |

---

## 3. Comprehensive Rule Inventory

### 3.1 Completeness Audits (`category: completeness`)

| Rule ID | Severity | Statutory Provision & Clause | Operator | Required Elements | Reviewer Remediation Action |
|---|---|---|---|---|---|
| **EOA-CMP-001** | `high` | AICTE APH 2024-27 Chapter II, Clause 2.4.1 & Annexure-2 §2.1, p. 14, 82 | `required_doc_types` | `EOA_APPLICATION_FORM`, `UNIVERSITY_AFFILIATION_ORDER`, `FIRE_SAFETY_CERTIFICATE`, `BUILDING_SAFETY_CERTIFICATE` | Request the institution upload the missing mandatory statutory documents. |
| **EOA-CMP-002** | `high` | AICTE APH 2024-27 Chapter II, Clause 2.4.2 & Annexure-2 §2.2, p. 15, 83 | `required_doc_types` | `LAND_DOCUMENT_AND_USE_CERTIFICATE`, `OCCUPANCY_CERTIFICATE` | Request registered copies of land ownership/lease documents and local authority occupancy certificate. |
| **EOA-CMP-003** | `medium` | AICTE APH 2024-27 Chapter II, Clause 2.3.1 & Clause 2.4.1, p. 13, 14 | `required_fields` | Form fields: `institution_name`, `institution_id`, `academic_year`, `principal_director_name`, `land_category`, `total_built_up_area` | Check the application page; if OCR failed to recognize the field, correct manually or request resubmission. |
| **EOA-CMP-004** | `medium` | AICTE APH 2024-27 Chapter II, Clause 2.9 & Annexure-2 §2.1(a), p. 18, 82 | `required_fields` | Affiliation order fields: `university_name`, `academic_year`, `affiliation_order_number`, `order_date` | Review the affiliation document to confirm the order covers the requested academic session. |
| **EOA-CMP-005** | `medium` | AICTE APH 2024-27 Chapter II, Clause 2.8.1 & Annexure-2 §2.1(b), p. 17, 82 | `required_fields` | Fire clearance fields: `fire_authority_name`, `noc_number`, `valid_until`, `building_coverage` | Check the uploaded fire safety clearance for designated authority seal, NOC number, and expiry date. |
| **EOA-CMP-006** | `medium` | AICTE APH 2024-27 Chapter II, Clause 2.8.2 & Annexure-2 §2.1(c), p. 17, 82 | `required_fields` | Structural safety fields: `structural_engineer_name`, `license_registration_number`, `valid_until` | Verify the certificate was issued by an empanelled structural engineer with valid license details. |

---

### 3.2 Format & Identifier Conformance (`category: compliance`)

| Rule ID | Severity | Statutory Provision & Clause | Operator | Pattern / Expected Format | Reviewer Remediation Action |
|---|---|---|---|---|---|
| **EOA-FMT-001** | `medium` | AICTE APH 2024-27 Chapter II, Clause 2.3.1, p. 13 | `regex` | `^\d-\d{9,10}$` (AICTE Permanent Institution ID) | Verify the permanent AICTE institution ID with central portal records. |
| **EOA-FMT-002** | `low` | AICTE APH 2024-27 Chapter II, Clause 2.2, p. 13 | `regex` | `^20\d{2}-\d{2}$` (Consecutive academic session format, e.g. `2024-25`) | Confirm that the academic session represents a valid consecutive cycle (e.g., 2024-25). |

---

### 3.3 Chronology & Certificate Validity (`category: compliance`)

| Rule ID | Severity | Statutory Provision & Clause | Operator | Temporal Verification | Reviewer Remediation Action |
|---|---|---|---|---|---|
| **EOA-DAT-001** | `medium` | AICTE APH 2024-27 Chapter II, Clause 2.2 & 2.3.2, p. 13, 14 | `date_not_future` | `application_date <= today` | Request clarification on the timeline discrepancy with the submitting registrar. |
| **EOA-DAT-002** | `high` | AICTE APH 2024-27 Chapter II, Clause 2.8.1 & Annexure-2 §2.1(b), p. 17, 82 | `date_order` | `application_date <= valid_until` (Fire Safety NOC) | Check if an official renewal receipt or updated certificate has been issued by the state fire authority. |
| **EOA-DAT-003** | `high` | AICTE APH 2024-27 Chapter II, Clause 2.8.2 & Annexure-2 §2.1(c), p. 17, 82 | `date_order` | `application_date <= valid_until` (Structural Safety) | Require submission of a current structural fitness report signed by a registered structural engineer. |

---

### 3.4 Statutory Committees & Regulatory Bodies (`category: compliance`)

Under Annexure-2 §2.3 and Chapter II Clause 2.7, every existing institution must establish and maintain active statutory student welfare, equity, and safety committees:

| Rule ID | Severity | Statutory Authority & APH Citation | Operator | Expected Value | Reviewer Remediation Action |
|---|---|---|---|---|---|
| **EOA-COM-001** | `high` | AICTE (Prevention and Prohibition of Ragging in Technical Institutions) Regulations, 2009; APH Cl 2.7.1 & Annexure-2 §2.3(a), p. 16, 83 | `field_equals` | `anti_ragging_committee_constituted: "yes"` | Request the formal order and member notification for the Anti-Ragging Committee. |
| **EOA-COM-002** | `high` | AICTE Anti-Ragging Regulations, 2009; APH Cl 2.7.1 & Annexure-2 §2.3(a), p. 16, 83 | `field_equals` | `anti_ragging_squad_constituted: "yes"` | Require upload of the active Anti-Ragging Squad duty roster and contact details. |
| **EOA-COM-003** | `high` | Sexual Harassment of Women at Workplace Act, 2013 (Act 14 of 2013); AICTE Regulations 2016; APH Cl 2.7.2 & Annexure-2 §2.3(b), p. 16, 83 | `field_equals` | `icc_constituted: "yes"` | Request institutional order establishing the ICC with presiding officer and non-governmental representative. |
| **EOA-COM-004** | `high` | AICTE (Redressal of Grievance of Students) Regulations, 2019; APH Cl 2.7.3 & Annexure-2 §2.3(c), p. 16, 83 | `field_equals` | `sgrc_constituted: "yes"` | Request constitution order for SGRC and confirmation of the university-appointed Ombudsman. |
| **EOA-COM-005** | `medium` | Scheduled Castes and Scheduled Tribes (Prevention of Atrocities) Act, 1989; APH Cl 2.7.4 & Annexure-2 §2.3(d), p. 16, 83 | `field_equals` | `sc_st_committee_constituted: "yes"` | Ask the institution to submit the formal constitution office order for the SC/ST committee. |
| **EOA-COM-006** | `medium` | AICTE APH 2024-27 Chapter II, Clause 2.7.5 & Annexure-2 §2.3(e), p. 16, 83 | `field_equals` | `iqac_established: "yes"` | Request institutional notification establishing the IQAC. |

---

### 3.5 Infrastructure & Transparency Norms (`category: compliance` / `completeness`)

| Rule ID | Severity | Statutory Provision & Clause | Operator | Expected Value | Reviewer Remediation Action |
|---|---|---|---|---|---|
| **EOA-INF-001** | `high` | Rights of Persons with Disabilities Act, 2016; APH Cl 2.7.6 & Annexure-2 §2.4, p. 16, 84 | `field_equals` | `barrier_free_environment_available: "yes"` | Request photographs and architect certificate showing accessible ramps, lifts, and specialized toilets. |
| **EOA-INF-002** | `medium` | AICTE APH 2024-27 Chapter II, Clause 2.4.3 & Clause 2.12, p. 15, 19 | `field_equals` | `mandatory_disclosure_url_active: "yes"` | Review the public institution website to confirm the mandatory disclosure is accessible. |
| **EOA-INF-003** | `high` | AICTE APH 2024-27 Chapter II, Clause 2.3.3 & Affidavit-2, p. 14, 186 | `field_equals` | `declaration_checked: "yes"` | Request the applicant re-sign and confirm the statutory undertaking declaration. |

---

### 3.6 Cross-Document Consistency (`category: consistency`)

| Rule ID | Severity | Statutory Provision & Clause | Operator | Comparison Strategy | Reviewer Remediation Action |
|---|---|---|---|---|---|
| **EOA-CON-001** | `high` | AICTE APH 2024-27 Chapter II, Clause 2.4.1 & Annexure-2 §2.1, p. 14, 82 | `cross_doc_match` | Fuzzy match (`kind: name`, similarity >= 88) across `EOA_APPLICATION_FORM`, `UNIVERSITY_AFFILIATION_ORDER`, `FIRE_SAFETY_CERTIFICATE` | Reconcile naming discrepancies across documents to confirm legal institutional identity. |
| **EOA-CON-002** | `high` | AICTE APH 2024-27 Chapter II, Clause 2.9 & Annexure-2 §2.1(a), p. 18, 82 | `cross_doc_match` | Exact match (`kind: exact`, threshold 100) between application form and university affiliation order | Request the current academic session affiliation letter from the affiliating university. |

---

### 3.7 Document Signal & Hygiene (`category: document_signal`)

| Rule ID | Severity | Statutory Provision & Clause | Operator | Trigger Condition | Reviewer Remediation Action |
|---|---|---|---|---|---|
| **EOA-SIG-001** | `medium` | AICTE APH 2024-27 Chapter II, Clause 2.3.2 & Chapter VII §7.4(a), p. 14, 71 | `duplicate_hash` | SHA-256 match on clearances across distinct cases | Inspect the matching files to determine whether documents were shared across multiple institutions. |
| **EOA-SIG-002** | `low` | AICTE APH 2024-27 Chapter II, Clause 2.3.2 & Annexure-2 §2.5, p. 14, 84 | `scan_quality` | OCR confidence < 80% or low DPI scan | Compare the extracted details against the original scan and correct any OCR misreadings. |

---

## 4. Complex Numerical Norms: Human Review Required Register

As directed by VeriScope's engineering guidelines, complex numerical thresholds that vary by geographical classification, course vertical, or historical approval dates are **not hardcoded into automated boolean checks without verified prerequisite conditions**. Instead, they are catalogued below for explicit human reviewer adjudication:

### 4.1 Land Norms (Chapter II Cl 2.4.2 & Appendix 4 Table 4.1)
* **Statutory Requirement**: Minimum contiguous land area held under registered title or minimum 30-year unencumbered lease.
* **Geographical Variances**:
  * *Mega / Metro Cities*: 1.5 Acres (Engineering & Technology), 0.5 Acres (Management/MCA).
  * *Urban Areas*: 2.5 Acres (Engineering & Technology), 1.0 Acres (Management/MCA).
  * *Rural Areas*: 7.5 Acres (Engineering & Technology), 2.0 Acres (Management/MCA).
* **Why Human Review is Required**:
  1. Land zoning classification (Mega/Metro/Urban/Rural) requires local municipal revenue authority verification.
  2. Contiguity exceptions (e.g. divided by public road with authorized overpass/underpass under Clause 4.1.3) cannot be resolved by simple numerical checks without revenue maps.
  3. North Eastern states, hilly regions, and specific UTs have statutory relaxations under Clause 4.1.2.

### 4.2 Built-Up Area Norms (Chapter II Cl 2.4.2 & Appendix 4 Table 4.2)
* **Statutory Requirement**: Carpet area compliance across Instructional Area, Administrative Area, Amenities Area, and Circulation area.
* **Norm Breakdown**:
  * Classrooms: 66 sq.m. minimum per division.
  * Tutorial Rooms: 33 sq.m. minimum per division.
  * Laboratories: Specific square meterage per branch (e.g., 66 to 132 sq.m. per lab).
  * Central Library: Minimum 400 sq.m. (Degree) or 300 sq.m. (Diploma).
  * Computer Centre: Minimum 150 sq.m.
* **Why Human Review is Required**:
  Total required carpet area is an aggregated mathematical sum of sanctioned course divisions, laboratory schedules, and intake tiers. Reviewers must cross-examine the approved floor plan drawing signed by a registered architect against portal figures.

### 4.3 Faculty Cadre Ratio & Faculty-Student Ratio (Chapter II Cl 2.8.3 & Appendix 7)
* **Statutory Requirement**:
  * Undergraduate Engineering & Technology: FSR of 1:20 (Cadre ratio 1 Professor : 2 Associate Professors : 6 Assistant Professors).
  * Postgraduate Management / Engineering: FSR of 1:15 or 1:12.
* **Why Human Review is Required**:
  Cadre distribution requires validating faculty appointment qualifications, experience, and bank disbursement statements. Incomplete rosters or faculty sharing across shifts require manual scrutiny rather than binary pass/fail determinations.

### 4.4 Joint Fixed Deposit Receipts (FDR) / Endowment Funds (Chapter II Cl 2.10 & Appendix 8)
* **Statutory Requirement**: Maintenance of FDR created in the joint names of the Society/Trust and Regional Officer, AICTE.
* **Why Human Review is Required**:
  Bank lien letters and encumbrance-free certificates must be verified directly with the issuing scheduled bank branch.

---

## 5. Verification & Test Evidence

The catalogue is comprehensively tested and verified in [`backend/tests/test_eoa_rules.py`](file:///C:/Users/Navya%20Anubhuti/.gemini/antigravity/scratch/Veriscope/backend/tests/test_eoa_rules.py):
* **Schema Integrity**: Verifies loader compatibility, checksum calculation, versioning, unique rule IDs, and valid category/severity definitions.
* **Statutory Traceability**: Confirms that 100% of rules possess valid `clause_citation`, `applicability`, `limitations`, and `next_action` properties.
* **Evaluator Coverage**: Tests passing evaluations against a complete reference case and isolated failure evaluations for every individual rule.
* **Trust Language Audit**: Asserts that zero prohibited verdict terms appear within the catalogue content.
