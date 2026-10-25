# VeriScope 3-Minute Regulatory Review Demo Script

**Smart India Hackathon (SIH26261) · Regulatory Partner: AICTE**  
*Recommended 3-minute live walkthrough script for jury and regulatory evaluators.*

---

## Pre-Demo Quick Setup

Before presenting:
```bash
# Seed synthetic demo cases (idempotent)
cd backend && python -m scripts.seed

# Launch backend (http://localhost:8000)
python wsgi.py

# Launch frontend (http://localhost:5173) in separate terminal
cd ../frontend && npm run dev
```

*Backup:* Keep a screen recording or the live hosted Render deployment (`https://veriscope-9hgl.onrender.com`) open on a backup browser tab.

---

## 3-Minute Walkthrough Flow

### 1. Automated Priority Queue & Triage (0:00 – 0:35)
* **Action:** Sign in using the 1-click **Reviewer** demo button (`Ravi Reviewer`).
* **Talking Point:**
  > *"Every year, AICTE officers manually evaluate thousands of complex institutional filings. VeriScope orders applications by weighted compliance urgency points—not arrival time. Applications with critical safety, affiliation, or committee violations bubble to the top automatically, preventing compliance bottlenecks."*

### 2. AICTE Extension of Approval Intake & Statutory Slots (0:35 – 1:05)
* **Action:** Click **"New application"**, point out the **Approval Scheme** dropdown (`AICTE Extension of Approval (EoA)` selected), and proceed to Step 2.
* **Talking Point:**
  > *"When an institution applies for Extension of Approval, VeriScope dynamically renders the exact 6 statutory document slots required under Chapter II of the Approval Process Handbook: the EoA Application Form, Affiliation Order, Fire Safety Certificate, Building Fitness Certificate, Land Document, and Occupancy Certificate. No generic document chaos."*

### 3. Reviewer Desk, Evaluation Summary Card & Bounding Box Provenance (1:05 – 1:55)
* **Action:** Navigate to **SIH-DEMO-014** on the Reviewer Desk.
* **Talking Point:**
  > *"This is the 3-pane Reviewer Desk. At the top, the Evaluation Summary Card gives officers an instant statutory breakdown across all 24 AICTE rules: 18 PASS, 3 FAIL, and 2 REVIEW REQUIRED. Notice that every finding card cites the exact statutory regulation—such as `📜 AICTE APH 2024-27 Clause 2.4 & Annexure-2`. When I click an evidence chip, the Evidence Viewer instantly navigates to page 1 and pulses the bounding box coordinates. Zero manual page flipping, zero hallucinations."*

### 4. Deterministic Gating & Automated Clarification Drafter (1:55 – 2:35)
* **Action:** Scroll to the **Decision Bar**. Show that **"Approve" is hard-blocked** because high-severity findings remain open. Click **"Request clarification"**.
* **Talking Point:**
  > *"Administrative due process requires procedural fairness. The system strictly disables approval while high-severity violations remain open. When the officer clicks 'Request clarification', VeriScope auto-synthesizes a formal statutory notice itemizing every open discrepancy and giving the college 7 working days to rectify. The officer reviews, edits if desired, and dispatches—saving 20 minutes of manual drafting."*

### 5. Multi-Tier OCR, Injection Defense & Tamper-Evident Report (2:35 – 3:00)
* **Action:** Open **SIH-DEMO-015** (Scanned document case), show OCR confidence gauges, mention the hidden injection text had zero effect, then click **"Case report"** and download PDF.
* **Talking Point:**
  > *"For degraded scans, VeriScope uses local Tesseract OCR with automatic Groq Vision OCR fallback. Adversarial prompt injection attacks inside documents are completely neutralized by our pure deterministic engine. Finally, with one click, we export a cryptographically hashed, court-ready inspection dossier. The machine automates extraction and rule checks; the human officer retains 100% final legal authority."*

---

## Key Presenter Summary Line

> **"VeriScope automates extraction, multi-document cross-referencing, and 24 statutory AICTE policy checks in sub-second time. It grounds every finding in exact pixel coordinates and official APH handbook clauses, while guaranteeing legal non-repudiation and human decision authority."**
