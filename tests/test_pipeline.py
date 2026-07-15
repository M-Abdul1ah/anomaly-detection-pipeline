"""
Smoke tests — just check each phase's entry point runs and returns the right
shape of data, without checking correctness yet (there's nothing to check
correctness of until the TODOs in detection.py etc. are filled in).

Run with: pytest
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion import load_dataset, stream_batches
from src.preprocessing import preprocess_batch
from src.context import get_context
from src.feature_engineering import build_features
from src.detection import detect
from src.scoring import score_and_classify
from src.alerting import generate_alerts
from src.response import respond


def test_full_pipeline_runs_end_to_end():
    data = load_dataset()
    batch = next(stream_batches(data))

    clean = preprocess_batch(batch)
    enriched = get_context(clean)
    features = build_features(enriched)
    scored = detect(features)
    assert "anomaly_score" in scored.columns

    classified = score_and_classify(scored)
    assert "risk_level" in classified.columns
    assert set(classified["risk_level"]).issubset({"Normal", "Warning", "Critical"})

    alerts = generate_alerts(classified)
    responded = respond(alerts)
    assert len(responded) == len(alerts)
