"""
Streamlit dashboard for opt-data observability.
"""

import streamlit as st
import pandas as pd
import sqlite3
import time
from pathlib import Path
from datetime import datetime, timedelta
import altair as alt
import os

# Page config
st.set_page_config(
    page_title="Opt-Data Dashboard",
    page_icon="📊",
    layout="wide",
)

# Load config to find DB path
# We'll use a simple heuristic or env var if config loading is complex
DB_PATH = os.getenv("OPT_DATA_METRICS_DB", "data/metrics.db")

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

def main():
    st.title("🚀 Opt-Data System Status")
    
    # Sidebar
    st.sidebar.header("Settings")
    auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)
    if auto_refresh:
        time.sleep(5)
        st.rerun()
        
    # Load data
    df = load_metrics(2000)
    
    if df.empty:
        st.warning("No metrics data found. System might be idle or starting up.")
        return

    # Overview Metrics
    st.header("Overview")
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
    st.header("Trends")
    
    # Snapshot Activity
    st.subheader("Snapshot Activity")
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

    # Latency Distribution
    st.subheader("Latency Distribution")
    lat_df = df[df['name'] == 'snapshot.fetch.duration']
    if not lat_df.empty:
        chart_lat = alt.Chart(lat_df).mark_bar().encode(
            x=alt.X('value', bin=True, title='Duration (ms)'),
            y='count()',
            tooltip=['value', 'count()']
        )
        st.altair_chart(chart_lat, use_container_width=True)
        
    # Recent Errors
    st.subheader("Recent Errors")
    errors_df = df[df['name'].str.contains('error')].head(10)
    if not errors_df.empty:
        st.dataframe(errors_df[['timestamp', 'name', 'value', 'tags']])
    else:
        st.info("No recent errors logged.")

if __name__ == "__main__":
    main()
