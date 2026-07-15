"""
PHASE 5 - ANOMALY DETECTION ENGINE

Runs three complementary detectors and combines them into one ensemble
anomaly score per record: statistical (Z-score), ML (Isolation Forest),
and rule-based (serror/same-service pattern).
"""

import pandas as pd


def _statistical_score(features: pd.DataFrame) -> pd.Series:
    """Z-score based statistical detector."""
    numeric_cols = [c for c in features.select_dtypes(include="number").columns if c != "label"]
    if not numeric_cols:
        return pd.Series(0.0, index=features.index)
    z_scores = (features[numeric_cols] - features[numeric_cols].mean()) / (features[numeric_cols].std() + 1e-9)
    avg_abs_z = z_scores.abs().mean(axis=1)
    score = (avg_abs_z / 3).clip(upper=1.0)
    return score


def _ml_score(features: pd.DataFrame) -> pd.Series:
    """Isolation Forest ML detector."""
    from sklearn.ensemble import IsolationForest
    numeric_cols = [c for c in features.select_dtypes(include="number").columns if c != "label"]
    if not numeric_cols or len(features) < 10:
        return pd.Series(0.0, index=features.index)
    model = IsolationForest(contamination=0.1, random_state=42)
    model.fit(features[numeric_cols])
    raw_scores = model.decision_function(features[numeric_cols])
    normalized = (raw_scores.max() - raw_scores) / (raw_scores.max() - raw_scores.min() + 1e-9)
    return pd.Series(normalized, index=features.index)


def _rule_score(features: pd.DataFrame) -> pd.Series:
    """Rule-based behaviour detector. Flags records where a high
    connection-error rate combines with an unusually low same-service
    rate - a classic sign of scanning/attack behaviour rather than a
    single noisy metric. Columns are already scaled (mean 0, std 1) by
    preprocessing.py, so thresholds here are in standard-deviation units."""
    if "serror_rate" not in features.columns or "same_srv_rate" not in features.columns:
        return pd.Series(0.0, index=features.index)
    flagged = (features["serror_rate"] > 2) & (features["same_srv_rate"] < -2)
    return flagged.astype(float)


def detect(features: pd.DataFrame) -> pd.DataFrame:
    """Entry point called by the orchestrator for Phase 5."""
    result = features.copy()
    stat = _statistical_score(features)
    ml = _ml_score(features)
    rule = _rule_score(features)
    result["anomaly_score"] = (stat + ml + rule) / 3
    print(f"[detection] scored {len(result)} records - min={result['anomaly_score'].min():.3f} mean={result['anomaly_score'].mean():.3f} max={result['anomaly_score'].max():.3f}")
    return result