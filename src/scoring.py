"""
PHASE 6 — RISK SCORING & CLASSIFICATION

Real job: enrich the raw anomaly score with context, estimate confidence,
predict false-positive likelihood, compute a final risk score/priority, and
classify each record as Normal / Warning / Critical against thresholds.

STATUS: partially functional — the threshold classification works now
(reads WARNING_THRESHOLD / CRITICAL_THRESHOLD from config.py), but since
Phase 5 currently returns 0.0 for everything, every record will show up as
Normal until detection.py is implemented. That's expected and will resolve
itself once Phase 5 is filled in.

TODO:
  1. Once Phase 5 has real detectors, revisit WARNING_THRESHOLD /
     CRITICAL_THRESHOLD in config.py — the right cutoffs depend on the
     actual score distribution you get, not a guess made before any model
     has run.
  2. Add a confidence/false-positive estimate here (e.g. how far the score
     is from the threshold, or how much Phase 3 context supports it).
"""

import pandas as pd

from config import WARNING_THRESHOLD, CRITICAL_THRESHOLD


def classify(score: float) -> str:
    if score >= CRITICAL_THRESHOLD:
        return "Critical"
    if score >= WARNING_THRESHOLD:
        return "Warning"
    return "Normal"


def score_and_classify(detected: pd.DataFrame) -> pd.DataFrame:
    """Entry point called by the orchestrator for Phase 6."""
    result = detected.copy()
    result["risk_level"] = result["anomaly_score"].apply(classify)
    counts = result["risk_level"].value_counts().to_dict()
    print(f"[scoring] classified {len(result)} records: {counts}")
    return result
