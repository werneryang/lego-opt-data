from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Mapping

logger = logging.getLogger(__name__)


class AuditLogger:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS mcp_audit_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        tool_name TEXT NOT NULL,
                        params TEXT,
                        rows_returned INTEGER,
                        duration_ms REAL,
                        status TEXT NOT NULL,
                        error TEXT
                    )
                    """
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_mcp_audit_ts ON mcp_audit_log(timestamp)"
                )
        except Exception as exc:  # pragma: no cover - filesystem issues
            logger.warning(f"Failed to initialize MCP audit DB: {exc}")

    def record(
        self,
        tool_name: str,
        params: Mapping[str, Any],
        rows_returned: int,
        duration_ms: float,
        status: str,
        error: str | None = None,
    ) -> None:
        try:
            params_json = json.dumps(params, ensure_ascii=False)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO mcp_audit_log (
                        tool_name,
                        params,
                        rows_returned,
                        duration_ms,
                        status,
                        error
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (tool_name, params_json, rows_returned, duration_ms, status, error),
                )
        except Exception as exc:  # pragma: no cover - best-effort audit
            logger.warning(f"Failed to write MCP audit record: {exc}")
