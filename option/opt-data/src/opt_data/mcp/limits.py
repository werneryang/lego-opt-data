from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class LimitConfig:
    default_limit: int = 200
    max_limit: int = 2000
    default_days: int = 3
    max_days: int = 14

    list_recent_runs_default: int = 20
    list_recent_runs_max: int = 200

    get_chain_sample_default: int = 200
    get_chain_sample_max: int = 1000

    get_partition_issues_default: int = 200
    get_partition_issues_max: int = 2000

    health_overview_days_default: int = 3
    health_overview_days_max: int = 14


def clamp_int(value: int | None, default: int, maximum: int) -> int:
    if value is None:
        return default
    if value < 0:
        return default
    return min(value, maximum)


def clamp_days(value: int | None, default: int, maximum: int) -> int:
    if value is None:
        return default
    if value < 1:
        return default
    return min(value, maximum)


def apply_caps(
    limits: LimitConfig,
    *,
    limit: int | None = None,
    days: int | None = None,
) -> LimitConfig:
    """Apply global caps to tool-specific limits without increasing defaults."""

    if limit is None and days is None:
        return limits

    updates: dict[str, int] = {}

    if limit is not None:
        capped_max = min(limits.max_limit, limit)
        updates["max_limit"] = capped_max
        updates["default_limit"] = min(limits.default_limit, capped_max)

        list_recent_runs_max = min(limits.list_recent_runs_max, limit)
        updates["list_recent_runs_max"] = list_recent_runs_max
        updates["list_recent_runs_default"] = min(
            limits.list_recent_runs_default, list_recent_runs_max
        )

        get_chain_sample_max = min(limits.get_chain_sample_max, limit)
        updates["get_chain_sample_max"] = get_chain_sample_max
        updates["get_chain_sample_default"] = min(
            limits.get_chain_sample_default, get_chain_sample_max
        )

        get_partition_issues_max = min(limits.get_partition_issues_max, limit)
        updates["get_partition_issues_max"] = get_partition_issues_max
        updates["get_partition_issues_default"] = min(
            limits.get_partition_issues_default, get_partition_issues_max
        )

    if days is not None:
        capped_days_max = min(limits.max_days, days)
        updates["max_days"] = capped_days_max
        updates["default_days"] = min(limits.default_days, capped_days_max)

        health_overview_days_max = min(limits.health_overview_days_max, days)
        updates["health_overview_days_max"] = health_overview_days_max
        updates["health_overview_days_default"] = min(
            limits.health_overview_days_default, health_overview_days_max
        )

    return replace(limits, **updates)
