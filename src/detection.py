"""
PHASE 5 - ANOMALY DETECTION ENGINE

Runs four complementary detectors and combines them into one ensemble
anomaly score per record: statistical (Z-score), ML (Isolation Forest +
Autoencoder), and rule-based.
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


def detect(features: pd.DataFrame) -> pd.DataFrame:
    """Entry point called by the orchestrator for Phase 5."""
    result = features.copy()
    stat = _statistical_score(features)
    iso_forest = _ml_score(features)
    autoencoder = _autoencoder_score(features)
    rule = _rule_score(features)
    result["anomaly_score"] = (stat + iso_forest + autoencoder + rule) / 4
    print(f"[detection] scored {len(result)} records - min={result['anomaly_score'].min():.3f} mean={result['anomaly_score'].mean():.3f} max={result['anomaly_score'].max():.3f}")
    return result