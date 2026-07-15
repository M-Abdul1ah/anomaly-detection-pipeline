"""
PHASE 2 — DATA PREPROCESSING

Real job: parse, validate, deduplicate, fill/mark missing values, filter
noise, sync timestamps, normalize and scale, and gate anything that fails a
data-quality check.

STATUS: functional (covers the core steps below at a basic level). Good
first place to come back and add more validation once Phase 5+ shows you
what "bad data" actually looks like for this dataset.
"""

import pandas as pd
from sklearn.preprocessing import StandardScaler

from config import CATEGORICAL_COLUMNS

_scaler = StandardScaler()
_scaler_fitted = False


def clean_batch(batch: pd.DataFrame) -> pd.DataFrame:
    """Basic cleaning: drop exact duplicates, fill missing numeric values."""
    batch = batch.drop_duplicates()
    numeric_cols = batch.select_dtypes(include="number").columns
    batch[numeric_cols] = batch[numeric_cols].fillna(0)
    return batch


def scale_batch(batch: pd.DataFrame) -> pd.DataFrame:
    """Scale numeric columns so later detectors aren't dominated by large-
    magnitude features like src_bytes/dst_bytes.

    TODO: right now this scaler is refit on every batch, which is fine for
    the skeleton but not correct for a real streaming system — a production
    version should fit the scaler once on historical data (or use an
    incremental/online scaler) and reuse it.
    """
    global _scaler_fitted
    numeric_cols = [
        c for c in batch.select_dtypes(include="number").columns
        if c not in ("label", "difficulty", "_record_id")
    ]
    if not numeric_cols:
        return batch
    if not _scaler_fitted:
        _scaler.fit(batch[numeric_cols])
        _scaler_fitted = True
    scaled = _scaler.transform(batch[numeric_cols])
    batch[numeric_cols] = scaled
    return batch


def preprocess_batch(batch: pd.DataFrame) -> pd.DataFrame:
    """Entry point called by the orchestrator for Phase 2."""
    batch = clean_batch(batch)
    batch = scale_batch(batch)
    return batch
