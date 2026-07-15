"""
PHASE 5 — ANOMALY DETECTION ENGINE

Real job: run three complementary families of detectors in parallel —
statistical (Z-score/IQR/EWMA), ML (Isolation Forest, Autoencoder, One-Class
SVM, LSTM), and behaviour/rule-based — then combine them with an ensemble
decision, checked against Phase 3's context.

STATUS: stub. Returns a constant score so Phases 6-8 have something to run
against and the whole pipeline is testable end to end today.

TODO (this is the core of the project — build it in this order):
  1. Statistical: implement a simple Z-score detector over one or two
     numeric columns (e.g. src_bytes, count) as `_statistical_score()`.
  2. ML: fit an IsolationForest (scikit-learn) on the feature DataFrame as
     `_ml_score()` — this is usually the fastest way to get a real anomaly
     signal working.
  3. Behaviour: add 1-2 hand-written rules as `_rule_score()` (e.g. flag if
     serror_rate is very high AND same_srv_rate is very low).
  4. Ensemble: combine the three scores in `detect()` below (simple average
     is fine to start; weight them once you can compare against label).
"""

import pandas as pd


def _statistical_score(features: pd.DataFrame) -> pd.Series:
    """TODO: implement Z-score / IQR / EWMA based scoring."""
    return pd.Series(0.0, index=features.index)


def _ml_score(features: pd.DataFrame) -> pd.Series:
    """TODO: implement IsolationForest / Autoencoder / One-Class SVM scoring."""
    return pd.Series(0.0, index=features.index)


def _rule_score(features: pd.DataFrame) -> pd.Series:
    """TODO: implement hand-written behaviour rules."""
    return pd.Series(0.0, index=features.index)


def detect(features: pd.DataFrame) -> pd.DataFrame:
    """Entry point called by the orchestrator for Phase 5.
    Currently returns a constant 0.0 anomaly_score for every record.
    """
    result = features.copy()
    stat = _statistical_score(features)
    ml = _ml_score(features)
    rule = _rule_score(features)
    result["anomaly_score"] = (stat + ml + rule) / 3  # TODO: weight properly later
    print(f"[detection] (stub) scored {len(result)} records (all 0.0 until detectors are implemented)")
    return result
