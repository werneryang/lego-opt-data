#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import subprocess

ET = ZoneInfo("America/New_York")
START = time(9, 35)


def sleep_until_next_start() -> None:
    now = datetime.now(ET)
    start_dt = datetime.combine(now.date(), START, tzinfo=ET)
    if now >= start_dt:
        start_dt = start_dt + timedelta(days=1)
    delta = int((start_dt - now).total_seconds())
    if delta > 0:
        print(f"[loop] sleeping {delta}s until {start_dt.isoformat()}")
        subprocess.run(["sleep", str(delta)], check=False)


while True:
    sleep_until_next_start()
    duration = (
        subprocess.check_output(
            ["./scripts/ops/streaming_duration.py", "--start-clock", "09:35"],
            text=True,
        )
        .strip()
    )
    if duration and int(duration) > 0:
        cmd = [
            "./.venv/bin/python",
            "-m",
            "opt_data.cli",
            "streaming",
            "--config",
            "config/opt-data.streaming.local.toml",
            "--duration",
            duration,
            "--flush-interval",
            "1800",
            "--metrics-interval",
            "300",
        ]
        print(f"[loop] starting streaming for {duration}s")
        subprocess.run(cmd, check=False)
