from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

mcp = pytest.importorskip("mcp")
types = mcp.types


def test_mcp_server_initialize_and_list_tools(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        """
[paths]
raw = "data/raw/ib/chain"
clean = "data/clean/ib/chain"
state = "state"
contracts_cache = "state/contracts_cache"
run_logs = "state/run_logs"

[observability]
metrics_db_path = "data/metrics.db"
""",
        encoding="utf-8",
    )

    cmd = [
        sys.executable,
        "-m",
        "opt_data.cli",
        "mcp-server",
        "--config",
        str(config),
    ]

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        init = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": types.LATEST_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "0.0"},
            },
        }
        assert proc.stdin is not None
        assert proc.stdout is not None
        proc.stdin.write(json.dumps(init) + "\n")
        proc.stdin.flush()

        init_line = proc.stdout.readline().strip()
        init_msg = json.loads(init_line)
        assert init_msg["id"] == 0
        assert init_msg["result"]["protocolVersion"] == types.LATEST_PROTOCOL_VERSION

        tools_req = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
        proc.stdin.write(json.dumps(tools_req) + "\n")
        proc.stdin.flush()

        tools_line = proc.stdout.readline().strip()
        tools_msg = json.loads(tools_line)
        tool_names = {tool["name"] for tool in tools_msg["result"]["tools"]}

        assert "health_overview" in tool_names
        assert "run_status_overview" in tool_names
        assert "list_recent_runs" in tool_names
        assert "get_partition_issues" in tool_names
        assert "get_chain_sample" in tool_names
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
