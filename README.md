# VeriScope — reviewer copilot for application validation

**SIH26261 · AICTE · Smart Automation**
*AI-Powered Application Validation, Document Authentication and Regulatory Compliance Verification*

VeriScope reads the documents attached to an application, runs a versioned rulebook over what it finds, and shows every finding next to the exact spot on the page it came from. A human reviewer corrects values, resolves or waives findings, and records the decision. Every step lands in an append-only audit trail and a downloadable case report.

![Review screen](docs/screenshots/review.png)

## What it does

| Stage | What happens |
|---|---|
| Intake | Upload PDF / PNG / JPG. Files are checked by content (not extension), size and page limits, encryption; SHA-256 hashed; stored privately. |
| Extraction | Native PDF text first, Tesseract OCR fallback for scans. Every value keeps its page, bounding box, source line and confidence. |
| Signals | Signature ink beside the signature label, circular seal, letterhead, scan quality, PDF edit history, duplicate files across cases. |
| Rules | 17 deterministic rules in `backend/app/rules/rulesets/*.yaml`: completeness, formats, dates, fee arithmetic, cross-document consistency, document signals. |
| Review | Three panes: document with highlights, extracted values (correctable), findings (resolve / waive with notes). Approve, reject or request clarification. |
| Record | Append-only audit log (DB triggers), PDF + JSON case report with ruleset version, hashes and a verification caveat. |

### Trust model

Every document and finding carries exactly one label: **Issuer verified** (only with a recorded issuer response), **Review required** (an automated signal), or **Not verified with issuer** (the default). The system never calls a document genuine or forged, anomaly signals cannot reject a case on their own, and approval is blocked while high-severity findings are open. A test fails the build if verdict words appear in user-facing text.

## Quick start (Docker)

```bash
cp .env.example .env        # optional
docker compose up --build
```

Open http://localhost:8000 and use a demo account (password `demo1234`):

| Account | Can do |
|---|---|
| `reviewer@demo.local` | Work the queue, correct values, resolve findings, decide |
| `applicant@demo.local` | Create applications, upload documents, answer clarifications |
| `admin@demo.local` | Reviewer rights plus reopening closed cases |

## Run locally

Requirements: Python 3.11+, Node 20+, and [Tesseract OCR](https://tesseract-ocr.github.io/tessdoc/Installation.html) (`apt install tesseract-ocr`, `brew install tesseract`, or the UB Mannheim installer on Windows — then set `TESSERACT_CMD` in `.env` if it is not on PATH). Without Tesseract, digital PDFs still work; scanned images fail with a clear message.

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m scripts.seed          # demo users + cases SIH-DEMO-013…016
python wsgi.py                  # API on http://localhost:8000

# frontend (second terminal)
cd frontend
npm install
npm run dev                     # UI on http://localhost:5173, proxies /api to :8000
```

To serve the UI from the API instead (one port), run `npm run build` once; the API serves `frontend/dist` automatically. On Windows, use `python serve_windows.py` for a production-style server. `make` targets exist for macOS/Linux (`make install seed dev test`).

## Demo cases

| Case | Scenario | Expected findings |
|---|---|---|
| SIH-DEMO-013 | Clean application | none |
| SIH-DEMO-014 | Unsigned form, wrong total, different institution on the letter, letter edited 74 days later in a PDF editor, enrolment proof byte-identical to another applicant's | CMP-001, CON-002, ARI-001, CON-001, SIG-001, SIG-002 |
| SIH-DEMO-015 | Scanned proof read by OCR, authorization expired before the application date, prompt-injection text hidden on the form | DAT-002, SIG-003 (injection has no effect) |
| SIH-DEMO-016 | Empty case | empty state |

`python -m scripts.reset` wipes local data and re-seeds. The 3-minute judging walkthrough is in [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md).

## Tests

```bash
cd backend && pytest -q          # 56 tests: rules, OCR fixtures, API, state machine, auth, audit, AI guardrails
cd frontend && npm run typecheck
cd frontend && npm run e2e       # browser walkthrough; needs a freshly seeded app running on :8000
```

CI (`.github/workflows/ci.yml`) runs lint, tests, type-check, build, the e2e walkthrough and a Docker build.

## Project layout

```
backend/
  app/
    api/routes.py          HTTP API v1 (thin: parse → authorise → service)
    core/                  config, SQLite layer, errors, JSON logging, JWT/roles/rate limits/headers
    processing/            upload validation, text + OCR, field extraction, normalisers, visual/metadata signals
    rules/                 pure rule engine, operators, YAML rulesets
    services/              case lifecycle, processing orchestration, audit, reports, job runner
    ai/adapter.py          optional LLM summary behind guardrails; template fallback
    issuer/verifier.py     issuer-verification adapter (null by default; labelled simulation available)
  migrations/              SQL schema (PostgreSQL-portable)
  scripts/                 generate_fixtures, seed, reset
  fixtures/                synthetic documents + expected_results.json
  tests/
frontend/src/
  pages/                   Login, Queue, NewCase, Case (review), Report
  components/              EvidenceViewer, FieldTable, FindingsPanel, DecisionBar, Uploader, …
docs/                      architecture, rulebook, demo script, decisions, limitations, threat model
```

## API

All under `/api/v1`, JSON, bearer token. Errors are `{"error": {"code", "message", "correlation_id", "details"}}`.

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/login` | Sign in |
| GET | `/cases?status=&q=&page=&sort=` | Queue (applicants see only their own) |
| POST | `/cases` | Create a case |
| GET | `/cases/{id}` | Detail: documents, fields, findings, decisions, audit, allowed actions |
| POST | `/cases/{id}/documents` | Upload (multipart `file`, `doc_type`) |
| POST | `/cases/{id}/process` | Run checks (background job, idempotent) |
| GET | `/jobs/{id}` | Job status |
| GET | `/documents/{id}/pages/{n}/image` | Rendered page for the evidence viewer |
| PATCH | `/fields/{id}` | Correct a value (original kept, rules re-run) |
| PATCH | `/findings/{id}` | Resolve / waive / reopen with note |
| POST | `/cases/{id}/decisions` | approve / request_clarification / reject |
| POST | `/cases/{id}/reopen` | Admin only |
| GET | `/cases/{id}/audit` | Audit trail |
| GET | `/cases/{id}/report?format=json\|pdf` | Case report |
| GET | `/rulesets/active` | Active rulebook |

## Configuration

See [.env.example](.env.example). Notable: `LLM_PROVIDER` (`none` by default — the app is fully functional offline), `ISSUER_VERIFIER` (`null` by default), `TESSERACT_CMD`, `MAX_UPLOAD_MB`.

## Limitations

The rulebook is a prototype and not official AICTE policy; there is no live issuer integration; visual signature/seal detection reports presence only. Full list: [docs/LIMITATIONS.md](docs/LIMITATIONS.md).
