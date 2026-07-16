"""
PHASE 9 — CONTINUOUS LEARNING & MLOPS
Real job: evaluate detection performance, collect feedback, retrain and
validate models, update the model registry, check for drift, update the
MemGraph knowledge base, and deploy the improved system — closing the loop
back to Phase 1.
STATUS: Step 1 done — every cycle's metrics are now tracked in MLflow
(local, no server/Docker needed). Drift checks and auto-retraining are
still TODO.
TODO (build only after everything else works):
  2. Add a simple drift check: compare this batch's feature means/stds
     against the training set's; log a warning if they've moved a lot.
  3. Only once 1-2 work: wire this into a GitHub Actions workflow so
     retraining runs automatically on push (this is the last milestone in
     the roadmap, not the first).
"""
import pandas as pd
import mlflow

mlflow.set_experiment("anomaly-detection-pipeline")


def log_cycle(responded: pd.DataFrame, scored: pd.DataFrame) -> None:
    """Entry point called by the orchestrator for Phase 9."""
    with mlflow.start_run():
        mlflow.log_metric("batch_size", len(scored))
        mlflow.log_metric("responses_routed", len(responded))
        if "anomaly_score" in scored.columns and len(scored) > 0:
            mlflow.log_metric("anomaly_score_mean", float(scored["anomaly_score"].mean()))
            mlflow.log_metric("anomaly_score_max", float(scored["anomaly_score"].max()))
            mlflow.log_metric("anomaly_score_min", float(scored["anomaly_score"].min()))

    print(f"[mlops] end of cycle — {len(responded)} responses logged, "
          f"metrics tracked in MLflow (run `mlflow ui` to view)")