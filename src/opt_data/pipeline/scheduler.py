from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, Iterable, List, Sequence
from zoneinfo import ZoneInfo

try:
    from apscheduler.schedulers.background import BackgroundScheduler
except Exception:  # pragma: no cover - optional dependency guard
    BackgroundScheduler = None  # type: ignore[assignment]

from ..config import AppConfig
from ..util.calendar import is_trading_day
from .snapshot import SnapshotRunner
from .rollup import RollupRunner
from .enrichment import EnrichmentRunner


JobKind = str


@dataclass(frozen=True)
class ScheduledJob:
    kind: JobKind
    run_time: datetime
    payload: Dict[str, Any]


@dataclass
class ScheduleSummary:
    snapshots: int = 0
    rollups: int = 0
    enrichments: int = 0
    errors: List[dict[str, Any]] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "snapshots": self.snapshots,
            "rollups": self.rollups,
            "enrichments": self.enrichments,
            "errors": self.errors or [],
        }


class ScheduleRunner:
    def __init__(
        self,
        cfg: AppConfig,
        *,
        snapshot_runner: SnapshotRunner | None = None,
        rollup_runner: RollupRunner | None = None,
        enrichment_runner: EnrichmentRunner | None = None,
    ) -> None:
        self.cfg = cfg
        self._tz = ZoneInfo(cfg.timezone.name)
        self._snapshot_runner = snapshot_runner or SnapshotRunner(cfg)
        self._rollup_runner = rollup_runner or RollupRunner(cfg)
        self._enrichment_runner = enrichment_runner or EnrichmentRunner(cfg)

    def plan_day(
        self,
        trade_date: date,
        *,
        symbols: Sequence[str] | None = None,
        enrichment_fields: Iterable[str] | None = None,
        include_snapshots: bool = True,
        include_rollup: bool = True,
        include_enrichment: bool = True,
    ) -> list[ScheduledJob]:
        if not is_trading_day(trade_date):
            return []

        jobs: list[ScheduledJob] = []
        if include_snapshots:
            slots = self._snapshot_runner.available_slots(trade_date)
            for slot in slots:
                jobs.append(
                    ScheduledJob(
                        kind="snapshot",
                        run_time=slot.et,
                        payload={
                            "slot_label": slot.label,
                            "symbols": list(symbols) if symbols else None,
                        },
                    )
                )

        if include_rollup:
            rollup_time = datetime.combine(trade_date, time(17, 0), tzinfo=self._tz)
            jobs.append(
                ScheduledJob(
                    kind="rollup",
                    run_time=rollup_time,
                    payload={
                        "symbols": list(symbols) if symbols else None,
                    },
                )
            )

        if include_enrichment:
            target_fields = [f.lower() for f in (enrichment_fields or self.cfg.enrichment.fields)]
            enrichment_time = datetime.combine(
                trade_date + timedelta(days=1), time(7, 30), tzinfo=self._tz
            )
            jobs.append(
                ScheduledJob(
                    kind="enrichment",
                    run_time=enrichment_time,
                    payload={
                        "symbols": list(symbols) if symbols else None,
                        "fields": target_fields,
                    },
                )
            )

        jobs.sort(key=lambda job: job.run_time)
        return jobs

    def run_simulation(
        self,
        trade_date: date,
        *,
        symbols: Sequence[str] | None = None,
        enrichment_fields: Iterable[str] | None = None,
        include_snapshots: bool = True,
        include_rollup: bool = True,
        include_enrichment: bool = True,
        snapshot_progress: callable[[str, str, Dict[str, Any]], None] | None = None,
        rollup_progress: callable[[str, str, Dict[str, Any]], None] | None = None,
        enrichment_progress: callable[[str, str, Dict[str, Any]], None] | None = None,
    ) -> ScheduleSummary:
        jobs = self.plan_day(
            trade_date,
            symbols=symbols,
            enrichment_fields=enrichment_fields,
            include_snapshots=include_snapshots,
            include_rollup=include_rollup,
            include_enrichment=include_enrichment,
        )
        summary = ScheduleSummary(errors=[])

        for job in jobs:
            try:
                if job.kind == "snapshot":
                    self._run_snapshot_job(
                        trade_date, job.payload, progress=snapshot_progress
                    )
                    summary.snapshots += 1
                elif job.kind == "rollup":
                    self._run_rollup_job(trade_date, job.payload, progress=rollup_progress)
                    summary.rollups += 1
                elif job.kind == "enrichment":
                    self._run_enrichment_job(
                        trade_date, job.payload, progress=enrichment_progress
                    )
                    summary.enrichments += 1
            except Exception as exc:  # pragma: no cover - surfaced in summary
                error = {
                    "kind": job.kind,
                    "run_time": job.run_time.isoformat(),
                    "error": str(exc),
                }
                summary.errors.append(error)
        if not summary.errors:
            summary.errors = []
        return summary

    def schedule(
        self,
        scheduler: Any,
        trade_date: date,
        *,
        symbols: Sequence[str] | None = None,
        enrichment_fields: Iterable[str] | None = None,
        include_snapshots: bool = True,
        include_rollup: bool = True,
        include_enrichment: bool = True,
        misfire_grace_seconds: int = 120,
        snapshot_progress: callable[[str, str, Dict[str, Any]], None] | None = None,
        rollup_progress: callable[[str, str, Dict[str, Any]], None] | None = None,
        enrichment_progress: callable[[str, str, Dict[str, Any]], None] | None = None,
    ) -> list[str]:
        if BackgroundScheduler is None:
            raise RuntimeError(
                "APScheduler is required to schedule jobs; install apscheduler >=3.10"
            )

        jobs = self.plan_day(
            trade_date,
            symbols=symbols,
            enrichment_fields=enrichment_fields,
            include_snapshots=include_snapshots,
            include_rollup=include_rollup,
            include_enrichment=include_enrichment,
        )
        job_ids: list[str] = []
        for idx, job in enumerate(jobs):
            job_id = f"{job.kind}-{trade_date.isoformat()}-{idx}"
            if job.kind == "snapshot":
                scheduler.add_job(
                    self._run_snapshot_job,
                    trigger="date",
                    run_date=job.run_time,
                    kwargs={
                        "trade_date": trade_date,
                        "payload": job.payload,
                        "progress": snapshot_progress,
                    },
                    id=job_id,
                    replace_existing=True,
                    misfire_grace_time=misfire_grace_seconds,
                )
            elif job.kind == "rollup":
                scheduler.add_job(
                    self._run_rollup_job,
                    trigger="date",
                    run_date=job.run_time,
                    kwargs={
                        "trade_date": trade_date,
                        "payload": job.payload,
                        "progress": rollup_progress,
                    },
                    id=job_id,
                    replace_existing=True,
                    misfire_grace_time=misfire_grace_seconds,
                )
            elif job.kind == "enrichment":
                scheduler.add_job(
                    self._run_enrichment_job,
                    trigger="date",
                    run_date=job.run_time,
                    kwargs={
                        "trade_date": trade_date,
                        "payload": job.payload,
                        "progress": enrichment_progress,
                    },
                    id=job_id,
                    replace_existing=True,
                    misfire_grace_time=misfire_grace_seconds,
                )
            job_ids.append(job_id)
        return job_ids

    def _run_snapshot_job(
        self,
        trade_date: date,
        payload: Dict[str, Any],
        *,
        progress: callable[[str, str, Dict[str, Any]], None] | None = None,
    ) -> None:
        slot_label = str(payload["slot_label"])
        symbols = payload.get("symbols")
        slot_obj = self._snapshot_runner.resolve_slot(trade_date, slot_label)
        self._snapshot_runner.run(
            trade_date,
            slot_obj,
            symbols,
            progress=progress,
        )

    def _run_rollup_job(
        self,
        trade_date: date,
        payload: Dict[str, Any],
        *,
        progress: callable[[str, str, Dict[str, Any]], None] | None = None,
    ) -> None:
        symbols = payload.get("symbols")
        self._rollup_runner.run(
            trade_date,
            symbols,
            progress=progress,
        )

    def _run_enrichment_job(
        self,
        trade_date: date,
        payload: Dict[str, Any],
        *,
        progress: callable[[str, str, Dict[str, Any]], None] | None = None,
    ) -> None:
        symbols = payload.get("symbols")
        fields = payload.get("fields")
        self._enrichment_runner.run(
            trade_date,
            symbols,
            fields=fields,
            progress=progress,
        )


__all__ = ["ScheduleRunner", "ScheduledJob", "ScheduleSummary"]
