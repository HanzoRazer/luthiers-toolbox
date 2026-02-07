"""
Workflow Sessions Store - Pure SQLite

Minimal SQLite-backed store for workflow_sessions table.

Schema-tolerant:
- Introspects columns at runtime
- Writes only to columns that exist
- Supports session_id column naming from migrations

Uses the workflow_sessions table created by:
    db/migrations/0001_init_workflow_sessions.sql
"""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_db_path() -> Path:
    """
    Resolve DB path (same logic as migrate_sqlite.py).

    Env precedence:
      RMOS_DB_PATH > DATABASE_URL(sqlite://...) > SQLITE_PATH > default
    """
    rmos_db_path = os.environ.get("RMOS_DB_PATH")
    if rmos_db_path:
        return Path(rmos_db_path).expanduser().resolve()

    db_url = os.environ.get("DATABASE_URL")
    if db_url and db_url.startswith("sqlite://"):
        raw = db_url[len("sqlite://"):]
        if raw.startswith("///"):
            raw = raw[2:]  # "///abs" -> "/abs"
        return Path(raw).expanduser().resolve()

    sqlite_path = os.environ.get("SQLITE_PATH")
    if sqlite_path:
        return Path(sqlite_path).expanduser().resolve()

    here = Path(__file__).resolve()
    # workflow/sessions/store.py -> services/api/app -> services/api/.data
    default_db = (here.parents[2] / ".data" / "rmos.sqlite").resolve()
    return default_db


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def _table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    rows = conn.execute(f"PRAGMA table_info({table});").fetchall()
    return [str(r["name"]) for r in rows]


def _json_load_maybe(v: Any) -> Dict[str, Any]:
    if v is None:
        return {}
    if isinstance(v, dict):
        return v
    if isinstance(v, str) and v.strip():
        try:
            obj = json.loads(v)
            return obj if isinstance(obj, dict) else {}
        except (json.JSONDecodeError, ValueError):  # WP-1: narrowed from except Exception
            return {}
    return {}


def _json_dump(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class WorkflowSessionStore:
    """
    Minimal SQLite-backed store for workflow_sessions.

    **Schema tolerant**
    - introspects columns
    - writes only to columns that exist
    - reads everything into `raw` and normalizes common fields
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or _resolve_db_path()

    def _conn(self) -> sqlite3.Connection:
        return _connect(self.db_path)

    def _ensure_ready(self, conn: sqlite3.Connection) -> Tuple[str, List[str]]:
        if not _table_exists(conn, "workflow_sessions"):
            raise RuntimeError(
                "workflow_sessions table not found. Run migrations first."
            )
        cols = _table_columns(conn, "workflow_sessions")
        return "workflow_sessions", cols

    def _id_column(self, cols: List[str]) -> str:
        # Tolerate either name (session_id is from our migration)
        if "workflow_session_id" in cols:
            return "workflow_session_id"
        if "session_id" in cols:
            return "session_id"
        # fallback to first plausible PK-ish column
        for c in cols:
            if c.endswith("_id"):
                return c
        raise RuntimeError("No id column found in workflow_sessions table.")

    def create(
        self,
        *,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        workflow_type: Optional[str] = None,
        current_step: Optional[str] = None,
        machine_id: Optional[str] = None,
        material_id: Optional[str] = None,
        tool_id: Optional[str] = None,
        context_json: Optional[Dict[str, Any]] = None,
        state_data_json: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        conn = self._conn()
        try:
            table, cols = self._ensure_ready(conn)
            id_col = self._id_column(cols)
            sid = f"ws_{uuid.uuid4().hex[:12]}"

            now = _utc_now_iso()
            payload: Dict[str, Any] = {}

            # ID and timestamps
            if id_col in cols:
                payload[id_col] = sid
            if "created_at_utc" in cols:
                payload["created_at_utc"] = now
            if "updated_at_utc" in cols:
                payload["updated_at_utc"] = now

            # Core fields
            if user_id is not None and "user_id" in cols:
                payload["user_id"] = user_id
            if status is not None and "status" in cols:
                payload["status"] = status
            if workflow_type is not None and "workflow_type" in cols:
                payload["workflow_type"] = workflow_type
            if current_step is not None and "current_step" in cols:
                payload["current_step"] = current_step

            # Reference IDs
            if machine_id and "machine_id" in cols:
                payload["machine_id"] = machine_id
            if material_id and "material_id" in cols:
                payload["material_id"] = material_id
            if tool_id and "tool_id" in cols:
                payload["tool_id"] = tool_id

            # JSON fields
            if context_json is not None and "context_json" in cols:
                payload["context_json"] = _json_dump(context_json)
            if state_data_json is not None and "state_data_json" in cols:
                payload["state_data_json"] = _json_dump(state_data_json)

            # Request correlation
            if request_id and "request_id" in cols:
                payload["request_id"] = request_id

            if not payload:
                raise RuntimeError("workflow_sessions schema has no writable columns.")

            col_names = list(payload.keys())
            placeholders = ", ".join(["?"] * len(col_names))
            sql = f"INSERT INTO {table} ({', '.join(col_names)}) VALUES ({placeholders})"

            with conn:
                conn.execute(sql, tuple(payload[c] for c in col_names))

            return self.get(sid) or {"session_id": sid}
        finally:
            conn.close()

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        conn = self._conn()
        try:
            table, cols = self._ensure_ready(conn)
            id_col = self._id_column(cols)
            row = conn.execute(
                f"SELECT * FROM {table} WHERE {id_col} = ?",
                (session_id,),
            ).fetchone()
            if row is None:
                return None
            return dict(row)
        finally:
            conn.close()

    def patch(
        self,
        session_id: str,
        *,
        status: Optional[str] = None,
        current_step: Optional[str] = None,
        workflow_type: Optional[str] = None,
        machine_id: Optional[str] = None,
        material_id: Optional[str] = None,
        tool_id: Optional[str] = None,
        context_json: Optional[Dict[str, Any]] = None,
        state_data_json: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        conn = self._conn()
        try:
            table, cols = self._ensure_ready(conn)
            id_col = self._id_column(cols)

            current = conn.execute(
                f"SELECT * FROM {table} WHERE {id_col} = ?",
                (session_id,),
            ).fetchone()
            if current is None:
                return None
            cur = dict(current)

            updates: Dict[str, Any] = {}

            if status is not None and "status" in cols:
                updates["status"] = status
            if current_step is not None and "current_step" in cols:
                updates["current_step"] = current_step
            if workflow_type is not None and "workflow_type" in cols:
                updates["workflow_type"] = workflow_type
            if machine_id is not None and "machine_id" in cols:
                updates["machine_id"] = machine_id
            if material_id is not None and "material_id" in cols:
                updates["material_id"] = material_id
            if tool_id is not None and "tool_id" in cols:
                updates["tool_id"] = tool_id
            if error_message is not None and "error_message" in cols:
                updates["error_message"] = error_message

            # JSON updates (merge with existing)
            if context_json is not None and "context_json" in cols:
                existing = _json_load_maybe(cur.get("context_json"))
                existing.update(context_json)
                updates["context_json"] = _json_dump(existing)

            if state_data_json is not None and "state_data_json" in cols:
                existing = _json_load_maybe(cur.get("state_data_json"))
                existing.update(state_data_json)
                updates["state_data_json"] = _json_dump(existing)

            if "updated_at_utc" in cols:
                updates["updated_at_utc"] = _utc_now_iso()

            if request_id and "request_id" in cols:
                updates["request_id"] = request_id

            if not updates:
                return self.get(session_id)

            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            sql = f"UPDATE {table} SET {set_clause} WHERE {id_col} = ?"

            with conn:
                conn.execute(sql, tuple(updates.values()) + (session_id,))

            return self.get(session_id)
        finally:
            conn.close()

    def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        workflow_type: Optional[str] = None,
        since_utc: Optional[str] = None,
        until_utc: Optional[str] = None,
        include_total: bool = False,
    ) -> Tuple[List[Dict[str, Any]], Optional[int]]:
        conn = self._conn()
        try:
            table, cols = self._ensure_ready(conn)
            where: List[str] = []
            params: List[Any] = []

            if user_id and "user_id" in cols:
                where.append("user_id = ?")
                params.append(user_id)
            if status and "status" in cols:
                where.append("status = ?")
                params.append(status)
            if workflow_type and "workflow_type" in cols:
                where.append("workflow_type = ?")
                params.append(workflow_type)
            if since_utc and "created_at_utc" in cols:
                where.append("created_at_utc >= ?")
                params.append(since_utc)
            if until_utc and "created_at_utc" in cols:
                where.append("created_at_utc <= ?")
                params.append(until_utc)

            where_sql = f"WHERE {' AND '.join(where)}" if where else ""
            order_sql = "ORDER BY created_at_utc DESC" if "created_at_utc" in cols else ""
            sql = f"SELECT * FROM {table} {where_sql} {order_sql} LIMIT ? OFFSET ?"
            params2 = params + [limit, offset]

            rows = conn.execute(sql, tuple(params2)).fetchall()
            items = [dict(r) for r in rows]

            total: Optional[int] = None
            if include_total:
                total_sql = f"SELECT COUNT(*) AS n FROM {table} {where_sql}"
                total = int(conn.execute(total_sql, tuple(params)).fetchone()["n"])

            return items, total
        finally:
            conn.close()

    def delete(self, session_id: str) -> bool:
        """Delete a session. Returns True if it existed."""
        conn = self._conn()
        try:
            table, cols = self._ensure_ready(conn)
            id_col = self._id_column(cols)

            row = conn.execute(
                f"SELECT 1 FROM {table} WHERE {id_col} = ?",
                (session_id,),
            ).fetchone()
            if row is None:
                return False

            with conn:
                conn.execute(f"DELETE FROM {table} WHERE {id_col} = ?", (session_id,))
            return True
        finally:
            conn.close()
