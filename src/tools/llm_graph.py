import json
import networkx as nx

from foundry_local_sdk import Configuration, FoundryLocalManager
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from tools.utils import log, get_month_year

# -----------------------------
# Node analysis
# -----------------------------
def get_node_neighbors(G: nx.DiGraph, node_id: str):
    incoming = list(G.predecessors(node_id))
    outgoing = list(G.successors(node_id))
    return {"incoming": incoming, "outgoing": outgoing}

def analyze_node(llm_chain, node, G: nx.DiGraph):
    node_json = json.dumps(node, indent=2)
    neighbors = get_node_neighbors(G, node["id"])
    neighbors_json = json.dumps(neighbors, indent=2)
    docs_json = json.dumps(node.get("docs_links", []), indent=2)

    #log("LLM", f"Analyzing node '{node}' \n node_json: '{node_json}' \n neighbors_json: '{neighbors_json}' \n docs_json: {docs_json}")
    log("LLM", f"Analyzing node '{node["id"]}' '{node["label"]}'")

    result = llm_chain.invoke(
        {
            "node_json": node_json,
            "neighbors_json": neighbors_json,
            "docs_json": docs_json,
            "current_month": get_month_year(),
        }
    )
    print(f"res='{result}'")
    return result

COMMUNITY_SYSTEM = """
You are an Azure AI Foundry architecture expert.
The following node belongs to a disconnected graph component.

Your task:
1. Determine where this node should connect
   into the main Azure AI ecosystem.
2. Suggest missing parent nodes.
3. Suggest missing child nodes.
4. Suggest Azure documentation
   supporting those connections.
Return JSON only.
"""

def investigate_component(
    llm_chain,
    component_nodes,
    node_lookup,
    G
):
    results = []

    print(
        f"\n[COMPONENT] "
        f"size={len(component_nodes)}"
    )

    for node_id in component_nodes:

        node = node_lookup[node_id]

        analysis = analyze_node(
            llm_chain,
            node,
            G
        )

        results.append({
            "node_id": node_id,
            "analysis": analysis
        })

    return results

def investigate_isolated_node(
    llm_chain,
    node,
    G
):
    print(
        f"\n[ISOLATED] {node['id']} "
        f"{node.get('label','')}"
    )

    analysis = analyze_node(
        llm_chain,
        node,
        G
    )

    return {
        "node_id": node["id"],
        "label": node.get("label"),
        "analysis": analysis
    }