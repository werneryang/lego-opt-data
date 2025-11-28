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
from pathlib import Path
from datetime import datetime, timedelta
import pytz

# Opt-Data Imports
from opt_data.config import load_config
from opt_data.universe import load_universe
from opt_data.util.calendar import to_et_date, is_trading_day, get_trading_session
from opt_data.pipeline.snapshot import SnapshotRunner
from opt_data.pipeline.rollup import RollupRunner
from opt_data.pipeline.enrichment import EnrichmentRunner
from opt_data.ib.session import IBSession
from opt_data.storage.layout import partition_for

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
        df['timestamp'] = pd.to_datetime(df['timestamp'])
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
    except Exception as e:
        return None, []

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
            with open(f, 'r') as fh:
                for line in fh:
                    try:
                        errors.append(json.loads(line))
                    except:
                        pass
        except:
            pass
            
    if not errors:
        return pd.DataFrame()
        
    df = pd.DataFrame(errors)
    if 'ts' in df.columns:
        df['ts'] = pd.to_datetime(df['ts'])
        df = df.sort_values('ts', ascending=False).head(limit)
    return df

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
    last_5m = df[df['timestamp'] > datetime.utcnow() - timedelta(minutes=5)]
    snapshots_5m = last_5m[last_5m['name'] == 'snapshot.fetch.success']['value'].sum()
    rate = snapshots_5m / 5 if snapshots_5m > 0 else 0
    col1.metric("Snapshot Rate", f"{rate:.1f}/min")
    
    # 2. Error Rate (last 5 mins)
    errors_5m = last_5m[last_5m['name'] == 'snapshot.fetch.error']['value'].sum()
    total_5m = snapshots_5m + errors_5m
    error_rate = (errors_5m / total_5m * 100) if total_5m > 0 else 0
    col2.metric("Error Rate", f"{error_rate:.2f}%", delta_color="inverse")
    
    # 3. Avg Latency (last 5 mins)
    latency_df = last_5m[last_5m['name'] == 'snapshot.fetch.duration']
    avg_latency = latency_df['value'].mean() if not latency_df.empty else 0
    col3.metric("Avg Latency", f"{avg_latency:.0f} ms")
    
    # 4. Rollup Rows (Last Run)
    rollup_df = df[df['name'] == 'rollup.rows_written'].sort_values('timestamp', ascending=False)
    last_rollup = rollup_df.iloc[0]['value'] if not rollup_df.empty else 0
    col4.metric("Last Rollup Rows", f"{int(last_rollup):,}")

    # Charts
    st.subheader("Trends")
    
    # Snapshot Activity
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.caption("Snapshot Activity")
        activity_df = df[df['name'].isin(['snapshot.fetch.success', 'snapshot.fetch.error'])].copy()
        if not activity_df.empty:
            # Resample to 1 min
            activity_df.set_index('timestamp', inplace=True)
            resampled = activity_df.groupby([pd.Grouper(freq='1min'), 'name'])['value'].sum().reset_index()
            
            chart = alt.Chart(resampled).mark_line().encode(
                x='timestamp',
                y='value',
                color='name',
                tooltip=['timestamp', 'name', 'value']
            ).interactive()
            st.altair_chart(chart, use_container_width=True)

    with col_chart2:
        st.caption("Latency Distribution")
        lat_df = df[df['name'] == 'snapshot.fetch.duration']
        if not lat_df.empty:
            chart_lat = alt.Chart(lat_df).mark_bar().encode(
                x=alt.X('value', bin=True, title='Duration (ms)'),
                y='count()',
                tooltip=['value', 'count()']
            )
            st.altair_chart(chart_lat, use_container_width=True)
        
    # Recent Errors
    st.subheader("Recent Errors (Metrics)")
    errors_df = df[df['name'].str.contains('error')].head(10)
    if not errors_df.empty:
        st.dataframe(errors_df[['timestamp', 'name', 'value', 'tags']], use_container_width=True)
    else:
        st.info("No recent errors logged in metrics.")

def render_console_tab():
    st.header("🛠 Console & Controls")
    
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
        today_et = to_et_date(datetime.utcnow())
        selected_date = st.date_input("Trade Date", value=today_et)
        
    with col_date_btn:
        st.write("") # Spacer
        st.write("") 
        c1, c2 = st.columns(2)
        if c1.button("Prev Trading Day"):
            # This is a bit tricky in Streamlit to update the date_input widget directly without session state
            # For now, just show a message or use session state if we want to be fancy.
            # Let's stick to simple for MVP.
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
    
    # Check data existence (Mock logic for now, or real check if possible)
    # We can check directories
    
    # Intraday
    intraday_path = Path(f"data/clean/option_chain/view=intraday/date={selected_date}")
    intraday_exists = intraday_path.exists()
    intraday_count = sum(1 for _ in intraday_path.glob("**/*.parquet")) if intraday_exists else 0
    
    # Daily
    daily_path = Path(f"data/clean/option_chain/view=daily_clean/date={selected_date}")
    daily_exists = daily_path.exists()
    
    # Enrichment
    enrich_path = Path(f"data/clean/option_chain/view=enrichment/date={selected_date}")
    enrich_exists = enrich_path.exists()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Intraday Partitions", f"{intraday_count}", delta="Exists" if intraday_exists else "Missing", delta_color="normal" if intraday_exists else "off")
    m2.metric("Daily Clean", "Exists" if daily_exists else "Missing", delta="OK" if daily_exists else "Pending", delta_color="normal" if daily_exists else "off")
    m3.metric("Enrichment (OI)", "Exists" if enrich_exists else "Missing", delta="OK" if enrich_exists else "Pending", delta_color="normal" if enrich_exists else "off")
    
    # Slot Coverage (Estimate)
    runner = SnapshotRunner(cfg)
    try:
        avail_slots = runner.available_slots(selected_date)
        total_slots = len(avail_slots)
        m4.metric("Total Slots", f"{total_slots}")
    except:
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
                selected_slot_label = st.selectbox("Select Slot", slot_labels, index=len(slot_labels)-1 if slot_labels else 0)
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
            
            # Use unique client ID for dashboard (200+) to avoid conflicts
            import random
            unique_client_id = 200 + random.randint(0, 50)
            
            def dashboard_session_factory():
                return IBSession(
                    host=run_cfg.ib.host,
                    port=run_cfg.ib.port,
                    client_id=unique_client_id,
                    market_data_type=run_cfg.ib.market_data_type
                )
            
            sn_runner = SnapshotRunner(run_cfg, snapshot_grace_seconds=run_cfg.cli.snapshot_grace_seconds, session_factory=dashboard_session_factory)
            
            if slot_mode == "Auto (Now)":
                slot_obj = sn_runner.resolve_slot(selected_date, "now")
            else:
                slot_obj = sn_runner.resolve_slot(selected_date, selected_slot_label)
            
            status_container.info(f"Running snapshot for {selected_date} slot {slot_obj.label}...")
            
            # Run
            result = sn_runner.run(selected_date, slot_obj, symbols=symbols_arg)
            
            if result.errors:
                status_container.error(f"Snapshot completed with {len(result.errors)} errors. Written: {result.rows_written}")
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
            try:
                run_cfg = load_config(Path(selected_config))
                
                # Use unique client ID for dashboard (200+) to avoid conflicts
                import random
                unique_client_id = 200 + random.randint(0, 50)
                
                # Factory for market_data_type=2 (Frozen)
                def frozen_session_factory():
                    return IBSession(
                        host=run_cfg.ib.host,
                        port=run_cfg.ib.port,
                        client_id=unique_client_id,
                        market_data_type=2
                    )
                
                sn_runner = SnapshotRunner(run_cfg, snapshot_grace_seconds=run_cfg.cli.snapshot_grace_seconds, session_factory=frozen_session_factory)
                
                # Close slot is usually the last one
                slots = sn_runner.available_slots(selected_date)
                if not slots:
                    raise ValueError("No slots found for date")
                close_slot = slots[-1]
                
                res = sn_runner.run(selected_date, close_slot, symbols=symbols_arg)
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
                
                # Use unique client ID for dashboard (200+) to avoid conflicts
                import random
                unique_client_id = 200 + random.randint(0, 50)
                
                def dashboard_session_factory():
                    return IBSession(
                        host=run_cfg.ib.host,
                        port=run_cfg.ib.port,
                        client_id=unique_client_id,
                        market_data_type=run_cfg.ib.market_data_type
                    )
                
                # Resolve slots
                sn_runner = SnapshotRunner(run_cfg)
                slots_today = sn_runner.available_slots(selected_date)
                if len(slots_today) < 2:
                    st_roll.warning("Not enough slots for full rollup logic, trying anyway...")
                
                close_slot_idx = slots_today[-1].index
                fallback_slot_idx = slots_today[-2].index if len(slots_today) >= 2 else slots_today[-1].index
                
                r_runner = RollupRunner(run_cfg, close_slot=close_slot_idx, fallback_slot=fallback_slot_idx, session_factory=dashboard_session_factory)
                res = r_runner.run(selected_date, symbols=symbols_arg)
                st_roll.success(f"Rollup Done. Written: {res.rows_written}")
            except Exception as e:
                st_roll.error(f"Failed: {e}")

    with eod_c3:
        st.markdown("**3. Enrichment (OI)**")
        st.caption("Fetch Open Interest (T+1).")
        if st.button("Run Enrichment"):
            st_enr = st.empty()
            st_enr.info("Running Enrichment...")
            try:
                run_cfg = load_config(Path(selected_config))
                
                # Use unique client ID for dashboard (200+) to avoid conflicts
                import random
                unique_client_id = 200 + random.randint(0, 50)
                
                def dashboard_session_factory():
                    return IBSession(
                        host=run_cfg.ib.host,
                        port=run_cfg.ib.port,
                        client_id=unique_client_id,
                        market_data_type=run_cfg.ib.market_data_type
                    )
                
                enr_runner = EnrichmentRunner(run_cfg, session_factory=dashboard_session_factory)
                res = enr_runner.run(selected_date, symbols=symbols_arg)
                st_enr.success(f"Enrichment Done. Updated: {res.rows_updated}")
            except Exception as e:
                st_enr.error(f"Failed: {e}")

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

    tab1, tab2 = st.tabs(["Overview", "Console"])
    
    # Load metrics for Overview
    df_metrics = load_metrics(2000)
    
    with tab1:
        render_overview_tab(df_metrics)
        
    with tab2:
        render_console_tab()

if __name__ == "__main__":
    main()
