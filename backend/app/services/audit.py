from __future__ import annotations

import hashlib
from typing import Any

from ..core.db import Database, dumps, loads, new_id, utcnow

SYSTEM_ACTOR = {"id": "system", "role": "system", "name": "VeriScope"}
GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


def compute_event_hash(
    eid: str,
    case_id: str | None,
    seq: int,
    prev_hash: str,
    actor_ref: str,
    action: str,
    entity_type: str,
    entity_id: str | None,
    created_at: str,
    payload_json: str,
) -> str:
    payload_canonical = dumps(loads(payload_json)) if payload_json else "{}"
    canonical = f"{eid}|{case_id or ''}|{seq}|{prev_hash}|{actor_ref}|{action}|{entity_type}|{entity_id or ''}|{created_at}|{payload_canonical}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def record(
    db: Database,
    case_id: str | None,
    actor: dict[str, Any],
    action: str,
    entity_type: str,
    entity_id: str | None,
    payload: dict[str, Any] | None = None,
) -> str:
    eid = new_id()
    now = utcnow()
    payload_json = dumps(payload or {})
    actor_id = actor.get("id", "system")

    if case_id:
        last = db.one(
            "SELECT seq, event_hash FROM audit_events WHERE case_id = ? ORDER BY seq DESC, created_at DESC LIMIT 1",
            (case_id,),
        )
        if last and last.get("event_hash"):
            seq = int(last.get("seq") or 0) + 1
            prev_hash = str(last["event_hash"])
        else:
            seq = 1
            prev_hash = GENESIS_HASH
    else:
        seq = 0
        prev_hash = GENESIS_HASH

    event_hash = compute_event_hash(
        eid, case_id, seq, prev_hash, actor_id, action, entity_type, entity_id, now, payload_json
    )

    db.insert(
        "audit_events",
        {
            "id": eid,
            "case_id": case_id,
            "actor_ref": actor_id,
            "actor_role": actor.get("role", "system"),
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "payload_json": payload_json,
            "created_at": now,
            "seq": seq,
            "prev_hash": prev_hash,
            "event_hash": event_hash,
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
            "seq": r.get("seq", 0),
            "action": r["action"],
            "actor": r["actor_name"] or ("VeriScope" if r["actor_ref"] == "system" else r["actor_ref"]),
            "actor_role": r["actor_role"],
            "entity_type": r["entity_type"],
            "entity_id": r["entity_id"],
            "payload": loads(r["payload_json"], {}),
            "created_at": r["created_at"],
            "prev_hash": r.get("prev_hash"),
            "event_hash": r.get("event_hash"),
        }
        for r in rows
    ]


def verify_audit_chain(db: Database, case_id: str) -> dict[str, Any]:
    rows = db.all(
        "SELECT id, case_id, seq, prev_hash, event_hash, actor_ref, action, entity_type, entity_id, payload_json, created_at "
        "FROM audit_events WHERE case_id = ? ORDER BY seq ASC, created_at ASC",
        (case_id,),
    )
    if not rows:
        return {"valid": True, "event_count": 0, "message": "Empty audit trail"}

    expected_prev = GENESIS_HASH
    for idx, r in enumerate(rows):
        expected_seq = idx + 1
        seq = r.get("seq", 0)
        prev_hash = r.get("prev_hash", "")
        event_hash = r.get("event_hash", "")

        if seq != expected_seq:
            return {
                "valid": False,
                "broken_at_seq": seq,
                "error": f"Sequence discontinuity at index {idx}: expected seq {expected_seq}, got {seq}",
            }

        if prev_hash != expected_prev:
            return {
                "valid": False,
                "broken_at_seq": seq,
                "error": f"Hash chain broken at seq {seq}: expected prev_hash {expected_prev}, got {prev_hash}",
            }

        computed = compute_event_hash(
            r["id"],
            r["case_id"],
            r["seq"],
            r["prev_hash"],
            r["actor_ref"],
            r["action"],
            r["entity_type"],
            r["entity_id"],
            r["created_at"],
            r["payload_json"] or "{}",
        )
        if computed != event_hash:
            return {
                "valid": False,
                "broken_at_seq": seq,
                "error": f"Hash mismatch at seq {seq}: stored {event_hash}, computed {computed}",
            }

        expected_prev = event_hash

    return {
        "valid": True,
        "event_count": len(rows),
        "head_hash": rows[-1].get("event_hash"),
        "algorithm": "SHA-256",
    }


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
