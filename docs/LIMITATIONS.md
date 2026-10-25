# VeriScope System Limitations & Operational Boundaries

To maintain full transparency with evaluation officers, auditors, and engineering teams, the following architectural and domain limitations are documented:

1. **Document Verification vs Document Authenticity**:
   - Automated checks assist human review by detecting discrepancies, arithmetic errors, and formatting inconsistencies; **they do not establish whether a physical document was issued by its stated issuer.**
   - No document receives the `Issuer verified` trust label unless a signed cryptographic confirmation from the issuing authority (e.g. DigiLocker PKI response) is recorded.
2. **Statutory Ruleset Scope**:
   - The primary statutory ruleset (`aicte_eoa_chapter2.v1.yaml`) strictly evaluates the 24 procedural requirements of **AICTE Approval Process Handbook (APH 2024–27 Chapter II)** for Extension of Approval (EoA).
   - Specialized Chapter I norms (e.g. New Institution land titles, detailed architectural carpet area calculations, multi-year endowment funds) are scheduled for Phase 3 expansion.
   - The secondary ruleset (`student_support_lite.v1.yaml`) remains an illustrative prototype and is clearly marked as `is_verified: false`.
3. **Visual Forensics Report Physical Presence Only**:
   - Signature ink stroke analysis, circular municipal seal detection, and letterhead identification confirm the physical presence and geometric characteristics of ink and stamps on the page. They do not perform biometric signature matching or cryptographic stamp authentication.
4. **Layout and Extraction Assumptions**:
   - Document field extraction relies on label-anchored patterns and synonym dictionaries alongside checkbox detection. Highly handwritten, unstructured free-form prose, or multi-column newspaper layouts require human reviewer verification using the Extracted Values Desk.
   - Multi-tier OCR utilizes native PyMuPDF vector streams first, falling back to local Tesseract OCR (English by default) and Groq Vision OCR (`qwen/qwen3.8-27b`) for degraded scans. Non-English regional languages require configuring additional Tesseract language packs (`OCR_LANG`).
5. **Single-Instance Prototype Infrastructure**:
   - The background job runner uses an in-process Python `ThreadPoolExecutor`, and rate limiting uses an in-memory queue. In production multi-node environments, this will transition to Celery with a Redis broker.
6. **Relational Database Concurrency**:
   - The system utilizes SQLite in WAL (Write-Ahead Logging) mode with database-level busy timeouts. While sufficient for single-instance hosted demos and pilots, enterprise nationwide deployments require migration to PostgreSQL with connection pooling.
7. **Simulated Issuer Adapters**:
   - The current issuer verification adapter provides a mock/null implementation. Live PKI integrations with DigiLocker and National Academic Depository (NAD) APIs are specified for Phase 3 national scaling.
