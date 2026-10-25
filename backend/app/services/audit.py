from __future__ import annotations

import hashlib
from typing import Any

from ..core.db import Database, dumps, loads, new_id, utcnow

SYSTEM_ACTOR = {"id": "system", "role": "system", "name": "VeriScope"}


def record(db: Database, case_id: str | None, actor: dict[str, Any], action: str, entity_type: str, entity_id: str | None, payload: dict[str, Any] | None = None) -> str:
    eid = new_id()
    db.insert(
        "audit_events",
        {
            "id": eid,
            "case_id": case_id,
            "actor_ref": actor.get("id", "system"),
            "actor_role": actor.get("role", "system"),
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "payload_json": dumps(payload or {}),
            "created_at": utcnow(),
        },
    )
    return eid


def list_events(db: Database, case_id: str, limit: int = 200, offset: int = 0) -> list[dict[str, Any]]:
    rows = db.all(
        """SELECT a.*, u.name AS actor_name FROM audit_events a LEFT JOIN users u ON u.id = a.actor_ref
           WHERE a.case_id = ? ORDER BY a.created_at DESC LIMIT ? OFFSET ?""",
        (case_id, limit, offset),
    )
    return [
        {
            "id": r["id"],
            "action": r["action"],
            "actor": r["actor_name"] or ("VeriScope" if r["actor_ref"] == "system" else r["actor_ref"]),
            "actor_role": r["actor_role"],
            "entity_type": r["entity_type"],
            "entity_id": r["entity_id"],
            "payload": loads(r["payload_json"], {}),
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def compute_merkle_root(db: Database, case_id: str) -> dict[str, Any]:
    """Computes a SHA-256 Merkle tree root hash across all append-only audit events of a case."""
    rows = db.all("SELECT id, action, payload_json, created_at FROM audit_events WHERE case_id = ? ORDER BY created_at ASC", (case_id,))
    if not rows:
        return {"merkle_root": None, "event_count": 0, "algorithm": "SHA-256", "tree_depth": 0}

    hashes = [
        hashlib.sha256(f"{r['id']}|{r['action']}|{r['created_at']}|{r['payload_json']}".encode()).hexdigest()
        for r in rows
    ]
    event_count = len(hashes)
    current_level = hashes
    depth = 1
    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i + 1] if i + 1 < len(current_level) else left
            combined = hashlib.sha256(f"{left}:{right}".encode()).hexdigest()
            next_level.append(combined)
        current_level = next_level
        depth += 1

    return {
        "merkle_root": current_level[0],
        "event_count": event_count,
        "algorithm": "SHA-256",
        "tree_depth": depth,
    }
