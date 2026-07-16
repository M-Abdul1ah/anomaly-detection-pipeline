"""
ORCHESTRATOR — wires Phases 1-9 together in sequence, matching the workflow
in the Documentation & Architecture doc. Run this file to see the whole
skeleton execute end to end.

Each phase function is imported from its own module so this file stays a
thin sequence of calls — the logic lives in src/<phase>.py, not here.
"""

from src.ingestion import load_dataset, stream_batches
from src.preprocessing import preprocess_batch
from src.context import get_context
from src.feature_engineering import build_features
from src.detection import detect
from src.scoring import score_and_classify
from src.alerting import generate_alerts
from src.response import respond
from src.mlops import log_cycle


def run_pipeline():
    data = load_dataset()

    for i, raw_batch in enumerate(stream_batches(data)):
        print(f"\n=== batch {i} ({len(raw_batch)} records) ===")
        clean = preprocess_batch(raw_batch)
        enriched = get_context(clean)
        features = build_features(enriched)
        scored = detect(features)
        classified = score_and_classify(scored)
        alerts = generate_alerts(classified)
        responded = respond(alerts)
        log_cycle(responded, scored)

        if i == 4:  # limit to a few batches for a quick demo run
            break


if __name__ == "__main__":
    run_pipeline()
