#!/usr/bin/env python3
"""
Small STK historical IV probe for IB TWS/Gateway.

Example (remote Gateway):
  python scripts/stk_iv_history_probe.py --host 100.71.7.100 --port 7496 \
      --client-id 211 --symbol AMZN --bar-sizes "1 day,8 hours,1 hour"
"""

from __future__ import annotations

import argparse
import json
import statistics
from typing import Any, List

from ib_insync import IB, Stock  # type: ignore


def _parse_bar_sizes(raw: str) -> List[str]:
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return parts or ["1 day"]


def _bar_date(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _bars_to_dicts(bars: List[Any]) -> List[dict[str, Any]]:
    return [
        {
            "date": _bar_date(b.date),
            "open": b.open,
            "high": b.high,
            "low": b.low,
            "close": b.close,
            "volume": b.volume,
            "barCount": b.barCount,
            "average": b.average,
        }
        for b in bars
    ]


def _index_by_date(bars: List[Any]) -> dict[str, Any]:
    return {_bar_date(b.date): b for b in bars}


def _compare_bars(
    primary_label: str,
    primary_bars: List[Any],
    secondary_label: str,
    secondary_bars: List[Any],
) -> None:
    primary_map = _index_by_date(primary_bars)
    secondary_map = _index_by_date(secondary_bars)
    overlap = sorted(set(primary_map.keys()) & set(secondary_map.keys()))
    if not overlap:
        print("[compare] no overlapping bars to compare")
        return

    diffs = []
    pct_diffs = []
    for key in overlap:
        a = primary_map[key].close
        b = secondary_map[key].close
        if a is None or b is None:
            continue
        diff = a - b
        diffs.append(diff)
        if b:
            pct_diffs.append(abs(diff) / abs(b))

    if not diffs:
        print("[compare] no comparable close values")
        return

    mean_diff = statistics.mean(diffs)
    mean_abs = statistics.mean(abs(d) for d in diffs)
    min_diff = min(diffs)
    max_diff = max(diffs)
    if pct_diffs:
        mean_pct = statistics.mean(pct_diffs)
        pct_str = f"{mean_pct:.6f}"
    else:
        pct_str = "n/a"

    print(
        "[compare] overlap=%d %s vs %s mean_diff=%.6f mean_abs=%.6f "
        "min_diff=%.6f max_diff=%.6f mean_abs_pct=%s"
        % (
            len(overlap),
            primary_label,
            secondary_label,
            mean_diff,
            mean_abs,
            min_diff,
            max_diff,
            pct_str,
        )
    )


def _fetch_bars(
    ib: IB,
    contract: Any,
    *,
    bar_size: str,
    duration: str,
    what: str,
    end_date_time: str,
    use_rth: bool,
    format_date: int,
    keep_up_to_date: bool,
) -> List[Any]:
    bars = ib.reqHistoricalData(
        contract,
        endDateTime=end_date_time,
        durationStr=duration,
        barSizeSetting=bar_size,
        whatToShow=what,
        useRTH=int(use_rth),
        formatDate=format_date,
        keepUpToDate=keep_up_to_date,
        chartOptions=[],
    )
    return list(bars) if bars else []


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe STK historical IV data via IB")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7496)
    parser.add_argument("--client-id", type=int, default=211)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--symbol", default="AMZN")
    parser.add_argument("--exchange", default="SMART")
    parser.add_argument("--currency", default="USD")
    parser.add_argument("--duration", default="300 D")
    parser.add_argument("--bar-sizes", default="1 day")
    parser.add_argument("--what", default="OPTION_IMPLIED_VOLATILITY")
    parser.add_argument("--end-date-time", default="")
    parser.add_argument("--format-date", type=int, default=1)
    parser.add_argument(
        "--use-rth",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Use Regular Trading Hours (default: true)",
    )
    parser.add_argument(
        "--keep-up-to-date",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Keep subscription updated (default: false)",
    )
    parser.add_argument("--print-head", type=int, default=3)
    parser.add_argument("--save-json", default="")
    args = parser.parse_args()

    bar_sizes = _parse_bar_sizes(args.bar_sizes)
    primary_what = args.what
    secondary_what = (
        "OPTION_IMPLIED_VOLATILITY"
        if primary_what == "HISTORICAL_VOLATILITY"
        else "HISTORICAL_VOLATILITY"
    )

    ib = IB()

    def on_error(req_id: int, error_code: int, error_string: str, _contract: Any) -> None:
        print(f"[ib-error] reqId={req_id} code={error_code} msg={error_string}")

    ib.errorEvent += on_error

    ib.connect(args.host, args.port, clientId=args.client_id, timeout=args.timeout)
    try:
        contract = Stock(args.symbol.upper(), args.exchange, args.currency)
        qualified = ib.qualifyContracts(contract)
        if not qualified:
            print(f"[probe] failed to qualify {args.symbol}")
            return 2

        for bar_size in bar_sizes:
            print(
                "[probe] requesting",
                f"symbol={args.symbol.upper()}",
                f"bar_size={bar_size}",
                f"duration={args.duration}",
                f"what={primary_what}",
                f"useRTH={int(args.use_rth)}",
            )
            primary_bars = _fetch_bars(
                ib,
                contract,
                bar_size=bar_size,
                duration=args.duration,
                what=primary_what,
                end_date_time=args.end_date_time,
                use_rth=args.use_rth,
                format_date=args.format_date,
                keep_up_to_date=args.keep_up_to_date,
            )
            if not primary_bars:
                print("[probe] no bars returned")
                continue

            first_date = _bar_date(primary_bars[0].date)
            last_date = _bar_date(primary_bars[-1].date)
            print(f"[probe] bars={len(primary_bars)} first={first_date} last={last_date}")

            head = primary_bars[: max(args.print_head, 0)]
            for idx, b in enumerate(head, start=1):
                print(
                    f"[probe] head[{idx}] date={_bar_date(b.date)} "
                    f"open={b.open} high={b.high} low={b.low} close={b.close}"
                )

            print(
                "[probe] requesting",
                f"symbol={args.symbol.upper()}",
                f"bar_size={bar_size}",
                f"duration={args.duration}",
                f"what={secondary_what}",
                f"useRTH={int(args.use_rth)}",
            )
            secondary_bars = _fetch_bars(
                ib,
                contract,
                bar_size=bar_size,
                duration=args.duration,
                what=secondary_what,
                end_date_time=args.end_date_time,
                use_rth=args.use_rth,
                format_date=args.format_date,
                keep_up_to_date=args.keep_up_to_date,
            )
            if not secondary_bars:
                print("[probe] no bars returned")
                continue

            print(
                f"[probe] compare {primary_what} vs {secondary_what} "
                f"bar_size={bar_size}"
            )
            _compare_bars(primary_what, primary_bars, secondary_what, secondary_bars)

            if args.save_json:
                primary_payload = _bars_to_dicts(primary_bars)
                with open(args.save_json, "w", encoding="utf-8") as f:
                    json.dump(primary_payload, f)
                print(f"[probe] saved {len(primary_payload)} bars to {args.save_json}")

                hv_path = None
                if args.save_json.endswith(".json"):
                    hv_path = args.save_json[:-5] + ".hv.json"
                else:
                    hv_path = args.save_json + ".hv.json"

                secondary_payload = _bars_to_dicts(secondary_bars)
                with open(hv_path, "w", encoding="utf-8") as f:
                    json.dump(secondary_payload, f)
                print(f"[probe] saved {len(secondary_payload)} bars to {hv_path}")
    finally:
        ib.disconnect()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
