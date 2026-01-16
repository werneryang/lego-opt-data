from __future__ import annotations

import anyio
import json
import logging
import time
from pathlib import Path
from typing import Any

from ..config import AppConfig
from .audit import AuditLogger
from .datasource import DataAccess
from .limits import LimitConfig, apply_caps
from .tools import tool_handlers, tool_specs

logger = logging.getLogger(__name__)


def _load_mcp_sdk() -> tuple[Any, Any, Any, Any]:
    try:
        from mcp.server import Server  # type: ignore
        from mcp.server.stdio import stdio_server  # type: ignore
        from mcp.types import Tool, TextContent  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("MCP SDK not installed. Install with: pip install -e .[mcp]") from exc
    return Server, stdio_server, Tool, TextContent


def _count_rows(payload: Any) -> int:
    if isinstance(payload, dict):
        rows = payload.get("rows")
        if isinstance(rows, list):
            return len(rows)
    return 0


def run_stdio_server(
    cfg: AppConfig,
    *,
    audit_db: Path | None = None,
    allow_raw: bool = True,
    allow_clean: bool = True,
    limits: LimitConfig | None = None,
) -> None:
    Server, stdio_server, Tool, TextContent = _load_mcp_sdk()

    effective_allow_raw = allow_raw and cfg.mcp.allow_raw
    effective_allow_clean = allow_clean and cfg.mcp.allow_clean
    data = DataAccess(cfg, allow_raw=effective_allow_raw, allow_clean=effective_allow_clean)
    limits = apply_caps(limits or LimitConfig(), limit=cfg.mcp.limit, days=cfg.mcp.days)

    audit_path = audit_db or (Path(cfg.paths.run_logs) / "mcp_audit.db")
    audit = AuditLogger(audit_path)

    server = Server("opt-data-mcp")
    handlers = tool_handlers(data, limits)

    @server.list_tools()
    async def list_tools() -> list[Any]:
        return [
            Tool(name=spec.name, description=spec.description, inputSchema=spec.input_schema)
            for spec in tool_specs()
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[Any]:
        start = time.perf_counter()
        status = "ok"
        error: str | None = None
        try:
            if name not in handlers:
                raise ValueError(f"Unknown tool: {name}")
            payload = handlers[name](arguments or {})
            text = json.dumps(payload, ensure_ascii=False, indent=2)
            return [TextContent(type="text", text=text)]
        except Exception as exc:
            status = "error"
            error = str(exc)
            logger.exception("MCP tool failed: %s", name)
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            try:
                rows_returned = _count_rows(locals().get("payload"))
                audit.record(
                    name,
                    arguments or {},
                    rows_returned,
                    duration_ms,
                    status,
                    error,
                )
            except Exception:  # pragma: no cover - audit is best-effort
                pass

    async def _run() -> None:
        async with stdio_server() as (read, write):
            init_options = server.create_initialization_options()
            await server.run(read, write, init_options)

    anyio.run(_run)
