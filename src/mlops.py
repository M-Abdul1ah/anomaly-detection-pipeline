"""
PHASE 9 — CONTINUOUS LEARNING & MLOPS

Real job: evaluate detection performance, collect feedback, retrain and
validate models, update the model registry, check for drift, update the
MemGraph knowledge base, and deploy the improved system — closing the loop
back to Phase 1.

STATUS: stub. Build this LAST — it needs Phases 5-8 to be real first, since
there's nothing meaningful to retrain on until then.

TODO (build only after everything else works):
  1. Wrap Phase 5's IsolationForest training in an MLflow run
     (`mlflow.start_run()` / `mlflow.log_metric()` / `mlflow.sklearn.log_model()`)
     so every retrain is tracked — `pip install mlflow` is already in
     requirements.txt, no server/Docker needed, it runs locally.
  2. Add a simple drift check: compare this batch's feature means/stds
     against the training set's; log a warning if they've moved a lot.
  3. Only once 1-2 work: wire this into a GitHub Actions workflow so
     retraining runs automatically on push (this is the last milestone in
     the roadmap, not the first).
"""

import pandas as pd


def log_cycle(responded: pd.DataFrame) -> None:
    """Entry point called by the orchestrator for Phase 9."""
    print(f"[mlops] (stub) end of cycle — {len(responded)} responses logged, "
          f"nothing retrained yet (see TODOs in this file)")
