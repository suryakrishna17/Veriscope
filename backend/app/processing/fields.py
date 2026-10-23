"""Deterministic, label-anchored field extraction with page + bounding-box provenance."""
from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from .normalize import normalize
from .text import PageText, Word

DOC_TYPES = ("APPLICATION_FORM", "INSTITUTION_AUTHORIZATION_LETTER", "ENROLMENT_OR_IDENTITY_PROOF")

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
    if doc_type == "APPLICATION_FORM":
        decl = _declaration(pages)
        if decl:
            found["declaration_checked"] = (1.0, decl)
    return [e for _, e in found.values()]


_CHECKED = re.compile(r"\[\s*[xX✓✔]\s*\]|☑|☒")
_UNCHECKED = re.compile(r"\[\s*\]|☐")


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
