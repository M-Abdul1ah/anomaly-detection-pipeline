"""
PHASE 7 — ALERT MANAGEMENT

Real job: turn Warning/Critical records into alerts, correlate and
de-duplicate them so one problem doesn't spam many alerts, assign severity,
route notifications, apply an escalation policy, and feed a dashboard.

STATUS: stub — currently just prints one line per Warning/Critical record.

TODO (build after Phase 6 is producing real classifications):
  1. Add de-duplication: group alerts by device/_record_id within a time
     window so repeated flags on the same device become one alert.
  2. Write alerts to a small SQLite table (data/processed/alerts.db) instead
     of just printing, so the dashboard (Streamlit, Phase 7/8) has something
     to read.
  3. Add a Streamlit page that reads that table and displays it live —
     this is the easiest "impressive demo" piece to show your supervisor.
"""

import pandas as pd


def generate_alerts(classified: pd.DataFrame) -> pd.DataFrame:
    """Entry point called by the orchestrator for Phase 7."""
    alerts = classified[classified["risk_level"] != "Normal"]
    for _, row in alerts.iterrows():
        print(f"[alerting] (stub) ALERT record={row.get('_record_id')} "
              f"level={row['risk_level']} score={row['anomaly_score']:.3f}")
    if alerts.empty:
        print("[alerting] (stub) no Warning/Critical records this batch")
    return alerts
