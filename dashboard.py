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

st.set_page_config(
    page_title="Anomaly Detection - Alert Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    h1, h2, h3, p, span, label, .stCaption, .stMarkdown { color: #fafafa !important; }
    .metric-card {
        background: #1a1d29;
        border: 1px solid #2a2d3a;
        border-radius: 10px;
        padding: 18px 20px;
        text-align: center;
    }
    .metric-card p { margin: 4px 0 0 0; color: #9aa0ac !important; font-size: 13px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Network / Modem Anomaly Detection")
st.caption(f"Live alert feed - auto-refreshes every {REFRESH_SECONDS}s - reads from alerts.db (Phase 7)")

placeholder = st.empty()

while True:
    with placeholder.container():
        if not DB_PATH.exists():
            st.warning("No alerts.db found yet. Run python -m src.pipeline first to generate alerts.")
        else:
            conn = sqlite3.connect(DB_PATH)
            alerts = pd.read_sql_query("SELECT * FROM alerts ORDER BY id DESC", conn)
            conn.close()

            total = len(alerts)
            critical = int((alerts["risk_level"] == "Critical").sum()) if not alerts.empty else 0
            warning = int((alerts["risk_level"] == "Warning").sum()) if not alerts.empty else 0

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f'<div class="metric-card"><h2 style="margin:0;font-size:30px;color:#fafafa !important">{total}</h2><p>TOTAL ALERTS</p></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="metric-card"><h2 style="margin:0;font-size:30px;color:#ff6b6b !important">{critical}</h2><p>CRITICAL</p></div>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="metric-card"><h2 style="margin:0;font-size:30px;color:#ffd166 !important">{warning}</h2><p>WARNING</p></div>', unsafe_allow_html=True)

            st.write("")

            col_left, col_right = st.columns(2)
            with col_left:
                st.subheader("Alerts by Risk Level")
                if not alerts.empty:
                    st.bar_chart(alerts["risk_level"].value_counts())
            with col_right:
                st.subheader("Alerts by Service")
                if not alerts.empty and "service" in alerts.columns:
                    st.bar_chart(alerts["service"].value_counts())

            st.subheader("Recent Alerts")
            if alerts.empty:
                st.info("No alerts logged yet.")
            else:
                display_cols = ["created_at", "service", "risk_level", "anomaly_score", "explanation"]
                display_cols = [c for c in display_cols if c in alerts.columns]
                st.dataframe(
                    alerts[display_cols],
                    use_container_width=True,
                    column_config={
                        "explanation": st.column_config.TextColumn("Why flagged", width="large"),
                        "anomaly_score": st.column_config.NumberColumn("Score", format="%.3f"),
                    },
                )

            st.caption("Critical alerts also trigger a Telegram notification (see src/notifications.py).")
    time.sleep(REFRESH_SECONDS)
