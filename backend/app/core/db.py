"""Thin SQLite data layer (PostgreSQL-ready schema: UUID text keys, UTC ISO timestamps).

One connection per thread, WAL mode, explicit transactions. Plain SQL keeps the schema in
migrations/ as the single source of truth.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


def new_id() -> str:
    return str(uuid.uuid4())


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def dumps(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), default=str)


def loads(value: str | None, default: Any = None) -> Any:
    if value in (None, ""):
        return default
    return json.loads(value)  # type: ignore[arg-type]


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()

    def conn(self) -> sqlite3.Connection:
        c: sqlite3.Connection | None = getattr(self._local, "conn", None)
        if c is None:
            c = sqlite3.connect(self.path, timeout=30, isolation_level=None, check_same_thread=False)
            c.row_factory = sqlite3.Row
            c.execute("PRAGMA foreign_keys = ON")
            c.execute("PRAGMA journal_mode = WAL")
            c.execute("PRAGMA busy_timeout = 30000")
            self._local.conn = c
            self._local.depth = 0
        return c

    def close(self) -> None:
        c = getattr(self._local, "conn", None)
        if c is not None:
            c.close()
            self._local.conn = None

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        c = self.conn()
        depth = getattr(self._local, "depth", 0)
        if depth == 0:
            c.execute("BEGIN IMMEDIATE")
        self._local.depth = depth + 1
        try:
            yield c
        except BaseException:
            self._local.depth = depth
            if depth == 0:
                c.execute("ROLLBACK")
            raise
        else:
            self._local.depth = depth
            if depth == 0:
                c.execute("COMMIT")

    def all(self, sql: str, params: tuple | dict = ()) -> list[dict[str, Any]]:  # type: ignore[type-arg]
        return [dict(r) for r in self.conn().execute(sql, params).fetchall()]

    def one(self, sql: str, params: tuple | dict = ()) -> dict[str, Any] | None:  # type: ignore[type-arg]
        row = self.conn().execute(sql, params).fetchone()
        return dict(row) if row else None

    def scalar(self, sql: str, params: tuple | dict = ()) -> Any:  # type: ignore[type-arg]
        row = self.conn().execute(sql, params).fetchone()
        return row[0] if row else None

    def execute(self, sql: str, params: tuple | dict = ()) -> int:  # type: ignore[type-arg]
        return self.conn().execute(sql, params).rowcount

    def insert(self, table: str, row: dict[str, Any]) -> dict[str, Any]:
        cols = ", ".join(row)
        marks = ", ".join(f":{k}" for k in row)
        self.conn().execute(f"INSERT INTO {table} ({cols}) VALUES ({marks})", row)
        return row

    def update(self, table: str, row_id: str, changes: dict[str, Any]) -> None:
        sets = ", ".join(f"{k} = :{k}" for k in changes)
        self.conn().execute(f"UPDATE {table} SET {sets} WHERE id = :_row_id", {**changes, "_row_id": row_id})

    def migrate(self) -> list[str]:
        c = self.conn()
        c.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
        applied = {r[0] for r in c.execute("SELECT version FROM schema_migrations")}
        done: list[str] = []
        for f in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if f.stem in applied:
                continue
            c.executescript("BEGIN;\n" + f.read_text() + "\nCOMMIT;")
            c.execute("INSERT INTO schema_migrations VALUES (?, ?)", (f.stem, utcnow()))
            done.append(f.stem)
        return done
