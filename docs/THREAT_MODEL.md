# Threat model (STRIDE summary)

**Assets:** uploaded documents, extracted personal data, decisions, audit trail, credentials.
**Trust boundaries:** browser ↔ API; API ↔ file parsers (untrusted content); API ↔ optional LLM provider.

| Threat | Example | Mitigation |
|---|---|---|
| Spoofing | Stolen or forged token | HS256 JWT with expiry; `prod` refuses the default secret; login rate-limited |
| Tampering | Editing audit history | DB triggers block UPDATE/DELETE on `audit_events`; decisions snapshot findings |
| Tampering | Path traversal via filename or storage key | Filenames sanitised; opaque storage keys validated and confined to the storage root |
| Repudiation | “I never approved that” | Every action recorded with actor, role, timestamp and payload |
| Information disclosure | Applicant reads another case (IDOR) | Ownership check on every case/document/job read returns 404 |
| Information disclosure | PII in logs | JSON logs redact emails and long numbers; raw document text is never logged |
| Denial of service | Huge or decompression-bomb files, OCR exhaustion | Size, page and pixel limits; OCR timeout; upload rate limit |
| Elevation / injection | Prompt injection inside a document | Document text never reaches the LLM as instructions; LLM sees findings only, inside delimiters; output schema- and citation-checked; AI cannot change any state (tested with a seeded injection fixture) |
| Malicious content | Active PDF content, disguised executables | Content sniffing (magic bytes); only PDF/PNG/JPEG; files are parsed, never executed; encrypted PDFs rejected |
| XSS | Script in filename or extracted text | React escapes output; strict CSP (`script-src 'self'`) |
