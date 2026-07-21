"""
Streamlit dashboard reading alerts logged by alerting.py (Phase 7).
Auto-refreshes every few seconds so it stays live as the pipeline runs.
Run with: streamlit run dashboard.py
"""

import sqlite3
import time
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).resolve().parent / "data" / "processed" / "alerts.db"
REFRESH_SECONDS = 5

st.set_page_config(page_title="Anomaly Detection - Alert Dashboard", layout="wide")
st.title("Network / Modem Anomaly Detection - Alert Dashboard")
st.caption(f"Auto-refreshes every {REFRESH_SECONDS} seconds")

placeholder = st.empty()

while True:
    with placeholder.container():
        if not DB_PATH.exists():
            st.warning("No alerts.db found yet. Run `python -m src.pipeline` first to generate alerts.")
        else:
            conn = sqlite3.connect(DB_PATH)
            alerts = pd.read_sql_query("SELECT * FROM alerts ORDER BY id DESC", conn)
            conn.close()

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Alerts", len(alerts))
            col2.metric("Critical Alerts", int((alerts["risk_level"] == "Critical").sum()) if not alerts.empty else 0)
            col3.metric("Warning Alerts", int((alerts["risk_level"] == "Warning").sum()) if not alerts.empty else 0)

            st.subheader("Alerts by Risk Level")
            if not alerts.empty:
                st.bar_chart(alerts["risk_level"].value_counts())

            st.subheader("Alerts by Service")
            if not alerts.empty and "service" in alerts.columns:
                st.bar_chart(alerts["service"].value_counts())

            st.subheader("Recent Alerts")
            st.dataframe(alerts, use_container_width=True)

    time.sleep(REFRESH_SECONDS)