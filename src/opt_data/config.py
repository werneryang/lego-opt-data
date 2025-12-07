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
    file: Path                      # Default full universe (backward compatible)
    refresh_days: int
    intraday_file: Path | None = None  # Optional: smaller set for intraday snapshots
    close_file: Path | None = None     # Optional: close-specific (defaults to file)


@dataclass
class ReferenceConfig:
    corporate_actions: Path


@dataclass
class FiltersConfig:
    moneyness_pct: float
    expiry_types: list[str]
    expiry_months_ahead: int | None


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
class ObservabilityConfig:
    metrics_db_path: Path
    webhook_url: str | None = None



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
    force_frozen_data: bool = False
    fetch_mode: str = "streaming"
    batch_size: int = 50


@dataclass
class AcquisitionConfig:
    mode: str
    duration: str
    bar_size: str
    what_to_show: str
    use_rth: bool
    max_strikes_per_expiry: int
    fill_missing_greeks_with_zero: bool
    fill_missing_greeks_with_zero: bool
    historical_timeout: float
    throttle_sec: float


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
class RollupConfig:
    close_slot: int = 13                    # 16:00 slot (default close)
    fallback_slot: int = 12                 # 15:30 slot (backup)
    allow_intraday_fallback: bool = False   # If True, fallback to intraday when close view empty


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
    observability: ObservabilityConfig
    cli: CLIConfig
    snapshot: SnapshotConfig
    enrichment: EnrichmentConfig
    qa: QAConfig
    acquisition: AcquisitionConfig
    rollup: RollupConfig = None  # Optional, with defaults

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors.
        
        Returns:
            List of validation error messages. Empty list means valid config.
        """
        errors = []

        # Validate IB configuration
        if not (1024 <= self.ib.port <= 65535):
            errors.append(f"Invalid IB port: {self.ib.port} (must be 1024-65535)")
        
        if self.ib.client_id < 0:
            errors.append(f"Invalid IB client_id: {self.ib.client_id} (must be >= 0)")
        
        if self.ib.market_data_type not in {1, 2, 3, 4}:
            errors.append(
                f"Invalid IB market_data_type: {self.ib.market_data_type} "
                "(must be 1=Live, 2=Frozen, 3=Delayed, 4=Delayed-Frozen)"
            )

        # Validate paths - paths will be created at runtime if needed
        # We only check that paths are properly resolved (no validation of existence)

        # Note: Universe file will be checked at runtime when actually needed
        # (tests may not have it, and it can be created/updated dynamically)
        
        if self.universe.refresh_days < 0:
            errors.append(
                f"Invalid universe.refresh_days: {self.universe.refresh_days} (must be >= 0)"
            )

        # Validate filters
        if not (0 < self.filters.moneyness_pct <= 1.0):
            errors.append(
                f"Invalid filters.moneyness_pct: {self.filters.moneyness_pct} "
                "(must be > 0 and <= 1.0)"
            )
        
        valid_expiry_types = {"monthly", "quarterly", "weekly"}
        invalid_types = set(self.filters.expiry_types) - valid_expiry_types
        if invalid_types:
            errors.append(
                f"Invalid expiry types: {invalid_types}. "
                f"Valid types are: {valid_expiry_types}"
            )

        # Validate rate limits
        for rl_name, rl_config in [
            ("discovery", self.rate_limits.discovery),
            ("snapshot", self.rate_limits.snapshot),
            ("historical", self.rate_limits.historical),
        ]:
            if rl_config.per_minute <= 0:
                errors.append(
                    f"Invalid rate_limits.{rl_name}.per_minute: {rl_config.per_minute} "
                    "(must be > 0)"
                )
            
            if rl_config.burst <= 0:
                errors.append(
                    f"Invalid rate_limits.{rl_name}.burst: {rl_config.burst} "
                    "(must be > 0)"
                )
            
            if rl_config.max_concurrent is not None and rl_config.max_concurrent <= 0:
                errors.append(
                    f"Invalid rate_limits.{rl_name}.max_concurrent: {rl_config.max_concurrent} "
                    "(must be > 0 or None)"
                )

        # Validate storage configuration
        if self.storage.hot_days < 0:
            errors.append(f"Invalid storage.hot_days: {self.storage.hot_days} (must be >= 0)")
        
        valid_codecs = {"snappy", "gzip", "zstd", "lz4", "brotli", "none"}
        if self.storage.hot_codec not in valid_codecs:
            errors.append(
                f"Invalid storage.hot_codec: {self.storage.hot_codec}. "
                f"Valid codecs: {valid_codecs}"
            )
        
        if self.storage.cold_codec not in valid_codecs:
            errors.append(
                f"Invalid storage.cold_codec: {self.storage.cold_codec}. "
                f"Valid codecs: {valid_codecs}"
            )

        # Validate compaction configuration
        if self.compaction.min_file_size_mb <= 0:
            errors.append(
                f"Invalid compaction.min_file_size_mb: {self.compaction.min_file_size_mb} "
                "(must be > 0)"
            )
        
        if self.compaction.max_file_size_mb <= 0:
            errors.append(
                f"Invalid compaction.max_file_size_mb: {self.compaction.max_file_size_mb} "
                "(must be > 0)"
            )
        
        if self.compaction.max_file_size_mb < self.compaction.min_file_size_mb:
            errors.append(
                f"compaction.max_file_size_mb ({self.compaction.max_file_size_mb}) must be "
                f">= min_file_size_mb ({self.compaction.min_file_size_mb})"
            )

        # Validate QA thresholds (all should be between 0 and 1)
        for qa_name, qa_value in [
            ("slot_coverage_threshold", self.qa.slot_coverage_threshold),
            ("delayed_ratio_threshold", self.qa.delayed_ratio_threshold),
            ("rollup_fallback_threshold", self.qa.rollup_fallback_threshold),
            ("oi_enrichment_threshold", self.qa.oi_enrichment_threshold),
        ]:
            if not (0 <= qa_value <= 1):
                errors.append(
                    f"Invalid qa.{qa_name}: {qa_value} (must be between 0.0 and 1.0)"
                )

        # Validate snapshot configuration
        if self.snapshot.strikes_per_side < 0:
            errors.append(
                f"Invalid snapshot.strikes_per_side: {self.snapshot.strikes_per_side} "
                "(must be >= 0)"
            )
        
        if self.snapshot.subscription_timeout <= 0:
            errors.append(
                f"Invalid snapshot.subscription_timeout: {self.snapshot.subscription_timeout} "
                "(must be > 0)"
            )
        
        if self.snapshot.subscription_poll_interval <= 0:
            errors.append(
                f"Invalid snapshot.subscription_poll_interval: "
                f"{self.snapshot.subscription_poll_interval} (must be > 0)"
            )
        
        valid_fetch_modes = {"streaming", "snapshot", "reqtickers"}
        if self.snapshot.fetch_mode not in valid_fetch_modes:
            errors.append(
                f"Invalid snapshot.fetch_mode: {self.snapshot.fetch_mode}. "
                f"Valid modes: {valid_fetch_modes}"
            )
        
        if self.snapshot.batch_size <= 0:
            errors.append(
                f"Invalid snapshot.batch_size: {self.snapshot.batch_size} (must be > 0)"
            )

        # Validate CLI configuration
        if self.cli.snapshot_grace_seconds < 0:
            errors.append(
                f"Invalid cli.snapshot_grace_seconds: {self.cli.snapshot_grace_seconds} "
                "(must be >= 0)"
            )
        
        if not (0 <= self.cli.rollup_close_slot <= 13):
            errors.append(
                f"Invalid cli.rollup_close_slot: {self.cli.rollup_close_slot} "
                "(must be 0-13)"
            )
        
        if not (0 <= self.cli.rollup_fallback_slot <= 13):
            errors.append(
                f"Invalid cli.rollup_fallback_slot: {self.cli.rollup_fallback_slot} "
                "(must be 0-13)"
            )

        # Validate acquisition configuration
        valid_modes = {"snapshot", "historical"}
        if self.acquisition.mode not in valid_modes:
            errors.append(
                f"Invalid acquisition.mode: {self.acquisition.mode}. "
                f"Valid modes: {valid_modes}"
            )
        
        if self.acquisition.max_strikes_per_expiry < 0:
            errors.append(
                f"Invalid acquisition.max_strikes_per_expiry: "
                f"{self.acquisition.max_strikes_per_expiry} (must be >= 0)"
            )
        
        if self.acquisition.historical_timeout <= 0:
            errors.append(
                f"Invalid acquisition.historical_timeout: {self.acquisition.historical_timeout} "
                "(must be > 0)"
            )

        # Validate logging level
        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.logging.level.upper() not in valid_log_levels:
            errors.append(
                f"Invalid logging.level: {self.logging.level}. "
                f"Valid levels: {valid_log_levels}"
            )

        return errors


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
        port=g("ib", "port", 7496),
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

    # Universe config with optional intraday/close files
    intraday_file_raw = g("universe", "intraday_file", "")
    close_file_raw = g("universe", "close_file", "")

    universe = UniverseConfig(
        file=_as_path(g("universe", "file", "config/universe.csv")),
        refresh_days=g("universe", "refresh_days", 30),
        intraday_file=_as_path(intraday_file_raw) if intraday_file_raw else None,
        close_file=_as_path(close_file_raw) if close_file_raw else None,
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

    expiry_months_ahead_raw = g("filters", "expiry_months_ahead", 12)
    expiry_months_ahead: int | None
    try:
        expiry_months_ahead = int(expiry_months_ahead_raw)
        if expiry_months_ahead <= 0:
            expiry_months_ahead = None
    except Exception:
        expiry_months_ahead = None

    filters = FiltersConfig(
        moneyness_pct=float(g("filters", "moneyness_pct", 0.30)),
        expiry_types=expiry_types,
        expiry_months_ahead=expiry_months_ahead,
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
        format=g("logging", "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
    )

    observability = ObservabilityConfig(
        metrics_db_path=_as_path(g("observability", "metrics_db_path", "data/metrics.db")),
        webhook_url=g("observability", "webhook_url", None),
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
        fallback_exchanges = [
            str(token).strip().upper() for token in fallback_raw if str(token).strip()
        ]

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
        force_frozen_data=bool(g("snapshot", "force_frozen_data", False)),
        fetch_mode=g("snapshot", "fetch_mode", "streaming"),
        batch_size=int(g("snapshot", "batch_size", 50)),
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
        throttle_sec=float(g("acquisition", "throttle_sec", 0.35)),
    )

    rollup = RollupConfig(
        close_slot=int(g("rollup", "close_slot", 13)),
        fallback_slot=int(g("rollup", "fallback_slot", 12)),
        allow_intraday_fallback=bool(g("rollup", "allow_intraday_fallback", False)),
    )

    cfg = AppConfig(
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
        observability=observability,
        cli=cli,
        snapshot=snapshot_cfg,
        enrichment=enrichment,
        qa=qa,
        acquisition=acquisition,
        rollup=rollup,
    )

    # Validate configuration before returning
    validation_errors = cfg.validate()
    if validation_errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(
            f"  - {error}" for error in validation_errors
        )
        raise ValueError(error_msg)

    return cfg
