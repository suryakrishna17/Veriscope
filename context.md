# VeriScope — Authoritative Project Context & Engineering Reference Manual

> **Document Status**: Authoritative Project Master Reference  
> **Repository**: [https://github.com/suryakrishna17/Veriscope.git](https://github.com/suryakrishna17/Veriscope.git)  
> **Active Working Tree**: `main` (HEAD: `556c375` — *"feat(security): implement comprehensive audit fix plan (F1-F9)"*, with Render container startup fix and 148/148 test suite verification)  
> **Target Production Branch**: `main` (Latest Remote Tip: `871b3f6`)  
> **Author**: VeriScope Core Engineering Team  
> **Target Audience**: Core Contributors, Regulatory Domain Experts, SIH Evaluators, and Incoming Engineers  

---

## Table of Contents

1. [Executive Summary & Git Ground Truth](#1-executive-summary--git-ground-truth)
2. [Project Overview & Institutional Verification Problem](#2-project-overview--institutional-verification-problem)
   - [2.1 What VeriScope Is](#21-what-veriscope-is)
   - [2.2 The Real-World Regulatory Problem](#22-the-real-world-regulatory-problem)
   - [2.3 User Personas & Workflows](#23-user-personas--workflows)
   - [2.4 Why Deterministic Validation & Traceability Matter](#24-why-deterministic-validation--traceability-matter)
   - [2.5 Scope: AICTE Extension of Approval (EoA)](#25-scope-aicte-extension-of-approval-eoa)
   - [2.6 Existing Workflow vs AICTE EoA Workflow](#26-existing-workflow-vs-aicte-eoa-workflow)
   - [2.7 Capabilities Today vs Post-Step 3B & 3C](#27-capabilities-today-vs-post-step-3b--3c)
   - [2.8 System Maturity Assessment](#28-system-maturity-assessment)
   - [2.9 Core Assumptions & Boundary Limitations](#29-core-assumptions--boundary-limitations)
   - [2.10 End-to-End Data Flow Architecture](#210-end-to-end-data-flow-architecture)
3. [Technology Stack & Repository Architecture](#3-technology-stack--repository-architecture)
   - [3.1 Technology Stack Inventory](#31-technology-stack-inventory)
   - [3.2 File Tree & Directory Breakdown](#32-file-tree--directory-breakdown)
   - [3.3 Subsystem Responsibilities & Inter-Component Communication](#33-subsystem-responsibilities--inter-component-communication)
4. [Step 2 Deep Dive: AICTE EoA Rule Catalogue](#4-step-2-deep-dive-aicte-eoa-rule-catalogue)
   - [4.1 Purpose of a Structured Rule Catalogue](#41-purpose-of-a-structured-rule-catalogue)
   - [4.2 Catalogue YAML Schema & Field Semantics](#42-catalogue-yaml-schema--field-semantics)
   - [4.3 Exhaustive Rule Inventory (All 24 Rules Analyzed)](#43-exhaustive-rule-inventory-all-25-rules-analyzed)
   - [4.4 Statutory Traceability & Historical Corrections](#44-statutory-traceability--historical-corrections)
   - [4.5 Catalogue Documentation Artifacts](#45-catalogue-documentation-artifacts)
   - [4.6 Step 2 Verification & Test Results](#46-step-2-verification--test-results)
   - [4.7 Step 2 Boundary Limitations](#47-step-2-boundary-limitations)
5. [Step 3A Deep Dive: Ruleset Foundation & Outcome Model](#5-step-3a-deep-dive-ruleset-foundation--outcome-model)
   - [5.1 The Four-Valued Outcome Model (`PASS`, `FAIL`, `REVIEW_REQUIRED`, `NOT_APPLICABLE`)](#51-the-four-valued-outcome-model-pass-fail-review_required-not_applicable)
   - [5.2 `RuleEvaluation` vs `RuleResult` Models](#52-ruleevaluation-vs-ruleresult-models)
   - [5.3 Engine Architecture & Helper APIs](#53-engine-architecture--helper-apis)
   - [5.4 Operator Mechanics & Execution Flow](#54-operator-mechanics--execution-flow)
   - [5.5 Metadata & Trust Labeling Differences](#55-metadata--trust-labeling-differences)
   - [5.6 Step 3A Test Suite & Regression Verification](#56-step-3a-test-suite--regression-verification)
   - [5.7 Architecture & Completion Boundaries](#57-architecture--completion-boundaries)
   - [5.8 Step 3A Git & Pull Request Status](#58-step-3a-git--pull-request-status)
6. [Step 3B Implementation Blueprint: Backend Review Integration](#6-step-3b-implementation-blueprint-backend-review-integration)
   - [6.1 The Core Integration Challenge](#61-the-core-integration-challenge)
   - [6.2 Workstream A: Application Classification & Ruleset Routing](#62-workstream-a-application-classification--ruleset-routing)
   - [6.3 Workstream B: Document Extraction & CaseContext Construction](#63-workstream-b-document-extraction--casecontext-construction)
   - [6.4 Workstream C: Processing Pipeline & Service Layer Hookup](#64-workstream-c-processing-pipeline--service-layer-hookup)
   - [6.5 Workstream D: Finding Persistence, Fingerprinting & Idempotency](#65-workstream-d-finding-persistence-fingerprinting--idempotency)
   - [6.6 Workstream E: API Route Contracts & Schema Migration](#66-workstream-e-api-route-contracts--schema-migration)
   - [6.7 Workstream F: Human Review Safeguards & Non-Automated Norms](#67-workstream-f-human-review-safeguards--non-automated-norms)
   - [6.8 Workstream G: Step 3B Verification & Test Strategy](#68-workstream-g-step-3b-verification--test-strategy)
   - [6.9 Workstream H: Step 3B Definition of Done](#69-workstream-h-step-3b-definition-of-done)
7. [Step 3C Implementation Blueprint: Reviewer Desk & E2E Validation](#7-step-3c-implementation-blueprint-reviewer-desk--e2e-validation)
   - [7.1 Reviewer Journey & Screen Modifications](#71-reviewer-journey--screen-modifications)
   - [7.2 Evaluation Summary Card & Metric Breakdown](#72-evaluation-summary-card--metric-breakdown)
   - [7.3 Statutory Citation Display & Evidence Deep-Linking](#73-statutory-citation-display--evidence-deep-linking)
   - [7.4 Visual Trust Guardrails & Anti-Hallucination UX](#74-visual-trust-guardrails--anti-hallucination-ux)
   - [7.5 UI Edge Cases & State Handling](#75-ui-edge-cases--state-handling)
   - [7.6 Access Control & Data Redaction](#76-access-control--data-redaction)
   - [7.7 Step 3C Testing Strategy](#77-step-3c-testing-strategy)
   - [7.8 Step 3C Definition of Done](#78-step-3c-definition-of-done)
8. [Security Audit & Deployment Hardening Workstream](#8-security-audit--deployment-hardening-workstream)
   - [8.1 High-Severity Security Concern 1: Production Demo Credentials](#81-high-severity-security-concern-1-production-demo-credentials)
   - [8.2 High-Severity Security Concern 2: Reverse-Proxy Rate Limiting](#82-high-severity-security-concern-2-reverse-proxy-rate-limiting)
   - [8.3 High-Severity Security Concern 3: JWT Secret Key Management](#83-high-severity-security-concern-3-jwt-secret-key-management)
   - [8.4 Comprehensive Infrastructure & Data Security Audit](#84-comprehensive-infrastructure--data-security-audit)
9. [Regulatory Verification & Document Authenticity](#9-regulatory-verification--document-authenticity)
   - [9.1 Document Verification vs Document Authenticity](#91-document-verification-vs-document-authenticity)
   - [9.2 What VeriScope Actually Verifies Today](#92-what-veriscope-actually-verifies-today)
   - [9.3 Three-Tier Trust State Model](#93-three-tier-trust-state-model)
   - [9.4 Statutory Versioning & Rulebook Governance](#94-statutory-versioning--rulebook-governance)
10. [Comprehensive Step-by-Step Project Roadmap](#10-comprehensive-step-by-step-project-roadmap)
    - [Step 1: Baseline Prototype & Architecture](#step-1-baseline-prototype--architecture)
    - [Step 2: AICTE EoA Rule Catalogue](#step-2-aicte-eoa-rule-catalogue)
    - [Step 3A: Ruleset Foundation & Outcome Model](#step-3a-ruleset-foundation--outcome-model)
    - [Step 3B: Backend Review Integration](#step-3b-backend-review-integration)
    - [Step 3C: Frontend Reviewer Desk & E2E Validation](#step-3c-frontend-reviewer-desk--e2e-validation)
    - [Step 4: Security Hardening & Deployment Readiness](#step-4-security-hardening--deployment-readiness)
    - [Step 5: Regulatory Source Governance & Legal Validation](#step-5-regulatory-source-governance--legal-validation)
    - [Step 6: Enterprise Scalability & National Integrations](#step-6-enterprise-scalability--national-integrations)
11. [Team Git Workflow & Collaboration Protocols](#11-team-git-workflow--collaboration-protocols)
12. [Final Project Status Dashboard](#12-final-project-status-dashboard)

---

## 1. Executive Summary & Git Ground Truth

This document serves as the single source of truth for **VeriScope**, an evidence-linked regulatory review copilot built for institutional compliance audits under statutory authorities such as the **All India Council for Technical Education (AICTE)**.

### Verified Git Repository State (Inspected October 25, 2026)

* **Repository Remote**: `https://github.com/suryakrishna17/Veriscope.git`
* **Local Working Tree**: Clean (`nothing to commit, working tree clean`).
* **Active Working Branch**: `main`
* **HEAD Commit**: `871b3f6` (*"fix(ocr): add hermetic test fallback for scanned fixtures when tesseract is uninstalled and update LIMITATIONS.md"*, Author: `suryakrishna17`).
* **Merged Milestones**:
  - **Step 2 (PR #1)**: [PR #1](https://github.com/suryakrishna17/Veriscope/pull/1) — **MERGED** via commit `7488b34` (25-rule catalogue `aicte_eoa_chapter2.v1.yaml`).
  - **Step 3A (PR #2)**: [PR #2](https://github.com/suryakrishna17/Veriscope/pull/2) — **MERGED** via commit `9bd893d` (4-outcome model and `evaluate_ruleset()`).
  - **Step 3B (Commit `9142deb`)**: **MERGED** into `main` (dynamic routing, migration `002`, Groq vision OCR engine, and `test_eoa_workflow.py`).
  - **Step 3C (Commit `bfce402`)**: **MERGED** into `main` (Reviewer desk, 4-outcome summary card, dynamic upload slots, and `test_step3c_e2e.mjs`).
  - **Step 4 (PR #3)**: [PR #3](https://github.com/suryakrishna17/Veriscope/pull/3) — **MERGED** via commit `d6c9e18` (production seed prohibition, Werkzeug `ProxyFix` middleware, 32-byte secret key enforcement, and `test_security_guards.py`).
  - **Analytics & SLA Telemetry (Commit `2a9fdeb`)**: **MERGED** into `main` (Institutional Compliance Analytics service, `#analytics` dashboard, API telemetry, and `test_analytics.py`).
  - **AICTE Land Norm Operators (Commit `0329a2b`)**: **MERGED** into `main` (`land_norm_by_category` and `numeric_min` operators in `operators.py`, tested in `test_rules.py`).
  - **Versioning, Built-Up Area, & Merkle Notarization (Commit `009a2f9`)**: **MERGED** into `main` (resubmission version tracking, visual diffing, built-up area norm calculator, and cryptographic SHA-256 Merkle audit trail).
  - **Enterprise Scalability & DPI Integrations**: **COMPLETED** (Dual-mode PostgreSQL & SQLite data layer, asynchronous Celery + Redis task queue with graceful fallback, and DigiLocker/NAD interactive DPI sandbox gateway).
  - **Comprehensive Security & Audit Hardening (F1–F9, Commit `556c375`)**: **COMPLETED** (Production CLI provisioning, honest DigiLocker sandbox labeling, bounded PDF processing geometry, fail-closed regulatory operators, strict case adjudication invariants, zero-contrast hidden text detection, sequential SHA-256 hash-chained audit trails, and background job heartbeat/reaper).
  - **Render Container Startup & Deployment Fix**: **COMPLETED** (Safe demo password fallback during authorized production seeding, multi-origin CORS, package-lock preservation, and idempotent PostgreSQL schema alterations).
  - **Win-Readiness Audit & Hardening Checklist (P0-P2 & ADD)**: **COMPLETED & VERIFIED** (148/148 tests passing; CI demo credential guard; README honesty pass; Groq OCR source/bbox/confidence hardening with `<think>` strip and consent gate; full ruleset provenance with `reviewed_by` and `source_page` across 24 verified rules; `EOA-SIG-003` labeled `ILLUSTRATIVE`; student ruleset `SIG-005` hidden text rule; auth hardening with token versioning, 5-failure lockout, password change, and user management; numeric area parsing; cross-case duplicate hash oracle leak prevention; dual-dialect PostgreSQL/SQLite SLA turnaround time calculations).

### Critical Historical Reconciliation

Code inspection confirms the exact current Git state:
1. **Step 2 is Merged**: The 25-rule YAML catalogue and catalogue markdown documentation exist on `main` (commit `7488b34` via PR #1).
2. **Step 3A is Merged**: The 4-outcome evaluation model (`PASS`, `FAIL`, `REVIEW_REQUIRED`, `NOT_APPLICABLE`), typed dataclasses (`RuleEvaluation`, `RuleResult`), and helper methods are fully merged into `main` (commit `9bd893d` via PR #2).
3. **Step 3B & Step 3C are Merged**: The backend review integration and frontend reviewer desk are fully operational on `main` (commits `9142deb` and `bfce402`). `AICTE_EOA` applications can be selected, multi-document uploaded, evaluated against 25 rules, and deep-linked to evidence pages.
4. **Step 4 Security Hardening is Merged**: Seed protection, ProxyFix middleware, and production 32-byte secret validation are live on `main` via PR #3 (commit `d6c9e18`).
5. **Analytics & Land Norm Operators are Merged**: Real-time SLA telemetry, systemic AICTE deficiency ranking, Three-Tier Trust distribution, and Appendix 4 Table 4.1 land category operators are active on `main` (commits `2a9fdeb` and `0329a2b`).

---

## 2. Project Overview & Institutional Verification Problem

### 2.1 What VeriScope Is

VeriScope is an evidence-grounded **reviewer copilot** designed for regulatory compliance audits. Rather than treating artificial intelligence as an autonomous black-box judge that decides whether an institution is approved or rejected, VeriScope acts as an automated audit assistant:
1. It ingests complex application dossiers containing multi-page PDF documents.
2. It parses text natively and falls back to Optical Character Recognition (OCR).
3. It extracts specific regulatory data fields with pixel-level spatial bounding boxes `(x1, y1, x2, y2)`.
4. It evaluates extracted data against an official, versioned, deterministic rulebook.
5. It renders findings directly beside the highlighted source document pages.
6. It enforces mandatory human reviewer authority for final administrative actions.

> **Simple Analogy (The Caveman Explanation)**:  
> Imagine an officer who has to read 10,000 thick paper folders every year to check if schools follow government rules. Reading every single page takes hours, and tired humans miss things.  
> VeriScope is a super-fast digital assistant sitting beside the officer. It opens the folder in one second, points a yellow highlighter at the exact paragraph where the school wrote its name or expiration date, compares it to the official government rulebook, and whispers to the officer: *"Look here: the fire certificate expired last Tuesday, and the school forgot page 4."*  
> The assistant **never** signs the papers. The human officer looks at the highlighted page, makes the decision, and signs their own name.

---

### 2.2 The Real-World Regulatory Problem

In India, regulatory bodies like the **All India Council for Technical Education (AICTE)** oversee more than 10,000 technical, engineering, management, and polytechnic institutions across the nation. Every year, existing institutions must apply for an **Extension of Approval (EoA)** to continue admitting students, introduce new courses, or expand campus infrastructure under the **AICTE Approval Process Handbook (APH)**.

Historically, this process suffers from four major systemic bottlenecks:
1. **Document Fatigue & Human Error**: A typical application dossier contains dozens of pages spanning land deeds, municipal building approvals, state fire department NOCs, university affiliation orders, and statutory committee rosters. Scrutiny committees must manually cross-verify hundreds of data points under tight deadlines.
2. **Disconnected Regulatory Traceability**: Rejections or deficiency memos issued to institutions often lack clear, line-item citations pointing back to the specific statutory handbook clause, leading to prolonged legal disputes and administrative appeals.
3. **Vulnerability to Surface Inconsistencies**: Submissions frequently suffer from uncoordinated data entries—such as the institution's legal name being spelled slightly differently on a land lease versus a university affiliation order, or a temporary fire safety certificate that expired days before the filing date.
4. **The "Black Box AI" Trap**: Generic machine learning classifiers or large language models (LLMs) often hallucinate facts, guess regulatory clauses, or claim a document is "100% authentic" when they have no way to verify issuance with the government authority.

---

### 2.3 User Personas & Workflows

VeriScope defines three explicit, role-gated user personas in its security model:

```mermaid
flowchart TD
    subgraph Personas["VeriScope User Roles"]
        A["Applicant / Registrar<br/>(e.g., Vidya Institute)"]
        R["Reviewer / Scrutiny Officer<br/>(e.g., AICTE Bureaucrat)"]
        ADM["Administrator / Regional Director<br/>(e.g., AICTE Director)"]
    end

    A -->|1. Creates Case & Uploads Dossier| APP_FLOW[Applicant Journey]
    APP_FLOW -->|2. Submits Case| QUEUE[Priority Triage Queue]
    QUEUE -->|3. Claims Case| R_FLOW[Reviewer Desk]
    R -->|4. Inspects Evidence & Corrects Data| R_FLOW
    R -->|5. Resolves/Waives Findings| R_FLOW
    R -->|6. Issues Decision| DEC[Decision: Approve / Clarify / Reject]
    ADM -->|7. Reopens or Audits Case| AUDIT[Append-Only Audit Inspection]
```

1. **Applicant (Institutional Registrar / Principal)**:
   - *Goal*: Submit an institutional dossier, upload required statutory documents, monitor processing status, and respond to official clarification notices.
   - *Permissions*: Can create cases, upload files, trigger initial processing, and read their own application status. Strictly forbidden from viewing other institutions' files (enforced via IDOR query filtering).
2. **Reviewer (AICTE Scrutiny Officer / Committee Member)**:
   - *Goal*: Review submitted applications, evaluate automated compliance findings against illuminated source documents, manually correct OCR misreadings, waive justifiable exceptions with written reasons, and issue regulatory decisions.
   - *Permissions*: Full read access to application queues, extracted fields, bounding boxes, rule findings, and decision submission tools.
3. **Administrator (AICTE Regional Officer / System Admin)**:
   - *Goal*: Maintain system integrity, monitor reviewer throughput, configure operational settings, inspect the immutable audit trail, and exercise administrative reopen authority over finalized decisions.
   - *Permissions*: Full administrative rights, including reopening finalized cases, inspecting server health, and reviewing append-only audit event logs.

---

### 2.4 Why Deterministic Validation & Traceability Matter

In administrative law, government agencies are bound by principles of **natural justice** and **due process**. If a regulatory body denies an institution's approval:
- The authority must cite the exact legal regulation violated.
- The evidence supporting the violation must be inspectable and verifiable.
- The decision cannot be based on a non-deterministic algorithm that produces different results on different runs.

VeriScope implements **100% deterministic rules**. Given the same extracted fields and documents, the rules engine will produce the exact same outcome every single time. It contains no random seeds, no temperature parameters, and no probabilistic heuristics in its compliance determinations. Every finding carries an exact statutory citation (e.g., `AICTE APH 2024-27 Chapter II, Clause 2.4 & Clause 2.5, and Annexure-2`).

---

### 2.5 Scope: AICTE Extension of Approval (EoA)

The primary operational scope of VeriScope's enterprise ruleset is **AICTE Extension of Approval (EoA) for Existing Institutions**, governed by **Chapter II** of the official **AICTE Approval Process Handbook (APH 2024-25 to 2026-27)**, enacted under the statutory authority of the **All India Council for Technical Education Act, 1987 (Act 52 of 1987)**.

> **What is EoA in Simple Words?**  
> When a technical college is already operating, it cannot just run forever without oversight. Every year, it must ask AICTE: *"Please extend our approval for another academic year."*  
> Under AICTE's rules, the college must prove it still has an active university affiliation, its fire safety certificate is up to date, its buildings are structurally sound, it has anti-ragging committees to protect students, and its campus facilities are accessible. If the college is expanding or adding new seats, it must also provide land and occupancy records.

---

### 2.6 Existing Workflow vs AICTE EoA Workflow

The repository currently contains two distinct operational workflows:

| Aspect | Baseline Workflow (`STUDENT_SUPPORT_LITE`) | New Regulatory Workflow (`AICTE_EOA`) |
|---|---|---|
| **Domain** | Student fee waiver / scholarship verification | Institutional Extension of Approval (EoA) |
| **Authority** | Prototype student support ruleset | AICTE Act, 1987 & APH 2024–27 Chapter II |
| **Verification Status** | `ILLUSTRATIVE` (`is_verified: false`) | `VERIFIED_OFFICIAL` (`is_verified: true`) |
| **Document Types** | 3 documents (`APPLICATION_FORM`, `INSTITUTION_AUTHORIZATION_LETTER`, `ENROLMENT_OR_IDENTITY_PROOF`) | 6 documents (`EOA_APPLICATION_FORM`, `UNIVERSITY_AFFILIATION_ORDER`, `FIRE_SAFETY_CERTIFICATE`, `BUILDING_SAFETY_CERTIFICATE`, `LAND_DOCUMENT_AND_USE_CERTIFICATE`, `OCCUPANCY_CERTIFICATE`) |
| **Ruleset File** | `backend/app/rules/rulesets/student_support_lite.v1.yaml` (17 rules) | `backend/app/rules/rulesets/aicte_eoa_chapter2.v1.yaml` (25 rules) |
| **Outcome Model** | Binary anomaly generation (`RuleResult` active findings) | Four-valued outcome model (`PASS`, `FAIL`, `REVIEW_REQUIRED`, `NOT_APPLICABLE`) via `RuleEvaluation` |
| **Integration Status** | Fully connected end-to-end (intake, DB, UI) | Rules engine complete (Step 2 & 3A); pipeline & UI connection pending (Step 3B & 3C) |

---

### 2.7 Capabilities Today vs Post-Step 3B & 3C

#### What VeriScope Can Do Today (Verified on `main` at Commit `9938a7f`, code from `9bd893d`):
1. **Intake & Digest**: Ingest PDF, PNG, and JPEG files, sniff MIME magic bytes, reject corrupt files, and calculate immutable SHA-256 digests.
2. **Extract & Coordinate-Ground**: Extract digital vector text (PyMuPDF) or OCR image text (Tesseract), grouping words into lines and retaining normalized bounding boxes `(x1, y1, x2, y2)`.
3. **Execute AICTE EoA Rules In Isolation**: The pure rules engine (`backend/app/rules/engine.py`) can load `aicte_eoa_chapter2.v1.yaml` and evaluate synthetic `CaseContext` objects against all 24 statutory rules, returning structured `RuleEvaluation` records with `PASS`, `FAIL`, `REVIEW_REQUIRED`, or `NOT_APPLICABLE` outcomes (verified by 40 passing tests in `test_eoa_rules.py`).
4. **End-to-End Review for Baseline Cases**: For `STUDENT_SUPPORT_LITE` applications, users can create cases, upload files, execute processing, view highlighted pages, edit fields, resolve findings, and issue approval/rejection decisions.

#### What VeriScope Cannot Do Until Steps 3B & 3C Are Implemented:
1. **Cannot Select AICTE EoA at Intake**: The application creation route (`cases.py`) and UI (`NewCasePage.tsx`) reject or omit `AICTE_EOA` as a selectable application type.
2. **Cannot Extract EoA Documents**: The extraction pipeline (`fields.py`) only recognizes the 3 student-support document types. Uploading an `EOA_APPLICATION_FORM` or `FIRE_SAFETY_CERTIFICATE` results in an unknown document type error.
3. **Cannot Persist Statutory Citations**: The database `findings` table lacks a `clause_citation` column in `001_init.sql`, so statutory citations cannot be stored or queried from the database.
4. **Cannot Display 4-Outcome Summaries**: The frontend reviewer desk only displays open and closed anomaly cards; it has no UI components to render passing rules, review-required flags, or applicability statistics for EoA cases.

---

### 2.8 System Maturity Assessment

Based on empirical inspection of the codebase, VeriScope is a **partially integrated, high-assurance prototype**:
- **Rules Engine Core**: **Tested deterministic prototype**. Pure, isolated, fully typed, thoroughly tested (65 rules tests passing), and decoupled from network or database side-effects. Passing tests establish correctness of the evaluation logic, not production readiness (which also requires deployment hardening, infrastructure scaling, and regulatory sign-off — see Sections 8–9).
- **Data Intake & Storage**: **Robust prototype**. Solid SQLite foundation with transactional triggers and local file storage; ready for PostgreSQL migration.
- **Workflow & UI Integration**: **Mixed maturity**. Fully integrated for the baseline `STUDENT_SUPPORT_LITE` scenario; unintegrated for the newly developed `AICTE_EOA` regulatory catalogue.

---

### 2.9 Core Assumptions & Boundary Limitations

1. **Document Verification is Not Authenticity Proof**: Automated checks verify that a submitted file conforms to formatting, date, and consistency rules; they do **not** prove that the file was legitimately issued by a government authority. Real authenticity requires cryptographic PKI verification with the issuing body (e.g., DigiLocker / National Academic Depository).
2. **Self-Disclosure vs Regulatory Compliance**: An applicant ticking `"yes"` on a web form indicates self-disclosure, not certified fact. VeriScope explicitly flags self-disclosures (such as committee formations) for human inspection of supporting appointment orders.
3. **No Non-Deterministic Decision-Making**: VeriScope never uses generative language models to issue regulatory verdicts or pass/fail grades.

---

### 2.10 End-to-End Data Flow Architecture

The following diagram illustrates the complete data lifecycle, clearly delineating working prototype pathways from planned integration steps:

```mermaid
flowchart TD
    subgraph Intake["1. Dossier Intake"]
        F1["Institutional PDF/Image Files"] --> UPL["MIME Sniffing & SHA-256 Digest"]
        UPL --> STOR["Private Storage (LocalStorage)"]
        UPL --> DB_DOC["DB: documents record"]
    end

    subgraph Processing["2. Document Processing Pipeline"]
        STOR --> PARSE["PyMuPDF Native Text Parser"]
        PARSE -->|Scanned Page Fallback| OCR["Tesseract OCR (300 DPI)"]
        PARSE & OCR --> BBOX["Word & Bounding Box Normalizer"]
        BBOX --> EXT["Label-Anchored Field Extractor<br/>(fields.py)"]
        EXT --> SIG["Visual & Metadata Signals<br/>(Ink, Seals, PDF Trailers)"]
    end

    subgraph RuleEvaluation["3. Deterministic Rules Engine"]
        EXT & SIG --> CTX["CaseContext Assembly<br/>(DocView + FieldView)"]
        CTX --> ROUTE{"Application Type Router<br/>[PLANNED IN 3B]"}
        ROUTE -->|AICTE_EOA| RS_EOA["aicte_eoa_chapter2.v1.yaml<br/>(24 Rules · VERIFIED_OFFICIAL)"]
        ROUTE -->|STUDENT_SUPPORT| RS_STUDENT["student_support_lite.v1.yaml<br/>(17 Rules · ILLUSTRATIVE)"]
        RS_EOA & RS_STUDENT --> ENG["Rules Engine (evaluate_ruleset)<br/>Pure, Zero-IO Evaluation"]
        ENG --> EVALS["RuleEvaluation Records<br/>(PASS, FAIL, REVIEW_REQ, NOT_APP)"]
    end

    subgraph Persistence["4. Persistence & Triage"]
        EVALS --> PERSIST{"Findings & Citations Upsert<br/>[PLANNED IN 3B]"}
        PERSIST --> DB_FIND["DB: findings table<br/>(Fingerprinted by Rule+Version+Subject)"]
        DB_FIND --> TRIAGE["Urgency Triage Calculator<br/>(High: 30, Med: 12, Low: 4)"]
        TRIAGE --> DB_CASE["DB: cases table<br/>(Priority Score & Summary)"]
    end

    subgraph ReviewerDesk["5. Reviewer Operations & Human Authority"]
        DB_CASE & DB_FIND --> UI_QUEUE["Reviewer Queue (QueuePage.tsx)"]
        UI_QUEUE --> UI_DESK["3-Pane Review Desk (CasePage.tsx)"]
        UI_DESK --> V1["Pane 1: EvidenceViewer (Zoom & BBox Pulsing)"]
        UI_DESK --> V2["Pane 2: FieldTable (Corrections & Audits)"]
        UI_DESK --> V3["Pane 3: FindingsPanel (Citations & Waivers)"]
        V3 --> UI_SUMMARY["4-Outcome Evaluation Banner<br/>[PLANNED IN 3C]"]
        V1 & V2 & V3 --> DEC["Human Reviewer Gate (DecisionBar.tsx)<br/>(Approve / Clarify / Reject)"]
        DEC --> AUDIT["Append-Only DB Audit Log<br/>(SQLite Block Triggers)"]
    end

    Intake --> Processing --> RuleEvaluation --> Persistence --> ReviewerDesk

    classDef planned fill:#fff3cd,stroke:#ffc107,stroke-width:2px;
    class ROUTE,PERSIST,UI_SUMMARY planned;
```

---

## 3. Technology Stack & Repository Architecture

### 3.1 Technology Stack Inventory

| Component / Layer | Technology | Version | Location / Usage | Architectural Rationale | Status |
|---|---|---|---|---|---|
| **Backend Runtime** | Python | 3.11+ | `backend/` | Strong type hinting (`__future__.annotations`), pattern matching, `StrEnum` support. | Active |
| **Web API Framework** | Flask | 3.0+ | `backend/app/api/` | Thin blueprint router. Chosen for zero-dependency execution and rapid testability. | Active |
| **HTTP WSGI Server** | Werkzeug / Gunicorn | 3.0+ | `backend/wsgi.py`, `backend/serve_windows.py` | Standalone development and production WSGI hosting. | Active |
| **Database Engine** | SQLite (PostgreSQL Ready) | 3.x | `backend/app/core/db.py`, `backend/migrations/` | Zero-setup embedded DB with WAL mode, foreign keys, and strict trigger-enforced append-only audit logs. | Active |
| **PDF Extraction** | PyMuPDF (`fitz`) | 1.23+ | `backend/app/processing/text.py` | Extracts raw character streams, layout fonts, and bounding boxes in milliseconds. | Active |
| **OCR Fallback** | Tesseract (`pytesseract`) | 5.x / 0.3.10 | `backend/app/processing/text.py` | Optical character recognition fallback for scanned PDFs and image files at 300 DPI. | Active (Optional without system binary) |
| **Image Analysis** | Pillow (PIL) | 10.x | `backend/app/processing/signals.py` | Image rendering, pixel thresholding, circular contour analysis for stamps/seals. | Active |
| **Rule Specification** | YAML | 1.2 | `backend/app/rules/rulesets/` | Human-readable, declarative, versioned policy rulebooks outside application code. | Active |
| **Security & Auth** | PyJWT & `werkzeug.security` | 2.8+ | `backend/app/core/security.py` | HS256 signed JSON Web Tokens; password hashing with scrypt. | Active |
| **Document Generation**| ReportLab | 4.0+ | `backend/app/services/reports.py` | Generates official, tamper-evident PDF inspection dossiers and summary reports. | Active |
| **Test Runners** | Pytest & Unittest | 9.x | `backend/tests/` | Unit testing, metadata assertion, regression suites, and API testing. | Active |
| **Linter / Formatter** | Ruff & Mypy | 0.3+ / 1.8+ | `backend/` | Fast static analysis, strict type checking, and style enforcement. | Active |
| **Frontend Framework** | React | 18.2+ | `frontend/src/` | Declarative component UI with hooks and Context API. | Active |
| **Language (Frontend)** | TypeScript | 5.2+ | `frontend/src/` | Strict end-to-end type safety shared with API models. | Active |
| **Build Tooling** | Vite | 5.0+ | `frontend/vite.config.ts` | Ultra-fast development server and optimized production bundler. | Active |
| **Styling System** | Custom Glassmorphic CSS | Vanilla CSS | `frontend/src/styles.css` | High-contrast frosted glass panels (`backdrop-filter`), responsive layout, dark mode. | Active |
| **Asynchronous Queue** | Celery + Redis | - | `docs/AUTOMATION_ROADMAP.md` | Background task distribution for bulk PDF extraction and OCR processing. | Planned (Phase 3) |
| **Identity / PKI** | DigiLocker / NAD API | - | `docs/AUTOMATION_ROADMAP.md` | Direct X.509 certificate validation with issuing authorities. | Planned (Phase 3) |

---

### 3.2 File Tree & Directory Breakdown

```
Veriscope/
├── .gitignore
├── .env.example                       # Reference environment variables
├── docker-compose.yml                 # Local container orchestration
├── Dockerfile                         # Production API container specification
├── Makefile                           # Development task automations
├── README.md                          # Public repository overview
├── render.yaml                        # Cloud deployment blueprint
├── context.md                         # Authoritative Project Master Reference (This File)
├── backend/
│   ├── pyproject.toml                 # Build system & tool configurations (Ruff, Pytest, Mypy)
│   ├── requirements.txt               # Production Python dependencies
│   ├── requirements-dev.txt           # Development & testing tooling
│   ├── wsgi.py                        # WSGI entrypoint for Gunicorn
│   ├── serve_windows.py               # Standalone multi-threaded Windows server
│   ├── app/
│   │   ├── __init__.py                # Flask application factory (create_app)
│   │   ├── container.py               # Dependency injection container (Services)
│   │   ├── ai/
│   │   │   ├── adapter.py             # Optional LLM summary adapter (Mock, OpenAI, Anthropic)
│   │   ├── api/
│   │   │   ├── routes.py              # HTTP REST API v1 endpoints
│   │   ├── core/
│   │   │   ├── config.py              # Environment configuration loader (Settings)
│   │   │   ├── db.py                  # SQLite database wrapper with WAL & migrations
│   │   │   ├── errors.py              # Standardized API error classes & handlers
│   │   │   ├── logging.py             # Structured JSON logging with PII redaction
│   │   │   └── security.py            # JWT authentication, role guards, rate limiting
│   │   ├── processing/
│   │   │   ├── fields.py              # Label-anchored field extraction & line grouping
│   │   │   ├── normalize.py           # Value normalization (dates, currency, names, phones)
│   │   │   ├── signals.py             # Visual ink density, seals, and PDF revision checks
│   │   │   ├── text.py                # PyMuPDF vector extraction & Tesseract OCR fallback
│   │   │   └── validation.py          # File upload hygiene & MIME magic byte checks
│   │   ├── rules/
│   │   │   ├── engine.py              # Deterministic ruleset loader & evaluator
│   │   │   ├── model.py               # RuleEvaluation, RuleResult, CaseContext dataclasses
│   │   │   ├── operators.py           # Pure rule evaluation operators (regex, date, match)
│   │   │   └── rulesets/
│   │   │       ├── aicte_eoa_chapter2.v1.yaml  # Official AICTE EoA rule catalogue (25 rules)
│   │   │       └── student_support_lite.v1.yaml # Baseline prototype ruleset (17 rules)
│   │   ├── services/
│   │   │   ├── audit.py               # Audit trail event recording
│   │   │   ├── cases.py               # Case lifecycle, access control, and decisions
│   │   │   ├── jobs.py                # In-process asynchronous thread pool runner
│   │   │   ├── processing.py          # Document processing & evaluation orchestration
│   │   │   └── reports.py             # Verifiable PDF & JSON case report generator
│   │   └── storage/
│   │       └── local.py               # Private local disk storage adapter
│   ├── migrations/
│   │   └── 001_init.sql               # Base database schema & append-only triggers
│   ├── scripts/
│   │   ├── seed.py                    # Database seeding for demo accounts & fixtures
│   │   └── reset.py                   # Development database wipe and re-initialization
│   └── tests/
│       ├── conftest.py                # Pytest global fixtures
│       ├── helpers.py                 # AppTestCase test base class
│       ├── test_api.py                # HTTP endpoint & authentication tests
│       ├── test_eoa_rules.py          # AICTE EoA rule catalogue & outcome model tests
│       ├── test_guardrails.py         # Anti-hallucination & verdict language guardrails
│       ├── test_normalize.py          # Field normalization & fuzzy matching unit tests
│       └── test_rules.py              # Baseline student support rule engine tests
├── docs/
│   ├── AICTE_EOA_RULE_CATALOGUE.md    # Markdown reference for 24 AICTE EoA rules
│   ├── ARCHITECTURE.md                # System architecture & component boundaries
│   ├── AUTOMATION_ROADMAP.md          # Multi-phase engineering roadmap & SIH pitch
│   ├── DECISIONS.md                   # Architectural decision records (ADRs)
│   ├── DEMO_SCRIPT.md                 # 3-minute hackathon judge walkthrough script
│   ├── INNOVATION_AND_RESEARCH.md     # Competitive matrix & legal due process research
│   ├── LIMITATIONS.md                 # Explicit boundaries & honesty disclosures
│   ├── PROJECT_SPEC.md                # Original SIH26261 functional specification
│   ├── RULEBOOK.md                    # Rule authoring guide & outcome specification
│   └── THREAT_MODEL.md                # STRIDE security threat analysis
└── frontend/
    ├── package.json                   # Node.js dependencies & scripts
    ├── tsconfig.json                  # TypeScript compiler configuration
    ├── vite.config.ts                 # Vite bundler configuration
    ├── index.html                     # Single-page web entrypoint
    └── src/
        ├── App.tsx                    # Root component & session provider
        ├── main.tsx                   # React DOM bootstrapping
        ├── styles.css                 # Frosted glassmorphic design system
        ├── api/
        │   ├── client.ts              # Fetch client wrapper with token handling
        │   └── types.ts               # TypeScript domain interfaces
        ├── components/
        │   ├── AuditTimeline.tsx      # Chronological audit trail event list
        │   ├── Badges.tsx             # Severity, status, and trust pill components
        │   ├── DecisionBar.tsx        # Floating reviewer decision bar & gates
        │   ├── EvidenceViewer.tsx     # Zoomable document canvas with bounding boxes
        │   ├── FieldTable.tsx         # Extracted values list with inline corrections
        │   ├── FindingsPanel.tsx      # Rule findings, citations, and waiver modal
        │   ├── Icons.tsx              # SVG icon system
        │   ├── Layout.tsx             # Top navigation bar & user role switcher
        │   ├── Modal.tsx              # Accessible modal dialog primitive
        │   └── Uploader.tsx           # Drag-and-drop document upload slots
        ├── lib/
        │   ├── format.ts              # Date, currency, byte, and string formatters
        │   ├── hooks.ts               # Asynchronous state & data fetching hooks
        │   ├── router.ts              # Lightweight hash-based client routing
        │   ├── session.tsx            # Global user authentication React context
        │   └── toast.tsx              # Floating toast notification primitive
        └── pages/
            ├── CasePage.tsx           # Main 3-pane reviewer workstation
            ├── LoginPage.tsx          # Credentials form with 1-click demo login
            ├── NewCasePage.tsx        # Multi-step application submission form
            ├── QueuePage.tsx          # Triage-ordered case list with filtering
            └── ReportPage.tsx         # Printable inspection dossier & case report
```

---

### 3.3 Subsystem Responsibilities & Inter-Component Communication

```mermaid
sequenceDiagram
    autonumber
    actor Officer as Scrutiny Officer
    participant UI as React Frontend
    participant API as Flask API v1
    participant Svc as Cases & Processing Service
    participant Engine as Rules Engine (engine.py)
    participant DB as SQLite Database

    Officer->>UI: Selects case from Queue
    UI->>API: GET /api/v1/cases/{case_id}
    API->>Svc: case_detail(case_id, user)
    Svc->>DB: Query case, documents, fields, findings, decisions
    DB-->>Svc: Case dossier record
    Svc-->>API: Serialized CaseDetail JSON
    API-->>UI: 200 OK
    UI->>Officer: Renders 3-Pane Workstation

    Officer->>UI: Clicks "Process Application"
    UI->>API: POST /api/v1/cases/{case_id}/process
    API->>Svc: start_processing(case_id)
    Svc->>DB: Record job queued & transition to "processing"
    Svc-->>API: 202 Accepted (job_id)
    API-->>UI: Status updating...

    rect rgb(240, 248, 255)
        Note over Svc,Engine: In-Process Asynchronous Job Execution
        Svc->>Svc: process_document() for pending files
        Svc->>Svc: Extract native text / OCR & bounding boxes
        Svc->>Svc: build_context() -> CaseContext
        Svc->>Engine: evaluate_ruleset(ruleset, CaseContext)
        Note over Engine: Pure evaluation of 25 rules (No I/O)
        Engine-->>Svc: list[RuleEvaluation] (PASS/FAIL/REVIEW/NOT_APP)
        Svc->>DB: Upsert findings with citations & fingerprint
        Svc->>DB: Compute triage score & transition to "needs_review"
    end

    UI->>API: GET /api/v1/cases/{case_id} (Polling / Reload)
    API-->>UI: Updated case with active findings & citations
    UI->>Officer: Displays illuminated evidence & findings
```

---

## 4. Step 2 Deep Dive: AICTE EoA Rule Catalogue

### 4.1 Purpose of a Structured Rule Catalogue

In Step 2 of the VeriScope engineering trajectory, the team established a formal, machine-readable rule catalogue representing the official requirements of **Chapter II of the AICTE Approval Process Handbook (APH 2024-25 to 2026-27)**.

#### Why Store Rules as Structured YAML Data Rather Than Scattered Code?
1. **Separation of Policy from Execution**: Legal statutes change periodically when AICTE issues new handbooks or gazette notifications. Hardcoding regulatory logic inside Python functions makes updating rules risky and requires code deployments. Storing rules in YAML allows regulatory experts to inspect, audit, and update policies without modifying application code.
2. **Version Control & Cryptographic Checksums**: Every ruleset carries an immutable version string and a SHA-256 content checksum. When an application is audited two years later in court, the system can prove the exact ruleset version that was executed on that date.
3. **Inspectability & Transparency**: Regulators and institutions can read the YAML rule definitions directly. The exact conditions, thresholds, and statutory citations are plain text, eliminating the opacity of black-box code.
4. **Independent Testability**: Storing rules in structured data allows automated test suites to validate schema compliance, verify that every rule has a statutory citation, and test boundary conditions against mock dossiers with zero network or database overhead.

> **Crucial Distinction**: A catalogue by itself is merely a specification of checks. Loading a YAML file into memory does **not** mean the checks are executing in the real application review workflow. That connection requires the backend integration executed in Step 3B.

---

### 4.2 Catalogue YAML Schema & Field Semantics

Every rule in [`backend/app/rules/rulesets/aicte_eoa_chapter2.v1.yaml`](backend/app/rules/rulesets/aicte_eoa_chapter2.v1.yaml) adheres to a strict schema validated by [`backend/app/rules/engine.py`](backend/app/rules/engine.py):

* **`id`** (`string`, mandatory): Unique rule identifier formatted as `EOA-<CAT>-<NUM>` (e.g., `EOA-CMP-001`). Used for fingerprinting findings and logging audit trails.
* **`category`** (`string`, mandatory): Must be one of five standardized categories:
  - `completeness`: Audits presence of mandatory statutory documents or required form fields.
  - `compliance`: Validates regulatory format rules, expiration dates, and committee self-disclosures.
  - `consistency`: Cross-references names, sessions, and identifiers across distinct documents in the dossier.
  - `document_signal`: Inspects visual and metadata properties (e.g., duplicate file hashes, low OCR confidence).
  - `issuer_check`: Reserved for external authority cryptographic verification adapters.
* **`severity`** (`string`, mandatory): Must be one of `high`, `medium`, `low`, or `info`. Determines the triage weight added to the case urgency score (`high = 30`, `medium = 12`, `low = 4`, `info = 0`). High-severity findings hard-block automated approval.
* **`summary`** (`string`, mandatory): Concise, plain-English description of what the check verifies. Displayed as the primary heading on the reviewer finding card.
* **`description`** (`string`, optional): Detailed technical explanation of the statutory scope and evaluation logic.
* **`clause_citation`** (`string`, mandatory in EoA): Exact chapter, clause, annexure, and appendix citations pointing to the official AICTE Approval Process Handbook (e.g., `AICTE APH 2024-27 Chapter II, Clause 2.4 & Clause 2.5, and Annexure-2`).
* **`applicable_condition`** / **`applicability`** (`string`, mandatory in EoA): Plain-English description explaining which institutions must comply and which are legally exempt (e.g., autonomous degree institutions exempt from affiliation orders).
* **`condition`** (`dict` or `string`, optional): Programmatic prerequisite evaluated by `check_rule_applicability()`. If the condition is not met (e.g. `doc_present: FIRE_SAFETY_CERTIFICATE`), the rule is marked `NOT_APPLICABLE` and skipped.
* **`limitations`** (`string`, mandatory in EoA): Explicit disclosure of what the automated check cannot verify (e.g., verifies document presence only; cannot verify municipal watermarks or physical building stability).
* **`is_verified`** (`boolean`, default `true`): **Software metadata field** indicating that the rule was authored by referencing an identified official statutory provision (e.g., AICTE APH Chapter II). This is a cataloguing label set by the rule author, **not** an assertion that an independent regulatory body has reviewed or validated the software implementation. Rules with `is_verified: true` must have corresponding `clause_citation` fields pointing to the source provision. Independent legal validation is a separate process described in Section 9.
* **`verification_status`** (`string`): Set to `VERIFIED_OFFICIAL` for rules authored against official handbook provisions, or `ILLUSTRATIVE` for prototype rules. Like `is_verified`, this is an internal cataloguing label — **not** a guarantee of regulatory approval of the code logic.
* **`outcome_on_pass`** (`string`, default `PASS`): Outcome emitted when the rule condition is satisfied.
* **`outcome_on_fail`** (`string`, default `FAIL`): Outcome emitted when the condition is violated. May be set to `REVIEW_REQUIRED` for checks requiring human adjudication.
* **`operator`** (`string`, mandatory): Evaluator function mapped in `backend/app/rules/operators.py` (e.g., `required_doc_types`, `required_fields`, `date_order`, `cross_doc_match`).
* **`params`** (`dict`, mandatory): Operator-specific parameters (e.g. required field lists, regex patterns, similarity thresholds).
* **`next_action`** (`string`, mandatory in EoA): Actionable, clear guidance instructing the human reviewer on what steps to take if the check flags an anomaly.

---

### 4.3 Exhaustive Rule Inventory (All 24 Rules Analyzed)

The AICTE EoA Chapter 2 catalogue contains exactly **24 deterministic rules**:

```
Total AICTE EoA Rules: 24
├── Completeness Audits (7 Rules): EOA-CMP-001 to EOA-CMP-006, EOA-INF-003
├── Regulatory Compliance & Format (8 Rules): EOA-FMT-001, EOA-FMT-002, EOA-DAT-001, EOA-DAT-002, EOA-DAT-003, EOA-INF-001, EOA-INF-002, EOA-COM-006
├── Statutory Committee Self-Disclosures (5 Rules): EOA-COM-001 to EOA-COM-005
├── Cross-Document Consistency (2 Rules): EOA-CON-001, EOA-CON-002
└── Document Signals & Hygiene (2 Rules): EOA-SIG-001, EOA-SIG-002
```

#### Detailed Breakdown of Every Rule:

```carousel
### 1. Completeness Rules (EOA-CMP-001 to EOA-CMP-006, EOA-INF-003)
* **EOA-CMP-001** (`high`, `required_doc_types`): Validates presence of core statutory documents (`EOA_APPLICATION_FORM`, `UNIVERSITY_AFFILIATION_ORDER`, `FIRE_SAFETY_CERTIFICATE`, `BUILDING_SAFETY_CERTIFICATE`). Emits `FAIL` if missing. *Statutory Citation*: AICTE APH 2024-27 Chapter II, Clause 2.4 & Clause 2.5, and Annexure-2. *Exemption*: Autonomous degree institutions and standalone PGDM institutions do not affiliate with state universities and are exempt from affiliation orders.
* **EOA-CMP-002** (`medium`, `required_doc_types`, `outcome_on_fail: REVIEW_REQUIRED`): Audits land documents (`LAND_DOCUMENT_AND_USE_CERTIFICATE`, `OCCUPANCY_CERTIFICATE`). Required for expansions, seat increases, or site changes under Clauses 2.6 to 2.10. Routine annual continuations rely on permanent AICTE record.
* **EOA-CMP-003** (`medium`, `required_fields`): Checks core institutional fields on application form (`institution_name`, `institution_id`, `academic_year`, `principal_director_name`, `land_category`, `total_built_up_area`). Emits `FAIL` if missing.
* **EOA-CMP-004** (`medium`, `required_fields`): Verifies mandatory affiliation metadata (`university_name`, `academic_year`, `affiliation_order_number`, `order_date`). Emits `FAIL` if missing.
* **EOA-CMP-005** (`medium`, `required_fields`): Verifies fire clearance metadata (`fire_authority_name`, `noc_number`, `valid_until`, `building_coverage`). Emits `FAIL` if missing.
* **EOA-CMP-006** (`medium`, `required_fields`): Verifies structural safety metadata (`structural_engineer_name`, `license_registration_number`, `valid_until`). Emits `FAIL` if missing.
* **EOA-INF-003** (`high`, `field_equals`): Audits statutory declaration undertaking (`declaration_checked == "yes"`). Emits `FAIL` if unchecked.
<!-- slide -->
### 2. Format & Chronology Rules (EOA-FMT-001, EOA-FMT-002, EOA-DAT-001 to EOA-DAT-003)
* **EOA-FMT-001** (`medium`, `regex`): Enforces permanent AICTE institution ID format (`^\d-\d{9,10}$`, e.g. `1-1234567890`). Emits `FAIL` if invalid.
* **EOA-FMT-002** (`low`, `regex`): Enforces consecutive academic cycle format (`^20\d{2}-\d{2}$`, e.g. `2024-25`). Emits `FAIL` if malformed.
* **EOA-DAT-001** (`medium`, `date_not_future`): Asserts `application_date <= today`. Prevents accidental future submission dates. Emits `FAIL` if in future.
* **EOA-DAT-002** (`high`, `date_order`, `outcome_on_fail: REVIEW_REQUIRED`): Compares `application_date <= valid_until` for fire safety NOC. If certificate expired prior to filing, emits `REVIEW_REQUIRED`. Reviewer must check if a renewal fee challan was uploaded.
* **EOA-DAT-003** (`high`, `date_order`, `outcome_on_fail: REVIEW_REQUIRED`): Compares `application_date <= valid_until` for structural safety certificate. Emits `REVIEW_REQUIRED` if expired or conditional.
<!-- slide -->
### 3. Statutory Committees & Infrastructure (EOA-COM-001 to EOA-COM-006, EOA-INF-001, EOA-INF-002)
* **EOA-COM-001** (`high`, `field_equals`): Anti-Ragging Committee self-disclosure (`anti_ragging_committee_constituted == "yes"`). Cites AICTE Anti-Ragging Regulations 2009.
* **EOA-COM-002** (`high`, `field_equals`): Anti-Ragging Squad self-disclosure (`anti_ragging_squad_constituted == "yes"`). Cites AICTE Anti-Ragging Regulations 2009.
* **EOA-COM-003** (`high`, `field_equals`): Internal Complaints Committee (ICC) self-disclosure (`icc_constituted == "yes"`). Cites PoSH Act 2013 & AICTE Regulations 2016.
* **EOA-COM-004** (`high`, `field_equals`): Student Grievance Redressal Committee (SGRC) (`sgrc_constituted == "yes"`). Cites Redressal of Grievance Regulations 2019.
* **EOA-COM-005** (`medium`, `field_equals`): SC/ST Committee self-disclosure (`sc_st_committee_constituted == "yes"`). Cites SC/ST Prevention of Atrocities Act 1989.
* **EOA-COM-006** (`medium`, `field_equals`): Internal Quality Assurance Cell (`iqac_established == "yes"`).
* **EOA-INF-001** (`high`, `field_equals`, `outcome_on_fail: REVIEW_REQUIRED`): Barrier-Free Environment accessibility self-disclosure (`barrier_free_environment_available == "yes"`). Cites Rights of Persons with Disabilities Act, 2016.
* **EOA-INF-002** (`medium`, `field_equals`): Active public website mandatory disclosure (`mandatory_disclosure_url_active == "yes"`).
<!-- slide -->
### 4. Cross-Document Consistency & Signals (EOA-CON-001, EOA-CON-002, EOA-SIG-001, EOA-SIG-002)
* **EOA-CON-001** (`high`, `cross_doc_match`): Cross-verifies `institution_name` across `EOA_APPLICATION_FORM`, `UNIVERSITY_AFFILIATION_ORDER`, and `FIRE_SAFETY_CERTIFICATE` using fuzzy token matching (threshold: 88). Handles legal name changes under Clause 2.12.
* **EOA-CON-002** (`high`, `cross_doc_match`): Exact cross-check of `academic_year` between application form and university affiliation order. Emits `FAIL` if mismatched.
* **EOA-SIG-001** (`medium`, `duplicate_hash`, `outcome_on_fail: REVIEW_REQUIRED`): Detects identical SHA-256 file hashes across distinct institutional cases. Prompts reviewer to check for shared or recycled documents.
* **EOA-SIG-002** (`low`, `scan_quality`, `outcome_on_fail: REVIEW_REQUIRED`): Evaluates mean OCR confidence (< 80%), blurry scans, or low resolution. Alerts reviewer that values may contain OCR misreadings.
```

---

### 4.4 Statutory Traceability & Historical Corrections

During the Step 2 audit of the AICTE Approval Process Handbook, the engineering team identified and implemented critical statutory corrections in commit `19321e2`:

1. **Autonomous & Standalone PGDM Affiliation Exemption**:
   - *Problem*: Initial rule drafts unconditionally required `UNIVERSITY_AFFILIATION_ORDER` for all institutions.
   - *Statutory Truth*: Under Chapter II, standalone institutions offering Post Graduate Diploma in Management (PGDM), autonomous degree institutions, and deemed universities do not affiliate with state universities.
   - *Correction*: Updated `EOA-CMP-001` and `EOA-CMP-004` documentation, applicability notes, and next actions to explicitly instruct reviewers not to penalize legally exempt institutions.
2. **Land Document Distinctions (Routine vs Expansion)**:
   - *Problem*: Initial drafts treated missing land titles as an immediate failure for all EoA applications.
   - *Statutory Truth*: Under Clause 2.5, routine annual EoA continuation is granted based on self-disclosure; land ownership records remain on permanent record at AICTE. Fresh land titles and occupancy certificates (`EOA-CMP-002`) are only mandatory for expansions, seat increases, or site relocations under Clauses 2.6 to 2.10.
   - *Correction*: Changed `outcome_on_fail` for `EOA-CMP-002` from `FAIL` to `REVIEW_REQUIRED`, prompting reviewers to confirm whether the application is routine or an expansion.
3. **In-Flight Certificate Renewals**:
   - *Problem*: Automated date checking (`EOA-DAT-002`, `EOA-DAT-003`) would flag expired fire or building certificates as outright compliance violations.
   - *Statutory Truth*: Local municipal fire departments often have processing delays. If an institution submitted a renewal application and paid the fee challan before expiry, AICTE permits review pending the final NOC.
   - *Correction*: Configured `outcome_on_fail: REVIEW_REQUIRED` so that automated checks never prematurely fail an institution with an in-flight renewal.
4. **Institutional Name Changes (Clause 2.12)**:
   - *Problem*: Rigid string matching between application forms and legacy land deeds triggered false-positive name mismatch errors.
   - *Statutory Truth*: Institutions frequently change names (e.g. upgrading from "College of Engineering" to "Institute of Technology").
   - *Correction*: Calibrated `EOA-CON-001` fuzzy matching threshold to 88 and instructed reviewers to verify AICTE/university name change orders under Clause 2.12 before taking adverse action.

---

### 4.5 Catalogue Documentation Artifacts

Step 2 produced two primary documentation artifacts:
1. [`docs/AICTE_EOA_RULE_CATALOGUE.md`](docs/AICTE_EOA_RULE_CATALOGUE.md): The exhaustive regulatory reference manual detailing all 25 rules, statutory authorities, complex numerical norms register (land acreage, carpet areas, FSR, FDRs), and reviewer remediation actions.
2. [`docs/RULEBOOK.md`](docs/RULEBOOK.md): The technical developer guide detailing YAML syntax, schema fields, operator mappings, and instructions for authoring new rules.

---

### 4.6 Step 2 Verification & Test Results

The catalogue was verified through a dedicated test suite in [`backend/tests/test_eoa_rules.py`](backend/tests/test_eoa_rules.py):
- **Metadata Tests (`EoaRulesetMetadataTests`)**: Asserts ruleset loader loads the YAML file, calculates a valid SHA-256 checksum, validates that all 24 rule IDs are unique, and verifies that 100% of rules possess valid `clause_citation`, `applicability`, `limitations`, and `next_action` fields.
- **Trust Language Tests**: Scans the YAML text and asserts zero forbidden verdict terms (`forged`, `fraudulent`, `counterfeit`, `fake`, `authentic`) appear in user-facing summaries.
- **Evaluator Unit Tests (`EoaRuleEvaluationTests`)**: Executes isolated unit tests for all 25 rules against clean and failing `CaseContext` fixtures, verifying date boundaries (equal date boundary passes) and name similarity thresholds (88 boundary pass/fail).

---

### 4.7 Step 2 Boundary Limitations

> [!IMPORTANT]
> **What Step 2 Did NOT Do**:
> Step 2 was solely catalogue definition, schema validation, and unit testing. It did **not** modify the backend application creation endpoints, did **not** connect the pipeline to extract EoA documents, did **not** alter database tables, and did **not** display EoA findings in the frontend UI.

---

## 5. Step 3A Deep Dive: Ruleset Foundation & Outcome Model

### 5.1 The Four-Valued Outcome Model (`PASS`, `FAIL`, `REVIEW_REQUIRED`, `NOT_APPLICABLE`)

In Step 3A (merged into `main` via PR #2, commit `9bd893d`, which brought in branch commit `541c4b8`), the rules engine was upgraded from a binary anomaly model to a **four-valued evaluation outcome model** defined by `RuleOutcome(StrEnum)` in [`backend/app/rules/model.py`](backend/app/rules/model.py):

```python
class RuleOutcome(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
```

#### Meaning & Behavior of Each Outcome:

```mermaid
flowchart TD
    START["Evaluate Rule against CaseContext"] --> APP{"Is Rule Applicable?<br/>(check_rule_applicability)"}
    APP -->|No| NA["Outcome: NOT_APPLICABLE<br/>(Prerequisite missing or institution exempt)"]
    APP -->|Yes| RUN["Execute Operator Function<br/>(operators.py)"]
    RUN --> COND{"Did Condition Pass?"}
    COND -->|Yes| PASS["Outcome: PASS<br/>(Condition satisfied on available evidence)"]
    COND -->|No| CHECK_CONF{"outcome_on_fail configured?"}
    CHECK_CONF -->|REVIEW_REQUIRED or category=document_signal| RR["Outcome: REVIEW_REQUIRED<br/>(Human judgment required: renewal challan, OCR blur)"]
    CHECK_CONF -->|FAIL| FAIL["Outcome: FAIL<br/>(Definite statutory violation or missing mandatory document)"]
```

1. **`PASS`**:
   - *Meaning*: The evaluated requirement was satisfied based on the available input data.
   - *Example*: All required fields on the application form are present; fire safety certificate validity extends beyond application date.
   - *Trust Caveat*: A `PASS` outcome does **not** prove the document is authentic. It only proves the extracted data satisfies the rule's criteria.
2. **`FAIL`**:
   - *Meaning*: An unambiguous statutory violation or missing mandatory requirement was detected.
   - *Example*: An affiliated college failed to upload its mandatory university affiliation order (`EOA-CMP-001`); application ID does not match the AICTE permanent ID regex (`EOA-FMT-001`).
   - *Trust Caveat*: A `FAIL` outcome is a finding for human examination, not legal proof of deliberate misconduct or fraud.
3. **`REVIEW_REQUIRED`**:
   - *Meaning*: The automated engine detected a condition that cannot be safely decided by code and requires human discretion.
   - *Example*: Stated fire safety expiration precedes the filing date, but the college may have uploaded an in-flight renewal receipt (`EOA-DAT-002`); land documents are missing, but the application may be a routine annual continuation (`EOA-CMP-002`); OCR confidence is below 80% (`EOA-SIG-002`).
4. **`NOT_APPLICABLE`**:
   - *Meaning*: The rule's prerequisite conditions do not apply to this specific institution or application type.
   - *Example*: A rule requiring a specific certificate is skipped because that certificate is only required for pharmacy colleges, or a rule is disabled in configuration.

---

### 5.2 `RuleEvaluation` vs `RuleResult` Models

Step 3A introduced a clean separation between **complete rule evaluations** and **active anomaly findings**:

| Model | Purpose | When Created | Emitted Outcomes | Downstream Consumer |
|---|---|---|---|---|
| **`RuleEvaluation`** | Represents the audit outcome of **every** rule in the ruleset. | Always (1 record per rule in the catalogue). | `PASS`, `FAIL`, `REVIEW_REQUIRED`, `NOT_APPLICABLE` | Reviewer Summary Banners, Statutory Audit Logs, Compliance Metrics. |
| **`RuleResult`** | Represents an **active discrepancy or finding** that requires reviewer attention. | Only when a rule violates its condition. | `FAIL`, `REVIEW_REQUIRED` | Triage Priority Scoring, Findings Desk, Clarification Drafters, Database `findings` Table. |

#### Model Definitions in `backend/app/rules/model.py`:

```python
@dataclass
class RuleEvaluation:
    rule_id: str
    rule_version: str
    category: str
    severity: str
    summary: str
    outcome: str  # PASS | FAIL | REVIEW_REQUIRED | NOT_APPLICABLE
    detail: str
    evidence_refs: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 1.0
    clause_citation: str | None = None
    is_verified: bool = True
    verification_status: str = "VERIFIED_OFFICIAL"
    next_action: str | None = None
    subject: str = ""
    findings: list[RuleResult] = field(default_factory=list)
    applicable_condition: str | None = None
```

```python
@dataclass
class RuleResult:
    rule_id: str
    rule_version: str
    category: str
    severity: str
    summary: str
    detail: str
    evidence_refs: list[dict[str, Any]]
    confidence: float
    next_action: str
    subject: str  # Stable identity of what failed, used for idempotent fingerprints
    trust_label: str = "ANOMALY_DETECTED"
    clause_citation: str | None = None
    outcome: str = "FAIL"  # FAIL | REVIEW_REQUIRED
    is_verified: bool = True
```

---

### 5.3 Engine Architecture & Helper APIs

In `backend/app/rules/engine.py`, Step 3A implemented two evaluation entrypoints to guarantee **100% backward compatibility**:

1. **`evaluate_ruleset(ruleset: Ruleset, ctx: CaseContext) -> list[RuleEvaluation]`**:
   - The modern 4-outcome evaluation engine. Evaluates every rule in the ruleset.
   - Evaluates applicability via `check_rule_applicability()`.
   - Invokes the appropriate operator function.
   - Catches unexpected internal exceptions and safely maps them to `REVIEW_REQUIRED` with severity `info`, ensuring unhandled errors never crash the processing job.
2. **`evaluate(ruleset: Ruleset, ctx: CaseContext) -> list[RuleResult]`**:
   - The legacy finding extractor. Calls `evaluate_ruleset()` internally, filters evaluations to non-passing rules (`FAIL` and `REVIEW_REQUIRED`), and flattens their active `RuleResult` findings.
   - Existing downstream consumers (such as `evaluate_case()` in `processing.py`) continue to function without breaking.

#### Ruleset Registry & Helper Methods:

```python
APPLICATION_RULESETS: dict[str, str] = {
    "STUDENT_SUPPORT_LITE": "student_support_lite.v1.yaml",
    "AICTE_EOA": "aicte_eoa_chapter2.v1.yaml",
}
```

The `Ruleset` class provides helper properties:
- `rs.get_rule(rule_id: str) -> dict | None`: Retrieves a rule definition by its unique ID.
- `rs.verified_rules -> list[dict]`: Returns rules tagged `is_verified: true` (e.g. AICTE APH rules).
- `rs.illustrative_rules -> list[dict]`: Returns rules tagged `is_verified: false` (e.g. prototype rules).
- `rs.rules_by_category -> dict[str, list[dict]]`: Groups rules into the 5 standard categories.

---

### 5.4 Operator Mechanics & Execution Flow

In [`backend/app/rules/operators.py`](backend/app/rules/operators.py), the `_result()` helper function was updated to propagate statutory clause citations and custom outcomes:

```python
def _result(
    rule: Rule,
    detail: str,
    refs: list[dict[str, Any]],
    confidence: float,
    subject: str,
    summary: str | None = None,
    outcome: str | None = None,
) -> RuleResult:
    rule_outcome = outcome or rule.get("outcome_on_fail") or (
        "REVIEW_REQUIRED" if rule.get("review_required") or rule.get("category") == "document_signal" else "FAIL"
    )
    return RuleResult(
        rule_id=rule["id"],
        rule_version=rule["_version"],
        category=rule["category"],
        severity=rule["severity"],
        summary=summary or rule["summary"],
        detail=detail,
        evidence_refs=refs,
        confidence=round(max(0.0, min(1.0, confidence)), 3),
        next_action=rule.get("next_action", "Review the evidence and decide."),
        subject=subject,
        clause_citation=rule.get("clause_citation"),
        outcome=rule_outcome,
        is_verified=bool(rule.get("is_verified", True)),
    )
```

---

### 5.5 Metadata & Trust Labeling Differences

| Dimension | `aicte_eoa_chapter2.v1.yaml` | `student_support_lite.v1.yaml` |
|---|---|---|
| **Ruleset Identifier** | `aicte_eoa_chapter2` | `student_support_lite` |
| **Version** | `1.0.0` | `1.0.0` |
| **`is_verified`** | `true` (Software catalogue metadata) | `false` |
| **`verification_status`** | `VERIFIED_OFFICIAL` (Internal authoring tag) | `ILLUSTRATIVE` |
| **Statutory Grounding** | Mapped clause-by-clause to AICTE Approval Process Handbook (APH 2024-27 Chapter II) | Prototype student fee waiver policy |
| **Trust Implication** | Rules cite specific handbook clauses and provide structured next actions for scrutiny officers. *Note: This is an internal catalogue mapping, NOT an independent legal or regulatory endorsement by AICTE.* | Illustrative prototype. Findings indicate demonstration checks and cannot be cited for legal enforcement. |

> [!NOTE]
> **Important Regulatory Clarification**:
> Marking a rule or ruleset as `VERIFIED_OFFICIAL` (`is_verified: true`) represents an internal software engineering classification: it asserts that the rule author formulated the rule logic, threshold, and citations directly from the text of the AICTE Approval Process Handbook (APH 2024-27 Chapter II), rather than creating an arbitrary mock check. It does **not** signify that AICTE, legal counsel, or any statutory authority has certified, formally audited, or legally approved this software implementation. Final administrative authority remains exclusively with human scrutiny officers and regulatory officials.

---

### 5.6 Step 3A Test Suite & Regression Verification

During verification on `main` (commit `9938a7f`, testing the codebase established in `9bd893d`), the test suites were executed with the following empirical results:

```
Test Execution Summary (Executed October 25, 2026):
--------------------------------------------------
Targeted Rules & Normalization Suite (python -m pytest tests/test_eoa_rules.py tests/test_rules.py tests/test_normalize.py):
backend/tests/test_eoa_rules.py ...... 40 PASSED (0.95s)
  ├── EoaRulesetMetadataTests (4 tests)
  ├── EoaRuleEvaluationTests (30 tests)
  └── EoaFoundationTests (6 tests)
      ├── test_ruleset_helper_methods_and_grouping ................. PASSED
      ├── test_verified_official_vs_illustrative_ruleset_distinction PASSED
      ├── test_evaluate_ruleset_returns_pass_on_clean_context ...... PASSED
      ├── test_evaluate_ruleset_distinguishes_fail_and_review_req .. PASSED
      ├── test_evaluate_ruleset_supports_not_applicable ............ PASSED
      └── test_backward_compatibility_evaluate_findings_only ....... PASSED

backend/tests/test_rules.py .......... 20 PASSED (0.92s)
  └── Baseline Student Support Ruleset Regression Tests (20 tests)

backend/tests/test_normalize.py ......  5 PASSED (0.15s)
  └── Field Normalization & Parsing Unit Tests (5 tests)

Result for Rules & Logic Suites: 65 PASSED (0 failures)

Static Analysis:
  ruff check backend/ ................ ALL CHECKS PASSED (0 errors)
```

**Full Repository Test Suite Execution (`python -m pytest tests/` - 96 Collected Tests)**:
- **91 Passed**, **5 Failed**, **30 Warnings** (in ~12.7s).
- **Passing Suites**:
  - `tests/test_eoa_rules.py`: 40/40 passed.
  - `tests/test_rules.py`: 20/20 passed.
  - `tests/test_normalize.py`: 5/5 passed.
  - `tests/test_api.py`: 23/26 passed (3 failed).
  - `tests/test_guardrails.py`: 3/5 passed (2 failed).
- **Documented Pre-Existing Failures (Unrelated to Step 3A Logic)**:
  1. `tests/test_api.py::FixtureCaseTests::test_documents_never_claim_issuer_verification_without_issuer`: `TypeError: 'NoneType' object is not subscriptable` when inspecting `doc["issuer_check"]["response_id"]` on mock data.
  2. `tests/test_api.py::FixtureCaseTests::test_expected_fields`: Assertion failure on baseline demo case `SIH-DEMO-015` (`ENROLMENT_OR_IDENTITY_PROOF.enrolment_number missing`).
  3. `tests/test_api.py::FixtureCaseTests::test_expected_findings`: Assertion failure comparing actual findings `['CMP-005', 'DAT-002']` vs expected `['DAT-002', 'SIG-003']` for demo case `SIH-DEMO-015`.
  4. `tests/test_guardrails.py::TrustLanguageTests::test_user_facing_text_has_no_verdict_words`: `UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d` occurring on Windows environments when reading files without explicit `encoding="utf-8"`.
  5. `tests/test_guardrails.py::PromptInjectionTests::test_injected_text_has_no_effect`: Assertion mismatch on demo fixture findings (`['CMP-005', 'DAT-002']` vs expected `['DAT-002', 'SIG-003']`).
- **Warnings (30 total)**: Primarily `InsecureKeyLengthWarning` from PyJWT regarding the 11-byte test secret in `tests/helpers.py`.

> [!IMPORTANT]
> Passing the 65 isolated rule-engine unit tests verifies the programmatic correctness of the deterministic evaluation operators and outcome models. It does **not** establish overall system production-readiness, nor does it imply that the full end-to-end application suite passes without remaining issues. Resolving the 5 fixture and encoding failures is tracked as part of Step 4 (Security Hardening & Deployment Readiness).

---

### 5.7 Architecture & Completion Boundaries

> [!WARNING]
> **Clear Scope Boundaries for Step 3A**:
> 1. **Engine Foundation != Application Review**: Having an outcome model in `model.py` and `engine.py` does **not** mean that real applications submitted through the web portal select or execute `aicte_eoa_chapter2.v1.yaml`.
> 2. **Registry != Dynamic Routing**: `APPLICATION_RULESETS` exists in `engine.py`, but `cases.py` still only defines `APPLICATION_TYPES = {"STUDENT_SUPPORT_LITE": ...}`.
> 3. **UI Findings Display != EoA Findings Display**: The frontend can display generic findings, but because EoA cases cannot yet be created or processed in the backend, no EoA-specific finding has ever reached the live reviewer UI on `main`.

---

### 5.8 Step 3A Git & Pull Request Status

* **Branch**: `main` (merged via PR #2)
* **Merge Commit**: `9bd893d` (merged branch commit `541c4b8`)
* **Remote Tracking**: Synchronized with `origin/main`.
* **Pull Request**: **MERGED** — PR #2 ([https://github.com/suryakrishna17/Veriscope/pull/2](https://github.com/suryakrishna17/Veriscope/pull/2)) was merged by `navyaanubhutii` on 25 Oct 2026.
* **Main Status**: **MERGED AND VERIFIED**. Commit `541c4b8` (branch head) is present on `main` and `origin/main` via merge commit `9bd893d`.

---

## 6. Step 3B Implementation Blueprint: Backend Review Integration

### 6.1 The Core Integration Challenge

> **The Central Problem in Simple Words**:  
> *"We built the brain (the rule catalogue) and taught it how to think (the 4-outcome engine), but the rest of the body is not connected. When an applicant submits an AICTE EoA application, the system still tries to treat it as a student scholarship form, looks for the wrong documents, runs the wrong rules, and cannot save the official legal citations in the database."*

Step 3B is the backend integration phase that wires the AICTE EoA ruleset into the real application intake, document extraction, processing pipeline, and persistence mechanisms.

---

### 6.2 Workstream A: Application Classification & Ruleset Routing

#### Objectives:
1. Allow applications to be explicitly classified as `AICTE_EOA` upon creation.
2. Select `aicte_eoa_chapter2.v1.yaml` for `AICTE_EOA` applications while preserving `student_support_lite.v1.yaml` for `STUDENT_SUPPORT_LITE` applications.
3. Fall back safely to `STUDENT_SUPPORT_LITE` if no application type is specified.

#### File Modifications:
- [`backend/app/services/cases.py`](backend/app/services/cases.py):
  - Expand `APPLICATION_TYPES` dictionary:
    ```python
    APPLICATION_TYPES = {
        "STUDENT_SUPPORT_LITE": "Student support application (prototype)",
        "AICTE_EOA": "AICTE Extension of Approval (Existing Institutions)",
    }
    ```
- [`backend/app/container.py`](backend/app/container.py):
  - Add ruleset cache or loader method `get_ruleset(app_type: str) -> Ruleset` to `Services`, loading rulesets from `APPLICATION_RULESETS` dynamically.

---

### 6.3 Workstream B: Document Extraction & CaseContext Construction

#### Objectives:
1. Register the 6 statutory EoA document types in `DOC_TYPES`.
2. Define label synonyms in `fields.py` to extract required fields from EoA forms and certificates.
3. Register field normalization rules in `normalize.py`.

#### Document Types to Register in `DOC_TYPES`:
1. `EOA_APPLICATION_FORM`
2. `UNIVERSITY_AFFILIATION_ORDER`
3. `FIRE_SAFETY_CERTIFICATE`
4. `BUILDING_SAFETY_CERTIFICATE`
5. `LAND_DOCUMENT_AND_USE_CERTIFICATE`
6. `OCCUPANCY_CERTIFICATE`

#### Label Synonyms Mapping in `backend/app/processing/fields.py`:
- `EOA_APPLICATION_FORM`:
  - `institution_name`: `["name of the institution", "institution name", "college name"]`
  - `institution_id`: `["aicte permanent id", "permanent institute id", "institution id", "current application id"]`
  - `academic_year`: `["academic year", "academic session", "session"]`
  - `application_date`: `["date of application", "submission date", "application date"]`
  - `principal_director_name`: `["name of principal / director", "principal director name", "head of institution"]`
  - `land_category`: `["land category", "location category", "geographical classification"]`
  - `total_built_up_area`: `["total built up area", "total carpet area", "constructed area"]`
  - `declaration_checked`: `["declaration", "statutory undertaking", "affidavit 2"]`
  - Committee checkboxes (`anti_ragging_committee_constituted`, `anti_ragging_squad_constituted`, `icc_constituted`, `sgrc_constituted`, `sc_st_committee_constituted`, `iqac_established`, `barrier_free_environment_available`, `mandatory_disclosure_url_active`).
- `UNIVERSITY_AFFILIATION_ORDER`:
  - `university_name`: `["affiliating university", "name of university", "university"]`
  - `academic_year`: `["academic session", "academic year", "period of affiliation"]`
  - `affiliation_order_number`: `["affiliation order no", "order number", "reference no"]`
  - `order_date`: `["order date", "date of issue", "dated"]`
- `FIRE_SAFETY_CERTIFICATE`:
  - `fire_authority_name`: `["fire safety authority", "issuing authority", "fire department"]`
  - `noc_number`: `["noc number", "certificate no", "reference number"]`
  - `valid_until`: `["valid until", "valid till", "date of expiry", "validity"]`
  - `building_coverage`: `["building coverage", "blocks covered", "premises inspected"]`
- `BUILDING_SAFETY_CERTIFICATE`:
  - `structural_engineer_name`: `["name of structural engineer", "competent engineer", "certifying engineer"]`
  - `license_registration_number`: `["registration number", "license no", "chartered engineer no"]`
  - `valid_until`: `["validity date", "valid till", "fitness valid up to"]`

#### Missing & Degraded Data Handling:
- Missing fields must **never** silently evaluate to `PASS`. If a field is not found by OCR, `ctx.field()` returns `None`.
- Completeness rules (`required_fields`) yield an explicit `FAIL` finding with `NO_EVIDENCE` explanation.
- Consistency rules (`cross_doc_match`) only evaluate when at least 2 candidate fields exist, preventing false-positive mismatch errors when a file is missing.

---

### 6.4 Workstream C: Processing Pipeline & Service Layer Hookup

#### Objectives:
1. Update `process_document()` in `processing.py` to route visual detectors (signatures and seals) appropriately for EoA document types.
2. Update `evaluate_case()` in `processing.py` to retrieve the case's specific `application_type` and evaluate against its designated ruleset.

---

### 6.5 Workstream D: Finding Persistence, Fingerprinting & Idempotency

#### Objectives:
1. Extend the database `findings` table to persist `clause_citation` and `outcome`.
2. Preserve idempotent deduplication using SHA-256 fingerprinting:
   $$\text{fingerprint} = \text{SHA256}(\text{rule\_id} \parallel \text{version} \parallel \text{subject})[:32]$$
3. When a case is reprocessed:
   - Existing open or resolved findings matching active fingerprints are updated in place, **preserving** human reviewer resolutions, notes, and waivers.
   - Findings that no longer trigger (e.g. after a corrected file is uploaded) are marked `is_current = 0` (cleared).
   - New findings are inserted with `is_current = 1` and `status = 'open'`.

#### Database Migration (`backend/migrations/002_add_clause_citation_to_findings.sql`):
```sql
ALTER TABLE findings ADD COLUMN clause_citation TEXT;
ALTER TABLE findings ADD COLUMN outcome TEXT DEFAULT 'FAIL';
```

---

### 6.6 Workstream E: API Route Contracts & Schema Migration

#### Objectives:
1. Update `/api/v1/meta` to return both application types and all 6 EoA document types.
2. Update `/api/v1/cases` (POST) to validate and accept `application_type: "AICTE_EOA"`.
3. Update `/api/v1/rulesets/active` to accept an optional query parameter `?application_type=AICTE_EOA`, returning the active rule inventory and clause citations.
4. Update `serialize_finding()` in `cases.py` to serialize `clause_citation` and `outcome`.
5. Update `reports.py` to include `clause_citation` in JSON and PDF exports.

---

### 6.7 Workstream F: Human Review Safeguards & Non-Automated Norms

To prevent false automation claims, complex numerical norms that vary by geographical classification, course verticals, or local municipal gazettes are **explicitly registered for human review**:
1. **Contiguous Land Area & Zoning Norms** (APH Appendix 4 Table 4.1): Mega/Metro (1.5 acres), Urban (2.5 acres), Rural (7.5 acres). Reviewer must cross-examine land zoning certificates.
2. **Built-Up Carpet Area Calculations** (APH Appendix 4 Table 4.2): Aggregated mathematical sums of classrooms, laboratories, and workshops. Reviewer must inspect architect-certified drawings.
3. **Faculty Cadre & Cadred Student-to-Faculty Ratios (FSR)** (APH Appendix 7): 1:20 (UG Engineering) with 1 Professor : 2 Associate : 6 Assistant Professors. Reviewer must verify university selection committee rosters.
4. **Joint Fixed Deposit Receipts (FDR)** (APH Appendix 8): Reviewer must verify bank lien letters created in joint names with the AICTE Regional Officer.

---

### 6.8 Workstream G: Step 3B Verification & Test Strategy

The Step 3B implementation must be verified by implementing [`backend/tests/test_eoa_workflow.py`](backend/tests/test_eoa_workflow.py):

| Test Name | Verification Goal | Failure Prevented |
|---|---|---|
| `test_eoa_ruleset_selection_and_metadata` | Confirms `application_type: "AICTE_EOA"` selects `aicte_eoa_chapter2@1.0.0` and exposes APH source note. | Prevents EoA applications from running student support rules. |
| `test_non_eoa_ruleset_regression_safety` | Confirms default or `STUDENT_SUPPORT_LITE` cases continue to select `student_support_lite@1.0.0`. | Prevents breaking baseline student support applications. |
| `test_eoa_doc_types_and_meta_endpoint` | Verifies `/api/v1/meta` lists all 6 EoA document types and both application types. | Prevents frontend dropdowns from missing upload slots. |
| `test_eoa_normalization_and_boolean_checkboxes` | Validates normalization of `[X]`, `☑`, `yes`, `true` across all 7 committee checkboxes. | Prevents valid committee self-disclosures from triggering false failures. |
| `test_eoa_pipeline_evaluation_and_finding_persistence`| Ingests mock EoA application form, executes evaluation, and verifies findings contain statutory clause citations in DB. | Prevents findings from omitting official legal citations. |
| `test_reprocessing_idempotency_and_resolution_preservation` | Reprocesses a case twice and verifies finding count is unchanged and reviewer waiver notes are preserved. | Prevents duplicate findings and loss of reviewer work during re-runs. |
| `test_missing_input_safety_deterministic_engine` | Evaluates empty `CaseContext` and confirms graceful `FAIL` findings with `NO_EVIDENCE` without server crash. | Prevents unhandled null-pointer crashes on incomplete dossiers. |

---

### 6.9 Workstream H: Step 3B Definition of Done

* [ ] Database migration `002_add_clause_citation_to_findings.sql` created and applied cleanly.
* [ ] `APPLICATION_TYPES` in `cases.py` contains `AICTE_EOA`.
* [ ] All 6 EoA document types and extracted fields registered in `fields.py` and `normalize.py`.
* [ ] `evaluate_case()` dynamically selects `aicte_eoa_chapter2.v1.yaml` for EoA cases.
* [ ] Findings table stores `clause_citation` and `outcome`, serialized via `/api/v1/cases/<id>`.
* [ ] Reprocessing a case preserves reviewer waivers and finding fingerprints.
* [ ] All 7 tests in `test_eoa_workflow.py` pass cleanly.
* [ ] Baseline tests in `test_rules.py` continue to pass 100%.

---

## 7. Step 3C Implementation Blueprint: Reviewer Desk & E2E Validation

### 7.1 Reviewer Journey & Screen Modifications

The objective of Step 3C is to surface backend compliance findings and statutory citations to the authorized scrutiny officer through the existing frosted glassmorphic workstation:

```mermaid
flowchart LR
    subgraph ReviewerWorkstation["3-Pane Review Desk (CasePage.tsx)"]
        subgraph Pane1["Pane 1: Evidence Viewer"]
            EV1["High-Res Page Canvas"]
            EV2["Coordinate Bounding Boxes"]
            EV3["Zoom & Page Navigator"]
        end
        subgraph Pane2["Pane 2: Extracted Values"]
            FT1["Normalized Field Values"]
            FT2["Confidence Gauges (%)"]
            FT3["Inline Field Correction Dialog"]
        end
        subgraph Pane3["Pane 3: Findings Desk"]
            FP1["Evaluation Summary Banner"]
            FP2["Findings Cards with APH Citations"]
            FP3["Evidence Deep-Linking Chips"]
            FP4["Resolution / Waiver Modal"]
        end
    end
```

---

### 7.2 Evaluation Summary Card & Metric Breakdown

When a case is evaluated, the top of the Findings Desk (`FindingsPanel.tsx`) must display an **Evaluation Summary Card** derived from actual rule evaluation counts:

$$\text{Total Rules Evaluated} = \text{PASS} + \text{FAIL} + \text{REVIEW\_REQUIRED} + \text{NOT\_APPLICABLE}$$

#### UI Presentation:
```
┌────────────────────────────────────────────────────────────────────────┐
│  AICTE EoA Regulatory Audit Summary (APH 2024-27 Chapter II)          │
│  ────────────────────────────────────────────────────────────────────  │
│  Total Evaluated: 24 Rules                                             │
│  [  18 PASS  ]   [  3 FAIL  ]   [  2 REVIEW REQUIRED  ]   [  1 N/A  ]  │
└────────────────────────────────────────────────────────────────────────┘
```
- **Integrity Rule**: Unexecuted rules must never be counted as `PASS`. Counts must be derived from actual backend evaluations.

---

### 7.3 Statutory Citation Display & Evidence Deep-Linking

Every finding card in `FindingsPanel.tsx` must prominently display:
1. **Rule ID & Version**: e.g., `EOA-CMP-001 · v1.0.0`
2. **Statutory Clause Badge**: e.g., `📜 AICTE APH 2024-27 Chapter II, Clause 2.4 & Clause 2.5, and Annexure-2`
3. **Outcome Tag**: `FAIL` (Red) or `REVIEW REQUIRED` (Amber).
4. **Summary & Detail**: Plain-English discrepancy description.
5. **Evidence Deep-Link Chips**: Clicking an evidence chip (e.g. `[👁 Fire Safety Certificate · p.1]`) instantly navigates `EvidenceViewer.tsx` to that page and pulses the bounding box.
6. **Suggested Next Step**: Actionable guidance from `next_action`.

---

### 7.4 Visual Trust Guardrails & Anti-Hallucination UX

To maintain strict regulatory trust, the UI must enforce defensive guardrails:
1. **No Authenticity Badges**: The UI must **never** state a document is "Authentic", "Verified Original", or "Genuine" unless an issuer adapter records an official PKI response.
2. **Clear Self-Disclosure Disclaimers**: Committee checks must display an informational prompt: *"Self-disclosure checked 'yes'. Reviewer must inspect uploaded office order to verify representation."*
3. **Decision Gating**: The "Approve" button on `DecisionBar.tsx` is strictly disabled while any `high`-severity finding remains open and unwaived.

---

### 7.5 UI Edge Cases & State Handling

- **Loading State**: Translucent skeleton shimmer across all 3 panes while fetching case details.
- **No Documents Uploaded**: Prompts user to upload mandatory statutory files.
- **Empty Findings State**: If all rules pass, displays: *"No findings recorded. Every automated rule check passed. This does not mean documents have been confirmed by their issuers."*
- **Long Findings Lists**: Sticky category and severity filter tabs (`ALL`, `HIGH`, `MEDIUM`, `LOW`).

---

### 7.6 Access Control & Data Redaction

- **Applicant Boundary**: Applicants can only view their own cases; findings and decisions are visible, but reviewer-internal notes and audit logs are hidden.
- **Reviewer Boundary**: Scrutiny officers can view all assigned dossiers, correct fields, and resolve findings.
- **Admin Boundary**: Regional directors have exclusive permissions to execute administrative reopens on finalized cases.

---

### 7.7 Step 3C Testing Strategy

Frontend verification will be conducted using component and end-to-end integration tests:
- `test_findings_panel_renders_clause_citations`: Asserts citation text appears on finding cards.
- `test_evaluation_summary_metric_counts`: Verifies metric badges match backend counts.
- `test_evidence_chip_click_illuminates_page`: Simulates chip click and verifies canvas coordinates update.
- `test_decision_bar_blocks_approval_on_high_findings`: Verifies "Approve" button is disabled until findings are resolved.

---

### 7.8 Step 3C Definition of Done

* [ ] `NewCasePage.tsx` allows user to select `AICTE Extension of Approval (Existing Institutions)`.
* [ ] `Uploader.tsx` dynamically renders the 6 statutory upload slots for EoA cases.
* [ ] `FindingsPanel.tsx` renders statutory clause citations directly from backend finding records.
* [ ] `FindingsPanel.tsx` renders the 4-outcome evaluation summary banner.
* [ ] Bounding-box deep linking works across all 6 EoA document types.
* [ ] Complete end-to-end flow verified: Case Creation → File Upload → Processing → Findings Review → Human Decision.

---

## 8. Security Audit & Deployment Hardening Workstream

During the codebase inspection, three high-severity security concerns and several infrastructure considerations were verified in the actual implementation:

### 8.1 High-Severity Security Concern 1: Production Demo Credentials

* **Affected Component**: [`backend/scripts/seed.py`](backend/scripts/seed.py) (Lines 19–24)
* **Confirmed Vulnerability**:
  ```python
  DEMO_PASSWORD = "demo1234"
  USERS = [
      ("applicant@demo.local", "Asha Applicant", "applicant"),
      ("reviewer@demo.local", "Ravi Reviewer", "reviewer"),
      ("admin@demo.local", "Aditi Admin", "admin"),
  ]
  ```
* **Security Risk**: If `seed.py` is executed on staging or production databases, administrative accounts with known credentials (`admin@demo.local` / `demo1234`) will grant full unauthorized administrative access.
* **Remediation**:
  1. Add an environment guard in `seed.py`:
     ```python
     if svc.settings.app_env not in {"dev", "test"}:
         raise RuntimeError("seed.py is prohibited in production environments.")
     ```
  2. Implement an administrative bootstrapping CLI requiring strong random passwords supplied via environment variables (`ADMIN_INITIAL_PASSWORD`).

---

### 8.2 High-Severity Security Concern 2: Reverse-Proxy Rate Limiting

* **Affected Component**: [`backend/app/core/security.py`](backend/app/core/security.py) (Line 109)
* **Confirmed Vulnerability**:
  ```python
  svc.rate_limiter.check(f"{bucket}:{request.remote_addr}", limit, window_s)
  ```
* **Security Risk**: When deployed behind reverse proxies or load balancers (Render, Vercel, Nginx, AWS ALB), `request.remote_addr` reflects the internal IP address of the reverse proxy, not the client. Consequently:
  - All external users share the exact same rate limit bucket; one user triggering a limit locks out every user globally.
  - Or, an attacker can spoof client IP headers if headers are read without validation.
* **Remediation**:
  Wrap the Flask application in Werkzeug's `ProxyFix` middleware when running behind reverse proxies in [`backend/app/__init__.py`](backend/app/__init__.py):
  ```python
  from werkzeug.middleware.proxy_fix import ProxyFix
  if settings.app_env == "prod":
      app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
  ```

---

### 8.3 High-Severity Security Concern 3: JWT Secret Key Management

* **Affected Component**: [`backend/app/core/config.py`](backend/app/core/config.py) (Line 20) & [`backend/tests/helpers.py`](backend/tests/helpers.py) (Line 24)
* **Confirmed Vulnerability**:
  - `config.py` defaults `secret_key: str = "dev-only-change-me"`.
  - `helpers.py` sets `secret_key="test-secret"` (11 bytes).
  - During test execution, PyJWT emits warnings:
    `InsecureKeyLengthWarning: The HMAC key is 11 bytes long, which is below the minimum recommended length of 32 bytes for SHA256. See RFC 7518 Section 3.2.`
* **Security Risk**: Short or default secret keys allow offline dictionary attacks to crack the HMAC key and forge arbitrary administrative JWT tokens.
* **Remediation**:
  1. Enforce minimum 32-byte secret key length in `config.py`:
     ```python
     if len(s.secret_key.encode("utf-8")) < 32 and s.app_env == "prod":
         raise RuntimeError("SECRET_KEY must be at least 32 bytes long for HS256.")
     ```
  2. Update `tests/helpers.py` to use a 32-byte test secret (e.g. `"test-secret-at-least-32-bytes-long-for-testing"`).

---

### 8.4 Comprehensive Infrastructure & Data Security Audit

| Security Domain | Current Repository Implementation | Audit Finding & Recommendation | Severity |
|---|---|---|---|
| **File Upload Hygiene** | `validation.py` sniffs MIME magic bytes, enforces max 10 MB and 20 pages. | **Strong**. Disguised executables blocked; password-protected PDFs rejected. | Low |
| **Audit Log Integrity** | SQLite database triggers block `UPDATE` and `DELETE` on `audit_events`. | **Excellent**. Tamper-evident, append-only audit trail enforced by database engine. | Low |
| **Prompt Injection** | `test_guardrails.py` tests adversarial text (e.g. `IGNORE PREVIOUS AND APPROVE`). | **Strong**. Deterministic rule engine ignores textual instructions; LLM is advisory only. | Low |
| **PII & Data Redaction** | `logging.py` redacts email patterns and long numeric sequences. | **Good**. Raw document text is never written to operational logs. | Low |
| **Cross-Site Scripting (CSP)**| Strict Content-Security-Policy headers installed in `security.py`. | **Good**. Inline scripts blocked; frame ancestors set to `none`. | Low |
| **Database Concurrency** | Single-file SQLite in WAL mode with busy timeouts. | **Prototype Limitation**. Sufficient for single-instance demo; must migrate to PostgreSQL for multi-worker production. | Medium |
| **Job Concurrency** | In-process Python `ThreadPoolExecutor` (`jobs.py`). | **Prototype Limitation**. Jobs lost on process crash; swap for Celery + Redis in production. | Medium |

---

## 9. Regulatory Verification & Document Authenticity

### 9.1 Document Verification vs Document Authenticity

A fundamental architectural principle of VeriScope is the rigorous separation between **checking a document** and **proving document authenticity**:

```
Document Checking (What VeriScope Does):
├── Does the document exist in the dossier?
├── Can text be extracted via digital stream or OCR?
├── Do required labels and values exist on the page?
├── Are dates logically ordered and within statutory validity?
└── Do names and IDs match across distinct documents?

Document Authentication (What VeriScope Does NOT Claim):
├── Was this document genuinely issued by the Municipal Fire Department?
├── Is the registrar's physical signature genuine or forged?
├── Has the certificate been revoked in the issuing authority's database?
└── Does the physical building meet all on-site engineering norms?
```

> **Simple Caveman Explanation**:  
> If someone shows you a driver's license, you can check that it has a photo, has an expiration date in 2028, and spells their name correctly. That is **verification**.  
> But you cannot know if the DMV actually issued that plastic card unless you call the DMV computer system. That is **authentication**.  
> VeriScope never lies to the reviewer. It says: *"The papers match the rules, but only a call to the government computer can prove they are genuine."*

---

### 9.2 What VeriScope Actually Verifies Today

1. **File Cryptographic Integrity**: Verifies SHA-256 digests and checks for duplicate submissions across cases.
2. **Deterministic Compliance Norms**: Verifies format regexes, chronological date ordering, and cross-document text consistency.
3. **Visual Heuristic Signals**: Detects ink density near signature lines and circular contours for official seals (reporting physical presence, not validity).

---

### 9.3 Three-Tier Trust State Model: Implementation Reality vs Proposed Architecture

VeriScope defines a three-tier trust model to prevent false claims of document authenticity. It is important to distinguish what is **implemented in code today** versus what is a **proposed conceptual architecture**:

#### 1. What is Implemented in Code Today:
- **`NOT_VERIFIED` (Implemented — Live Document Default)**:
  - In the database schema (`001_init.sql`), every uploaded document defaults to `trust_label = 'NOT_VERIFIED'`.
  - The active default verifier in `backend/app/issuer/verifier.py` is `NullIssuerVerifier`, which explicitly records that no issuer integration is connected and assigns `NOT_VERIFIED`.
  - In the current application, 100% of non-mocked ingested documents carry this label.
- **`ANOMALY_DETECTED` (Implemented — Active Findings)**:
  - In `backend/app/rules/model.py` and `001_init.sql`, active rule discrepancy findings are assigned `trust_label = "ANOMALY_DETECTED"`.
  - This informs the reviewer that a rule condition was violated or requires human scrutiny.
- **Extracted Fields**:
  - In the codebase, individual extracted fields (`extracted_fields` table) **do not** have a `trust_label` attribute; they carry extraction `confidence` scores (0.0 to 1.0), coordinate bounding boxes `(x1, y1, x2, y2)`, and text source indicators (`pdf_stream` vs `ocr`).
- **`ISSUER_VERIFIED` Adapter Protocol & Mock Stub (Implemented for Testing Only)**:
  - An `IssuerVerifier` protocol is defined in `backend/app/issuer/verifier.py`.
  - A `MockIssuerVerifier` fixture exists to simulate registry lookups against a local JSON file (`simulated_registry.json`) for automated tests. It is disabled by default in production.

#### 2. What is Planned / Proposed Architecture:
- **Live `ISSUER_VERIFIED` Integration (Proposed — Step 6 / Phase 3)**:
  - Direct cryptographic verification via live external authority APIs (e.g., DigiLocker PKI, National Academic Depository, or state fire department registry lookup) is an architectural roadmap item.
  - Until external API adapters are connected and certified, **no production document is ever marked `ISSUER_VERIFIED`**.
  - The UI and reports explicitly disclaim authenticity for all documents lacking external issuer verification.

---

### 9.4 Statutory Versioning & Rulebook Governance

To ensure legal non-repudiation:
- Rulesets are versioned (e.g. `aicte_eoa_chapter2@1.0.0`) and stored with SHA-256 checksums in the database `rulesets` table.
- Future APH editions (e.g. 2027-28) will be added as new YAML rulesets (`aicte_eoa_chapter2.v2.yaml`), allowing legacy applications to be re-evaluated against the exact historical ruleset active at the time of submission.

---

## 10. Comprehensive Step-by-Step Project Roadmap

```
PROJECT ROADMAP MILESTONES:
├── STEP 1: Foundation & Prototype Review Workflow (COMPLETED & VERIFIED)
├── STEP 2: AICTE EoA Rule Catalogue (COMPLETED & VERIFIED ON MAIN)
├── STEP 3A: Ruleset Foundation & Outcome Model (COMPLETED AND VERIFIED ON MAIN)
├── STEP 3B: Backend Review Integration (SPECIFIED · READY FOR IMPLEMENTATION)
├── STEP 3C: Frontend Reviewer Desk & E2E Validation (SPECIFIED · READY FOR IMPLEMENTATION)
├── STEP 4: Security Hardening & Deployment Readiness (SPECIFIED · HIGH PRIORITY)
├── STEP 5: Regulatory Source Governance & Legal Validation (PLANNED)
└── STEP 6: Enterprise Scalability & National Integrations (PLANNED)
```

---

### Step 1: Baseline Prototype & Architecture
* **Objective**: Build foundational end-to-end review application for prototype student support applications.
* **Delivered**: Flask backend, PyMuPDF/Tesseract extraction, SQLite database, 17-point rulebook (`student_support_lite.v1.yaml`), React 3-pane reviewer desk, ReportLab PDF export.
* **Status**: **COMPLETED AND VERIFIED** (Existing on `main`).

---

### Step 2: AICTE EoA Rule Catalogue
* **Objective**: Research, author, and validate an official 25-rule catalogue based on AICTE APH 2024-27 Chapter II.
* **Delivered**: `aicte_eoa_chapter2.v1.yaml`, `AICTE_EOA_RULE_CATALOGUE.md`, `RULEBOOK.md`, `test_eoa_rules.py` (34 tests).
* **Status**: **COMPLETED AND VERIFIED** (Merged into `main` via PR #1, commit `7488b34`).

---

### Step 3A: Ruleset Foundation & Outcome Model
* **Objective**: Build a typed 4-outcome evaluation model (`PASS`, `FAIL`, `REVIEW_REQUIRED`, `NOT_APPLICABLE`), ruleset lookup helpers, and backward-compatible evaluation APIs.
* **Delivered**: `RuleOutcome`, `RuleEvaluation`, `evaluate_ruleset()`, `Ruleset` class helpers, `EoaFoundationTests` (6 tests).
* **Status**: **COMPLETED AND VERIFIED** (Merged into `main` via PR #2, commit `9bd893d`, which brought in branch commit `541c4b8`). All 40 unit tests in `test_eoa_rules.py` pass on `main`.

---

### Step 3B: Backend Review Integration
* **Objective**: Connect the AICTE EoA ruleset to application creation, document extraction, pipeline execution, and finding persistence.
* **Delivered**: `AICTE_EOA` registered in `cases.py`, 6 statutory documents in `fields.py`, migration `002_add_clause_citation_to_findings.sql`, dynamic ruleset routing, Groq vision OCR integration, `test_eoa_workflow.py`.
* **Status**: **COMPLETED AND VERIFIED ON MAIN** (Merged via commit `9142deb`).

---

### Step 3C: Frontend Reviewer Desk & E2E Validation
* **Objective**: Expose EoA findings, 4-outcome summary metrics, statutory clause citations, and dynamic upload slots in the reviewer interface.
* **Delivered**: Application type selector in `NewCasePage.tsx`, dynamic 6-document upload slots in `Uploader.tsx`, 4-outcome Evaluation Summary Card in `FindingsPanel.tsx`, deep-linking evidence chips, and `test_step3c_e2e.mjs`.
* **Status**: **COMPLETED AND VERIFIED ON MAIN** (Merged via commit `bfce402`).

---

### Step 4: Security Hardening & Deployment Readiness
* **Objective**: Resolve verified security vulnerabilities and pre-existing test failures prior to staging or production hosting.
* **Delivered**: `seed.py` production guard, Werkzeug `ProxyFix` reverse-proxy middleware, minimum 32-byte `SECRET_KEY` enforcement, test helper secret upgrade, and `test_security_guards.py`.
* **Status**: **COMPLETED AND VERIFIED ON MAIN** (Merged via PR #3, commit `d6c9e18`).

---

### Step 5: Regulatory Source Governance & Legal Validation
* **Objective**: Formalize regulatory policy review with named legal and AICTE domain experts.
* **Features to Implement**:
  1. Periodic statutory handbook synchronization pipeline.
  2. Transition `is_provisional: false` upon sign-off by regulatory policy officers.
  3. Verification protocols for complex numerical norms (land acreage, FSR, FDR).
* **Status**: **PLANNED** (Phase 2 Roadmap).

---

### Step 6: Enterprise Scalability & National Integrations
* **Objective**: Scale architecture to handle nationwide institutional filing volume.
* **Features to Implement**:
  1. Migrate SQLite to PostgreSQL with connection pooling.
  2. Implement distributed Celery + Redis asynchronous task workers.
  3. Integrate live DigiLocker & National Academic Depository (NAD) OAuth2 / PKI APIs.
  4. Merkle-tree cryptographic audit log notarization.
* **Status**: **PLANNED** (Phase 3 Roadmap).

---

## 11. Team Git Workflow & Collaboration Protocols

To ensure seamless collaboration across teammates and prevent accidental regressions or lost work:

### Agreed Team Git Rules

1. **Feature-Branch Workflow vs Direct Pushes**:
   - **Feature Branches for All Code Work (Standard Practice)**:
     All new feature implementations (Step 3B backend integration, Step 3C reviewer desk), database migrations, and schema modifications must be developed on dedicated feature branches (e.g., `git checkout -b feat/step-3b-backend-integration origin/main`).
   - **Authorized Direct-to-Main Documentation Updates**:
     Direct pushes to `main` without a pull request are reserved exclusively for authorized documentation updates (such as updating `context.md`) or critical project-lead hotfixes when explicitly requested. Never push untested application code, experimental migrations, or WIP stashes directly to `main`.

2. **Strict Prohibition on Rewriting Shared History**:
   - **Never Force-Push**: `git push --force` and `git push --force-with-lease` are strictly prohibited on `main` and all shared remote branches.
   - **Do Not Rebase Shared History**: Once a branch is pushed to remote and shared with teammates, never rebase it. Rebasing rewrites commit hashes and causes silent divergence for collaborators.
   - **Safe Conflict Resolution**: If a remote branch has advanced, synchronize by pulling or merging:
     ```bash
     git fetch origin
     git merge origin/main  # Preferred for shared branches to preserve true history
     ```
     `git rebase origin/main` is acceptable *only* for private, unpushed local commits before publishing a branch.

3. **Always Pull and Verify Before You Build**:
   ```bash
   git fetch origin
   git checkout main
   git merge origin/main --ff-only
   ```
   Confirm your local tree matches `origin/main` before creating new branches or beginning any task.

4. **Coordinate Shared File Edits**:
   Components like `backend/app/api/routes.py`, `backend/app/services/cases.py`, and `frontend/src/api/types.ts` are shared across workstreams. Communicate in team channels before modifying these files to prevent merge conflicts.

5. **Run Verification Tests Before Pushing**:
   Never push code that fails unit tests or linting:
   ```bash
   cd backend
   ruff check .
   python -m pytest tests/test_eoa_rules.py tests/test_rules.py tests/test_normalize.py
   ```

6. **Current Base Tip for Future Workstreams**:
   Both Step 2 (PR #1, `7488b34`) and Step 3A (PR #2, `9bd893d`) are fully merged into `main`. The current verified repository tip is commit `9938a7f` (which established this comprehensive project context manual). All new Step 3B feature branches must branch off this tip (`origin/main`).

---

## 12. Final Project Status Dashboard

### Comprehensive Subsystem Matrix

| Subsystem / Area | Current Status | Codebase Evidence | Remaining Work | Priority |
|---|---|---|---|---|
| **Step 2: EoA Catalogue** | **COMPLETED & VERIFIED** | `aicte_eoa_chapter2.v1.yaml`, `AICTE_EOA_RULE_CATALOGUE.md`, commit `7488b34` on `main`. | None for Step 2. | Done |
| **Step 3A: Ruleset Foundation** | **COMPLETED & VERIFIED** | `RuleEvaluation`, `RuleOutcome`, `evaluate_ruleset()` in `engine.py`, merged to `main` via PR #2 (`9bd893d`). | None — Step 3A is complete. | Done |
| **Step 3B: Backend Integration** | **COMPLETED & VERIFIED ON MAIN** | Commit `9142deb` on `main`. Dynamic ruleset routing, migration `002`, Groq OCR fallback, and `test_eoa_workflow.py`. | None — fully operational on `main`. | Done |
| **Step 3C: Frontend Reviewer Desk**| **COMPLETED & VERIFIED ON MAIN** | Commit `bfce402` on `main`. 4-outcome summary banner, dynamic 6-document uploader, and E2E validation. | None — fully operational on `main`. | Done |
| **Security Hardening** | **COMPLETED & VERIFIED ON MAIN** | PR #3 (`d6c9e18`). Seed production guard, ProxyFix middleware, 32-byte JWT enforcement, and `test_security_guards.py`. | None — verified and live on `main`. | Done |
| **Institutional Analytics & SLA Telemetry** | **COMPLETED & VERIFIED ON MAIN** | Commit `2a9fdeb`. `analytics.py`, `AnalyticsPage.tsx`, `/api/v1/analytics`, and `test_analytics.py`. | None — fully operational on `main`. | Done |
| **Mathematical Land Norm Operators** | **COMPLETED & VERIFIED ON MAIN** | Commit `0329a2b`. `land_norm_by_category` & `numeric_min` in `operators.py`, tested in `test_rules.py`. | None — verified and operational on `main`. | Done |
| **Document Resubmission Versioning & Diffing** | **COMPLETED & VERIFIED ON MAIN** | Document version tracking, `EvidenceViewer.tsx` version tabs & diff toggle. | None — operational on `main`. | Done |
| **Built-Up Area & FSR Calculator** | **COMPLETED & VERIFIED ON MAIN** | `built_up_area_norm` operator in `operators.py`, tested in `test_rules.py`. | None — verified on `main`. | Done |
| **Merkle Audit Notarization** | **COMPLETED & VERIFIED ON MAIN** | SHA-256 Merkle tree in `audit.py`, `/audit/merkle` route, `AuditTimeline.tsx` badge, and `test_merkle_audit.py`. | None — verified on `main`. | Done |
| **DigiLocker DPI Adapter** | **COMPLETED & VERIFIED ON MAIN** | `DigiLockerIssuerVerifier` in `verifier.py`, `ISSUER_VERIFIED` state, tested in `test_issuer.py`. | None — operational on `main`. | Done |
| **PostgreSQL Dual-Mode Migration** | **COMPLETED & VERIFIED ON MAIN** | `db.py` dual engine, `postgresql_schema.sql` with PL/pgSQL immutable triggers, auto-dialect translation. | None — operational on `main`. | Done |
| **Distributed Task Queue (Celery + Redis)** | **COMPLETED & VERIFIED ON MAIN** | `celery_app.py`, `tasks.py`, `jobs.py` distributed dispatch with thread fallback, `test_workers.py`. | None — verified on `main`. | Done |
| **DigiLocker DPI Interactive Gateway** | **COMPLETED & VERIFIED ON MAIN** | `digilocker.py` sandbox certificates & pull endpoint, `Uploader.tsx` 1-click pull, `test_digilocker_service.py`. | None — operational on `main`. | Done |
| **P0 Rules Missing-Evidence Safeguard** | **COMPLETED & VERIFIED ON MAIN** | `required_fields` and `field_equals` in `operators.py` yield explicit failures when target documents are absent. Tested in `test_empty_dossier_rules.py`. | None — verified on `main`. | Done |
| **Production CLI Provisioning (F1)** | **COMPLETED & VERIFIED ON MAIN** | `create_user.py` provisioner CLI; demo login chips gated behind `VITE_DEMO_MODE`. Tested in `test_security_guards.py`. | None — operational. | Done |
| **Honest DigiLocker Sandbox (F2)** | **COMPLETED & VERIFIED ON MAIN** | Sandbox imports marked `NOT_VERIFIED` with `simulated: true`; gated to reviewer/admin; heuristic `DL-` bypass eliminated. Tested in `test_issuer_integrity.py`. | None — verified on `main`. | Done |
| **Bounded PDF Processing & Memory Safety (F3)** | **COMPLETED & VERIFIED ON MAIN** | Dimensions capped (36-3400 pt, `PAGE_SIZE_UNSUPPORTED`); 12M pixel render limit. Tested in `test_processing_bounds.py`. | None — verified on `main`. | Done |
| **Fail-Closed Statutory Engine (F4)** | **COMPLETED & VERIFIED ON MAIN** | Missing documents/fields never evaluate to PASS; unhandled exceptions preserve rule severity. Tested in `test_rules_fail_closed.py`. | None — verified on `main`. | Done |
| **Strict Case Adjudication Invariants (F5)** | **COMPLETED & VERIFIED ON MAIN** | 0 unanalyzed docs required for approval; 20+ char justification for high-severity waivers; uploads locked in `needs_review`. Tested in `test_hardened_gates.py`. | None — verified on `main`. | Done |
| **Zero-Contrast Hidden Text Defense (F6)** | **COMPLETED & VERIFIED ON MAIN** | Low-contrast text isolated into `hidden_words` and flagged as `hidden_text_detected`. Tested in `test_processing_bounds.py`. | None — verified on `main`. | Done |
| **Sequential Hash-Chained Audit Trail (F7)** | **COMPLETED & VERIFIED ON MAIN** | Migration `003_audit_chain.sql`; SHA-256 sequential hashing (`seq`, `prev_hash`, `event_hash`); verification via `/audit/verify`. Tested in `test_audit_chain.py`. | None — verified on `main`. | Done |
| **Job Heartbeat & Stale Task Reaper (F8)** | **COMPLETED & VERIFIED ON MAIN** | Migration `004_job_heartbeat.sql`; `reap_stale_jobs()` sweeps tasks idle >300s. Tested in `test_reaper.py`. | None — verified on `main`. | Done |
| **Render Container Startup Resilience (F9)** | **COMPLETED & VERIFIED ON MAIN** | Safe demo password fallback in `seed.py`, `render.yaml` CORS & demo seed configuration, `Dockerfile` lockfile preservation, PostgreSQL schema idempotency. | None — operational on Render. | Done |
| **Test Suite Health** | **COMPLETED & VERIFIED ON MAIN** | 148 tests across all 19 test modules (`test_analytics.py`, `test_api.py`, `test_audit_chain.py`, `test_digilocker_service.py`, `test_empty_dossier_rules.py`, `test_eoa_rules.py`, `test_eoa_workflow.py`, `test_guardrails.py`, `test_hardened_gates.py`, `test_issuer.py`, `test_issuer_integrity.py`, `test_merkle_audit.py`, `test_normalize.py`, `test_processing_bounds.py`, `test_reaper.py`, `test_rules.py`, `test_rules_fail_closed.py`, `test_security_guards.py`, `test_workers.py`). | None — 148/148 passing (100% green), 0 ruff lint errors, 0 type errors. | Done |

---

### Top Three Recommended Next Actions for the Engineering Team

1. **Advance Step 5: Regulatory Source Governance & Legal Validation**:
   - Establish formal handbook transition protocols (`is_provisional: false`) upon designated regulatory officer review.
   - Build handbook versioning synchronization allowing past applications to remain audited against APH 2024-27 (`aicte_eoa_chapter2.v1.yaml`) while upcoming cycles audit against future editions (`v2`).
   - Implement complex mathematical rule operators for land acreage (Annexure-4 Mega/Metro/Urban/Rural classifications) and Floor Space Ratio (FSR/FDR) computations.
2. **Step 6: Enterprise Scalability & National Integrations (Phase 3)** — **COMPLETED**:
   - Native dual-mode PostgreSQL & SQLite data layer with PL/pgSQL append-only triggers and auto-dialect translation implemented.
   - Asynchronous Celery + Redis worker pool with in-process ThreadPool fallback implemented.
   - Interactive DigiLocker & NAD DPI Sandbox Gateway with 1-click UI pull and X.509 cryptographic metadata implemented.
3. **Monitor Live Render Production Service & Field Pilots**:
   - Monitor live container performance on Render (`https://veriscope-9hgl.onrender.com`).
   - Track Groq Vision OCR fallback latency and token usage metrics.

---

### Developer Onboarding Quick-Start

To spin up VeriScope locally for development and testing:

```bash
# 1. Clone the repository
git clone https://github.com/suryakrishna17/Veriscope.git
cd Veriscope

# 2. Check out the latest main branch (Step 3A is fully merged here)
git checkout main

# 3. Setup Python Backend Environment
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt -r requirements-dev.txt

# 4. Run Verified Rule Engine & Catalogue Tests
python -m pytest tests/test_eoa_rules.py tests/test_rules.py tests/test_normalize.py -v

# 5. Run Static Linting
ruff check .

# 6. Setup Frontend Environment (In a separate terminal)
cd ../frontend
npm install
npm run build
```

---

*This document is maintained by the VeriScope Core Engineering Team. Any changes to regulatory rulesets, outcome models, or architectural boundaries must be documented herein.*
