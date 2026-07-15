"""
PHASE 3 — CONTEXT RETRIEVAL (the MemGraph layer)

Real job: before judging a record as normal/anomalous, look up what's
already known about the device/session it belongs to — profile, history,
prior incidents, connected devices, network topology, reputation, threat
intel, compliance rules.

STATUS: stub. Using NetworkX (in-memory graph, zero setup) for now — per
ADR-001 this can be swapped for Memgraph (Docker) later without changing
the function signature below.

TODO (build this next, after Phase 2 is solid):
  1. Build a small NetworkX graph in `_build_graph()` below: nodes = devices
     / IPs / services from the dataset, edges = "communicated with" /
     "same service" relationships.
  2. In `get_context()`, look up the node for each record's device and
     return its attributes (degree = how connected, past-anomaly count,
     etc.) as a dict.
  3. Once ingestion.py has real device IDs (not just src_bytes/service),
     use those as node keys instead of a placeholder.
"""

import networkx as nx
import pandas as pd

_graph = nx.Graph()  # TODO: populate with real device/service relationships


def _build_graph():
    """TODO: construct nodes/edges from historical data. Currently empty —
    get_context() below falls back to a neutral default until this is built.
    """
    pass


def get_context(batch: pd.DataFrame) -> pd.DataFrame:
    """Entry point called by the orchestrator for Phase 3.
    Currently a pass-through: attaches a neutral placeholder context column
    so downstream phases have something to read, without breaking anything
    once real context lookups are added here.
    """
    batch = batch.copy()
    batch["_context_known"] = False  # TODO: True once _build_graph() is real
    print(f"[context] (stub) passed {len(batch)} records through unchanged")
    return batch
