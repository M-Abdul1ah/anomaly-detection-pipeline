"""
PHASE 5 - ANOMALY DETECTION ENGINE

Runs three complementary detectors and combines them into one ensemble
anomaly score per record: statistical (Z-score), ML (Isolation Forest),
and rule-based (still a TODO).
"""

import pandas as pd


def _statistical_score(features: pd.DataFrame) -> pd.Series:
    """Z-score based statistical detector. Computes how many standard
    deviations each value is from its column's mean, averages the
    absolute Z-scores per record, and squeezes the result into 0-1."""
    numeric_cols = [c for c in features.select_dtypes(include="number").columns if c != "label"]
    if not numeric_cols:
        return pd.Series(0.0, index=features.index)
    z_scores = (features[numeric_cols] - features[numeric_cols].mean()) / (features[numeric_cols].std() + 1e-9)
    avg_abs_z = z_scores.abs().mean(axis=1)
    score = (avg_abs_z / 3).clip(upper=1.0)
    return score


def _ml_score(features: pd.DataFrame) -> pd.Series:
    """Isolation Forest ML detector. Records that get isolated in very
    few random splits are scored as more anomalous."""
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
    """TODO: implement hand-written behaviour rules."""
    return pd.Series(0.0, index=features.index)


def detect(features: pd.DataFrame) -> pd.DataFrame:
    """Entry point called by the orchestrator for Phase 5."""
    result = features.copy()
    stat = _statistical_score(features)
    ml = _ml_score(features)
    rule = _rule_score(features)
    result["anomaly_score"] = (stat + ml + rule) / 3
    print(f"[detection] scored {len(result)} records - min={result['anomaly_score'].min():.3f} mean={result['anomaly_score'].mean():.3f} max={result['anomaly_score'].max():.3f}")
    return result