import json
from pathlib import Path

import networkx as nx
import community as community_louvain

# -----------------------------
# Graph utilities
# -----------------------------

def compute_graph_diagnostics(G: nx.DiGraph):
    """
    Returns:
        isolated_nodes
        connected_components
        giant_component
        secondary_components
    """

    undirected = G.to_undirected()

    isolated_nodes = [
        n
        for n in G.nodes()
        if G.degree(n) == 0
    ]

    components = list(nx.connected_components(undirected))
    components.sort(key=len, reverse=True)

    giant_component = components[0]

    secondary_components = components[1:]

    return {
        "isolated_nodes": isolated_nodes,
        "components": components,
        "giant_component": giant_component,
        "secondary_components": secondary_components,
    }

def load_graph(path: Path):
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    G = nx.DiGraph()
    for node in data:
        node_id = node["id"]
        G.add_node(node_id, **node)

    # edges from "from" and "to"
    for node in data:
        src = node["id"]
        for parent in node.get("from", []):
            G.add_edge(parent, src)
        for child in node.get("to", []):
            G.add_edge(src, child)

    return data, G


def compute_louvain_communities(G: nx.DiGraph):
    # Louvain expects an undirected graph
    undirected = G.to_undirected()
    partition = community_louvain.best_partition(undirected)
    # partition: dict node_id -> community_id
    return partition

def attach_communities_to_nodes(nodes, partition):
    for node in nodes:
        node_id = node["id"]
        node["community_id"] = partition.get(node_id, None)

