from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any, Dict, List
import os

try:  # Python 3.11+
    import tomllib as toml
except ModuleNotFoundError:  # Python 3.10
    import tomli as toml  # type: ignore

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional at runtime

    def load_dotenv(*_: Any, **__: Any) -> None:  # type: ignore
        return None


@dataclass
class IBConfig:
    host: str
    port: int
    client_id: int
    market_data_type: int


@dataclass
class TimezoneConfig:
    name: str
    update_time: str


@dataclass
class PathsConfig:
    raw: Path
    clean: Path
    state: Path
    contracts_cache: Path
    run_logs: Path


@dataclass
class UniverseConfig:
    file: Path
    refresh_days: int


@dataclass
class ReferenceConfig:
    corporate_actions: Path


@dataclass
class FiltersConfig:
    moneyness_pct: float
    expiry_types: list[str]


@dataclass
class RateLimitClassConfig:
    per_minute: int
    burst: int
    max_concurrent: int | None = None


@dataclass
class RateLimitsConfig:
    discovery: RateLimitClassConfig
    snapshot: RateLimitClassConfig
    historical: RateLimitClassConfig


@dataclass
class StorageConfig:
    hot_days: int
    cold_codec: str
    cold_codec_level: int
    hot_codec: str


@dataclass
class CompactionConfig:
    enabled: bool
    schedule: str
    weekday: str
    start_time: str
    min_file_size_mb: int
    max_file_size_mb: int


@dataclass
class LoggingConfig:
    level: str
    format: str


@dataclass
class CLIConfig:
    default_generic_ticks: str
    snapshot_grace_seconds: int
    rollup_close_slot: int
    rollup_fallback_slot: int


@dataclass
class SnapshotConfig:
    exchange: str
    fallback_exchanges: List[str]
    generic_ticks: str
    strikes_per_side: int
    subscription_timeout: float
    subscription_poll_interval: float
    require_greeks: bool


@dataclass
class AcquisitionConfig:
    mode: str
    duration: str
    bar_size: str
    what_to_show: str
    use_rth: bool
    max_strikes_per_expiry: int
    fill_missing_greeks_with_zero: bool
    historical_timeout: float


@dataclass
class EnrichmentConfig:
    fields: list[str]
    oi_duration: str
    oi_use_rth: bool


@dataclass
class QAConfig:
    slot_coverage_threshold: float
    delayed_ratio_threshold: float
    rollup_fallback_threshold: float
    oi_enrichment_threshold: float


@dataclass
class AppConfig:
    ib: IBConfig
    timezone: TimezoneConfig
    paths: PathsConfig
    universe: UniverseConfig
    reference: ReferenceConfig
    filters: FiltersConfig
    rate_limits: RateLimitsConfig
    storage: StorageConfig
    compaction: CompactionConfig
    logging: LoggingConfig
    cli: CLIConfig
    snapshot: SnapshotConfig
    enrichment: EnrichmentConfig
    qa: QAConfig
    acquisition: AcquisitionConfig


def _as_path(p: str | Path) -> Path:
    return Path(p).expanduser().resolve()


def load_config(file: Optional[Path] = None) -> AppConfig:
    """Load configuration from a TOML file with environment overrides.

    Order of precedence:
    1. File values (TOML)
    2. Environment variables (e.g., IB_HOST, IB_PORT, ...)
    3. Built-in defaults (from template if missing keys)
    """

    load_dotenv()  # load .env if present

    cfg_path = (
        _as_path(file) if file else _as_path(os.getenv("OPT_DATA_CONFIG", "config/opt-data.toml"))
    )
    with open(cfg_path, "rb") as fh:
        raw: Dict[str, Any] = toml.load(fh)

    def g(section: str, key: str, default: Any) -> Any:
        # construct env var like SECTION_KEY (dots -> underscores)
        env_key = f"{section}_{key}".upper().replace(".", "_")
        val = os.getenv(env_key)
        if val is not None:
            # best-effort casting
            if isinstance(default, int):
                try:
                    return int(val)
                except ValueError:
                    return default
            if isinstance(default, float):
                try:
                    return float(val)
                except ValueError:
                    return default
            if isinstance(default, bool):
                lowered = val.strip().lower()
                if lowered in {"1", "true", "yes", "on"}:
                    return True
                if lowered in {"0", "false", "no", "off"}:
                    return False
                return default
            return val
        # fallback to file or default with dotted lookups
        sec: Any = raw
        for part in section.split("."):
            if isinstance(sec, dict):
                sec = sec.get(part, {})
            else:
                sec = {}
                break
        return sec.get(key, default) if isinstance(sec, dict) else default

    ib = IBConfig(
        host=g("ib", "host", "127.0.0.1"),
        port=g("ib", "port", 7497),
        client_id=g("ib", "client_id", 101),
        market_data_type=g("ib", "market_data_type", 2),
    )

    tz = TimezoneConfig(
        name=g("timezone", "name", "America/New_York"),
        update_time=g("timezone", "update_time", "17:00"),
    )

    paths = PathsConfig(
        raw=_as_path(g("paths", "raw", "data/raw/ib/chain")),
        clean=_as_path(g("paths", "clean", "data/clean/ib/chain")),
        state=_as_path(g("paths", "state", "state")),
        contracts_cache=_as_path(g("paths", "contracts_cache", "state/contracts_cache")),
        run_logs=_as_path(g("paths", "run_logs", "state/run_logs")),
    )

    universe = UniverseConfig(
        file=_as_path(g("universe", "file", "config/universe.csv")),
        refresh_days=g("universe", "refresh_days", 30),
    )

    reference = ReferenceConfig(
        corporate_actions=_as_path(
            g("reference", "corporate_actions", "config/corporate_actions.csv")
        ),
    )

    expiry_raw = g("filters", "expiry_types", ["monthly", "quarterly"])
    if isinstance(expiry_raw, str):
        expiry_types = [token.strip() for token in expiry_raw.split(",") if token.strip()]
    else:
        expiry_types = list(expiry_raw)

    filters = FiltersConfig(
        moneyness_pct=float(g("filters", "moneyness_pct", 0.30)),
        expiry_types=expiry_types,
    )

    rl = RateLimitsConfig(
        discovery=RateLimitClassConfig(
            per_minute=g("rate_limits.discovery", "per_minute", 5),
            burst=g("rate_limits.discovery", "burst", 5),
        ),
        snapshot=RateLimitClassConfig(
            per_minute=g("rate_limits.snapshot", "per_minute", 20),
            burst=g("rate_limits.snapshot", "burst", 10),
            max_concurrent=g("rate_limits.snapshot", "max_concurrent", 4),
        ),
        historical=RateLimitClassConfig(
            per_minute=g("rate_limits.historical", "per_minute", 20),
            burst=g("rate_limits.historical", "burst", 10),
        ),
    )

    storage = StorageConfig(
        hot_days=g("storage", "hot_days", 14),
        cold_codec=g("storage", "cold_codec", "zstd"),
        cold_codec_level=g("storage", "cold_codec_level", 7),
        hot_codec=g("storage", "hot_codec", "snappy"),
    )

    compaction = CompactionConfig(
        enabled=bool(g("compaction", "enabled", True)),
        schedule=g("compaction", "schedule", "weekly"),
        weekday=g("compaction", "weekday", "sunday"),
        start_time=g("compaction", "start_time", "03:00"),
        min_file_size_mb=g("compaction", "min_file_size_mb", 32),
        max_file_size_mb=g("compaction", "max_file_size_mb", 256),
    )

    logging = LoggingConfig(
        level=g("logging", "level", "INFO"),
        format=g("logging", "format", "json"),
    )

    cli = CLIConfig(
        default_generic_ticks=g(
            "cli", "default_generic_ticks", "100,101,104,105,106,165,221,225,233,293,294,295"
        ),
        snapshot_grace_seconds=int(g("cli", "snapshot_grace_seconds", 120)),
        rollup_close_slot=int(g("cli", "rollup_close_slot", 13)),
        rollup_fallback_slot=int(g("cli", "rollup_fallback_slot", 12)),
    )

    fallback_raw = g("snapshot", "fallback_exchanges", ["CBOE", "CBOEOPT"])
    if isinstance(fallback_raw, str):
        fallback_exchanges = [
            token.strip().upper() for token in fallback_raw.split(",") if token.strip()
        ]
    else:
        fallback_exchanges = [str(token).strip().upper() for token in fallback_raw if str(token).strip()]

    snapshot_generic_ticks = g(
        "snapshot",
        "generic_ticks",
        cli.default_generic_ticks or "100,101,104,105,106,165,221,225,233,293,294,295",
    )

    snapshot_cfg = SnapshotConfig(
        exchange=g("snapshot", "exchange", "SMART"),
        fallback_exchanges=fallback_exchanges,
        generic_ticks=snapshot_generic_ticks,
        strikes_per_side=int(g("snapshot", "strikes_per_side", 3)),
        subscription_timeout=float(g("snapshot", "subscription_timeout_sec", 12.0)),
        subscription_poll_interval=float(g("snapshot", "subscription_poll_interval", 0.25)),
        require_greeks=bool(g("snapshot", "require_greeks", True)),
    )

    enrichment_fields_raw = g("enrichment", "fields", ["open_interest"])
    if isinstance(enrichment_fields_raw, str):
        enrichment_fields = [
            token.strip().lower() for token in enrichment_fields_raw.split(",") if token.strip()
        ]
    else:
        enrichment_fields = [str(token).lower() for token in enrichment_fields_raw]

    enrichment = EnrichmentConfig(
        fields=enrichment_fields,
        oi_duration=g("enrichment", "oi_duration", "7 D"),
        oi_use_rth=bool(g("enrichment", "oi_use_rth", False)),
    )

    qa = QAConfig(
        slot_coverage_threshold=float(g("qa", "slot_coverage_threshold", 0.90)),
        delayed_ratio_threshold=float(g("qa", "delayed_ratio_threshold", 0.10)),
        rollup_fallback_threshold=float(g("qa", "rollup_fallback_threshold", 0.05)),
        oi_enrichment_threshold=float(g("qa", "oi_enrichment_threshold", 0.95)),
    )

    acquisition = AcquisitionConfig(
        mode=g("acquisition", "mode", "snapshot").lower(),
        duration=g("acquisition", "duration", "1 D"),
        bar_size=g("acquisition", "bar_size", "1 day"),
        what_to_show=g("acquisition", "what_to_show", "TRADES"),
        use_rth=bool(g("acquisition", "use_rth", True)),
        max_strikes_per_expiry=int(g("acquisition", "max_strikes_per_expiry", 21)),
        fill_missing_greeks_with_zero=bool(
            g("acquisition", "fill_missing_greeks_with_zero", False)
        ),
        historical_timeout=float(g("acquisition", "historical_timeout", 30.0)),
    )

    return AppConfig(
        ib=ib,
        timezone=tz,
        paths=paths,
        universe=universe,
        reference=reference,
        filters=filters,
        rate_limits=rl,
        storage=storage,
        compaction=compaction,
        logging=logging,
        cli=cli,
        snapshot=snapshot_cfg,
        enrichment=enrichment,
        qa=qa,
        acquisition=acquisition,
    )
