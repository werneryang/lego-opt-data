from __future__ import annotations

import argparse
import sys
import importlib.util
from pathlib import Path


async def _run_smoke(
    python: str,
    config: str,
    suppress_pandera_warning: bool,
) -> None:
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    env = None
    if suppress_pandera_warning:
        env = {"DISABLE_PANDERA_IMPORT_WARNING": "True"}

    server = StdioServerParameters(
        command=python,
        args=[
            "-m",
            "opt_data.cli",
            "mcp-server",
            "--config",
            config,
        ],
        cwd=str(Path.cwd()),
        env=env,
    )

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {tool.name for tool in tools.tools}

            expected = {
                "health_overview",
                "run_status_overview",
                "list_recent_runs",
                "get_partition_issues",
                "get_chain_sample",
            }
            missing = expected - names
            if missing:
                raise RuntimeError(f"Missing tools: {sorted(missing)}")

            result = await session.call_tool("health_overview", {"days": 1})
            if result.isError:
                raise RuntimeError("health_overview returned error")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MCP stdio smoke test.")
    parser.add_argument(
        "--config",
        default="config/opt-data.test.toml",
        help="Path to opt-data config TOML",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable to use for server",
    )
    parser.add_argument(
        "--keep-pandera-warning",
        action="store_true",
        help="Do not suppress Pandera import warning",
    )

    args = parser.parse_args()

    if importlib.util.find_spec("mcp") is None:
        print("[mcp-smoke] skipped: mcp not installed")
        return 0

    try:
        import anyio

        anyio.run(
            _run_smoke,
            args.python,
            args.config,
            not args.keep_pandera_warning,
        )
    except Exception as exc:
        print(f"[mcp-smoke] failed: {exc}", file=sys.stderr)
        return 1

    print("[mcp-smoke] ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
