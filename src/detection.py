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

Graph context validation: the score is nudged slightly using Phase 3's
context columns (_context_service_seen_count, _context_service_degree) -
a first-time-seen service nudges the score UP a little (less trust,
unknown behavior); a well-established, well-connected service nudges it
DOWN a little (more trust, established pattern). This closes the "Graph
Context Validation" gap noted in the README's Diagram vs. Built table.
Because these two columns now have a deliberate job, they're excluded
from the raw numeric features fed into the statistical/ML detectors
below, so they aren't double-counted as noise AND as validation.
"""

import numpy as np
import pandas as pd

# Columns that are graph-context metadata, not raw signal - excluded from
# the statistical/ML detectors' numeric_cols since they're used
# deliberately in _graph_context_adjustment() instead.
_CONTEXT_COLUMNS = ("_context_service_seen_count", "_context_service_degree")


def _statistical_score(features: pd.DataFrame) -> pd.Series:
    """Z-score based statistical detector."""
    numeric_cols = [
        c for c in features.select_dtypes(include="number").columns
        if c != "label" and c not in _CONTEXT_COLUMNS
    ]
    if not numeric_cols:
        return pd.Series(0.0, index=features.index)
    z_scores = (features[numeric_cols] - features[numeric_cols].mean()) / (features[numeric_cols].std() + 1e-9)
    avg_abs_z = z_scores.abs().mean(axis=1)
    score = (avg_abs_z / 3).clip(upper=1.0)
    return score


def _ml_score(features: pd.DataFrame) -> pd.Series:
    """Isolation Forest ML detector."""
    from sklearn.ensemble import IsolationForest
    numeric_cols = [
        c for c in features.select_dtypes(include="number").columns
        if c != "label" and c not in _CONTEXT_COLUMNS
    ]
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

    numeric_cols = [
        c for c in features.select_dtypes(include="number").columns
        if c != "label" and c not in _CONTEXT_COLUMNS
    ]
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


def _graph_context_adjustment(features: pd.DataFrame) -> pd.Series:
    """Nudges the blended score using graph history, not another raw
    feature: a first-time-seen service (low seen_count, low degree)
    nudges the score UP slightly (less trust, unknown behavior); a
    well-established, well-connected service nudges it DOWN slightly
    (more trust, established pattern). Scales gradually rather than a
    hard on/off, and returns a small signed value (-0.05 to +0.05) meant
    to validate/adjust the four-detector average, not dominate it."""
    if "_context_service_seen_count" not in features.columns or "_context_service_degree" not in features.columns:
        return pd.Series(0.0, index=features.index)

    seen = features["_context_service_seen_count"].clip(lower=0)
    degree = features["_context_service_degree"].clip(lower=0)

    # familiarity: 0 = never seen before / isolated, 1 = well-established
    # and well-connected. seen_count weighted more heavily than degree
    # since "have we seen this before" matters more than "how many
    # protocols does it use".
    familiarity = (seen.clip(upper=20) / 20) * 0.7 + (degree.clip(upper=5) / 5) * 0.3
    adjustment = 0.05 - 0.10 * familiarity
    return adjustment


# Human-readable names for each core detector, used when building explanations.
_DETECTOR_LABELS = {
    "score_zscore": "Z-score",
    "score_isoforest": "Isolation Forest",
    "score_autoencoder": "Autoencoder",
    "score_rule": "Rule-based",
}


def _build_explanation(row, top_n: int = 2) -> str:
    """Pick the top_n highest-scoring core detectors for this record and
    format them as a short human-readable string, then append a note
    about graph context if it meaningfully moved the score, e.g.
    'Isolation Forest (0.81), Rule-based (1.00); unfamiliar service (+0.05)'."""
    scores = {col: row[col] for col in _DETECTOR_LABELS}
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top = ranked[:top_n]
    parts = [f"{_DETECTOR_LABELS[col]} ({val:.2f})" for col, val in top if val > 0]
    explanation = ", ".join(parts) if parts else "no single detector dominant"

    graph_adj = row.get("score_graph_context", 0.0)
    if graph_adj > 0.02:
        explanation += f"; unfamiliar service (+{graph_adj:.2f})"
    elif graph_adj < -0.02:
        explanation += f"; established service ({graph_adj:.2f})"

    return explanation


def detect(features: pd.DataFrame) -> pd.DataFrame:
    """Entry point called by the orchestrator for Phase 5."""
    result = features.copy()
    stat = _statistical_score(features)
    iso_forest = _ml_score(features)
    autoencoder = _autoencoder_score(features)
    rule = _rule_score(features)
    graph_adj = _graph_context_adjustment(features)

    # Keep each detector's individual score - what makes "why was this
    # flagged?" answerable later, and what alerting.py/the dashboard use.
    result["score_zscore"] = stat
    result["score_isoforest"] = iso_forest
    result["score_autoencoder"] = autoencoder
    result["score_rule"] = rule
    result["score_graph_context"] = graph_adj

    blended = (stat + iso_forest + autoencoder + rule) / 4
    result["anomaly_score"] = (blended + graph_adj).clip(lower=0.0, upper=1.0)
    result["explanation"] = result.apply(_build_explanation, axis=1)

    print(f"[detection] scored {len(result)} records - min={result['anomaly_score'].min():.3f} mean={result['anomaly_score'].mean():.3f} max={result['anomaly_score'].max():.3f}")
    return result
