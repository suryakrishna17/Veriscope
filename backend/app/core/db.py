"""Dual-mode Database layer: SQLite (default zero-dependency) and PostgreSQL (production).

One connection per thread, explicit transactions, parameter isolation.
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

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None  # type: ignore[assignment]

UTC = getattr(datetime, "UTC", timezone.utc)

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


def new_id() -> str:
    return str(uuid.uuid4())


def utcnow() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def dumps(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), default=str)


def loads(value: Any, default: Any = None) -> Any:
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    return json.loads(value)  # type: ignore[arg-type]


class Database:
    def __init__(self, target: Path | str) -> None:
        target_str = str(target)
        if target_str.startswith(("postgres://", "postgresql://")):
            self.is_postgres = True
            self.url = target_str
            self.path = None
        else:
            self.is_postgres = False
            self.url = None
            self.path = Path(target)
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()

    def conn(self) -> Any:
        c = getattr(self._local, "conn", None)
        if c is not None:
            return c
        if self.is_postgres:
            if psycopg2 is None:
                raise RuntimeError("psycopg2 is required to connect to PostgreSQL. Install psycopg2-binary.")
            c = psycopg2.connect(self.url, cursor_factory=psycopg2.extras.RealDictCursor)
            c.autocommit = False
            self._local.conn = c
            self._local.depth = 0
            return c
        c = sqlite3.connect(self.path, timeout=30, isolation_level=None, check_same_thread=False)  # type: ignore[arg-type]
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
    def transaction(self) -> Iterator[Any]:
        c = self.conn()
        depth = getattr(self._local, "depth", 0)
        if depth == 0:
            if not self.is_postgres:
                c.execute("BEGIN IMMEDIATE")
        self._local.depth = depth + 1
        try:
            yield c
        except BaseException:
            self._local.depth = depth
            if depth == 0:
                c.rollback() if self.is_postgres else c.execute("ROLLBACK")
            raise
        else:
            self._local.depth = depth
            if depth == 0:
                c.commit() if self.is_postgres else c.execute("COMMIT")

    def _prep_sql(self, sql: str) -> str:
        if self.is_postgres and "?" in sql:
            return sql.replace("?", "%s")
        return sql

    def all(self, sql: str, params: tuple | dict = ()) -> list[dict[str, Any]]:  # type: ignore[type-arg]
        sql = self._prep_sql(sql)
        if self.is_postgres:
            with self.conn().cursor() as cur:
                cur.execute(sql, params)
                return [dict(r) for r in cur.fetchall()]
        return [dict(r) for r in self.conn().execute(sql, params).fetchall()]

    def one(self, sql: str, params: tuple | dict = ()) -> dict[str, Any] | None:  # type: ignore[type-arg]
        sql = self._prep_sql(sql)
        if self.is_postgres:
            with self.conn().cursor() as cur:
                cur.execute(sql, params)
                row = cur.fetchone()
                return dict(row) if row else None
        row = self.conn().execute(sql, params).fetchone()
        return dict(row) if row else None

    def scalar(self, sql: str, params: tuple | dict = ()) -> Any:  # type: ignore[type-arg]
        sql = self._prep_sql(sql)
        if self.is_postgres:
            with self.conn().cursor() as cur:
                cur.execute(sql, params)
                row = cur.fetchone()
                if row:
                    return list(row.values())[0]
                return None
        row = self.conn().execute(sql, params).fetchone()
        return row[0] if row else None

    def execute(self, sql: str, params: tuple | dict = ()) -> int:  # type: ignore[type-arg]
        sql = self._prep_sql(sql)
        if self.is_postgres:
            with self.conn().cursor() as cur:
                cur.execute(sql, params)
                return cur.rowcount  # type: ignore[no-any-return]
        return self.conn().execute(sql, params).rowcount

    def insert(self, table: str, row: dict[str, Any]) -> dict[str, Any]:
        cols = ", ".join(row)
        if self.is_postgres:
            marks = ", ".join(f"%({k})s" for k in row)
            with self.conn().cursor() as cur:
                cur.execute(f"INSERT INTO {table} ({cols}) VALUES ({marks})", row)
        else:
            marks = ", ".join(f":{k}" for k in row)
            self.conn().execute(f"INSERT INTO {table} ({cols}) VALUES ({marks})", row)
        return row

    def update(self, table: str, row_id: str, changes: dict[str, Any]) -> None:
        if self.is_postgres:
            sets = ", ".join(f"{k} = %({k})s" for k in changes)
            with self.conn().cursor() as cur:
                cur.execute(f"UPDATE {table} SET {sets} WHERE id = %(_row_id)s", {**changes, "_row_id": row_id})
        else:
            sets = ", ".join(f"{k} = :{k}" for k in changes)
            self.conn().execute(f"UPDATE {table} SET {sets} WHERE id = :_row_id", {**changes, "_row_id": row_id})

    def migrate(self) -> list[str]:
        if self.is_postgres:
            # Execute postgresql_schema.sql on PostgreSQL
            schema_file = MIGRATIONS_DIR / "postgresql_schema.sql"
            if schema_file.exists():
                with self.conn().cursor() as cur:
                    cur.execute(schema_file.read_text())
                self.conn().commit()
                return ["postgresql_schema"]
            return []

        c = self.conn()
        c.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
        applied = {r[0] for r in c.execute("SELECT version FROM schema_migrations")}
        done: list[str] = []
        for f in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if f.stem in applied or f.stem == "postgresql_schema":
                continue
            stem_safe = f.stem.replace("'", "''")
            try:
                c.executescript(
                    f"BEGIN;\n"
                    f"{f.read_text()}\n"
                    f"INSERT INTO schema_migrations(version, applied_at) VALUES ('{stem_safe}', datetime('now'));\n"
                    f"COMMIT;"
                )
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    c.execute(f"INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES ('{stem_safe}', datetime('now'))")
                else:
                    raise
            done.append(f.stem)
        return done
