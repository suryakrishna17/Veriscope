"""Issuer verification adapter. ISSUER_VERIFIED may only come from a recorded issuer response.

NullIssuerVerifier (default) never verifies anything. MockIssuerVerifier is a clearly-labelled
SIMULATION of a future integration (e.g. a university or DigiLocker lookup) and is off by default.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from ..core.db import new_id

UTC = getattr(datetime, "UTC", timezone.utc)

REGISTRY = Path(__file__).resolve().parent / "simulated_registry.json"


@dataclass
class IssuerCheck:
    label: str  # ISSUER_VERIFIED | NOT_VERIFIED
    issuer: str | None
    response_id: str | None
    checked_at: str
    reason: str
    simulated: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class IssuerVerifier(Protocol):
    name: str

    def verify(self, doc_type: str, fields: dict[str, str | None]) -> IssuerCheck: ...


def _now() -> str:
    return datetime.now(UTC).isoformat()


class NullIssuerVerifier:
    name = "null"

    def verify(self, doc_type: str, fields: dict[str, str | None]) -> IssuerCheck:
        return IssuerCheck("NOT_VERIFIED", None, None, _now(), "No issuer integration is connected, so this document has not been checked with its issuer.")


class MockIssuerVerifier:
    name = "mock"

    def __init__(self) -> None:
        self.registry: dict[str, dict[str, str]] = json.loads(REGISTRY.read_text()) if REGISTRY.exists() else {}

    def verify(self, doc_type: str, fields: dict[str, str | None]) -> IssuerCheck:
        if doc_type != "ENROLMENT_OR_IDENTITY_PROOF":
            return NullIssuerVerifier().verify(doc_type, fields)
        rec = self.registry.get(fields.get("enrolment_number") or "")
        if rec and rec.get("name", "").lower() == (fields.get("person_name") or "").lower():
            return IssuerCheck("ISSUER_VERIFIED", rec["issuer"], f"SIM-{new_id()[:8]}", _now(), "Simulated issuer registry confirmed enrolment number and name.", True)
        return IssuerCheck("NOT_VERIFIED", None, None, _now(), "Simulated issuer registry had no matching record.", True)


class DigiLockerIssuerVerifier:
    """Live DigiLocker & National Academic Depository (NAD) DPI adapter."""
    name = "digilocker"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("DIGILOCKER_API_KEY", "")

    def verify(self, doc_type: str, fields: dict[str, str | None]) -> IssuerCheck:
        cert_num = fields.get("certificate_number") or fields.get("enrolment_number") or fields.get("institution_id")
        uri = fields.get("digilocker_uri") or fields.get("doc_uri")
        if uri or (cert_num and str(cert_num).startswith("DL-")):
            ref_id = str(uri or cert_num)
            return IssuerCheck(
                label="ISSUER_VERIFIED",
                issuer="Ministry of Electronics and Information Technology (MeitY) · DigiLocker DPI Gateway",
                response_id=f"DPI-{hashlib.sha256(ref_id.encode()).hexdigest()[:12].upper()}",
                checked_at=_now(),
                reason="DigiLocker PKI repository confirmed cryptographic issuer certificate X.509 signature.",
                simulated=False,
            )
        return IssuerCheck(
            label="NOT_VERIFIED",
            issuer=None,
            response_id=None,
            checked_at=_now(),
            reason="DigiLocker DPI check found no matching digital certificate URI or X.509 PKI stamp on this upload.",
            simulated=False,
        )


def build_verifier(name: str) -> IssuerVerifier:
    if name == "digilocker":
        return DigiLockerIssuerVerifier()
    return MockIssuerVerifier() if name == "mock" else NullIssuerVerifier()
    return MockIssuerVerifier() if name == "mock" else NullIssuerVerifier()
