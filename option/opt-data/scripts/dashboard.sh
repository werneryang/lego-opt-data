#!/bin/bash
# Launch the opt-data dashboard

export OPT_DATA_METRICS_DB="data/metrics.db"
streamlit run src/opt_data/dashboard/app.py
