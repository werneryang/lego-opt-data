from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from opt_data.pipeline.scheduler import ScheduleRunner
from opt_data.pipeline.snapshot import SnapshotSlot

from helpers import build_config


def test_plan_day_includes_all_job_types(tmp_path):
    cfg = build_config(tmp_path)
    runner = ScheduleRunner(cfg)
    trade_date = date(2025, 10, 6)

    jobs = runner.plan_day(trade_date)

    snapshot_jobs = [job for job in jobs if job.kind == "snapshot"]
    rollup_jobs = [job for job in jobs if job.kind == "rollup"]
    enrichment_jobs = [job for job in jobs if job.kind == "enrichment"]

    assert len(snapshot_jobs) == 14  # 09:30 through 16:00 inclusive, 30-minute spacing
    assert len(rollup_jobs) == 1
    assert len(enrichment_jobs) == 1
    assert jobs[0].kind == "snapshot"
    assert jobs[-1].kind == "enrichment"
    assert jobs[-1].run_time.tzinfo == ZoneInfo(cfg.timezone.name)


def test_plan_day_skips_non_trading_day(tmp_path):
    cfg = build_config(tmp_path)
    runner = ScheduleRunner(cfg)
    saturday = date(2025, 10, 4)

    jobs = runner.plan_day(saturday)
    assert jobs == []


def test_run_simulation_invokes_runners_in_order(tmp_path):
    cfg = build_config(tmp_path)
    tz = ZoneInfo(cfg.timezone.name)

    events: list[tuple[str, str | None]] = []

    class FakeSnapshotRunner:
        def __init__(self) -> None:
            self.calls: list[tuple] = []
            start = datetime(2025, 10, 6, 9, 30, tzinfo=tz)
            next_slot = start + timedelta(minutes=30)
            self._slots = [
                SnapshotSlot(index=0, et=start, utc=start.astimezone(ZoneInfo("UTC"))),
                SnapshotSlot(index=1, et=next_slot, utc=next_slot.astimezone(ZoneInfo("UTC"))),
            ]
            self._slots_by_label = {slot.label: slot for slot in self._slots}

        def available_slots(self, _trade_date: date):
            return list(self._slots)

        def resolve_slot(self, _trade_date: date, label: str):
            return self._slots_by_label[label]

        def run(self, trade_date: date, slot, symbols=None, **_: object):
            self.calls.append((trade_date, slot.label, tuple(symbols or [])))
            events.append(("snapshot", slot.label))

    class FakeRollupRunner:
        def __init__(self) -> None:
            self.calls: list[tuple] = []

        def run(self, trade_date: date, symbols=None, **_: object):
            self.calls.append((trade_date, tuple(symbols or [])))
            events.append(("rollup", None))

    class FakeEnrichmentRunner:
        def __init__(self) -> None:
            self.calls: list[tuple] = []

        def run(self, trade_date: date, symbols=None, fields=None, **_: object):
            self.calls.append((trade_date, tuple(symbols or []), tuple(fields or [])))
            events.append(("enrichment", None))

    snapshot_runner = FakeSnapshotRunner()
    rollup_runner = FakeRollupRunner()
    enrichment_runner = FakeEnrichmentRunner()

    runner = ScheduleRunner(
        cfg,
        snapshot_runner=snapshot_runner,
        rollup_runner=rollup_runner,
        enrichment_runner=enrichment_runner,
    )

    trade_date = date(2025, 10, 6)
    summary = runner.run_simulation(
        trade_date,
        symbols=["AAPL"],
        enrichment_fields=["open_interest"],
    )

    assert summary.snapshots == 2
    assert summary.rollups == 1
    assert summary.enrichments == 1
    assert summary.errors == []

    # maintain chronological order: 09:30 snapshot -> 10:00 snapshot -> rollup -> enrichment
    expected_order = [
        ("snapshot", "09:30"),
        ("snapshot", "10:00"),
        ("rollup", None),
        ("enrichment", None),
    ]
    assert events == expected_order
