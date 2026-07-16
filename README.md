# AI-Based Network / Modem Anomaly Detection Pipeline

A 9-phase anomaly detection pipeline, built as a modular monolith (one module per
phase) per ADR-001. All 9 phases are implemented and wired into the orchestrator,
running end to end on real NSL-KDD data (with a synthetic fallback if the dataset
isn't present):

1. `src/ingestion.py` — loads real data or generates a synthetic fallback stream
2. `src/preprocessing.py` — basic cleaning/scaling
3. `src/context.py` — NetworkX graph, service/protocol context lookups
4. `src/feature_engineering.py` — rolling-window features
5. `src/detection.py` — Z-score + Isolation Forest + rule-based detectors
6. `src/scoring.py` — ensemble scoring (`config.py`: WARNING ≥ 0.3, CRITICAL ≥ 0.55)
7. `src/alerting.py` — SQLite alert log + dedup
8. `src/response.py` — response routing by severity
9. `src/mlops.py` — MLflow tracking per cycle

## Architecture

The pipeline runs as a modular monolith — each stage lives in its own file under `src/`, orchestrated by `pipeline.py`, and repeats every monitoring cycle.

```mermaid
flowchart TD
    A["<b>Data Ingestion</b><br/>real logs or synthetic<br/>→ raw records"]
    B["<b>Feature Engineering</b><br/>feature_engineering.py<br/>→ rolling-window features"]
    C["<b>Detection Engine</b><br/>detection.py<br/>Z-score + Isolation Forest + rule-based<br/>→ per-detector scores"]
    D["<b>Ensemble Scoring</b><br/>config.py<br/>WARNING ≥ 0.3, CRITICAL ≥ 0.55<br/>→ combined risk score"]
    E["<b>Context Enrichment</b><br/>context.py<br/>NetworkX service/protocol graph<br/>→ enriched score + history"]
    F["<b>Alerting</b><br/>alerting.py<br/>SQLite log + dedup<br/>→ alert record"]
    G["<b>Response Routing</b><br/>response.py<br/>→ action taken"]
    H["<b>MLOps Logging</b><br/>mlops.py<br/>MLflow local tracking<br/>→ cycle metrics"]

    A --> B --> C --> D --> E --> F --> G --> H
    H -.->|next monitoring cycle| A

    classDef infra fill:#E1F5EE,stroke:#0F6E56,color:#04342C;
    classDef ml fill:#FAECE7,stroke:#993C1D,color:#4A1B0C;
    class A,B,E,F,G,H infra;
    class C,D ml;
```

### How the code executes each cycle

```mermaid
sequenceDiagram
    participant P as pipeline.py
    participant I as Ingestion
    participant FE as feature_engineering.py
    participant D as detection.py
    participant CFG as config.py
    participant CX as context.py
    participant AL as alerting.py
    participant R as response.py
    participant ML as mlops.py

    loop Every monitoring cycle
        P->>I: get next record
        I-->>P: raw data
        P->>FE: extract rolling-window features
        FE-->>P: features
        P->>D: detect(features)
        D-->>P: zscore, isolation_forest, rule scores
        P->>CFG: combine ensemble score
        CFG-->>P: risk_score
        P->>CX: enrich(risk_score, features)
        CX-->>P: enriched score + history
        P->>P: classify vs WARNING/CRITICAL thresholds
        P->>AL: log_alert(enriched, classification)
        AL-->>P: alert record (or dedup skip)
        P->>R: route(alert)
        R-->>P: responded
        P->>ML: log_cycle(responded, scored)
        ML-->>P: metrics logged to MLflow
    end
```
## Setup (all free, no Docker required)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
```

## Dataset

This project uses **NSL-KDD**, a well-known free/public network-intrusion
dataset (a solid stand-in for "modem/network telemetry" — it's per-connection
records with duration, protocol, byte counts, error rates, etc., which is the
same shape of data a real ISP pipeline would ingest).

1. Download `KDDTrain+.txt` from the official mirror:
https://www.unb.ca/cic/datasets/nsl.html
(or any of the GitHub mirrors, e.g. `jmnwong/NSL-KDD-Dataset`)
2. Place it at `data/raw/KDDTrain+.txt`

**Don't have it downloaded yet?** That's fine — `src/ingestion.py` auto-generates
a small synthetic dataset with the same 41-column NSL-KDD schema if the real
file isn't found, so the whole pipeline runs today. Swap in the real file
whenever you have it; nothing else changes.

## Run it

```bash
python -m src.pipeline
```

You should see each of the 9 phases print what it received and passed on —
that's the skeleton working. Each `TODO` in `src/` is one build session.

## Why these choices (see full ADR in the Documentation \& Architecture doc)

* **Modular monolith, not microservices** — one codebase, one laptop, no infra cost.
* **NetworkX before Memgraph** — zero setup; swap in Memgraph (Docker) later if needed.
* **SQLite before PostgreSQL** — zero setup; same upgrade path.
* **No message broker yet** — `ingestion.py` simulates a stream with a Python
generator; swap in MQTT/Kafka later without touching downstream code.



\## Documentation



Full workflow documentation and the architecture decision record (tech

stack, diagrams, roadmap) are in `docs/anomaly\_detection\_documentation\_and\_architecture.txt`.



The day-by-day GitHub development plan is in `docs/anomaly\_detection\_github\_development\_plan.txt`.

