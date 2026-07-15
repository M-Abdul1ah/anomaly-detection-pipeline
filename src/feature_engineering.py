"""
PHASE 4 - FEATURE ENGINEERING

Turns cleaned, context-aware records into the actual inputs the detectors
use: the existing numeric columns, plus a rolling-window mean/std per
batch (a simple stand-in for "trend" - how far is this record's key
metrics from what's typical in this batch), and the two graph-context
columns from Phase 3 (service history, service degree).
"""

import pandas as pd


def _add_rolling_features(features: pd.DataFrame) -> pd.DataFrame:
    """Rolling-window style features: for a couple of key columns, add
    how far each value is from this batch's own rolling mean. This is a
    simplified stand-in for a true time-ordered rolling window, since our
    batches don't carry real timestamps yet."""
    for col in ["src_bytes", "count"]:
        if col in features.columns:
            window = features[col].rolling(window=5, min_periods=1)
            features[f"{col}_rolling_mean"] = window.mean()
            features[f"{col}_dev_from_rolling"] = features[col] - features[f"{col}_rolling_mean"]
    return features


def build_features(batch: pd.DataFrame) -> pd.DataFrame:
    """Entry point called by the orchestrator for Phase 4."""
    numeric_cols = [
        c for c in batch.select_dtypes(include="number").columns
        if c not in ("difficulty", "_record_id")
    ]
    features = batch[numeric_cols].copy()
    if "label" in batch.columns:
        features["label"] = batch["label"]

    features = _add_rolling_features(features)

    print(f"[feature_engineering] built {features.shape[1]} features "
          f"(base numeric columns + rolling deviation + graph context)")
    return features