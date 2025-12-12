"""
Metrics collection using SQLite.
"""

import logging
import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Simple metrics collector using SQLite.
    """

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize the metrics database schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        name TEXT NOT NULL,
                        value REAL NOT NULL,
                        type TEXT NOT NULL,
                        tags TEXT
                    )
                """)
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_metrics_name_ts ON metrics(name, timestamp)"
                )
        except Exception as e:
            logger.error(f"Failed to initialize metrics DB: {e}")

    def _record(
        self, name: str, value: float, metric_type: str, tags: Optional[Dict[str, Any]] = None
    ):
        """Internal record method."""
        try:
            tags_json = json.dumps(tags) if tags else None
            # Use a new connection per write to be thread-safe and simple
            # For high throughput, we might want a background worker, but this is fine for now
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO metrics (name, value, type, tags) VALUES (?, ?, ?, ?)",
                    (name, value, metric_type, tags_json),
                )
        except Exception as e:
            # Don't crash app on metrics failure
            logger.warning(f"Failed to record metric {name}: {e}")

    def count(self, name: str, value: int = 1, tags: Optional[Dict[str, Any]] = None):
        """Record a counter metric."""
        self._record(name, float(value), "counter", tags)

    def gauge(self, name: str, value: float, tags: Optional[Dict[str, Any]] = None):
        """Record a gauge metric."""
        self._record(name, value, "gauge", tags)

    def timing(self, name: str, duration_ms: float, tags: Optional[Dict[str, Any]] = None):
        """Record a timing metric."""
        self._record(name, duration_ms, "timing", tags)

    def get_recent_metrics(self, name: str, limit: int = 100) -> list:
        """Query recent metrics for dashboard."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM metrics WHERE name = ? ORDER BY timestamp DESC LIMIT ?",
                    (name, limit),
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []
