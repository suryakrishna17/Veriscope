"""Field registry and deterministic normalisers. Normalised values are what rules compare."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher


@dataclass(frozen=True)
class FieldSpec:
    key: str
    label: str
    kind: str  # text | name | org | date | money | email | phone | id | bool


FIELDS: dict[str, FieldSpec] = {
    s.key: s
    for s in [
        FieldSpec("applicant_name", "Applicant name", "name"),
        FieldSpec("student_name", "Student name", "name"),
        FieldSpec("person_name", "Person name", "name"),
        FieldSpec("institution_name", "Institution name", "org"),
        FieldSpec("institution_id", "Institution ID", "id"),
        FieldSpec("application_date", "Application date", "date"),
        FieldSpec("programme_name", "Programme", "text"),
        FieldSpec("course_name", "Course", "text"),
        FieldSpec("tuition_fee", "Tuition fee", "money"),
        FieldSpec("hostel_fee", "Hostel fee", "money"),
        FieldSpec("exam_fee", "Examination fee", "money"),
        FieldSpec("total_amount", "Total amount claimed", "money"),
        FieldSpec("contact_email", "Email", "email"),
        FieldSpec("contact_phone", "Phone", "phone"),
        FieldSpec("declaration_checked", "Declaration ticked", "bool"),
        FieldSpec("signature_present", "Signature detected", "bool"),
        FieldSpec("authorized_signatory_name", "Authorised signatory", "name"),
        FieldSpec("designation", "Designation", "text"),
        FieldSpec("letter_date", "Letter date", "date"),
        FieldSpec("valid_until", "Valid until", "date"),
        FieldSpec("seal_present", "Seal detected", "bool"),
        FieldSpec("letterhead_present", "Letterhead detected", "bool"),
        FieldSpec("enrolment_number", "Enrolment number", "id"),
        FieldSpec("enrolment_date", "Enrolment date", "date"),
        FieldSpec("document_issue_date", "Issue date", "date"),
        # -------------------------------------------------------- AICTE EoA fields (Step 3B)
        FieldSpec("academic_year", "Academic year", "text"),
        FieldSpec("principal_director_name", "Principal / Director name", "name"),
        FieldSpec("land_category", "Land category", "text"),
        FieldSpec("total_built_up_area", "Total built-up area", "text"),
        FieldSpec("university_name", "University name", "org"),
        FieldSpec("affiliation_order_number", "Affiliation order number", "id"),
        FieldSpec("order_date", "Order date", "date"),
        FieldSpec("fire_authority_name", "Fire authority name", "org"),
        FieldSpec("noc_number", "NOC number", "id"),
        FieldSpec("building_coverage", "Building coverage", "text"),
        FieldSpec("structural_engineer_name", "Structural engineer name", "name"),
        FieldSpec("license_registration_number", "License / Registration number", "id"),
        FieldSpec("land_area", "Land area", "text"),
        FieldSpec("survey_number", "Survey number", "id"),
        FieldSpec("building_area", "Building area", "text"),
        FieldSpec("issuing_authority", "Issuing authority", "org"),
        # EoA committee self-disclosure boolean checkboxes
        FieldSpec("anti_ragging_committee_constituted", "Anti-Ragging Committee constituted", "bool"),
        FieldSpec("anti_ragging_squad_constituted", "Anti-Ragging Squad constituted", "bool"),
        FieldSpec("icc_constituted", "Internal Complaints Committee (ICC) constituted", "bool"),
        FieldSpec("sgrc_constituted", "Student Grievance Redressal Committee constituted", "bool"),
        FieldSpec("sc_st_committee_constituted", "SC/ST Committee constituted", "bool"),
        FieldSpec("iqac_established", "IQAC established", "bool"),
        FieldSpec("barrier_free_environment_available", "Barrier-Free Environment available", "bool"),
        FieldSpec("mandatory_disclosure_url_active", "Mandatory Disclosure website active", "bool"),
    ]
}


_DATE_FORMATS = ("%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d", "%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y", "%d-%b-%Y")
_ORG_STOPWORDS = {"the", "of", "and", "pvt", "private", "ltd", "limited", "&"}
_ORG_SYNONYMS = {"tech": "technical", "inst": "institute", "instt": "institute", "univ": "university", "engg": "engineering"}


def _clean(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    return re.sub(r"\s+", " ", value).strip(" .,:;-_|")


def parse_date(value: str) -> date | None:
    v = _clean(value)
    v = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", v)
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(v, fmt).date()
        except ValueError:
            continue
    return None


def parse_money(value: str) -> Decimal | None:
    v = re.sub(r"(?i)(rs\.?|inr|₹|/-)", "", value).replace(",", "").strip()
    m = re.search(r"-?\d+(\.\d{1,2})?", v)
    if not m:
        return None
    try:
        return Decimal(m.group(0)).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


def normalize(key: str, raw: str | None) -> str | None:
    if raw is None:
        return None
    spec = FIELDS.get(key)
    v = _clean(str(raw))
    if not v:
        return None
    kind = spec.kind if spec else "text"
    if kind == "date":
        d = parse_date(v)
        return d.isoformat() if d else None
    if kind == "money":
        m = parse_money(v)
        return str(m) if m is not None else None
    if kind == "email":
        return v.lower().replace(" ", "")
    if kind == "phone":
        digits = re.sub(r"\D", "", v)
        if digits.startswith("91") and len(digits) == 12:
            digits = digits[2:]
        return digits or None
    if kind == "id":
        return re.sub(r"[^A-Z0-9-]", "", v.upper()) or None
    if kind == "bool":
        low = v.lower()
        if low in {"yes", "true", "1", "y", "x", "detected", "[x]", "[✓]", "[✔]", "☑", "✓", "✔"} or bool(re.search(r"\[\s*[xX✓✔]\s*\]|☑", low)):
            return "yes"
        return "no"
    if kind in {"name", "org"}:
        small = {"of", "and", "the", "for", "in", "&"}
        words = v.split()
        out = []
        for i, w in enumerate(words):
            if i > 0 and w.lower() in small:
                out.append(w.lower())
            elif w.islower() or (w.isupper() and len(w) > 3):
                out.append(w.capitalize())
            else:
                out.append(w)
        return " ".join(out)
    return v


def comparison_key(kind: str, value: str) -> str:
    v = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    tokens = re.findall(r"[a-z0-9]+", v)
    if kind == "org":
        tokens = [_ORG_SYNONYMS.get(t, t) for t in tokens if t not in _ORG_STOPWORDS]
    return " ".join(sorted(tokens))


def similarity(kind: str, a: str, b: str) -> float:
    """Token-set similarity 0..100 (order-insensitive, stopword-aware for organisations)."""
    ka, kb = comparison_key(kind, a), comparison_key(kind, b)
    if not ka or not kb:
        return 0.0
    if ka == kb:
        return 100.0
    sa, sb = set(ka.split()), set(kb.split())
    inter = " ".join(sorted(sa & sb))
    da, db = " ".join(sorted(sa - sb)), " ".join(sorted(sb - sa))
    cands = [
        SequenceMatcher(None, ka, kb).ratio(),
        SequenceMatcher(None, inter, (inter + " " + da).strip()).ratio() if inter else 0.0,
        SequenceMatcher(None, inter, (inter + " " + db).strip()).ratio() if inter else 0.0,
    ]
    # token-set ratio: the strongest of the comparisons, but penalise when both sides have extra tokens
    score = max(cands)
    if da and db:
        score = min(score, SequenceMatcher(None, ka, kb).ratio())
    return round(score * 100, 1)
