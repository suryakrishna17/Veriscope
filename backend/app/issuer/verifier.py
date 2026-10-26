"""Issuer verification adapter. ISSUER_VERIFIED may only come from a recorded issuer response.

NullIssuerVerifier (default) never verifies anything. MockIssuerVerifier is a clearly-labelled
SIMULATION of a future integration (e.g. a university or DigiLocker lookup) and is off by default.
"""
from __future__ import annotations

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
        if doc_type == "EOA_APPLICATION_FORM":
            from ..records.registry import aicte_records
            inst_id = str(fields.get("institution_id") or "").strip()
            inst_name = str(fields.get("institution_name") or "").strip()
            res = aicte_records.cross_check_application(inst_id, inst_name)
            if res["verified"]:
                return IssuerCheck(
                    label="VERIFIED",
                    issuer="AICTE Central Portal",
                    response_id=f"AICTE-REG-{inst_id}",
                    checked_at=_now(),
                    reason=f"AICTE Central Database confirmed active accreditation: {res['notes']}",
                    simulated=True,
                )
            elif res["status"] == "MISMATCH_DETECTED":
                return IssuerCheck(
                    label="MISMATCH_DETECTED",
                    issuer="AICTE Central Portal",
                    response_id=f"AICTE-REG-{inst_id}",
                    checked_at=_now(),
                    reason=res["notes"],
                    simulated=True,
                )
            else:
                return IssuerCheck(
                    label="NOT_VERIFIED",
                    issuer="AICTE Central Portal",
                    response_id=None,
                    checked_at=_now(),
                    reason=res["notes"],
                    simulated=True,
                )

        if doc_type != "ENROLMENT_OR_IDENTITY_PROOF":
            return NullIssuerVerifier().verify(doc_type, fields)
        rec = self.registry.get(fields.get("enrolment_number") or "")
        if rec and rec.get("name", "").lower() == (fields.get("person_name") or "").lower():
            return IssuerCheck("ISSUER_VERIFIED", rec["issuer"], f"SIM-{new_id()[:8]}", _now(), "Simulated issuer registry confirmed enrolment number and name.", True)
        return IssuerCheck("NOT_VERIFIED", None, None, _now(), "Simulated issuer registry had no matching record.", True)


class DigiLockerIssuerVerifier:
    """DigiLocker & National Academic Depository (NAD) DPI adapter."""
    name = "digilocker"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("DIGILOCKER_API_KEY", "")

    def verify(self, doc_type: str, fields: dict[str, str | None]) -> IssuerCheck:
        if not self.api_key:
            return IssuerCheck(
                label="NOT_VERIFIED",
                issuer=None,
                response_id=None,
                checked_at=_now(),
                reason="DigiLocker API key not configured. Live issuer verification disabled.",
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
