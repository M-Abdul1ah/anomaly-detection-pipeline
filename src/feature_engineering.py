"""
PHASE 4 — FEATURE ENGINEERING

Real job: turn cleaned, context-aware records into the actual inputs models
use — statistical features, time-series features (rolling windows, trends,
seasonality), behavioural features, cross-device correlations, then select
only the informative ones.

STATUS: stub. Currently just selects the existing numeric columns as-is.

TODO (build this after Phase 3):
  1. Add rolling-window aggregates per device (mean/std of src_bytes over
     the last N records) — this is where tsfresh (see requirements.txt)
     can help auto-generate time-series features.
  2. Add a same_srv_rate / diff_srv_rate style behavioural ratio feature
     specific to this dataset if the built-in ones aren't enough.
  3. Once you have >1 candidate feature set, add a feature-selection step
     (e.g. sklearn's SelectKBest) so Phase 5 isn't slowed down by noise.
"""

import pandas as pd


def build_features(batch: pd.DataFrame) -> pd.DataFrame:
    """Entry point called by the orchestrator for Phase 4.
    Currently a pass-through: returns the numeric columns already produced
    by preprocessing.py, unchanged.
    """
    numeric_cols = [
        c for c in batch.select_dtypes(include="number").columns
        if c not in ("difficulty", "_record_id")
    ]
    features = batch[numeric_cols + ["label"]].copy() if "label" in batch.columns else batch[numeric_cols].copy()
    print(f"[feature_engineering] (stub) passed through {len(numeric_cols)} numeric columns as-is")
    return features
