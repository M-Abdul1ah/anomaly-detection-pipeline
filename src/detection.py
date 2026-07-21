"""
PHASE 5 - ANOMALY DETECTION ENGINE

Runs four complementary detectors and combines them into one ensemble
anomaly score per record: statistical (Z-score), ML (Isolation Forest +
Autoencoder), and rule-based.

Also keeps each detector's individual score as its own column (not just
the blended average), plus a plain-text "explanation" of which
detector(s) drove each record's score - this is what alerting.py and the
dashboard use to answer "why was this flagged?" instead of showing a
single opaque number.
"""

import numpy as np
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


def _autoencoder_score(features: pd.DataFrame) -> pd.Series:
    """Autoencoder ML detector. Trains a small neural net to reconstruct
    each record from a compressed representation. Records the model
    reconstructs poorly (high error) are treated as anomalies - it
    learned what 'normal' looks like, and struggles on anything unusual."""
    from sklearn.neural_network import MLPRegressor

    numeric_cols = [c for c in features.select_dtypes(include="number").columns if c != "label"]
    if not numeric_cols or len(features) < 10:
        return pd.Series(0.0, index=features.index)

    X = features[numeric_cols].fillna(0).values
    bottleneck = max(2, len(numeric_cols) // 4)

    model = MLPRegressor(
        hidden_layer_sizes=(bottleneck,), max_iter=200, random_state=42
    )
    model.fit(X, X)  # autoencoder: learns to reproduce its own input
    reconstructed = model.predict(X)

    reconstruction_error = np.mean((X - reconstructed) ** 2, axis=1)
    normalized = (reconstruction_error - reconstruction_error.min()) / (
        reconstruction_error.max() - reconstruction_error.min() + 1e-9
    )
    return pd.Series(normalized, index=features.index)


def _rule_score(features: pd.DataFrame) -> pd.Series:
    """Rule-based behaviour detector."""
    if "serror_rate" not in features.columns or "same_srv_rate" not in features.columns:
        return pd.Series(0.0, index=features.index)
    flagged = (features["serror_rate"] > 2) & (features["same_srv_rate"] < -2)
    return flagged.astype(float)


# Human-readable names for each detector, used when building explanations.
_DETECTOR_LABELS = {
    "score_zscore": "Z-score",
    "score_isoforest": "Isolation Forest",
    "score_autoencoder": "Autoencoder",
    "score_rule": "Rule-based",
}


def _build_explanation(row, top_n: int = 2) -> str:
    """Pick the top_n highest-scoring detectors for this record and format
    them as a short human-readable string, e.g.
    'Isolation Forest (0.81), Rule-based (1.00)'."""
    scores = {col: row[col] for col in _DETECTOR_LABELS}
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top = ranked[:top_n]
    parts = [f"{_DETECTOR_LABELS[col]} ({val:.2f})" for col, val in top if val > 0]
    return ", ".join(parts) if parts else "no single detector dominant"


def detect(features: pd.DataFrame) -> pd.DataFrame:
    """Entry point called by the orchestrator for Phase 5."""
    result = features.copy()
    stat = _statistical_score(features)
    iso_forest = _ml_score(features)
    autoencoder = _autoencoder_score(features)
    rule = _rule_score(features)

    # Keep each detector's individual score - previously these were local
    # variables only used for the average, then thrown away. Keeping them
    # as columns is what makes "why was this flagged?" answerable later.
    result["score_zscore"] = stat
    result["score_isoforest"] = iso_forest
    result["score_autoencoder"] = autoencoder
    result["score_rule"] = rule

    result["anomaly_score"] = (stat + iso_forest + autoencoder + rule) / 4
    result["explanation"] = result.apply(_build_explanation, axis=1)

    print(f"[detection] scored {len(result)} records - min={result['anomaly_score'].min():.3f} mean={result['anomaly_score'].mean():.3f} max={result['anomaly_score'].max():.3f}")
    return result
