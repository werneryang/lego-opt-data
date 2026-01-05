#!/usr/bin/env python3
"""
Probe IB 30-day implied vol for a stock via reqMktData + generic tick 106.

Example (remote Gateway):
  python scripts/stk_iv_tick106_probe.py --host 100.71.7.100 --port 4001 \
      --client-id 211 --symbol AMZN
"""

from __future__ import annotations

import argparse
import threading
import time
from typing import Any

from ibapi.client import EClient  # type: ignore
from ibapi.contract import Contract  # type: ignore
from ibapi.wrapper import EWrapper  # type: ignore


class Tick106Probe(EWrapper, EClient):
    def __init__(self, req_id: int) -> None:
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)
        self.req_id = req_id
        self.ready = threading.Event()
        self.done = threading.Event()
        self.value: float | None = None

    def nextValidId(self, orderId: int) -> None:  # noqa: N802 - IB API callback name
        self.ready.set()

    def tickGeneric(self, reqId: int, tickType: int, value: float) -> None:  # noqa: N802
        if reqId != self.req_id:
            return
        if tickType == 24:
            self.value = value
            print(f"[probe] tickGeneric type=24 value={value}")
            self.done.set()
        else:
            print(f"[probe] tickGeneric type={tickType} value={value}")

    def error(  # noqa: N802 - IB API callback name
        self,
        reqId: int,
        errorTime: int,
        errorCode: int,
        errorString: str,
        advancedOrderRejectJson: str = "",
    ) -> None:
        print(
            f"[ib-error] reqId={reqId} time={errorTime} code={errorCode} msg={errorString}"
        )


def _build_stock(symbol: str, exchange: str, currency: str) -> Contract:
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "STK"
    contract.exchange = exchange
    contract.currency = currency
    return contract


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probe IB 30-day implied volatility (tickType=24)"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4001)
    parser.add_argument("--client-id", type=int, default=211)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--symbol", default="AMZN")
    parser.add_argument("--exchange", default="SMART")
    parser.add_argument("--currency", default="USD")
    parser.add_argument("--req-id", type=int, default=1)
    parser.add_argument("--generic-ticks", default="106")
    parser.add_argument("--market-data-type", type=int, default=1)
    parser.add_argument(
        "--snapshot",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Use snapshot request (default: false)",
    )
    args = parser.parse_args()

    app = Tick106Probe(args.req_id)
    app.connect(args.host, args.port, clientId=args.client_id)
    thread = threading.Thread(target=app.run, daemon=True)
    thread.start()

    if not app.ready.wait(timeout=args.timeout):
        print("[probe] timed out waiting for API ready")
        app.disconnect()
        return 2

    contract = _build_stock(args.symbol.upper(), args.exchange, args.currency)

    if args.market_data_type:
        app.reqMarketDataType(args.market_data_type)

    print(
        "[probe] requesting",
        f"symbol={args.symbol.upper()}",
        f"genericTicks={args.generic_ticks}",
        f"snapshot={args.snapshot}",
        f"marketDataType={args.market_data_type}",
    )
    app.reqMktData(
        args.req_id,
        contract,
        args.generic_ticks,
        args.snapshot,
        False,
        [],
    )

    if not app.done.wait(timeout=args.timeout):
        print("[probe] timed out waiting for tick type 24")
    else:
        print(f"[probe] received 30d IV={app.value}")

    app.cancelMktData(args.req_id)
    time.sleep(0.5)
    app.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
