"""
PHASE 6 - RISK SCORING & CLASSIFICATION

Classifies each record's anomaly score as Normal / Warning / Critical
against the configured thresholds, and - since NSL-KDD provides a real
ground-truth label - compares detections against that label so we can
report actual accuracy (recall/precision), not just "it runs".
"""

import pandas as pd

from config import WARNING_THRESHOLD, CRITICAL_THRESHOLD


def classify(score: float) -> str:
    if score >= CRITICAL_THRESHOLD:
        return "Critical"
    if score >= WARNING_THRESHOLD:
        return "Warning"
    return "Normal"


def _evaluate_against_ground_truth(result: pd.DataFrame):
    """NSL-KDD's label column is 'normal' or an attack type. Compare that
    to whether our pipeline flagged the record (Warning/Critical) to get
    real precision/recall for this batch."""
    if "label" not in result.columns:
        return

    actual_attack = result["label"] != "normal"
    predicted_attack = result["risk_level"] != "Normal"

    true_positives = (actual_attack & predicted_attack).sum()
    false_positives = (~actual_attack & predicted_attack).sum()
    false_negatives = (actual_attack & ~predicted_attack).sum()

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) else 0.0

    print(f"[scoring] accuracy this batch - precision={precision:.2f} "
          f"recall={recall:.2f} (TP={true_positives} FP={false_positives} FN={false_negatives})")


def score_and_classify(detected: pd.DataFrame) -> pd.DataFrame:
    """Entry point called by the orchestrator for Phase 6."""
    result = detected.copy()
    result["risk_level"] = result["anomaly_score"].apply(classify)
    counts = result["risk_level"].value_counts().to_dict()
    print(f"[scoring] classified {len(result)} records: {counts}")
    _evaluate_against_ground_truth(result)
    return result