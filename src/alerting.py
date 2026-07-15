"""
PHASE 7 - ALERT MANAGEMENT

Turns Warning/Critical records into alerts, de-duplicates repeated alerts
on the same service within a batch, and logs every alert to a small
SQLite database so there's a persistent record (a stand-in for a real
dashboard's data source).
"""

import sqlite3
from pathlib import Path

import pandas as pd

_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "alerts.db"


def _init_db():
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT,
            risk_level TEXT,
            anomaly_score REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def _log_alerts(alerts: pd.DataFrame):
    if alerts.empty:
        return
    conn = _init_db()
    for _, row in alerts.iterrows():
        conn.execute(
            "INSERT INTO alerts (service, risk_level, anomaly_score) VALUES (?, ?, ?)",
            (str(row.get("service", "unknown")), row["risk_level"], float(row["anomaly_score"])),
        )
    conn.commit()
    conn.close()


def generate_alerts(classified: pd.DataFrame) -> pd.DataFrame:
    """Entry point called by the orchestrator for Phase 7."""
    alerts = classified[classified["risk_level"] != "Normal"].copy()

    if not alerts.empty and "service" in alerts.columns:
        before = len(alerts)
        alerts = alerts.drop_duplicates(subset=["service", "risk_level"])
        deduped = before - len(alerts)
        if deduped:
            print(f"[alerting] de-duplicated {deduped} repeated alerts")

    _log_alerts(alerts)

    for _, row in alerts.iterrows():
        print(f"[alerting] ALERT service={row.get('service', 'unknown')} "
              f"level={row['risk_level']} score={row['anomaly_score']:.3f}")
    if alerts.empty:
        print("[alerting] no Warning/Critical records this batch")
    return alerts