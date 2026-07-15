"""
PHASE 3 - CONTEXT RETRIEVAL (the MemGraph layer)

Builds a graph of service/protocol relationships as records flow through,
and looks up each record's history in that graph before scoring it -
standing in for MemGraph until Memgraph/Docker is available.

Nodes = service types and protocol types seen so far.
Edges = "this service was used over this protocol" relationships.
Each service node tracks how many times it's been seen (seen_count) - a
simple stand-in for "historical baseline" from the architecture doc.
"""

import networkx as nx
import pandas as pd

_graph = nx.Graph()


def _ensure_node(node_id, node_type):
    if node_id not in _graph:
        _graph.add_node(node_id, type=node_type, seen_count=0)


def _update_graph(batch: pd.DataFrame):
    """Grow the graph with this batch's records - called AFTER context is
    read for this batch, so a record never sees itself in its own history."""
    for _, row in batch.iterrows():
        service = f"service:{row.get('service', 'unknown')}"
        protocol = f"protocol:{row.get('protocol_type', 'unknown')}"
        _ensure_node(service, "service")
        _ensure_node(protocol, "protocol")
        _graph.add_edge(service, protocol)
        _graph.nodes[service]["seen_count"] += 1


def get_context(batch: pd.DataFrame) -> pd.DataFrame:
    """Entry point called by the orchestrator for Phase 3.
    Attaches, per record: how many times this service has been seen
    before (seen_count) and how many distinct protocols it connects to
    (degree) - real graph-based context, not a placeholder.
    """
    batch = batch.copy()
    seen_counts, degrees = [], []
    for _, row in batch.iterrows():
        service = f"service:{row.get('service', 'unknown')}"
        if service in _graph:
            seen_counts.append(_graph.nodes[service]["seen_count"])
            degrees.append(_graph.degree[service])
        else:
            seen_counts.append(0)
            degrees.append(0)

    _update_graph(batch)

    batch["_context_service_seen_count"] = seen_counts
    batch["_context_service_degree"] = degrees
    print(f"[context] graph now has {_graph.number_of_nodes()} nodes; "
          f"attached history for {len(batch)} records")
    return batch