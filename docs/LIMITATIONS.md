# Limitations (be upfront about these)

- **Not authenticity proof.** No check here establishes that a document was issued by its stated issuer. Only a recorded issuer response can produce *Issuer verified*, and no real issuer is connected.
- **Prototype rulebook.** Rules are illustrative, not official AICTE policy.
- **Visual heuristics report presence only.** Signature, seal and letterhead detection say whether ink/shapes exist, not whether they are valid.
- **Extraction expects `Label: value` layouts.** Free-form or tabular layouts, handwriting and multi-column forms need additional extractors or a layout model.
- **OCR is English-only by default.** Add Tesseract language packs (e.g. `hin`) and set `OCR_LANG`.
- **Single-instance runtime.** In-process jobs and rate limiting; use a queue and Redis to scale out.
- **SQLite.** Fine for demos and small pilots; move to PostgreSQL for concurrent production use.
- **Retention.** Demo data is wiped with `scripts/reset`; there is no per-case deletion or retention policy yet.
- **Synthetic data only.** Do not upload real personal documents to this prototype.
