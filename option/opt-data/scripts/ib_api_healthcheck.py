#!/usr/bin/env python3
"""
IB Gateway/TWS API healthcheck.

This script is meant to answer:
- Is TCP port open?
- Does the server speak the IB API protocol (server greeting bytes)?
- Can ib_insync complete the API handshake (apiStart)?

If TCP is open but ib_insync connect times out, the most common causes are:
- Gateway not fully logged in yet (stuck on 2FA/CHALLENGE, locked, or not connected)
- "Enable ActiveX and Socket Clients" is OFF
- You are connecting to the wrong port (paper vs live; or a non-API service)
"""

from __future__ import annotations

import argparse
import logging
import socket
import sys
import time
from dataclasses import dataclass

from ib_insync import IB  # type: ignore

logger = logging.getLogger("ib_api_healthcheck")


@dataclass(frozen=True)
class TcpProbeResult:
    ok: bool
    elapsed_sec: float
    received_bytes: int
    received_hex: str
    error: str | None = None


def _tcp_probe(host: str, port: int, *, read_timeout_sec: float) -> TcpProbeResult:
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=5) as sock:
            sock.settimeout(read_timeout_sec)
            try:
                data = sock.recv(64)
            except TimeoutError:
                data = b""
            elapsed = time.perf_counter() - start
            return TcpProbeResult(
                ok=True,
                elapsed_sec=elapsed,
                received_bytes=len(data),
                received_hex=data[:32].hex(),
            )
    except Exception as e:  # noqa: BLE001
        elapsed = time.perf_counter() - start
        return TcpProbeResult(
            ok=False,
            elapsed_sec=elapsed,
            received_bytes=0,
            received_hex="",
            error=f"{type(e).__name__}: {e}",
        )


def _setup_logging(verbosity: int) -> None:
    level = logging.INFO if verbosity <= 0 else logging.DEBUG
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="IB Gateway/TWS API healthcheck")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4001)
    parser.add_argument("--client-id", type=int, default=210)
    parser.add_argument("--connect-timeout", type=float, default=15.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--retry-sleep", type=float, default=2.0)
    parser.add_argument("--tcp-read-timeout", type=float, default=1.0)
    parser.add_argument("-v", "--verbose", action="count", default=0)
    args = parser.parse_args(argv)

    _setup_logging(args.verbose)

    logger.info("TCP probe: host=%s port=%s", args.host, args.port)
    tcp = _tcp_probe(args.host, args.port, read_timeout_sec=args.tcp_read_timeout)
    if not tcp.ok:
        logger.error("TCP probe failed: %s (elapsed=%.2fs)", tcp.error, tcp.elapsed_sec)
        return 2
    logger.info(
        "TCP probe OK (elapsed=%.2fs, received=%s bytes, hex32=%s)",
        tcp.elapsed_sec,
        tcp.received_bytes,
        tcp.received_hex or "-",
    )
    if tcp.received_bytes == 0:
        logger.warning(
            "No server greeting bytes received. IB API ports typically send a greeting on connect; "
            "if ib_insync also times out, re-check Gateway/TWS API settings and login state."
        )

    last_err: Exception | None = None
    for attempt in range(1, args.retries + 1):
        ib = IB()

        def _on_err(req_id: int, code: int, msg: str, contract) -> None:  # type: ignore[no-untyped-def]
            logger.error("IB error: reqId=%s code=%s msg=%s", req_id, code, msg)

        def _on_disc() -> None:
            logger.error("IB disconnected event fired")

        ib.errorEvent += _on_err
        ib.disconnectedEvent += _on_disc

        logger.info(
            "ib_insync connect attempt %s/%s: host=%s port=%s clientId=%s timeout=%.1fs",
            attempt,
            args.retries,
            args.host,
            args.port,
            args.client_id,
            args.connect_timeout,
        )
        try:
            ib.connect(args.host, args.port, clientId=args.client_id, timeout=args.connect_timeout)
            logger.info("Connected: serverVersion=%s", ib.client.serverVersion())
            now = ib.reqCurrentTime()
            logger.info("reqCurrentTime OK: %s", now)
            ib.disconnect()
            logger.info("Disconnected cleanly")
            return 0
        except Exception as e:  # noqa: BLE001
            last_err = e
            try:
                ib.disconnect()
            except Exception:  # noqa: BLE001
                pass
            logger.error("Connect attempt failed: %s: %s", type(e).__name__, e)
            if attempt < args.retries:
                time.sleep(args.retry_sleep)

    logger.error("All attempts failed. Last error: %s: %s", type(last_err).__name__, last_err)
    logger.error(
        "If TCP connects but ib_insync times out, check IB Gateway/TWS UI:\n"
        "- Configure -> API -> Settings: enable 'ActiveX and Socket Clients'\n"
        "- Confirm the socket port matches --port (live default 4001; paper default 4002; TWS default 7497)\n"
        "- Ensure Gateway is fully logged in (not waiting on 2FA/CHALLENGE) and not locked\n"
        "- If 'Use SSL' for API is enabled, disable it (ib_insync expects the plain socket API)"
    )
    return 3


if __name__ == "__main__":
    raise SystemExit(main())

