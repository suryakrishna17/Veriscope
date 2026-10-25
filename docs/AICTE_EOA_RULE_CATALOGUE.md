# AICTE Extension of Approval (EoA) Regulatory Rule Catalogue

**Source Document**: AICTE Approval Process Handbook (APH 2024–25 to 2026–27)  
**Statutory Authority**: All India Council for Technical Education Act, 1987 (Act 52 of 1987)  
**Operational Scope**: Chapter II (*Grant of Extension of Approval for Existing Institutions*), Annexure-2 (*Documents to be Uploaded / Submitted by Existing Institutions*), and Appendix 6 (*Essential Requirements*)  
**Ruleset File**: [`backend/app/rules/rulesets/aicte_eoa_chapter2.v1.yaml`](../backend/app/rules/rulesets/aicte_eoa_chapter2.v1.yaml)  
**Status**: `is_provisional: true` (Provisional regulatory interpretation; review required prior to production enforcement)

---

## 1. Executive Summary & Regulatory Authority

Under Chapter II of the official AICTE Approval Process Handbook (APH 2024–27), existing technical institutions seeking annual **Extension of Approval (EoA)**, intake variations, or continuation of approved programmes must fulfill rigorous statutory, infrastructural, and academic prerequisites. 

VeriScope models these statutory mandates as **deterministic, source-traceable rules**. Every rule in this catalogue is grounded in specific chapters, clauses, annexures, and published sections of the official handbook.

### Trust, Language & Regulatory Boundaries
In strict compliance with VeriScope's high-assurance trust architecture:
* **No Speculative Verdicts**: Rules flag discrepancies, missing records, or unconfirmed declarations; they never assert binary authenticity claims or use speculative labels.
* **Provisional Standing**: Rules remain marked `is_provisional: true` until verified by a named regulatory policy reviewer.
* **Self-Disclosure vs. Statutory Compliance**: An applicant checking `"yes"` on a web-portal form constitutes self-disclosure, **not** certified statutory compliance. Reviewers are explicitly prompted to inspect underlying evidentiary appointment orders, gazette notifications, and committee rosters.
* **Reviewer Gating**: Rule evaluations provide structured evidence citations and recommended next actions, serving as an automated copilot for human regulatory decision-makers rather than an autonomous decision-maker.

---

## 2. Institutional Applicability & Exceptions

The catalogue models concrete institutional scope distinctions grounded in APH provisions:

1. **Affiliated Institutions vs. Autonomous / Standalone Institutions**:
   * Technical institutions affiliated with State or Central Universities require a valid `UNIVERSITY_AFFILIATION_ORDER` (`EOA-CMP-001`, `EOA-CMP-004`, `EOA-CON-002`).
   * **Statutory Exception**: Standalone institutions offering PGDM, autonomous degree institutions, and deemed-to-be universities do not affiliate with state universities and are legally exempt from submitting university affiliation orders under Chapter II.
2. **Routine EoA Continuation vs. Expansions / Alterations**:
   * For **routine annual EoA continuation** based on Self-Disclosure (Clause 2.5), land title deeds and occupancy certificates remain on permanent AICTE record from establishment and do not require annual re-upload.
   * Upload of fresh `LAND_DOCUMENT_AND_USE_CERTIFICATE` and `OCCUPANCY_CERTIFICATE` (`EOA-CMP-002`) is strictly mandatory when applying for **Increase in Intake / Additional Course(s)** (Clause 2.6), **New Programmes** (Clause 2.8), or **Change of Site / Location** (Clause 2.10).
3. **Safety Certificate In-Flight Renewals**:
   * Automated date checks (`EOA-DAT-002`, `EOA-DAT-003`) flag when stated certificate expiration dates precede application filing. However, where municipal fire authorities have renewal backlogs and the institution has submitted an official renewal receipt or fee challan, automated checks cannot determine compliance; such cases require explicit human reviewer adjudication.

---

## 3. Comprehensive Rule Inventory

### 3.1 Completeness Audits (`category: completeness`)

| Rule ID | Severity | Statutory Provision & Clause | Operator | Required Elements | Reviewer Remediation Action |
|---|---|---|---|---|---|
| **EOA-CMP-001** | `high` | AICTE APH 2024-27 Chapter II, Clause 2.4 & Clause 2.5, and Annexure-2 | `required_doc_types` | `EOA_APPLICATION_FORM`, `UNIVERSITY_AFFILIATION_ORDER`, `FIRE_SAFETY_CERTIFICATE`, `BUILDING_SAFETY_CERTIFICATE` | Request missing statutory documents. For autonomous or standalone PGDM institutions, verify statutory non-affiliation status. |
| **EOA-CMP-002** | `medium` | AICTE APH 2024-27 Chapter II, Clause 2.5, Clause 2.6, and Annexure-2 | `required_doc_types` | `LAND_DOCUMENT_AND_USE_CERTIFICATE`, `OCCUPANCY_CERTIFICATE` | Confirm whether application is routine continuation or expansion. If expansion is sought, require registered land deeds and municipal occupancy certificate. |
| **EOA-CMP-003** | `medium` | AICTE APH 2024-27 Chapter II, Clause 2.3 & Clause 2.5, and Annexure-2 | `required_fields` | Form fields: `institution_name`, `institution_id`, `academic_year`, `principal_director_name`, `land_category`, `total_built_up_area` | Check application page; correct OCR misreads or request clarification. |
| **EOA-CMP-004** | `medium` | AICTE APH 2024-27 Chapter II, Clause 2.5, and Annexure-2 | `required_fields` | Affiliation order fields: `university_name`, `academic_year`, `affiliation_order_number`, `order_date` | Confirm affiliation order covers approved courses and session. For autonomous institutions, verify non-affiliation status. |
| **EOA-CMP-005** | `medium` | AICTE APH 2024-27 Chapter II, Clause 2.5, Annexure-2, and Appendix 6 | `required_fields` | Fire clearance fields: `fire_authority_name`, `noc_number`, `valid_until`, `building_coverage` | Inspect fire clearance for authority seal, NOC number, and campus block coverage. |
| **EOA-CMP-006** | `medium` | AICTE APH 2024-27 Chapter II, Clause 2.5, Annexure-2, and Appendix 6 | `required_fields` | Structural safety fields: `structural_engineer_name`, `license_registration_number`, `valid_until` | Verify certificate was issued by an empanelled structural engineer with active registration details. |

---

### 3.2 Format & Regulatory Conformance (`category: compliance`)

| Rule ID | Severity | Statutory Provision & Clause | Operator | Pattern / Expected Format | Reviewer Remediation Action |
|---|---|---|---|---|---|
| **EOA-FMT-001** | `medium` | AICTE APH 2024-27 Chapter II, Clause 2.3 | `regex` | `^\d-\d{9,10}$` (AICTE Permanent Institution ID) | Verify the permanent AICTE institution ID with central portal records. |
| **EOA-FMT-002** | `low` | AICTE APH 2024-27 Chapter II, Clause 2.2 & Clause 2.3 | `regex` | `^20\d{2}-\d{2}$` (Consecutive academic session format, e.g. `2024-25`) | Confirm that the academic session represents a valid consecutive cycle. |

---

### 3.3 Chronology & Certificate Validity (`category: compliance`)

| Rule ID | Severity | Statutory Provision & Clause | Operator | Temporal Verification | Reviewer Remediation Action |
|---|---|---|---|---|---|
| **EOA-DAT-001** | `medium` | AICTE APH 2024-27 Chapter II, Clause 2.2 & Clause 2.3 | `date_not_future` | `application_date <= today` | Request clarification on timeline discrepancy with submitting registrar. |
| **EOA-DAT-002** | `high` | AICTE APH 2024-27 Chapter II, Clause 2.5, Annexure-2, and Appendix 6 | `date_order` | `application_date <= valid_until` (Fire Safety NOC) | If stated expiration precedes filing, inspect whether a valid renewal receipt or temporary fire department extension was uploaded. |
| **EOA-DAT-003** | `high` | AICTE APH 2024-27 Chapter II, Clause 2.5, Annexure-2, and Appendix 6 | `date_order` | `application_date <= valid_until` (Structural Safety) | If expired or granted on a perpetual/conditional basis, refer to reviewer to inspect engineer's fitness endorsement. |

---

### 3.4 Statutory Committees: Self-Disclosure Audits (`category: compliance`)

Under Annexure-2 and Chapter II Clause 2.5, every existing institution must establish and maintain active statutory student welfare, equity, and safety committees:

| Rule ID | Severity | Statutory Authority & APH Citation | Operator | Expected Value | Reviewer Remediation Action |
|---|---|---|---|---|---|
| **EOA-COM-001** | `high` | AICTE Anti-Ragging Regulations, 2009; APH Ch II, Cl 2.5, Annexure-2, App 6 | `field_equals` | `anti_ragging_committee_constituted: "yes"` | Review self-disclosure. Inspect uploaded office order to verify representation from police, civil administration, NGOs, faculty, and students. |
| **EOA-COM-002** | `high` | AICTE Anti-Ragging Regulations, 2009; APH Ch II, Cl 2.5, Annexure-2, App 6 | `field_equals` | `anti_ragging_squad_constituted: "yes"` | Review self-disclosure. Inspect active Anti-Ragging Squad duty roster and emergency contact details. |
| **EOA-COM-003** | `high` | Sexual Harassment of Women at Workplace Act, 2013; AICTE Regulations 2016; APH Ch II, Cl 2.5, Annexure-2, App 6 | `field_equals` | `icc_constituted: "yes"` | Review self-disclosure. Inspect uploaded institutional order to confirm female presiding officer, faculty/staff, and external NGO representative. |
| **EOA-COM-004** | `high` | AICTE (Redressal of Grievance of Students) Regulations, 2019; APH Ch II, Cl 2.5, Annexure-2, App 6 | `field_equals` | `sgrc_constituted: "yes"` | Review self-disclosure. Inspect SGRC constitution order and verify appointment of university Ombudsman. |
| **EOA-COM-005** | `medium` | Scheduled Castes and Scheduled Tribes (Prevention of Atrocities) Act, 1989; APH Ch II, Cl 2.5, Annexure-2, App 6 | `field_equals` | `sc_st_committee_constituted: "yes"` | Review self-disclosure. Inspect constitution office order for SC/ST committee to verify representation. |
| **EOA-COM-006** | `medium` | AICTE APH 2024-27 Chapter II, Clause 2.5, Annexure-2, and Appendix 6 | `field_equals` | `iqac_established: "yes"` | Review self-disclosure. Inspect institutional notification establishing the IQAC. |

---

### 3.5 Infrastructure & Transparency Norms (`category: compliance` / `completeness`)

| Rule ID | Severity | Statutory Provision & Clause | Operator | Expected Value | Reviewer Remediation Action |
|---|---|---|---|---|---|
| **EOA-INF-001** | `high` | Rights of Persons with Disabilities Act, 2016; APH Ch II, Cl 2.5, Annexure-2, App 6 | `field_equals` | `barrier_free_environment_available: "yes"` | Examine self-disclosure. Inspect architect certificate and campus photographs to verify accessible ramps, lifts, and Divyangjan-friendly toilets. |
| **EOA-INF-002** | `medium` | AICTE APH 2024-27 Chapter II, Clause 2.13 and Annexure-2 | `field_equals` | `mandatory_disclosure_url_active: "yes"` | Review public institution website to confirm mandatory disclosure is active and accessible. |
| **EOA-INF-003** | `high` | AICTE APH 2024-27 Chapter II, Clause 2.3, Clause 2.5, and Affidavit-2 | `field_equals` | `declaration_checked: "yes"` | Request applicant confirm statutory undertaking and inspect uploaded notarized Affidavit-2. |

---

### 3.6 Cross-Document Consistency (`category: consistency`)

| Rule ID | Severity | Statutory Provision & Clause | Operator | Comparison Strategy | Reviewer Remediation Action |
|---|---|---|---|---|---|
| **EOA-CON-001** | `high` | AICTE APH 2024-27 Chapter II, Clause 2.4, Clause 2.5, and Annexure-2 | `cross_doc_match` | Fuzzy match (`kind: name`, threshold: 88) across application, affiliation, and fire clearance | Reconcile naming discrepancies. If institution underwent a legal name change under Clause 2.12, verify AICTE/university name change orders. |
| **EOA-CON-002** | `high` | AICTE APH 2024-27 Chapter II, Clause 2.5 and Annexure-2 | `cross_doc_match` | Exact match (`kind: exact`, threshold: 100) between application form and affiliation order | Request current academic session affiliation letter from affiliating university. |

---

### 3.7 Document Signal & Hygiene (`category: document_signal`)

| Rule ID | Severity | Statutory Provision & Clause | Operator | Trigger Condition | Reviewer Remediation Action |
|---|---|---|---|---|---|
| **EOA-SIG-001** | `medium` | AICTE APH 2024-27 Chapter II, Clause 2.3 & Chapter VII | `duplicate_hash` | SHA-256 match on files across distinct cases | Inspect matching files to determine whether documents were shared across multiple institutions. |
| **EOA-SIG-002** | `low` | AICTE APH 2024-27 Chapter II, Clause 2.3 and Annexure-2 | `scan_quality` | OCR confidence < 80% or low DPI scan | Compare extracted details against original scan and correct any OCR misreadings. |

---

## 4. Complex Numerical Norms: Human Review Required Register

Complex numerical thresholds that vary by geographical classification, course vertical, or historical approval dates are **not hardcoded into automated boolean checks without verified prerequisite conditions**. Instead, they are catalogued below for explicit human reviewer adjudication:

### 4.1 Land Norms (Chapter II Cl 2.5, 2.6 & Appendix 4 Table 4.1)
* **Statutory Requirement**: Minimum contiguous land area held under registered title or minimum 30-year unencumbered lease.
* **Geographical Variances**:
  * *Mega / Metro Cities*: 1.5 Acres (Engineering & Technology), 0.5 Acres (Management/MCA).
  * *Urban Areas*: 2.5 Acres (Engineering & Technology), 1.0 Acres (Management/MCA).
  * *Rural Areas*: 7.5 Acres (Engineering & Technology), 2.0 Acres (Management/MCA).
* **Why Human Review is Required**:
  1. Land zoning classification (Mega/Metro/Urban/Rural) requires local municipal revenue authority verification.
  2. Contiguity exceptions (e.g. divided by public road with authorized overpass/underpass under Clause 4.1.3) cannot be resolved by simple numerical checks without revenue maps.
  3. North Eastern states, hilly regions, and specific UTs have statutory relaxations under Clause 4.1.2.

### 4.2 Built-Up Area Norms (Chapter II Cl 2.5, 2.6 & Appendix 4 Table 4.2)
* **Statutory Requirement**: Carpet area compliance across Instructional Area, Administrative Area, Amenities Area, and Circulation area.
* **Norm Breakdown**:
  * Classrooms: 66 sq.m. minimum per division.
  * Tutorial Rooms: 33 sq.m. minimum per division.
  * Laboratories: Specific square meterage per branch (e.g., 66 to 132 sq.m. per lab).
  * Central Library: Minimum 400 sq.m. (Degree) or 300 sq.m. (Diploma).
  * Computer Centre: Minimum 150 sq.m.
* **Why Human Review is Required**:
  Total required carpet area is an aggregated mathematical sum of sanctioned course divisions, laboratory schedules, and intake tiers. Reviewers must cross-examine the approved floor plan drawing signed by a registered architect against portal figures.

### 4.3 Faculty Cadre Ratio & Faculty-Student Ratio (Chapter II Cl 2.5 & Appendix 7)
* **Statutory Requirement**:
  * Undergraduate Engineering & Technology: FSR of 1:20 (Cadre ratio 1 Professor : 2 Associate Professors : 6 Assistant Professors).
  * Postgraduate Management / Engineering: FSR of 1:15 or 1:12.
* **Why Human Review is Required**:
  Cadre distribution requires validating faculty appointment qualifications, experience, and bank disbursement statements. Incomplete rosters or faculty sharing across shifts require manual scrutiny rather than binary pass/fail determinations.

### 4.4 Joint Fixed Deposit Receipts (FDR) / Endowment Funds (Chapter II Cl 2.5 & Appendix 8)
* **Statutory Requirement**: Maintenance of FDR created in the joint names of the Society/Trust and Regional Officer, AICTE.
* **Why Human Review is Required**:
  Bank lien letters and encumbrance-free certificates must be verified directly with the issuing scheduled bank branch.

---

## 5. Ruleset Foundation & Outcome Model

Under Step 3A, the AICTE EoA catalogue is executed through the unified ruleset foundation (`backend/app/rules/engine.py`):
- **Structured Outcome Model**: Every rule evaluation returns a typed `RuleEvaluation` record with an explicit outcome:
  - `PASS`: Requirement fully satisfied against submitted dossier.
  - `FAIL`: Unambiguous violation or missing statutory document/field.
  - `REVIEW_REQUIRED`: Discrepancy detected where official handbook provisions mandate human reviewer verification (e.g., safety renewal receipts, structural engineer endorsements, or document signals).
  - `NOT_APPLICABLE`: Rule condition was not met for this institution type or dossier.
- **Human Verification Boundaries**: Rules `EOA-CMP-002`, `EOA-DAT-002`, `EOA-DAT-003`, `EOA-INF-001`, `EOA-SIG-001`, and `EOA-SIG-002` are explicitly configured with `outcome_on_fail: REVIEW_REQUIRED` to preserve human discretion.
- **Rulebook Reference**: Complete guide for extending rules, operator mappings, and configuration fields is available in [docs/RULEBOOK.md](RULEBOOK.md).

---

## 6. Verification & Test Evidence

The catalogue is comprehensively tested and verified in [`backend/tests/test_eoa_rules.py`](../backend/tests/test_eoa_rules.py):
* **Schema Integrity**: Verifies loader compatibility, checksum calculation, versioning, unique rule IDs, and valid category/severity definitions.
* **Statutory Traceability**: Confirms that 100% of rules possess valid `clause_citation`, `applicability`, `limitations`, and `next_action` properties.
* **Evaluator Coverage**: Tests passing evaluations against a complete reference case, boundary conditions (equal date expiration, name similarity threshold margins), and isolated failure evaluations for every individual rule.
* **Foundation Tests (`EoaFoundationTests`)**: Tests the 4-outcome evaluation model (`PASS`, `FAIL`, `REVIEW_REQUIRED`, `NOT_APPLICABLE`), applicability filtering, verified vs. illustrative rule partition, and backward-compatible active findings extraction.
* **Trust Language Audit**: Asserts that zero prohibited verdict terms appear within the catalogue content.
