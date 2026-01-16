from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:  # Python 3.11+
    import tomllib as toml
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as toml  # type: ignore

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional at runtime

    def load_dotenv(*_: Any, **__: Any) -> None:  # type: ignore
        return None


@dataclass
class IBClientIdPoolConfig:
    role: str
    range: tuple[int, int]
    randomize: bool
    state_dir: Path
    lock_ttl_seconds: int


@dataclass
class IBConfig:
    host: str
    port: int
    client_id: int | None
    market_data_type: int
    client_id_pool: IBClientIdPoolConfig | None = None


@dataclass
class TimezoneConfig:
    name: str
    update_time: str


@dataclass
class PathsConfig:
    raw: Path
    clean: Path
    state: Path


@dataclass
class UniverseConfig:
    file: Path
    refresh_days: int


@dataclass
class ReferenceConfig:
    corporate_actions: Path


@dataclass
class StorageConfig:
    hot_days: int
    cold_codec: str
    cold_codec_level: int
    hot_codec: str


@dataclass
class MCPConfig:
    limit: int
    days: int
    allow_raw: bool
    allow_clean: bool
    enabled_tools: list[str]
    audit_db: Path


@dataclass
class AppConfig:
    ib: IBConfig
    timezone: TimezoneConfig
    paths: PathsConfig
    reference: ReferenceConfig
    universe: UniverseConfig
    storage: StorageConfig
    mcp: MCPConfig


def _resolve_path(base: Path, value: str | Path) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return (base / path).resolve()


def _read_section(payload: dict[str, Any], key: str) -> dict[str, Any]:
    section = payload.get(key)
    if not isinstance(section, dict):
        raise ValueError(f"Missing config section [{key}]")
    return section


def _parse_client_id(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, str) and value.strip().lower() in {"auto", "-1"}:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid client_id: {value}") from exc
    return None if parsed < 0 else parsed


def _parse_pool_range(value: Any) -> tuple[int, int]:
    if value is None:
        return (0, 0)
    if isinstance(value, (list, tuple)) and len(value) == 0:
        return (0, 0)
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return (int(value[0]), int(value[1]))
    raise ValueError(f"Invalid client_id_pool.range: {value}")


def _load_repo_dotenv() -> None:
    base = Path(__file__).resolve()
    if base.is_file():
        base = base.parent

    repo_root = None
    for candidate in [base, *base.parents]:
        if (candidate / ".git").exists():
            repo_root = candidate
            break

    if repo_root:
        env_path = repo_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()
        return

    for candidate in [base, *base.parents]:
        env_path = candidate / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            return

    load_dotenv()


def load_config(path: Path) -> AppConfig:
    _load_repo_dotenv()
    cfg_path = Path(path)
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config not found: {cfg_path}")
    payload = toml.loads(cfg_path.read_text(encoding="utf-8"))
    base = cfg_path.parent
    if base.name == "config":
        base = base.parent

    ib_cfg = _read_section(payload, "ib")
    tz_cfg = _read_section(payload, "timezone")
    paths_cfg = _read_section(payload, "paths")
    reference_cfg = _read_section(payload, "reference")
    universe_cfg = _read_section(payload, "universe")
    storage_cfg = _read_section(payload, "storage")
    mcp_cfg = _read_section(payload, "mcp")

    pool_cfg = ib_cfg.get("client_id_pool")
    client_id_pool = None
    if isinstance(pool_cfg, dict):
        client_id_pool = IBClientIdPoolConfig(
            role=str(pool_cfg.get("role", "stock")),
            range=_parse_pool_range(pool_cfg.get("range", (0, 0))),
            randomize=bool(pool_cfg.get("randomize", True)),
            state_dir=_resolve_path(base, pool_cfg.get("state_dir", "state/client_ids")),
            lock_ttl_seconds=int(pool_cfg.get("lock_ttl_seconds", 7200)),
        )

    ib = IBConfig(
        host=str(ib_cfg.get("host", "127.0.0.1")),
        port=int(ib_cfg.get("port", 7496)),
        client_id=_parse_client_id(ib_cfg.get("client_id", -1)),
        market_data_type=int(ib_cfg.get("market_data_type", 1)),
        client_id_pool=client_id_pool,
    )
    timezone = TimezoneConfig(
        name=str(tz_cfg.get("name", "America/New_York")),
        update_time=str(tz_cfg.get("update_time", "17:30")),
    )
    paths = PathsConfig(
        raw=_resolve_path(base, paths_cfg.get("raw", "data/raw/ib/stk")),
        clean=_resolve_path(base, paths_cfg.get("clean", "data/clean/ib/stk")),
        state=_resolve_path(base, paths_cfg.get("state", "state")),
    )
    reference = ReferenceConfig(
        corporate_actions=_resolve_path(
            base,
            reference_cfg.get("corporate_actions", "config/corporate_actions.csv"),
        ),
    )
    universe = UniverseConfig(
        file=_resolve_path(base, universe_cfg.get("file", "config/stock-universe.csv")),
        refresh_days=int(universe_cfg.get("refresh_days", 30)),
    )
    storage = StorageConfig(
        hot_days=int(storage_cfg.get("hot_days", 14)),
        cold_codec=str(storage_cfg.get("cold_codec", "zstd")),
        cold_codec_level=int(storage_cfg.get("cold_codec_level", 7)),
        hot_codec=str(storage_cfg.get("hot_codec", "snappy")),
    )
    mcp = MCPConfig(
        limit=int(mcp_cfg.get("limit", 200)),
        days=int(mcp_cfg.get("days", 3)),
        allow_raw=bool(mcp_cfg.get("allow_raw", True)),
        allow_clean=bool(mcp_cfg.get("allow_clean", True)),
        enabled_tools=str(
            mcp_cfg.get(
                "enabled_tools",
                "health_overview,run_status_overview,list_recent_runs",
            )
        ).split(","),
        audit_db=_resolve_path(base, mcp_cfg.get("audit_db", "state/run_logs/mcp_audit.db")),
    )

    return AppConfig(
        ib=ib,
        timezone=timezone,
        paths=paths,
        reference=reference,
        universe=universe,
        storage=storage,
        mcp=mcp,
    )
