from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from typing import Any, Iterable, Sequence, TYPE_CHECKING

from ..util.expiry import is_standard_monthly_expiry, is_quarterly_expiry

if TYPE_CHECKING:  # pragma: no cover
    from ib_insync import IB
    from ib_insync.contract import ContractDetails

DEFAULT_MONEYNESS_PCT = 0.30


@dataclass(frozen=True)
class OptionSpec:
    """Option contract prototype resolved from `reqSecDefOptParams`."""

    symbol: str
    expiry: str  # ISO date `YYYY-MM-DD`
    strike: float
    right: str  # "C" or "P"
    exchange: str = "SMART"
    currency: str = "USD"
    trading_class: str | None = None
    multiplier: float | None = None


@dataclass(frozen=True)
class ResolvedOption:
    """Concrete option contract with a stable IB conId."""

    conid: int
    spec: OptionSpec
    contract: Any  # `ib_insync.contract.Option`


def connect_ib(
    host: str = "127.0.0.1",
    port: int = 7497,
    client_id: int = 101,
    market_data_type: int = 2,
) -> "IB":
    """Return a connected `IB` instance for quick experiments."""

    from ib_insync import IB  # type: ignore

    ib = IB()
    ib.connect(host, port, clientId=client_id)
    ib.reqMarketDataType(market_data_type)
    return ib


def sec_def_params(
    ib: "IB",
    symbol: str,
    *,
    underlying_conid: int | None = None,
) -> list[Any]:
    """Fetch option security definition parameters for *symbol*."""

    underlying_id = underlying_conid or 0
    params = ib.reqSecDefOptParams(symbol, "", "STK", underlying_id)
    return list(params)


def enumerate_options(
    params: Iterable[Any],
    *,
    symbol: str,
    underlying_price: float,
    moneyness_pct: float = DEFAULT_MONEYNESS_PCT,
    only_standard_monthly: bool = True,
    include_quarterly: bool = True,
) -> list[OptionSpec]:
    """Enumerate option prototypes filtered by expiry type and moneyness band."""

    strikes_low, strikes_high = _moneyness_band(underlying_price, moneyness_pct)
    specs: list[OptionSpec] = []

    for param in params:
        strikes = sorted(_to_float(s) for s in getattr(param, "strikes", []) if s is not None)
        if not strikes:
            continue

        raw_expirations = getattr(param, "expirations", [])
        expiries = [_parse_expiration(exp) for exp in raw_expirations]
        filtered_expiries = [
            exp
            for exp in expiries
            if exp
            and _allow_expiry(
                exp,
                only_standard_monthly=only_standard_monthly,
                include_quarterly=include_quarterly,
            )
        ]
        if not filtered_expiries:
            continue

        exchange = getattr(param, "exchange", None) or "SMART"
        trading_class = getattr(param, "tradingClass", None) or symbol
        multiplier = _to_float(getattr(param, "multiplier", None)) or 100.0
        currency = getattr(param, "currency", None) or "USD"

        for expiry_date in filtered_expiries:
            expiry_iso = expiry_date.isoformat()
            for strike in strikes:
                if strikes_low is not None and strike < strikes_low:
                    continue
                if strikes_high is not None and strike > strikes_high:
                    continue
                for right in ("C", "P"):
                    specs.append(
                        OptionSpec(
                            symbol=symbol,
                            expiry=expiry_iso,
                            strike=strike,
                            right=right,
                            exchange=exchange,
                            currency=currency,
                            trading_class=trading_class,
                            multiplier=multiplier,
                        )
                    )

    return sorted(specs, key=lambda s: (s.expiry, s.strike, s.right, s.exchange))


def resolve_conids(
    ib: "IB",
    options: Sequence[OptionSpec],
    *,
    include_expired: bool = True,
) -> list[ResolvedOption]:
    """Resolve *options* into concrete contracts with stable conIds."""

    from ib_insync import Option  # type: ignore

    resolved: dict[int, ResolvedOption] = {}
    for spec in options:
        contract = Option(
            spec.symbol,
            _expiry_to_yyyymmdd(spec.expiry),
            spec.strike,
            spec.right,
            exchange=spec.exchange,
        )
        if spec.currency:
            contract.currency = spec.currency
        if spec.trading_class:
            contract.tradingClass = spec.trading_class
        if spec.multiplier:
            multiplier_value = float(spec.multiplier)
            contract.multiplier = (
                str(int(multiplier_value))
                if multiplier_value.is_integer()
                else str(multiplier_value)
            )
        contract.includeExpired = include_expired

        try:
            details: list[ContractDetails] = ib.reqContractDetails(contract)
        except Exception:  # pragma: no cover - network failure
            continue

        for detail in details:
            ib_contract = detail.contract
            conid = int(getattr(ib_contract, "conId"))
            updated_spec = replace(
                spec,
                symbol=getattr(ib_contract, "symbol", spec.symbol) or spec.symbol,
                expiry=_normalize_expiry(
                    getattr(ib_contract, "lastTradeDateOrContractMonth", spec.expiry)
                ),
                strike=_to_float(getattr(ib_contract, "strike", spec.strike)) or spec.strike,
                right=getattr(ib_contract, "right", spec.right) or spec.right,
                exchange=getattr(ib_contract, "exchange", spec.exchange) or spec.exchange,
                currency=getattr(ib_contract, "currency", spec.currency) or spec.currency,
                trading_class=getattr(
                    ib_contract, "tradingClass", spec.trading_class or spec.symbol
                )
                or spec.trading_class
                or spec.symbol,
                multiplier=_to_float(getattr(ib_contract, "multiplier", spec.multiplier))
                or spec.multiplier,
            )
            resolved[conid] = ResolvedOption(conid=conid, spec=updated_spec, contract=ib_contract)

    return sorted(
        resolved.values(), key=lambda r: (r.spec.expiry, r.spec.strike, r.spec.right, r.conid)
    )


def _allow_expiry(expiry: date, *, only_standard_monthly: bool, include_quarterly: bool) -> bool:
    if only_standard_monthly and not is_standard_monthly_expiry(expiry):
        if include_quarterly and is_quarterly_expiry(expiry):
            return True
        return False
    if not include_quarterly and is_quarterly_expiry(expiry):
        return False
    return True


def _parse_expiration(value: Any) -> date | None:
    text = str(value)
    if not text:
        return None
    if len(text) == 8 and text.isdigit():
        return date(int(text[0:4]), int(text[4:6]), int(text[6:8]))
    if len(text) == 6 and text.isdigit():
        return date(int(text[0:4]), int(text[4:6]), 1)
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _normalize_expiry(value: str) -> str:
    if len(value) == 8 and value.isdigit():
        return f"{value[0:4]}-{value[4:6]}-{value[6:8]}"
    if len(value) == 6 and value.isdigit():
        year = value[0:4]
        month = value[4:6]
        return f"{year}-{month}-01"
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        return value


def _expiry_to_yyyymmdd(expiry: str) -> str:
    clean = expiry.replace("-", "")
    if len(clean) == 8:
        return clean
    if len(clean) == 6:
        return f"{clean}01"
    if len(clean) == 4:
        return f"{clean}0101"
    raise ValueError(f"Unsupported expiry value: {expiry}")


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _moneyness_band(price: float, pct: float) -> tuple[float | None, float | None]:
    if price <= 0 or pct <= 0:
        return (None, None)
    low = price * (1.0 - pct)
    high = price * (1.0 + pct)
    return (low, high)


__all__ = [
    "OptionSpec",
    "ResolvedOption",
    "connect_ib",
    "sec_def_params",
    "enumerate_options",
    "resolve_conids",
]
