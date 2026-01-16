#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
import time as time_module
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
VENV_PY = ROOT / ".venv" / "bin" / "python"
if VENV_PY.exists() and Path(sys.executable) != VENV_PY:
    os.execv(str(VENV_PY), [str(VENV_PY), str(Path(__file__).resolve())] + sys.argv[1:])

SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from opt_data.util.calendar import get_trading_session, is_trading_day  # noqa: E402

ET = ZoneInfo("America/New_York")
START = time(9, 35)
PYTHON = str(VENV_PY) if VENV_PY.exists() else sys.executable
DURATION_SCRIPT = ROOT / "scripts/ops/streaming_duration.py"
CONFIG_PATH = ROOT / "config/opt-data.streaming.local.toml"


def _next_trading_start(now: datetime) -> datetime:
    candidate = datetime.combine(now.date(), START, tzinfo=ET)
    if is_trading_day(now.date()):
        if now < candidate:
            return candidate
        session = get_trading_session(now.date())
        if now < session.market_close:
            return now
    next_day = now.date() + timedelta(days=1)
    while not is_trading_day(next_day):
        next_day += timedelta(days=1)
    return datetime.combine(next_day, START, tzinfo=ET)


def sleep_until_next_start() -> None:
    now = datetime.now(ET)
    start_dt = _next_trading_start(now)
    delta = int((start_dt - now).total_seconds())
    if delta > 0:
        print(f"[loop] sleeping {delta}s until {start_dt.isoformat()}")
        time_module.sleep(delta)


def main() -> None:
    try:
        while True:
            sleep_until_next_start()
            duration = (
                subprocess.check_output(
                    [PYTHON, str(DURATION_SCRIPT), "--start-clock", "09:35"],
                    text=True,
                )
                .strip()
            )
            if duration and int(duration) > 0:
                cmd = [
                    PYTHON,
                    "-m",
                    "opt_data.cli",
                    "streaming",
                    "--config",
                    str(CONFIG_PATH),
                    "--duration",
                    duration,
                    "--flush-interval",
                    "1800",
                    "--metrics-interval",
                    "300",
                ]
                print(f"[loop] starting streaming for {duration}s")
                subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        print("[loop] interrupted; exiting")


if __name__ == "__main__":
    main()
