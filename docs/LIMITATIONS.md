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
   - Multi-tier OCR utilizes native pdfplumber / pypdfium2 vector streams first, falling back to local Tesseract OCR (English by default) and Groq Vision OCR (`qwen/qwen3.8-27b`) for degraded scans. Non-English regional languages require configuring additional Tesseract language packs (`OCR_LANG`).
5. **Distributed Task Queue Architecture**:
   - The system defaults to an in-process Python `ThreadPoolExecutor` for zero-dependency local runs, and seamlessly scales to a distributed Celery + Redis worker pool when configured with `REDIS_URL` in production multi-worker environments.
6. **Dual-Mode Database Architecture**:
   - The system defaults to SQLite in WAL (Write-Ahead Logging) mode with busy timeouts for instant local dev and zero-config testing. In enterprise deployments, it automatically engages PostgreSQL 16 with connection pooling and PL/pgSQL append-only immutable triggers when `DATABASE_URL` is configured.
7. **DigiLocker & NAD DPI Sandbox Integration**:
   - The issuer verification adapter provides a mock/null baseline for offline applications and an interactive DigiLocker & NAD DPI Gateway.
   - In sandbox mode without production national PKI certificates, imported documents are explicitly assigned the `NOT_VERIFIED` trust state with `simulated: true` metadata. The system strictly disallows synthetic elevation to `ISSUER_VERIFIED` and requires authorized human scrutiny officer validation.
8. **Bounded Document Dimensions and Memory Safety**:
   - PDF pages are strictly bounded between `36 pt` (0.5 inch minimum) and `3400 pt` (~47 inches maximum). Oversized canvas bombs or micro-dimensioned pages trigger `PAGE_SIZE_UNSUPPORTED` and are safely rejected without exhausting worker memory.
   - Image and page rendering is capped at `12,000,000` pixels per page to prevent raster decompression denial-of-service.
