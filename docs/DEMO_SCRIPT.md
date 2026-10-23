# 3-minute demo script

Before judging: `python -m scripts.reset` (or a fresh `docker compose up`). Keep a screen recording as backup.

1. **Queue (20 s)** — Sign in as Reviewer. “Cases are ordered by triage priority. Hover the number: it is the sum of open findings, and it never decides anything.”
2. **Open SIH-DEMO-014 (20 s)** — Point at the summary and the provisional-rulebook line. “Every document shows its hash and *Not verified with issuer*: we have not connected to an issuer.”
3. **Evidence (40 s)** — Click **CMP-001**: the empty signature area lights up. Click **CON-001** → the letter chip: the Northgate name is highlighted. Click **SIG-001**: “this exact file was already submitted by another applicant — a review signal, not an accusation.”
4. **Correct (25 s)** — Correct *Total amount claimed* to 1,33,500 with a reason. ARI-001 disappears; the original value stays on record.
5. **Decide (30 s)** — Show Approve is disabled while high findings are open. Request clarification: “Upload a signed form.”
6. **Scanned case (20 s)** — Open SIH-DEMO-015, the enrolment proof tab: OCR confidence badge, click a value to see where it was read. Mention the hidden injection text had no effect.
7. **Report (25 s)** — Case report → Download PDF: hashes, findings with evidence, decision, ruleset checksum, verification caveat.

**Presenter line:** “The system automates intake and evidence-linked checks. It found mismatches and a duplicate-file signal — anomalies for a person to examine. We have not connected to the issuing authority, so nothing here is issuer-authenticated. The reviewer makes and records the decision.”
