"""
PHASE 8 — RESPONSE & REMEDIATION

Real job: for each alert, either trigger an automated response (restart
modem, adjust QoS, isolate device, ...) or route it to manual investigation
(root cause analysis, ticketing, engineer review), then log user/ISP
feedback — this feedback is what Phase 9 learns from.

STATUS: stub — currently just logs which path an alert *would* take.

TODO (build after Phase 7 is generating real alerts):
  1. Pick 1-2 simple automated rules to actually implement, e.g. "if
     risk_level == Critical and same device fired 3+ times → log
     'isolate device' action" (simulated, not a real network action).
  2. Everything else routes to 'manual investigation' — just log it for now.
  3. Store the outcome (auto vs manual, and later, human feedback on whether
     it was a true/false positive) in the same SQLite store as alerts.py —
     that log is literally the training signal Phase 9 needs.
"""

import pandas as pd


def respond(alerts: pd.DataFrame) -> pd.DataFrame:
    """Entry point called by the orchestrator for Phase 8."""
    result = alerts.copy()
    if result.empty:
        print("[response] (stub) nothing to respond to this batch")
        return result
    result["response_path"] = result["risk_level"].apply(
        lambda lvl: "automated (stub)" if lvl == "Critical" else "manual investigation (stub)"
    )
    print(f"[response] (stub) routed {len(result)} alerts: "
          f"{result['response_path'].value_counts().to_dict()}")
    return result
