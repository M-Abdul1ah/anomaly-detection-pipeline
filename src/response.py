"""
PHASE 8 - RESPONSE & REMEDIATION

Routes each alert to an automated or manual response path. Critical
alerts get a simulated automated action logged, plus a Telegram
notification; everything else routes to manual investigation.
"""

import pandas as pd

from src.notifications import send_critical_alert


def _automated_action(row) -> str:
    """Pick a simulated automated action for a Critical alert. Not a real
    network action - just a logged decision, matching the architecture
    doc's 'automated response' list."""
    if row["anomaly_score"] > 0.7:
        return "isolate device (simulated)"
    return "reset interface (simulated)"


def respond(alerts: pd.DataFrame) -> pd.DataFrame:
    """Entry point called by the orchestrator for Phase 8."""
    result = alerts.copy()
    if result.empty:
        print("[response] nothing to respond to this batch")
        return result

    actions = []
    for _, row in result.iterrows():
        if row["risk_level"] == "Critical":
            actions.append(_automated_action(row))
            send_critical_alert(row)
        else:
            actions.append("manual investigation")
    result["response_action"] = actions

    print(f"[response] routed {len(result)} alerts: "
          f"{result['response_action'].value_counts().to_dict()}")
    return result