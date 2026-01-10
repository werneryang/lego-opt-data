#!/usr/bin/env python3
"""
Minimal IB Gateway/TWS connect smoke test (ib_insync).

Usage:
  python scripts/ib_connect_smoke.py --host 127.0.0.1 --port 4001 --client-id 230
"""

from __future__ import annotations

import argparse

from ib_insync import IB  # type: ignore


def main() -> int:
    parser = argparse.ArgumentParser(description="Minimal IB connect smoke test")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7496)
    parser.add_argument("--client-id", type=int, default=230)
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args()

    ib = IB()
    ib.connect(args.host, args.port, clientId=args.client_id, timeout=args.timeout)
    try:
        print(f"connected: serverVersion={ib.client.serverVersion()}")
        print(f"currentTime: {ib.reqCurrentTime()}")
    finally:
        ib.disconnect()
        print("disconnected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

