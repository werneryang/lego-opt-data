"""
Streamlit dashboard for opt-data observability and control.
"""

import streamlit as st
import pandas as pd
import json
import altair as alt
from typing import Any, Dict
from pathlib import Path
from datetime import datetime
import pytz
import pyarrow.dataset as ds
import pyarrow.compute as pc
import asyncio

# Fix for ib_insync/eventkit in Streamlit thread
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# Opt-Data Imports
from opt_data.config import load_config, IBClientIdPoolConfig
from opt_data.universe import load_universe
from opt_data.util.calendar import to_et_date
from opt_data.pipeline.snapshot import SnapshotRunner
from opt_data.pipeline.rollup import RollupRunner
from opt_data.pipeline.enrichment import EnrichmentRunner
from opt_data.pipeline.history import HistoryRunner
from opt_data.ib.session import IBSession

# Page config
st.set_page_config(
    page_title="Opt-Data Dashboard",
    page_icon="📊",
    layout="wide",
)


@st.cache_data(ttl=60)
def load_universe_data(config_path):
    try:
        cfg = load_config(Path(config_path))
        univ = load_universe(cfg.universe.file)
        return cfg, univ
    except Exception:
        return None, []


def _ui_client_id_pool(cfg):
    """Use test pool (200-250) with locking to avoid UI collisions."""
    pool = cfg.ib.client_id_pool
    return IBClientIdPoolConfig(
        role="test",
        range=(200, 250),
        randomize=pool.randomize if pool else True,
        state_dir=pool.state_dir if pool else Path("state/client_ids"),
        lock_ttl_seconds=pool.lock_ttl_seconds if pool else 7200,
    )


def _ui_session_factory(cfg, *, market_data_type=None):
    pool = _ui_client_id_pool(cfg)
    md_type = market_data_type if market_data_type is not None else cfg.ib.market_data_type
    return lambda: IBSession(
        host=cfg.ib.host,
        port=cfg.ib.port,
        client_id=None,  # use pool allocator
        client_id_pool=pool,
        market_data_type=md_type,
    )


def get_recent_errors(limit=50):
    """Load recent errors from jsonl logs."""
    error_dir = Path("state/run_logs/errors")
    if not error_dir.exists():
        return pd.DataFrame()

    # Get recent log files
    files = sorted(error_dir.glob("errors_*.log"), reverse=True)[:3]
    errors = []
    for f in files:
        try:
            with open(f, "r") as fh:
                for line in fh:
                    try:
                        errors.append(json.loads(line))
                    except Exception:
                        pass
        except Exception:
            pass

    if not errors:
        return pd.DataFrame()

    df = pd.DataFrame(errors)
    if "ts" in df.columns:
        df["ts"] = pd.to_datetime(df["ts"])
        df = df.sort_values("ts", ascending=False).head(limit)
    return df


@st.cache_data(ttl=30, max_entries=6, show_spinner=False)
def load_parquet_data(path_str, _filter_expr=None, columns=None, row_limit: int | None = 2000):
    """Generic helper to load parquet data with optional projection, filter, and row cap."""
    try:
        path = Path(path_str)
        if not path.exists():
            return pd.DataFrame()

        # Use pyarrow dataset for robust partitioned loading
        # This handles schema evolution/mismatches better than pd.read_parquet(dir)
        dataset = ds.dataset(path, partitioning="hive")

        scanner = dataset.scanner(columns=columns, filter=_filter_expr, use_threads=True)
        table = scanner.head(row_limit) if row_limit else scanner.to_table()
        df = table.to_pandas()
        if row_limit is not None and len(df) > row_limit:
            df = df.head(row_limit)
        return df
    except Exception:
        # st.warning(f"Failed to load data from {path_str}: {e}")
        return pd.DataFrame()


def compute_dataset_stats(path_str: str, _filter_expr=None, columns: list[str] | None = None):
    """Stream dataset to compute counts without loading full tables into pandas."""
    path = Path(path_str)
    if not path.exists():
        return None

    dataset = ds.dataset(path, partitioning="hive")
    try:
        scanner = dataset.scanner(columns=columns, filter=_filter_expr, use_threads=True)
        stats: dict[str, Any] = {
            "rows": scanner.count_rows(),
            "underlyings": 0,
            "error_count": 0,
            "market_data_type_counts": {},
            "rollup_strategy_counts": {},
            "data_quality_present": False,
            "oi_positive": 0,
        }

        underlying_vals: set[Any] = set()

        for batch in scanner.to_reader():
            if "underlying" in batch.column_names:
                uniques = pc.unique(batch["underlying"])
                underlying_vals.update(val.as_py() for val in uniques if val is not None)

            if "snapshot_error" in batch.column_names:
                err_sum = pc.sum(batch["snapshot_error"])
                if err_sum is not None:
                    stats["error_count"] += err_sum.as_py()

            if "market_data_type" in batch.column_names:
                vc = pc.value_counts(batch["market_data_type"])
                for val, cnt in zip(vc["values"], vc["counts"]):
                    key = val.as_py()
                    if key is None:
                        continue
                    stats["market_data_type_counts"][key] = (
                        stats["market_data_type_counts"].get(key, 0) + cnt.as_py()
                    )

            if "rollup_strategy" in batch.column_names:
                vc = pc.value_counts(batch["rollup_strategy"])
                for val, cnt in zip(vc["values"], vc["counts"]):
                    key = val.as_py()
                    if key is None:
                        continue
                    stats["rollup_strategy_counts"][key] = (
                        stats["rollup_strategy_counts"].get(key, 0) + cnt.as_py()
                    )

            if "data_quality_flag" in batch.column_names and len(batch["data_quality_flag"]) > 0:
                stats["data_quality_present"] = True

            if "open_interest" in batch.column_names:
                pos_sum = pc.sum(pc.greater(batch["open_interest"], 0))
                if pos_sum is not None:
                    stats["oi_positive"] += pos_sum.as_py()

        stats["underlyings"] = len(underlying_vals)
        return stats
    except Exception:
        return None


@st.cache_data(ttl=60, show_spinner=False)
def compute_fast_stats(path_str: str) -> dict | None:
    """Read Parquet metadata only - no data scan. Ultra-fast for mobile."""
    path = Path(path_str)
    if not path.exists():
        return {"exists": False, "rows": 0, "files": 0}

    try:
        dataset = ds.dataset(path, partitioning="hive")
        fragments = list(dataset.get_fragments())
        total_rows = 0
        for frag in fragments:
            try:
                meta = frag.metadata
                if meta is not None:
                    total_rows += meta.num_rows
            except Exception:
                pass
        return {"exists": True, "rows": total_rows, "files": len(fragments)}
    except Exception:
        return {"exists": True, "rows": 0, "files": 0}


def load_history_data(base_path: Path, symbol: str, date_str: str) -> pd.DataFrame:
    """Load history JSON files for a symbol and date."""
    target_dir = base_path / symbol / date_str
    if not target_dir.exists():
        return pd.DataFrame()

    data = []
    for f in target_dir.glob("*.json"):
        try:
            content = json.loads(f.read_text())
            # content is a list of bars
            for bar in content:
                bar["conid"] = f.stem
                data.append(bar)
        except Exception:
            pass

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    return df


def render_history_tab(cfg, universe, *, lightweight_mode: bool = False):
    st.header("📜 Daily Option History")

    if not cfg:
        st.error("Config not loaded.")
        return

    # 1. Fetch Controls
    with st.expander("Fetch History", expanded=True):
        # Row 1: Primary Controls
        c1, c2, c3 = st.columns([2, 1, 1])

        with c1:
            # Symbol selection
            univ_symbols = [u.symbol for u in universe] if universe else []
            selected_symbols = st.multiselect("Symbols", univ_symbols, default=["AAPL"])

            if not selected_symbols:
                st.warning("⚠️ No symbols selected. This will fetch the ENTIRE universe.")

        with c2:
            days = st.number_input(
                "Days (Full Fetch)", min_value=1, max_value=365, value=30, help="Days to look back"
            )

        with c3:
            fetch_mode = st.radio(
                "Fetch Mode",
                ["Incremental", "Full Overwrite"],
                horizontal=True,
                help="Incremental checks existing data and only fetches missing days.",
            )
            incremental = fetch_mode == "Incremental"

        # Row 2: Advanced Settings
        with st.expander("Advanced Settings"):
            a1, a2, a3, a4 = st.columns(4)
            with a1:
                bar_size = st.selectbox(
                    "Bar Size",
                    ["8 hours", "1 day", "1 hour", "30 mins", "15 mins", "5 mins", "1 min"],
                    index=0,
                    help="Time interval for bars. '8 hours' uses the daily aggregator workaround.",
                )
            with a2:
                what_to_show = st.selectbox(
                    "Data Type",
                    ["MIDPOINT", "TRADES", "BID", "ASK", "BID_ASK", "ADJUSTED_LAST"],
                    index=0,
                    help="Data type to fetch.",
                )
            with a3:
                use_rth = st.checkbox("Regular Trading Hours (RTH)", value=True)
            with a4:
                force_refresh = st.checkbox(
                    "Force Refresh Contracts", value=False, help="Re-run contract discovery"
                )

        st.write("")
        if st.button("Start Fetching", type="primary"):
            st_status = st.empty()
            st_prog_bar = st.progress(0)
            st_prog_text = st.empty()

            st_status.info("Initializing History Runner...")

            def ui_progress_callback(
                current: int, total: int, status: str, details: Dict[str, Any]
            ):
                pct = (current / total) if total > 0 else 0
                pct = min(max(pct, 0.0), 1.0)
                st_prog_bar.progress(pct)
                st_prog_text.text(f"{int(pct * 100)}% - {status}")

            try:
                runner = HistoryRunner(cfg)
                res = runner.run(
                    symbols=selected_symbols,
                    days=days,
                    what_to_show=what_to_show,
                    use_rth=use_rth,
                    force_refresh=force_refresh,
                    incremental=incremental,
                    bar_size=bar_size,
                    progress_callback=ui_progress_callback,
                )

                st_prog_bar.progress(1.0)
                st_status.success(
                    f"Fetch Complete! Processed: {res.get('processed')} symbols. Errors: {res.get('errors')}"
                )

                if res.get("errors", 0) > 0:
                    with st.expander("Error Details"):
                        st.json(res["symbols"])

            except Exception as e:
                st_status.error(f"Failed: {e}")

    st.divider()

    # 2. Data Viewer
    st.subheader("📊 History Viewer")

    # Source Selection
    data_source = st.radio(
        "Data Source",
        ["Legacy JSON (Production)", "Weekend Backfill (Experiment)"],
        horizontal=True,
    )

    if data_source == "Legacy JSON (Production)":
        # Original Logic
        history_base = Path(cfg.paths.clean) / "ib" / "history"

        if not history_base.exists():
            st.info("No history data found yet.")
            return

        avail_symbols = [d.name for d in history_base.iterdir() if d.is_dir()]
        if not avail_symbols:
            st.info("No symbols in history directory.")
            return

        v1, v2 = st.columns([1, 3])

        with v1:
            view_symbol = st.selectbox("Select Symbol", sorted(avail_symbols))

            sym_dir = history_base / view_symbol
            avail_dates = sorted([d.name for d in sym_dir.iterdir() if d.is_dir()], reverse=True)

            if not avail_dates:
                st.warning("No dates found for symbol.")
                view_date = None
            else:
                view_date = st.selectbox("Select Run Date", avail_dates)

        with v2:
            if view_symbol and view_date:
                df = load_history_data(history_base, view_symbol, view_date)

                if df.empty:
                    st.warning("No data found in files.")
                else:
                    st.caption(f"Loaded {len(df)} records (bars) for {view_symbol} on {view_date}")

                    m1, m2, m3 = st.columns(3)
                    m1.metric("Total Bars", len(df))
                    m2.metric("Unique Contracts", df["conid"].nunique())

                    if lightweight_mode:
                        st.info("📱 Lightweight mode: data tables and charts are hidden.")
                    else:
                        tab_data, tab_chart = st.tabs(["Data Table", "Visualization"])

                        with tab_data:
                            st.dataframe(df, use_container_width=True)

                        with tab_chart:
                            if "close" in df.columns:
                                c = (
                                    alt.Chart(
                                        df.sample(min(len(df), 5000)) if len(df) > 5000 else df
                                    )
                                    .mark_bar()
                                    .encode(
                                        x=alt.X("close", bin=True, title="Close Price"),
                                        y="count()",
                                        tooltip=["count()"],
                                    )
                                    .properties(title="Close Price Distribution (Sampled)")
                                )
                                st.altair_chart(c, use_container_width=True)
                            else:
                                st.info("No 'close' column to chart.")

    else:
        # Weekend Backfill Viewer logic
        backfill_base = Path("data_test/raw/ib/historical_bars_weekend")

        if not backfill_base.exists():
            st.info(f"Backfill directory not found: {backfill_base}")
            return

        # Listing Symbols
        avail_symbols = sorted([d.name for d in backfill_base.iterdir() if d.is_dir()])
        if not avail_symbols:
            st.info("No symbols found in backfill directory.")
            return

        c1, c2, c3 = st.columns([1, 1, 2])

        with c1:
            bf_symbol = st.selectbox("Symbol", avail_symbols, key="bf_sym")

        # List contracts for symbol
        sym_dir = backfill_base / bf_symbol
        avail_cons = sorted([d.name for d in sym_dir.iterdir() if d.is_dir()])

        with c2:
            bf_conid = st.selectbox("Contract ID", avail_cons, key="bf_con") if avail_cons else None

        if not bf_conid:
            st.warning("No contracts found.")
            return

        # List Parquet files for contract
        # Structure: SYMBOL/conId/TRADES/*.parquet
        trades_dir = sym_dir / bf_conid / "TRADES"
        files = sorted(list(trades_dir.glob("*.parquet"))) if trades_dir.exists() else []

        with c3:
            selected_file = (
                st.selectbox("Select File", [f.name for f in files], key="bf_file")
                if files
                else None
            )

        if not selected_file:
            st.warning("No Parquet files found in TRADES directory.")
        else:
            file_path = trades_dir / selected_file
            try:
                # For Parquet, always read to get metrics, but maybe skip table if lightweight?
                # Reading small parquet is usually fast.
                df = pd.read_parquet(file_path)
                st.success(f"Loaded {len(df)} rows from {selected_file}")

                # Metrics
                m1, m2, m3 = st.columns(3)
                m1.metric("Rows", len(df))
                if "date" in df.columns:
                    min_date = df["date"].min()
                    max_date = df["date"].max()
                    m2.metric("Start", str(min_date))
                    m3.metric("End", str(max_date))

                if lightweight_mode:
                    st.info("📱 Lightweight mode: data tables and charts are hidden.")
                else:
                    # Table & Chart
                    t1, t2 = st.tabs(["Data Table", "Chart"])

                    with t1:
                        st.dataframe(df, use_container_width=True)

                    with t2:
                        if "close" in df.columns and "date" in df.columns:
                            chart = (
                                alt.Chart(df)
                                .mark_line()
                                .encode(
                                    x="date:T",
                                    y=alt.Y("close:Q", scale=alt.Scale(zero=False)),
                                    tooltip=["date", "open", "high", "low", "close", "volume"],
                                )
                                .properties(title=f"{bf_symbol} - {selected_file}")
                                .interactive()
                            )
                            st.altair_chart(chart, use_container_width=True)
                        else:
                            st.info("Chart requires 'date' and 'close' columns.")

            except Exception as e:
                st.error(f"Failed to read parquet: {e}")


def render_operations_tab(*, lightweight_mode: bool = True):
    st.header("🛠 Operations & Controls")

    # 1. Top Bar: Context & Date
    col_cfg, col_date, col_date_btn = st.columns([2, 1, 2])

    with col_cfg:
        config_options = ["config/opt-data.toml", "config/opt-data.test.toml"]
        selected_config = st.selectbox("Config File", config_options, index=0)

    cfg, universe = load_universe_data(selected_config)
    if not cfg:
        st.error("Failed to load config/universe.")
        return

    with col_date:
        # Default to today if trading day, else last trading day?
        # For simplicity, default to today ET
        # Use aware UTC to ensure correct conversion to ET
        today_et = to_et_date(datetime.now(pytz.utc))
        selected_date = st.date_input("Trade Date", value=today_et)

    with col_date_btn:
        st.write("")  # Spacer
        st.write("")
        c1, c2 = st.columns(2)
        if c1.button("Prev Trading Day"):
            st.info("Use date picker to select previous dates.")
        if c2.button("Today (ET)"):
            st.info(f"Today is {today_et}")

    # Symbol Selection
    with st.expander("Symbol Selection", expanded=False):
        selected_symbols = st.multiselect("Select Symbols (Empty = All)", universe, default=[])

    symbols_arg = selected_symbols if selected_symbols else None
    row_limit_default = 100 if lightweight_mode else 2000

    if lightweight_mode:
        st.info("📱 Lightweight mode (mobile/5G): showing stats only, tables hidden.")

    st.divider()

    # 2. Data Status Panel
    st.subheader(f"Data Status: {selected_date}")

    # Paths - CORRECTED to ib/chain
    intraday_path = Path(f"data/clean/ib/chain/view=intraday/date={selected_date}")
    close_path = Path(f"data/clean/ib/chain/view=close/date={selected_date}")
    daily_path = Path(f"data/clean/ib/chain/view=daily_clean/date={selected_date}")
    enrich_path = Path(f"data/clean/ib/chain/view=enrichment/date={selected_date}")

    # Use fast stats in lightweight mode, skip expensive file counting
    if lightweight_mode:
        # Fast metadata-only stats
        intraday_stats = compute_fast_stats(str(intraday_path))
        close_stats = compute_fast_stats(str(close_path))
        daily_stats = compute_fast_stats(str(daily_path))
        enrich_stats = compute_fast_stats(str(enrich_path))

        # Mobile layout: 2 columns
        row1_c1, row1_c2 = st.columns(2)
        row1_c1.metric(
            "Intraday",
            f"{intraday_stats.get('rows', 0):,}" if intraday_stats.get("exists") else "Missing",
            delta="OK" if intraday_stats.get("exists") else "Missing",
            delta_color="normal" if intraday_stats.get("exists") else "off",
        )
        row1_c2.metric(
            "Close",
            f"{close_stats.get('rows', 0):,}" if close_stats.get("exists") else "Missing",
            delta="OK" if close_stats.get("exists") else "Missing",
            delta_color="normal" if close_stats.get("exists") else "off",
        )

        row2_c1, row2_c2 = st.columns(2)
        row2_c1.metric(
            "Daily",
            f"{daily_stats.get('rows', 0):,}" if daily_stats.get("exists") else "Missing",
            delta="OK" if daily_stats.get("exists") else "Pending",
            delta_color="normal" if daily_stats.get("exists") else "off",
        )
        row2_c2.metric(
            "OI Enrichment",
            f"{enrich_stats.get('rows', 0):,}" if enrich_stats.get("exists") else "Missing",
            delta="OK" if enrich_stats.get("exists") else "Pending",
            delta_color="normal" if enrich_stats.get("exists") else "off",
        )

        # Slot count
        runner = SnapshotRunner(cfg)
        try:
            avail_slots = runner.available_slots(selected_date)
            st.metric("Total Slots", f"{len(avail_slots)}")
        except Exception:
            st.metric("Total Slots", "N/A")

    else:
        # Desktop mode: original 5-column layout
        intraday_exists = intraday_path.exists()
        intraday_count = (
            sum(1 for _ in intraday_path.glob("**/*.parquet")) if intraday_exists else 0
        )
        close_exists = close_path.exists()
        daily_exists = daily_path.exists()
        enrich_exists = enrich_path.exists()

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric(
            "Intraday Partitions",
            f"{intraday_count}",
            delta="Exists" if intraday_exists else "Missing",
            delta_color="normal" if intraday_exists else "off",
        )
        m2.metric(
            "Close Snapshot",
            "Exists" if close_exists else "Missing",
            delta="OK" if close_exists else "Missing",
            delta_color="normal" if close_exists else "off",
        )
        m3.metric(
            "Daily Clean",
            "Exists" if daily_exists else "Missing",
            delta="OK" if daily_exists else "Pending",
            delta_color="normal" if daily_exists else "off",
        )
        m4.metric(
            "Enrichment (OI)",
            "Exists" if enrich_exists else "Missing",
            delta="OK" if enrich_exists else "Pending",
            delta_color="normal" if enrich_exists else "off",
        )

        # Slot Coverage (Estimate)
        runner = SnapshotRunner(cfg)
        try:
            avail_slots = runner.available_slots(selected_date)
            total_slots = len(avail_slots)
            m5.metric("Total Slots", f"{total_slots}")
        except Exception:
            m5.metric("Total Slots", "N/A")

    st.divider()

    # 3. Intraday Snapshot Controls
    st.subheader("📸 Intraday Snapshot")

    col_snap_1, col_snap_2 = st.columns([1, 3])

    with col_snap_1:
        slot_mode = st.radio("Slot Mode", ["Auto (Now)", "Manual"])

    with col_snap_2:
        selected_slot_label = None
        if slot_mode == "Manual":
            try:
                slots = runner.available_slots(selected_date)
                slot_labels = [s.label for s in slots]
                selected_slot_label = st.selectbox(
                    "Select Slot", slot_labels, index=len(slot_labels) - 1 if slot_labels else 0
                )
            except Exception as e:
                st.error(f"Could not load slots: {e}")
        else:
            st.info("Will use current time to resolve slot.")

    # -------------------------------------------------------------------------
    # WEEKEND BACKFILL STATUS (Experiment)
    # -------------------------------------------------------------------------
    st.divider()
    st.subheader("🧪 Weekend Backfill Status (Experiment)")

    backfill_path = Path("data_test/raw/ib/historical_bars_weekend")
    if not backfill_path.exists():
        st.info(f"No experimental backfill data found at {backfill_path}")
    else:
        # Simple stats: count symbols
        bf_symbols = [x for x in backfill_path.iterdir() if x.is_dir()]
        count_syms = len(bf_symbols)

        # Check if we have data for selected Date? No, backfill structure is Symbol/ConId/TRADES/file.parquet
        # It's not strictly date partitioned at top level.
        # But we can check if any file modification time is recent, or just general stats.

        bf1, bf2 = st.columns(2)
        bf1.metric("Backfill Symbols", count_syms)
        bf1.caption(f"Path: {backfill_path}")

        if count_syms > 0:
            if lightweight_mode:
                bf2.info("Lightweight mode: deeper stats hidden.")
            else:
                # Count total parquet files? Might be slow if many files.
                # Just show a sample symbol
                sample_sym = bf_symbols[0].name
                bf2.info(f"Sample data available for {sample_sym}. View in 'History' tab.")

    st.divider()

    if st.button("Run Intraday Snapshot", type="primary"):
        status_container = st.empty()
        status_container.info("Starting snapshot...")
        try:
            # Re-init runner with fresh config just in case
            run_cfg = load_config(Path(selected_config))

            def dashboard_session_factory():
                return _ui_session_factory(run_cfg, market_data_type=run_cfg.ib.market_data_type)()

            sn_runner = SnapshotRunner(
                run_cfg,
                snapshot_grace_seconds=run_cfg.cli.snapshot_grace_seconds,
                session_factory=dashboard_session_factory,
            )

            if slot_mode == "Auto (Now)":
                slot_obj = sn_runner.resolve_slot(selected_date, "now")
            else:
                slot_obj = sn_runner.resolve_slot(selected_date, selected_slot_label)

            status_container.info(f"Running snapshot for {selected_date} slot {slot_obj.label}...")

            # Run
            result = sn_runner.run(selected_date, slot_obj, symbols=symbols_arg)

            if result.errors:
                status_container.error(
                    f"Snapshot completed with {len(result.errors)} errors. Written: {result.rows_written}"
                )
                st.expander("Errors").write(result.errors)
            else:
                status_container.success(f"Snapshot success! Written: {result.rows_written} rows.")

        except Exception as e:
            status_container.error(f"Snapshot failed: {e}")

    st.divider()

    # 4. EOD Controls
    st.subheader("🌙 EOD Pipeline")

    eod_c1, eod_c2, eod_c3 = st.columns(3)

    with eod_c1:
        st.markdown("**1. Close Snapshot**")
        st.caption("Fetch frozen data at market close.")
        if st.button("Run Close Snapshot"):
            st_eod = st.empty()
            st_eod.info("Running Close Snapshot...")
            progress_box = st.empty()
            progress_lines: list[str] = []
            try:
                run_cfg = load_config(Path(selected_config))

                # Factory for market_data_type=2 (Frozen)
                def frozen_session_factory():
                    return _ui_session_factory(run_cfg, market_data_type=2)()

                sn_runner = SnapshotRunner(
                    run_cfg,
                    snapshot_grace_seconds=run_cfg.cli.snapshot_grace_seconds,
                    session_factory=frozen_session_factory,
                )

                # Close slot is usually the last one
                slots = sn_runner.available_slots(selected_date)
                if not slots:
                    raise ValueError("No slots found for date")
                close_slot = slots[-1]

                def progress_cb(symbol: str, status: str, extra: dict[str, Any]) -> None:
                    parts = [status]
                    if symbol:
                        parts.append(symbol)
                    if extra:
                        parts.append(", ".join(f"{k}={v}" for k, v in extra.items()))
                    progress_lines.append(" ".join(parts))
                    # Show the last few updates to avoid flooding the UI
                    progress_box.markdown("\n".join(progress_lines[-8:]))

                res = sn_runner.run(
                    selected_date,
                    close_slot,
                    symbols=symbols_arg,
                    ingest_run_type="close_snapshot",
                    view="close",
                    progress=progress_cb,
                )
                st_eod.success(f"Close Snapshot Done. Rows: {res.rows_written}")
            except Exception as e:
                st_eod.error(f"Failed: {e}")

    with eod_c2:
        st.markdown("**2. Rollup**")
        st.caption("Aggregate intraday + close to daily.")
        if st.button("Run Rollup"):
            st_roll = st.empty()
            st_roll.info("Running Rollup...")
            try:
                run_cfg = load_config(Path(selected_config))

                # Resolve slots
                sn_runner = SnapshotRunner(run_cfg)
                slots_today = sn_runner.available_slots(selected_date)
                if len(slots_today) < 2:
                    st_roll.warning("Not enough slots for full rollup logic, trying anyway...")

                close_slot_idx = slots_today[-1].index
                fallback_slot_idx = (
                    slots_today[-2].index if len(slots_today) >= 2 else slots_today[-1].index
                )

                # RollupRunner doesn't need session_factory - it only processes already-captured data
                r_runner = RollupRunner(
                    run_cfg, close_slot=close_slot_idx, fallback_slot=fallback_slot_idx
                )
                res = r_runner.run(selected_date, symbols=symbols_arg)
                st_roll.success(f"Rollup Done. Written: {res.rows_written}")
            except Exception as e:
                st_roll.error(f"Failed: {e}")

    with eod_c3:
        st.markdown("**3. Enrichment (OI)**")
        st.caption("Fetch Open Interest (T+1).")

        # Overwrite option
        allow_overwrite = st.checkbox("允许覆盖已有 OI（仅本日期）", value=False)

        if st.button("Run Enrichment"):
            st_enr = st.empty()
            progress_box = st.empty()
            progress_lines: list[str] = []
            st_enr.info(f"Running Enrichment (Overwrite={allow_overwrite})...")
            try:
                run_cfg = load_config(Path(selected_config))

                def dashboard_session_factory():
                    return _ui_session_factory(
                        run_cfg, market_data_type=run_cfg.ib.market_data_type
                    )()

                def progress_cb(symbol: str, status: str, extra: dict[str, Any]) -> None:
                    # Build a readable progress line with totals and symbol info
                    done = extra.get("done")
                    total = extra.get("total")
                    symbols_done = extra.get("symbols_done")
                    symbols_total = extra.get("symbols_total")

                    pieces = [status]
                    if symbol:
                        pieces.append(f"symbol={symbol}")
                    if done is not None and total is not None:
                        pieces.append(f"{done}/{total}")
                    if symbols_done is not None and symbols_total is not None:
                        pieces.append(f"symbols {symbols_done}/{symbols_total}")

                    # Append any remaining fields for debugging
                    remaining = {
                        k: v
                        for k, v in extra.items()
                        if k not in {"done", "total", "symbols_done", "symbols_total"}
                    }
                    if remaining:
                        pieces.append(", ".join(f"{k}={v}" for k, v in remaining.items()))

                    progress_lines.append(" ".join(pieces))
                    progress_box.markdown("\n".join(progress_lines[-8:]))

                enr_runner = EnrichmentRunner(run_cfg, session_factory=dashboard_session_factory)
                res = enr_runner.run(
                    selected_date,
                    symbols=symbols_arg,
                    force_overwrite=allow_overwrite,
                    progress=progress_cb,
                )

                st_enr.success(f"Enrichment Done. Updated: {res.rows_updated}")

                if res.oi_stats:
                    s = res.oi_stats
                    st.markdown(f"""
                    **Overwrite Stats:**
                    - ✨ Filled (was missing): `{s.get("filled_from_missing", 0)}`
                    - 🟢 Same (unchanged): `{s.get("same", 0)}`
                    - 🔴 Changed: `{s.get("changed", 0)}`
                    """)

                    if res.oi_diffs:
                        with st.expander(f"View Changed Items ({len(res.oi_diffs)})"):
                            st.dataframe(pd.DataFrame(res.oi_diffs))

            except Exception as e:
                st_enr.error(f"Failed: {e}")

    st.divider()

    # -------------------------------------------------------------------------
    # 1. Close Snapshot View (Desktop only - tables hidden in lightweight mode)
    # -------------------------------------------------------------------------
    if not lightweight_mode:
        st.subheader("🏁 Close Snapshot Data")

        close_exists = close_path.exists()
        if not close_exists:
            st.warning(
                "Close snapshot partition is missing for this date. Please run Close Snapshot."
            )
        else:
            close_stats_key = f"close_stats_{selected_date.isoformat()}_{','.join(symbols_arg) if symbols_arg else 'ALL'}"
            if st.button(
                "Compute full metrics (may be heavy on mobile/5G)",
                key=f"compute_close_metrics_{selected_date.isoformat()}",
                help="Runs full-partition counts using Arrow; may take time on large dates.",
            ):
                st.session_state[close_stats_key] = compute_dataset_stats(
                    str(close_path),
                    _filter_expr=ds.field("underlying").isin(symbols_arg) if symbols_arg else None,
                    columns=[
                        "underlying",
                        "snapshot_error",
                        "market_data_type",
                    ],
                )

            stats_close = st.session_state.get(close_stats_key)

            # Full-count metrics (shown if computed)
            c1, c2, c3, c4 = st.columns(4)
            if stats_close:
                c1.metric("Underlyings", f"{stats_close.get('underlyings', 0)}")
                c2.metric("Contracts", f"{stats_close.get('rows', 0)}")

                err_count = stats_close.get("error_count", 0)
                rows_total = stats_close.get("rows", 0)
                err_pct = (err_count / rows_total * 100) if rows_total else 0
                c3.metric("Errors", f"{err_count} ({err_pct:.1f}%)")

                mdt_dist = stats_close.get("market_data_type_counts", {})
                if mdt_dist:
                    c4.json(mdt_dist, expanded=False)
            else:
                c1.info("Click to compute full metrics")

            load_close = st.checkbox(
                "Load Close Snapshot Table",
                value=False,
                key=f"load_close_{selected_date.isoformat()}",
            )

            if not load_close:
                st.info("Table not loaded. Enable the checkbox to fetch close snapshot data.")
            else:
                if st.button("Refresh Close Data"):
                    st.cache_data.clear()

                close_filter = ds.field("underlying").isin(symbols_arg) if symbols_arg else None

                close_cols = [
                    "underlying",
                    "exchange",
                    "conid",
                    "expiry",
                    "right",
                    "strike",
                    "bid",
                    "ask",
                    "mid",
                    "last",
                    "volume",
                    "iv",
                    "delta",
                    "gamma",
                    "theta",
                    "vega",
                    "market_data_type",
                    "sample_time",
                    "snapshot_error",
                    "data_quality_flag",
                ]

                df_close = load_parquet_data(
                    str(close_path),
                    columns=close_cols,
                    _filter_expr=close_filter,
                    row_limit=row_limit_default,
                )

                if df_close.empty:
                    st.info(
                        "Close snapshot data exists but returned no rows. "
                        "Check partitions or adjust filters."
                    )
                else:
                    st.caption(
                        f"Row cap: {row_limit_default} (increase by disabling lightweight mode)"
                    )
                    st.dataframe(df_close, use_container_width=True)

        st.divider()

    # -------------------------------------------------------------------------
    # 2. Daily Rollup View (Desktop only)
    # -------------------------------------------------------------------------
    if not lightweight_mode:
        st.subheader("📦 Daily Rollup Data")

        daily_exists = daily_path.exists()
        if not daily_exists:
            st.warning("Daily Rollup data does not exist. Please run Rollup.")
        else:
            rollup_stats_key = f"rollup_stats_{selected_date.isoformat()}_{','.join(symbols_arg) if symbols_arg else 'ALL'}"
            if st.button(
                "Compute full metrics (may be heavy on mobile/5G)",
                key=f"compute_rollup_metrics_{selected_date.isoformat()}",
                help="Runs full-partition counts using Arrow; may take time on large dates.",
            ):
                st.session_state[rollup_stats_key] = compute_dataset_stats(
                    str(daily_path),
                    _filter_expr=ds.field("underlying").isin(symbols_arg) if symbols_arg else None,
                    columns=[
                        "underlying",
                        "rollup_strategy",
                        "data_quality_flag",
                    ],
                )

            stats_rollup = st.session_state.get(rollup_stats_key)

            r1, r2, r3 = st.columns(3)
            if stats_rollup:
                r1.metric("Contracts", f"{stats_rollup.get('rows', 0)}")
                strat_dist_full = stats_rollup.get("rollup_strategy_counts", {})
                if strat_dist_full:
                    r2.write("Strategy Dist (full):")
                    r2.json(strat_dist_full, expanded=False)
                if stats_rollup.get("data_quality_present"):
                    r3.caption("Data quality flags present; see table for details.")
            else:
                r1.info("Click to compute full metrics")

            load_rollup = st.checkbox(
                "Load Daily Rollup Table",
                value=False,
                key=f"load_rollup_{selected_date.isoformat()}",
            )

            if not load_rollup:
                st.info("Table not loaded. Enable the checkbox to fetch rollup data.")
            else:
                cols_rollup = [
                    "trade_date",
                    "underlying",
                    "exchange",
                    "conid",
                    "expiry",
                    "right",
                    "strike",
                    "underlying_close",
                    "bid",
                    "ask",
                    "mid",
                    "last",
                    "volume",
                    "iv",
                    "delta",
                    "gamma",
                    "theta",
                    "vega",
                    "rollup_strategy",
                    "rollup_source_slot",
                    "rollup_source_time",
                    "data_quality_flag",
                ]

                rollup_filter = ds.field("underlying").isin(symbols_arg) if symbols_arg else None
                df_rollup = load_parquet_data(
                    str(daily_path),
                    columns=cols_rollup,
                    _filter_expr=rollup_filter,
                    row_limit=row_limit_default,
                )

                if df_rollup.empty:
                    st.info("Daily data file exists but is empty or unreadable.")
                else:
                    st.caption(
                        f"Row cap: {row_limit_default} (increase by disabling lightweight mode)"
                    )
                    st.dataframe(df_rollup, use_container_width=True)

        st.divider()

    # -------------------------------------------------------------------------
    # 3. OI Enrichment View (Desktop only)
    # -------------------------------------------------------------------------
    if not lightweight_mode:
        st.subheader("💰 OI Enrichment (T+1)")

        enrich_exists = enrich_path.exists()
        if not enrich_exists:
            st.warning("OI Enrichment has not been run (view=enrichment missing).")
        else:
            st.success("OI Enrichment executed.")

        # We load from daily_clean because enrichment updates daily_clean in place
        if not daily_exists:
            st.error("Daily clean data missing, cannot show OI.")
        else:
            oi_stats_key = f"oi_stats_{selected_date.isoformat()}_{','.join(symbols_arg) if symbols_arg else 'ALL'}"
            if st.button(
                "Compute full metrics (may be heavy on mobile/5G)",
                key=f"compute_oi_metrics_{selected_date.isoformat()}",
                help="Runs full-partition counts using Arrow; may take time on large dates.",
            ):
                st.session_state[oi_stats_key] = compute_dataset_stats(
                    str(daily_path),
                    _filter_expr=ds.field("underlying").isin(symbols_arg) if symbols_arg else None,
                    columns=[
                        "underlying",
                        "open_interest",
                        "data_quality_flag",
                    ],
                )

            stats_oi = st.session_state.get(oi_stats_key)

            oi1, oi2, oi3 = st.columns(3)
            if stats_oi:
                oi1.metric("Contracts", f"{stats_oi.get('rows', 0)}")
                rows_oi = stats_oi.get("rows", 0)
                oi_pos = stats_oi.get("oi_positive", 0)
                coverage_full = (oi_pos / rows_oi * 100) if rows_oi else 0
                oi2.metric("OI Coverage (>0)", f"{coverage_full:.1f}%")
                if stats_oi.get("data_quality_present"):
                    oi3.caption("Data quality flags present; see table for details.")
            else:
                oi1.info("Click to compute full metrics")

            load_oi = st.checkbox(
                "Load OI Table",
                value=False,
                key=f"load_oi_{selected_date.isoformat()}",
            )

            if not load_oi:
                st.info("Table not loaded. Enable the checkbox to fetch OI data.")
            else:
                if st.button("Refresh OI Data"):
                    st.cache_data.clear()

                cols_oi = [
                    "underlying",
                    "exchange",
                    "conid",
                    "expiry",
                    "right",
                    "strike",
                    "underlying_close",
                    "bid",
                    "ask",
                    "mid",
                    "last",
                    "volume",
                    "open_interest",
                    "oi_asof_date",
                    "data_quality_flag",
                ]

                oi_filter = ds.field("underlying").isin(symbols_arg) if symbols_arg else None
                df_oi = load_parquet_data(
                    str(daily_path),
                    columns=cols_oi,
                    _filter_expr=oi_filter,
                    row_limit=row_limit_default,
                )

                if symbols_arg:
                    df_oi = df_oi[df_oi["underlying"].isin(symbols_arg)]

                if not df_oi.empty:
                    st.caption(
                        f"Row cap: {row_limit_default} (increase by disabling lightweight mode)"
                    )
                    st.dataframe(df_oi, use_container_width=True)

    st.divider()


def main():
    # Sidebar
    st.sidebar.title("Opt-Data")
    lightweight_mode = st.sidebar.checkbox("Lightweight mode (mobile/5G)", value=True)

    tab_ops, tab_hist = st.tabs(["Operations", "History"])

    with tab_ops:
        render_operations_tab(lightweight_mode=lightweight_mode)

    with tab_hist:
        # Load config for history tab
        cfg_hist, univ_hist = load_universe_data("config/opt-data.toml")
        render_history_tab(cfg_hist, univ_hist, lightweight_mode=lightweight_mode)


if __name__ == "__main__":
    main()
