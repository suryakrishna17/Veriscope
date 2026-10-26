"""AICTE Institutional Records Store (SIH26261 Requirement R2).

Provides simulated integration with AICTE Central Database to cross-validate:
- Permanent Institute ID & Registered Legal Name
- Previous Extension of Approval (EoA) Status
- Approved Programmes & Annual Sanctioned Intake
- Technical Education Regulatory (TER) Fee Payment Confirmation
- Past Deficiency / Debarment Records
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UTC = getattr(datetime, "UTC", timezone.utc)
REGISTRY_FILE = Path(__file__).resolve().parent / "aicte_registry.json"


def _now() -> str:
    return datetime.now(UTC).isoformat()


class AicteRecordsStore:
    def __init__(self, registry_path: Path | None = None) -> None:
        p = registry_path or REGISTRY_FILE
        self._records: dict[str, dict[str, Any]] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

    def lookup(self, institute_id: str) -> dict[str, Any] | None:
        return self._records.get(institute_id.strip())

    def cross_check_application(
        self,
        institute_id: str,
        declared_name: str,
        declared_intake: int | None = None,
    ) -> dict[str, Any]:
        """Validates submitted application data against official AICTE Central Records (R2)."""
        clean_id = institute_id.strip()
        rec = self.lookup(clean_id)
        checked_at = _now()

        if rec is None:
            return {
                "status": "NOT_FOUND",
                "institute_id": clean_id,
                "source": "AICTE Central Database (SIH-Portal)",
                "checked_at": checked_at,
                "verified": False,
                "notes": f"AICTE Permanent ID '{clean_id}' does not match any registered institution in the master database.",
            }

        # Check Name consistency
        reg_name = rec["name"]
        from difflib import SequenceMatcher
        ratio = SequenceMatcher(None, declared_name.lower().strip(), reg_name.lower().strip()).ratio()
        name_match = ratio >= 0.82

        # Check Intake
        intake_match = True
        if declared_intake is not None:
            intake_match = declared_intake <= rec["approved_intake"]

        # Check TER payment
        ter_ok = rec.get("ter_fee_paid", False)

        is_fully_verified = name_match and intake_match and ter_ok and rec["status"] == "APPROVED_ACTIVE"

        notes = []
        if not name_match:
            notes.append(f"Name mismatch: declared '{declared_name}' vs registered '{reg_name}'.")
        if not intake_match:
            notes.append(f"Declared intake {declared_intake} exceeds approved intake {rec['approved_intake']}.")
        if not ter_ok:
            notes.append("TER Processing Fee payment is unconfirmed in central portal.")

        return {
            "status": "VERIFIED" if is_fully_verified else "MISMATCH_DETECTED",
            "institute_id": clean_id,
            "registered_name": reg_name,
            "source": "AICTE Central Database (SIH-Portal)",
            "checked_at": checked_at,
            "verified": is_fully_verified,
            "ter_payment_status": "PAID" if ter_ok else "UNPAID",
            "ter_transaction_ref": rec.get("ter_transaction_ref"),
            "approved_intake": rec.get("approved_intake"),
            "deficiency_status": rec.get("deficiency_status", "NIL"),
            "notes": " ".join(notes) if notes else "Institution verified active with TER payment confirmed.",
        }


# Global singleton instance
aicte_records = AicteRecordsStore()
