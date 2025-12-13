"""
Streamlit dashboard for opt-data observability and control.
"""

import streamlit as st
import pandas as pd
import sqlite3
import time
import json
import altair as alt
import os
from typing import Any
from pathlib import Path
from datetime import datetime, timedelta
import pytz
import pyarrow.dataset as ds
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

# Load config to find DB path
# We'll use a simple heuristic or env var if config loading is complex
DB_PATH = os.getenv("OPT_DATA_METRICS_DB", "data/metrics.db")
DEFAULT_CONFIG_PATH = os.getenv("OPT_DATA_CONFIG", "config/opt-data.toml")


@st.cache_data(ttl=10)
def load_metrics(limit=1000):
    """Load recent metrics from SQLite."""
    try:
        conn = sqlite3.connect(DB_PATH)
        query = f"""
            SELECT timestamp, name, value, type, tags 
            FROM metrics 
            ORDER BY timestamp DESC 
            LIMIT {limit}
        """
        df = pd.read_sql_query(query, conn)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    except Exception as e:
        st.error(f"Failed to load metrics: {e}")
        return pd.DataFrame()


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


def render_overview_tab(df):
    st.header("🚀 System Status")

    # Auto Refresh in Sidebar (Global)

    if df.empty:
        st.warning("No metrics data found. System might be idle or starting up.")
        return

    # Overview Metrics
    st.subheader("Key Metrics")
    col1, col2, col3, col4 = st.columns(4)

    # 1. Snapshot Rate (last 5 mins)
    last_5m = df[df["timestamp"] > datetime.utcnow() - timedelta(minutes=5)]
    snapshots_5m = last_5m[last_5m["name"] == "snapshot.fetch.success"]["value"].sum()
    rate = snapshots_5m / 5 if snapshots_5m > 0 else 0
    col1.metric("Snapshot Rate", f"{rate:.1f}/min")

    # 2. Error Rate (last 5 mins)
    errors_5m = last_5m[last_5m["name"] == "snapshot.fetch.error"]["value"].sum()
    total_5m = snapshots_5m + errors_5m
    error_rate = (errors_5m / total_5m * 100) if total_5m > 0 else 0
    col2.metric("Error Rate", f"{error_rate:.2f}%", delta_color="inverse")

    # 3. Avg Latency (last 5 mins)
    latency_df = last_5m[last_5m["name"] == "snapshot.fetch.duration"]
    avg_latency = latency_df["value"].mean() if not latency_df.empty else 0
    col3.metric("Avg Latency", f"{avg_latency:.0f} ms")

    # 4. Rollup Rows (Last Run)
    rollup_df = df[df["name"] == "rollup.rows_written"].sort_values("timestamp", ascending=False)
    last_rollup = rollup_df.iloc[0]["value"] if not rollup_df.empty else 0
    col4.metric("Last Rollup Rows", f"{int(last_rollup):,}")

    # Charts
    st.subheader("Trends")

    # Snapshot Activity
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.caption("Snapshot Activity")
        activity_df = df[df["name"].isin(["snapshot.fetch.success", "snapshot.fetch.error"])].copy()
        if not activity_df.empty:
            # Resample to 1 min
            activity_df.set_index("timestamp", inplace=True)
            resampled = (
                activity_df.groupby([pd.Grouper(freq="1min"), "name"])["value"].sum().reset_index()
            )

            chart = (
                alt.Chart(resampled)
                .mark_line()
                .encode(
                    x="timestamp", y="value", color="name", tooltip=["timestamp", "name", "value"]
                )
                .interactive()
            )
            st.altair_chart(chart, use_container_width=True)

    with col_chart2:
        st.caption("Latency Distribution")
        lat_df = df[df["name"] == "snapshot.fetch.duration"]
        if not lat_df.empty:
            chart_lat = (
                alt.Chart(lat_df)
                .mark_bar()
                .encode(
                    x=alt.X("value", bin=True, title="Duration (ms)"),
                    y="count()",
                    tooltip=["value", "count()"],
                )
            )
            st.altair_chart(chart_lat, use_container_width=True)

    # Recent Errors
    st.subheader("Recent Errors (Metrics)")
    errors_df = df[df["name"].str.contains("error")].head(10)
    if not errors_df.empty:
        st.dataframe(errors_df[["timestamp", "name", "value", "tags"]], use_container_width=True)
    else:
        st.info("No recent errors logged in metrics.")


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


def render_history_tab(cfg, universe):
    st.header("📜 Daily Option History")

    if not cfg:
        st.error("Config not loaded.")
        return

    # 1. Fetch Controls
    with st.expander("Fetch History", expanded=True):
        c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])

        with c1:
            # Symbol selection
            univ_symbols = [u.symbol for u in universe] if universe else []
            selected_symbols = st.multiselect("Symbols", univ_symbols, default=["AAPL"])

        with c2:
            days = st.number_input("Days", min_value=1, max_value=365, value=30)

        with c3:
            what_to_show = st.selectbox(
                "Data Type",
                ["TRADES", "MIDPOINT"],
                index=0,
                help="Use TRADES to get real volume/barCount/WAP; MIDPOINT has no real volume.",
            )

        with c4:
            force_refresh = st.checkbox("Force Refresh Cache", value=False)

        with c5:
            st.write("")
            st.write("")
            if st.button("Fetch History", type="primary"):
                st_hist = st.empty()
                st_hist.info("Fetching history...")
                try:
                    runner = HistoryRunner(cfg)
                    res = runner.run(
                        symbols=selected_symbols,
                        days=days,
                        what_to_show=what_to_show,
                        force_refresh=force_refresh,
                    )
                    st_hist.success(
                        f"History Fetch Complete. Processed: {res.get('processed')} symbols."
                    )
                    if res.get("errors", 0) > 0:
                        st.warning(f"Errors encountered: {res.get('errors')}")
                except Exception as e:
                    st_hist.error(f"Failed: {e}")

    st.divider()

    # 2. Data Viewer
    st.subheader("📊 History Viewer")

    # Path resolution
    history_base = Path(cfg.paths.clean) / "ib" / "history"

    if not history_base.exists():
        st.info("No history data found yet.")
        return

    # List available symbols
    avail_symbols = [d.name for d in history_base.iterdir() if d.is_dir()]
    if not avail_symbols:
        st.info("No symbols in history directory.")
        return

    v1, v2 = st.columns([1, 3])

    with v1:
        view_symbol = st.selectbox("Select Symbol", sorted(avail_symbols))

        # List dates for symbol
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

                # Metrics
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Bars", len(df))
                m2.metric("Unique Contracts", df["conid"].nunique())

                # Charting - Close Price of Underlying (if available) or aggregated stats
                # Since these are option bars, plotting them all is messy.
                # Let's plot the distribution of Close prices or Volume.

                tab_data, tab_chart = st.tabs(["Data Table", "Visualization"])

                with tab_data:
                    st.dataframe(df, use_container_width=True)

                with tab_chart:
                    # Simple scatter of Strike vs Volume (if strike available in data? No, data is OHLCV)
                    # We only have conid. We'd need to join with contract info to get strike.
                    # For now, just plot Volume distribution.

                    c = (
                        alt.Chart(df)
                        .mark_bar()
                        .encode(
                            x=alt.X("close", bin=True, title="Close Price"),
                            y="count()",
                            tooltip=["count()"],
                        )
                        .properties(title="Close Price Distribution")
                    )
                    st.altair_chart(c, use_container_width=True)


def render_operations_tab():
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

    st.divider()

    # 2. Data Status Panel
    st.subheader(f"Data Status: {selected_date}")

    # Paths - CORRECTED to ib/chain
    intraday_path = Path(f"data/clean/ib/chain/view=intraday/date={selected_date}")
    daily_path = Path(f"data/clean/ib/chain/view=daily_clean/date={selected_date}")
    enrich_path = Path(f"data/clean/ib/chain/view=enrichment/date={selected_date}")

    intraday_exists = intraday_path.exists()
    intraday_count = sum(1 for _ in intraday_path.glob("**/*.parquet")) if intraday_exists else 0

    daily_exists = daily_path.exists()
    enrich_exists = enrich_path.exists()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(
        "Intraday Partitions",
        f"{intraday_count}",
        delta="Exists" if intraday_exists else "Missing",
        delta_color="normal" if intraday_exists else "off",
    )
    m2.metric(
        "Daily Clean",
        "Exists" if daily_exists else "Missing",
        delta="OK" if daily_exists else "Pending",
        delta_color="normal" if daily_exists else "off",
    )
    m3.metric(
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
        m4.metric("Total Slots", f"{total_slots}")
    except Exception:
        m4.metric("Total Slots", "N/A")

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
    # 1. Close Snapshot View
    # -------------------------------------------------------------------------
    st.subheader("🏁 Close Snapshot Data")

    # Determine close slot
    close_slot_val = None
    try:
        slots = runner.available_slots(selected_date)
        if slots:
            close_slot_val = slots[-1].index
    except Exception:
        pass

    if not close_slot_val:
        st.warning("Could not determine close slot for this date.")
    else:
        # Load intraday data
        # We need to filter by slot_30m == close_slot_val
        # Since parquet partitioning is by date/underlying, we load and then filter
        # Optimization: If we could push down filters to read_parquet, that would be better.
        # But partition structure is date=.../underlying=...
        # So we load the date partition and filter in memory (or use pyarrow filters if possible)

        # Columns to load
        cols = [
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
            "slot_30m",
            "snapshot_error",
            "data_quality_flag",
        ]

        if st.button("Refresh Close Data"):
            st.cache_data.clear()

        close_filter = ds.field("slot_30m") == close_slot_val
        if symbols_arg:
            sym_filter = ds.field("underlying").isin(symbols_arg)
            close_filter = close_filter & sym_filter

        df_close = load_parquet_data(
            str(intraday_path),
            columns=cols,
            _filter_expr=close_filter,
            row_limit=2000,
        )

        if df_close.empty:
            st.info("No intraday data found for this date.")
        else:
            # Filter for close slot
            df_close_filtered = df_close[df_close["slot_30m"] == close_slot_val].copy()

            if symbols_arg:
                df_close_filtered = df_close_filtered[
                    df_close_filtered["underlying"].isin(symbols_arg)
                ]

            if df_close_filtered.empty:
                st.warning(
                    f"No data found for close slot ({close_slot_val}). Please run Close Snapshot."
                )
            else:
                # Metrics
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Underlyings", f"{df_close_filtered['underlying'].nunique()}")
                c2.metric("Contracts", f"{len(df_close_filtered)}")

                err_count = (
                    df_close_filtered["snapshot_error"].sum()
                    if "snapshot_error" in df_close_filtered.columns
                    else 0
                )
                err_pct = (
                    (err_count / len(df_close_filtered) * 100) if len(df_close_filtered) > 0 else 0
                )
                c3.metric("Errors", f"{err_count} ({err_pct:.1f}%)")

                mdt_dist = df_close_filtered["market_data_type"].value_counts().to_dict()
                c4.json(mdt_dist, expanded=False)

                st.dataframe(df_close_filtered, use_container_width=True)

    st.divider()

    # -------------------------------------------------------------------------
    # 2. Daily Rollup View
    # -------------------------------------------------------------------------
    st.subheader("📦 Daily Rollup Data")

    if not daily_exists:
        st.warning("Daily Rollup data does not exist. Please run Rollup.")
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
            row_limit=2000,
        )

        if df_rollup.empty:
            st.info("Daily data file exists but is empty or unreadable.")
        else:
            if symbols_arg:
                df_rollup = df_rollup[df_rollup["underlying"].isin(symbols_arg)]

            # Metrics
            r1, r2, r3 = st.columns(3)
            r1.metric("Contracts", f"{len(df_rollup)}")

            strat_dist = (
                df_rollup["rollup_strategy"].value_counts().to_dict()
                if "rollup_strategy" in df_rollup.columns
                else {}
            )
            r2.write("Strategy Dist:")
            r2.json(strat_dist, expanded=False)

            # Flags
            if "data_quality_flag" in df_rollup.columns:
                # Count occurrences of flags
                # Assuming list or string? Usually list in pandas from parquet if array
                # But might be stringified. Let's just show raw value counts for now or simple check
                pass

            st.dataframe(df_rollup, use_container_width=True)

    st.divider()

    # -------------------------------------------------------------------------
    # 3. OI Enrichment View (T+1)
    # -------------------------------------------------------------------------
    st.subheader("💰 OI Enrichment (T+1)")

    # Check if enrichment marker exists
    if not enrich_exists:
        st.warning("OI Enrichment has not been run (view=enrichment missing).")
    else:
        st.success("OI Enrichment executed.")

    # We load from daily_clean because enrichment updates daily_clean in place (or rather, creates a new version/overwrites)
    # But wait, the user request says: "OI View displays daily_clean/date=D ... updated by enrichment"
    # And also mentions "view=enrichment/date=D partition" as a status indicator.

    if not daily_exists:
        st.error("Daily clean data missing, cannot show OI.")
    else:
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

        if st.button("Refresh OI Data"):
            st.cache_data.clear()

        oi_filter = ds.field("underlying").isin(symbols_arg) if symbols_arg else None
        df_oi = load_parquet_data(
            str(daily_path),
            columns=cols_oi,
            _filter_expr=oi_filter,
            row_limit=2000,
        )

        if symbols_arg:
            df_oi = df_oi[df_oi["underlying"].isin(symbols_arg)]

        if not df_oi.empty:
            # Metrics
            oi1, oi2, oi3 = st.columns(3)

            # Rows with OI > 0
            has_oi = df_oi[df_oi["open_interest"] > 0]
            coverage = (len(has_oi) / len(df_oi) * 100) if len(df_oi) > 0 else 0
            oi1.metric("OI Coverage (>0)", f"{coverage:.1f}%")

            # Missing OI flag
            # Assuming data_quality_flag is a list or string.
            # If it's a list column in parquet, pandas reads as array.
            # Let's try to handle it safely.
            # Simple string check if it's string, or apply if list
            # For performance, let's just sample or assume string for now if simple
            # Or just don't calculate if complex

            st.dataframe(df_oi, use_container_width=True)

    st.divider()

    # 5. Errors & Logs
    st.subheader("⚠️ Recent Pipeline Errors")
    err_df = get_recent_errors()
    if not err_df.empty:
        st.dataframe(err_df, use_container_width=True)
    else:
        st.info("No recent error logs found in state/run_logs/errors/")


def main():
    # Sidebar
    st.sidebar.title("Opt-Data")
    auto_refresh = st.sidebar.checkbox("Auto Refresh Metrics", value=True)

    if auto_refresh:
        time.sleep(5)
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["Overview", "Operations", "History"])

    # Load metrics for Overview
    df_metrics = load_metrics(2000)

    with tab1:
        render_overview_tab(df_metrics)

    with tab2:
        render_operations_tab()

    with tab3:
        # Load config for history tab
        # We need to pick a config. Default to main config for now or let user select inside tab?
        # render_operations_tab has its own config selector.
        # Let's reuse the logic or just load default.
        # Better: Move config selection to sidebar or top level?
        # For now, load default config for History tab to keep it simple.
        cfg_hist, univ_hist = load_universe_data("config/opt-data.toml")
        render_history_tab(cfg_hist, univ_hist)


if __name__ == "__main__":
    main()
