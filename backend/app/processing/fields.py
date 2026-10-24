"""Deterministic, label-anchored field extraction with page + bounding-box provenance."""
from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from .normalize import normalize
from .text import PageText, Word

DOC_TYPES = (
    # --- Baseline student-support workflow ---
    "APPLICATION_FORM",
    "INSTITUTION_AUTHORIZATION_LETTER",
    "ENROLMENT_OR_IDENTITY_PROOF",
    # --- AICTE EoA statutory workflow (Step 3B) ---
    "EOA_APPLICATION_FORM",
    "UNIVERSITY_AFFILIATION_ORDER",
    "FIRE_SAFETY_CERTIFICATE",
    "BUILDING_SAFETY_CERTIFICATE",
    "LAND_DOCUMENT_AND_USE_CERTIFICATE",
    "OCCUPANCY_CERTIFICATE",
)

LABELS: dict[str, dict[str, list[str]]] = {
    "APPLICATION_FORM": {
        "applicant_name": ["applicant name", "name of applicant", "student name"],
        "institution_name": ["institution name", "name of institution"],
        "institution_id": ["aicte institution id", "institution id", "permanent id"],
        "application_date": ["application date", "date of application"],
        "programme_name": ["programme", "program", "course"],
        "tuition_fee": ["tuition fee"],
        "hostel_fee": ["hostel fee"],
        "exam_fee": ["examination fee", "exam fee"],
        "total_amount": ["total amount claimed", "total amount", "total claimed"],
        "contact_email": ["email", "e mail", "email address"],
        "contact_phone": ["phone", "mobile", "contact number", "mobile number"],
    },
    "INSTITUTION_AUTHORIZATION_LETTER": {
        "institution_name": ["institution name", "institution"],
        "institution_id": ["aicte institution id", "institution id", "permanent id"],
        "student_name": ["student name", "applicant name", "name of student"],
        "authorized_signatory_name": ["authorized signatory", "authorised signatory", "signatory name"],
        "designation": ["designation"],
        "letter_date": ["letter date", "date of issue", "date"],
        "valid_until": ["valid until", "validity", "valid till"],
    },
    "ENROLMENT_OR_IDENTITY_PROOF": {
        "person_name": ["student name", "name"],
        "enrolment_number": ["enrolment number", "enrollment number", "enrolment no", "roll number"],
        "institution_name": ["institution", "institution name"],
        "course_name": ["course", "programme"],
        "enrolment_date": ["date of enrolment", "enrolment date", "date of enrollment"],
        "document_issue_date": ["issue date", "date of issue"],
    },
    # ------------------------------------------------------------------ AICTE EoA document types
    "EOA_APPLICATION_FORM": {
        "institution_name": ["name of the institution", "institution name", "college name", "institution"],
        "institution_id": ["aicte permanent id", "permanent institute id", "institution id", "current application id", "aicte id"],
        "academic_year": ["academic year", "academic session", "session", "academic year of approval"],
        "application_date": ["date of application", "submission date", "application date", "date"],
        "principal_director_name": ["name of principal", "principal director name", "head of institution", "director name", "principal name"],
        "land_category": ["land category", "location category", "geographical classification", "zone"],
        "total_built_up_area": ["total built up area", "total carpet area", "constructed area", "built up area"],
        # Statutory declaration and committee self-disclosures (checkbox fields)
        "declaration_checked": ["declaration", "statutory undertaking", "affidavit"],
        "anti_ragging_committee_constituted": ["anti ragging committee", "anti-ragging committee", "ragging committee constituted"],
        "anti_ragging_squad_constituted": ["anti ragging squad", "anti-ragging squad", "ragging squad constituted"],
        "icc_constituted": ["internal complaints committee", "icc constituted", "icc"],
        "sgrc_constituted": ["student grievance redressal committee", "sgrc constituted", "grievance redressal"],
        "sc_st_committee_constituted": ["sc st committee", "sc/st committee", "sc st atrocities committee"],
        "iqac_established": ["iqac", "internal quality assurance cell", "iqac established"],
        "barrier_free_environment_available": ["barrier free environment", "barrier-free environment", "disability access", "accessibility"],
        "mandatory_disclosure_url_active": ["mandatory disclosure", "public website", "website disclosure", "mandatory public disclosure"],
    },
    "UNIVERSITY_AFFILIATION_ORDER": {
        "university_name": ["affiliating university", "name of university", "university", "name of affiliating university"],
        "institution_name": ["institution name", "name of institution", "college name"],
        "academic_year": ["academic session", "academic year", "period of affiliation", "year"],
        "affiliation_order_number": ["affiliation order no", "order number", "reference no", "order no", "letter no"],
        "order_date": ["order date", "date of issue", "dated", "date"],
    },
    "FIRE_SAFETY_CERTIFICATE": {
        "fire_authority_name": ["fire safety authority", "issuing authority", "fire department", "fire officer"],
        "institution_name": ["institution name", "name of institution", "name of building", "premises"],
        "noc_number": ["noc number", "certificate no", "reference number", "noc no"],
        "valid_until": ["valid until", "valid till", "date of expiry", "validity", "validity date", "expiry date"],
        "building_coverage": ["building coverage", "blocks covered", "premises inspected", "scope"],
    },
    "BUILDING_SAFETY_CERTIFICATE": {
        "structural_engineer_name": ["name of structural engineer", "competent engineer", "certifying engineer", "structural engineer"],
        "institution_name": ["institution name", "name of building", "premises"],
        "license_registration_number": ["registration number", "license no", "chartered engineer no", "registration no", "license number"],
        "valid_until": ["validity date", "valid till", "fitness valid up to", "valid until", "expiry date"],
    },
    "LAND_DOCUMENT_AND_USE_CERTIFICATE": {
        "institution_name": ["institution name", "name of institution", "owner"],
        "land_area": ["land area", "plot area", "total area", "survey area"],
        "land_category": ["land category", "land use", "zoning", "category"],
        "survey_number": ["survey number", "survey no", "plot number", "plot no", "khasra no"],
        "document_issue_date": ["issue date", "date of issue", "dated", "registration date"],
    },
    "OCCUPANCY_CERTIFICATE": {
        "institution_name": ["institution name", "name of institution", "building owner"],
        "building_area": ["built up area", "floor area", "plinth area", "carpet area"],
        "document_issue_date": ["date of issue", "issue date", "certificate date", "dated"],
        "issuing_authority": ["issuing authority", "municipal authority", "local body", "corporation"],
    },
}


@dataclass
class Extracted:
    field_key: str
    raw_value: str | None
    normalized_value: str | None
    confidence: float
    page_number: int | None
    evidence_excerpt: str | None
    bbox: list[float] | None
    source: str


def _norm_label(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s.lower())).strip()


def group_lines(words: list[Word]) -> list[list[Word]]:
    if not words:
        return []
    heights = sorted(w.y1 - w.y0 for w in words)
    tol = max(heights[len(heights) // 2] * 0.55, 0.002)
    lines: list[list[Word]] = []
    for w in sorted(words, key=lambda w: ((w.y0 + w.y1) / 2, w.x0)):
        cy = (w.y0 + w.y1) / 2
        if lines:
            last = lines[-1]
            lcy = sum((x.y0 + x.y1) / 2 for x in last) / len(last)
            if abs(cy - lcy) <= tol:
                last.append(w)
                continue
        lines.append([w])
    return [sorted(line, key=lambda w: w.x0) for line in lines]


def bbox_of(words: list[Word]) -> list[float]:
    return [round(min(w.x0 for w in words), 5), round(min(w.y0 for w in words), 5), round(max(w.x1 for w in words), 5), round(max(w.y1 for w in words), 5)]


def _split_label(line: list[Word]) -> tuple[str, list[Word], list[Word]] | None:
    for i, w in enumerate(line):
        if ":" in w.t:
            before, _, after = w.t.partition(":")
            label_words = line[:i] + ([Word(before, w.x0, w.y0, w.x1, w.y1, w.c)] if before else [])
            value_words = ([Word(after, w.x0, w.y0, w.x1, w.y1, w.c)] if after else []) + line[i + 1 :]
            label = " ".join(x.t for x in label_words)
            return label, label_words, value_words
    return None


def _match(label: str, synonyms: list[str], fuzzy: bool) -> float:
    n = _norm_label(label)
    if n in synonyms:
        return 1.0
    if fuzzy:
        best = max(SequenceMatcher(None, n, s).ratio() for s in synonyms)
        return best if best >= 0.86 else 0.0
    return 0.0


def extract_fields(doc_type: str, pages: list[PageText]) -> list[Extracted]:
    spec = LABELS.get(doc_type, {})
    found: dict[str, tuple[float, Extracted]] = {}
    for page in pages:
        fuzzy = page.source == "ocr"
        for line in group_lines(page.words):
            split = _split_label(line)
            if not split:
                continue
            label, _, value_words = split
            value_words = [w for w in value_words if w.t.strip()]
            if not value_words:
                continue
            for key, syns in spec.items():
                score = _match(label, syns, fuzzy)
                if score <= 0:
                    continue
                raw = " ".join(w.t for w in value_words).strip()
                conf = (sum(w.c for w in value_words) / len(value_words)) / 100.0
                conf = round(conf * (0.98 if page.source == "pdf_text" else 1.0) * score, 3)
                ext = Extracted(
                    key, raw, normalize(key, raw), conf, page.page_number,
                    " ".join(w.t for w in line)[:200], bbox_of(value_words), page.source,
                )
                prev = found.get(key)
                if prev is None or score > prev[0]:
                    found[key] = (score, ext)
                break
    # Baseline workflow: extract declaration checkbox from APPLICATION_FORM
    if doc_type == "APPLICATION_FORM":
        decl = _declaration(pages)
        if decl:
            found["declaration_checked"] = (1.0, decl)
    # AICTE EoA workflow: extract committee checkboxes from EOA_APPLICATION_FORM
    if doc_type == "EOA_APPLICATION_FORM":
        for field_key, extracted in _eoa_committee_checkboxes(pages).items():
            if field_key not in found:
                found[field_key] = (1.0, extracted)
    return [e for _, e in found.values()]


_CHECKED = re.compile(r"\[\s*[xX✓✔]\s*\]|☑|☒")
_UNCHECKED = re.compile(r"\[\s*\]|☐")

# Keyword anchors for EoA committee checkbox fields — order matters (more specific first)
_EOA_CHECKBOX_KEYS: list[tuple[str, list[str]]] = [
    ("anti_ragging_committee_constituted", ["anti ragging committee", "anti-ragging committee"]),
    ("anti_ragging_squad_constituted", ["anti ragging squad", "anti-ragging squad"]),
    ("icc_constituted", ["internal complaints committee", "icc"]),
    ("sgrc_constituted", ["student grievance redressal", "sgrc"]),
    ("sc_st_committee_constituted", ["sc st committee", "sc/st"]),
    ("iqac_established", ["internal quality assurance", "iqac"]),
    ("barrier_free_environment_available", ["barrier free", "barrier-free", "disability access"]),
    ("mandatory_disclosure_url_active", ["mandatory disclosure", "mandatory public disclosure"]),
    ("declaration_checked", ["declaration", "statutory undertaking", "affidavit"]),
]


def _eoa_committee_checkboxes(pages: list[PageText]) -> dict[str, Extracted]:
    """Scan all page lines for EoA committee self-disclosure checkboxes and declaration.

    A line that contains both a recognisable committee keyword AND a checkbox marker
    (checked or unchecked) is recorded as a boolean extracted field.
    Lines with only a keyword and no checkbox are scored as 'yes' when they appear
    next to a checked marker in an adjacent word, providing best-effort coverage
    of multi-column form layouts.
    """
    results: dict[str, Extracted] = {}
    for page in pages:
        for line in group_lines(page.words):
            text = " ".join(w.t for w in line)
            text_lower = text.lower()
            checked = bool(_CHECKED.search(text))
            unchecked = bool(_UNCHECKED.search(text)) and not checked
            if not (checked or unchecked):
                continue  # line has no checkbox; skip
            conf = round(sum(w.c for w in line) / max(len(line), 1) / 100, 3)
            val = "yes" if checked else "no"
            for field_key, keywords in _EOA_CHECKBOX_KEYS:
                if field_key in results:
                    continue
                if any(kw in text_lower for kw in keywords):
                    results[field_key] = Extracted(field_key, val, val, conf, page.page_number, text[:200], bbox_of(line), page.source)
                    break
    return results


def _declaration(pages: list[PageText]) -> Extracted | None:
    for page in pages:
        for line in group_lines(page.words):
            text = " ".join(w.t for w in line)
            if "declare" not in text.lower():
                continue
            checked = bool(_CHECKED.search(text))
            unchecked = bool(_UNCHECKED.search(text)) and not checked
            if checked or unchecked:
                val = "yes" if checked else "no"
                conf = round(sum(w.c for w in line) / len(line) / 100, 3)
                return Extracted("declaration_checked", val, val, conf, page.page_number, text[:200], bbox_of(line), page.source)
    return None
