# AI-Based Network / Modem Anomaly Detection Pipeline

A 9-phase anomaly detection pipeline, built as a modular monolith (one module per
phase) per ADR-001. This is the **skeleton** — every phase is wired into the
orchestrator and runs end to end today, but most phases are stubs with clear
`TODO`s. Fill them in one at a time, in this order:

1. `src/ingestion.py` — already functional (loads real data or generates a
   synthetic fallback stream)
2. `src/preprocessing.py` — already functional (basic cleaning/scaling)
3. `src/context.py` — stub (NetworkX graph — build device/context lookups)
4. `src/feature_engineering.py` — stub (turn cleaned rows into model features)
5. `src/detection.py` — stub (statistical + ML anomaly detectors)
6. `src/scoring.py` — stub (combine detector outputs into a risk score)
7. `src/alerting.py` — stub (turn Warning/Critical scores into alerts)
8. `src/response.py` — stub (log automated/manual response actions)
9. `src/mlops.py` — stub (retraining/tracking hooks — do this last)

## Setup (all free, no Docker required)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
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

## Why these choices (see full ADR in the Documentation & Architecture doc)

- **Modular monolith, not microservices** — one codebase, one laptop, no infra cost.
- **NetworkX before Memgraph** — zero setup; swap in Memgraph (Docker) later if needed.
- **SQLite before PostgreSQL** — zero setup; same upgrade path.
- **No message broker yet** — `ingestion.py` simulates a stream with a Python
  generator; swap in MQTT/Kafka later without touching downstream code.
