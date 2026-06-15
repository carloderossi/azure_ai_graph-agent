# graph_agent.py
## python -m src.azure_ai_graph_agent.graph_agent
import json
import sys

from pathlib import Path

import networkx as nx

from tools.search_tools import web_search, ms_docs_search
from tools.graph import load_graph, compute_louvain_communities, attach_communities_to_nodes, compute_graph_diagnostics
from tools.utils import save_investigation, log, get_month_year
from tools.llm_graph import investigate_component, investigate_isolated_node, analyze_node

from foundry_local_sdk import Configuration, FoundryLocalManager
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# -----------------------------
# Config
# -----------------------------
GRAPH_PATH = Path("azure_ai_graph.json")
APP_NAME = "cdr-foundry-local"
MODEL_ID = "phi-4-mini" #"deepseek-r1-1.5b" #"qwen2.5-0.5b"  # replace with 7B–14B model when available

# -----------------------------
# Foundry Local + LangChain setup
# -----------------------------
def init_foundry_and_llm():
    log("LLM", f"Initializing Foundry Local WebGPU- and OpenVINO- Providers..")
    config = Configuration(app_name=APP_NAME)
    FoundryLocalManager.initialize(config)
    manager = FoundryLocalManager.instance

    # Download and register execution providers
    current_ep = ""

    def ep_progress(ep_name: str, percent: float):
        nonlocal current_ep
        if ep_name != current_ep:
            if current_ep:
                print()
            current_ep = ep_name
        print(f"\r  {ep_name:<30}  {percent:5.1f}%", end="", flush=True)

    manager.download_and_register_eps(progress_callback=ep_progress)
    if current_ep:
        print()

    # Load model
    model = manager.catalog.get_model(MODEL_ID)
    model.download(
        lambda progress: print(
            f"\rDownloading model: {progress:.2f}%", end="", flush=True
        )
    )
    print()
    log("LLM", f"Loading local Model '{MODEL_ID}'...")
    model.load()
    log("LLM", f"Model '{MODEL_ID}' loaded.")
    log("LLM", f"Name: '{model.info.name}',\n Capabilities '{model.info.capabilities}',\n Modalities: {model.info.input_modalities},\n Publisher: {model.info.publisher},\n FileSize: {model.info.file_size_mb},\n ContextLength: {model.info.context_length}")

    # Start OpenAI-compatible endpoint
    manager.start_web_service()
    base_url = f"{manager.urls[0]}/v1"

    # LangChain LLM
    llm = ChatOpenAI(
        base_url=base_url,
        api_key="none",
        model=model.id,
    )

    return manager, model, llm


# -----------------------------
# Prompt / chain
# -----------------------------
NODE_ANALYSIS_SYSTEM = """
You are an expert on Azure AI, Azure ML, Azure AI Services and Microsoft Foundry (aka Azure AI Foundry) architecture.

You are given:
- A single node from a knowledge graph
- Its edges (incoming and outgoing)
- Optionally, some documentation URLs

Your tasks:
1. Decide whether this node and its edges faithfully represent Azure AI / Azure ML / Microsoft Foundry architecture {current_month}.
2. Suggest fixes to the node (definition, category, edges) if needed.
3. Suggest any additional relevant documentation URLs that should be attached to this node.

Respond in JSON with the following fields:
- "architecture_feedback": string
- "suggested_edge_changes": {{ "add_from": [], "add_to": [], "remove_from": [], "remove_to": [] }}
- "suggested_docs": [ {{ "title": "...", "url": "..." }} ]
"""

NODE_ANALYSIS_USER_TEMPLATE = """
Node:
```json
{node_json}
```
Neighbors:
```json
{neighbors_json}
```
Existing Documentation Links:
```json
{docs_json}
```
Tasks:
1. Evaluate whether this node and its incoming/outgoing edges correctly represent Azure AI, Azure Machine Learning, or Azure AI Foundry architecture.
2. Suggest missing relationships.
3. Suggest incorrect relationships that should be removed.
4. Suggest additional Microsoft Learn documentation relevant to this node.
Return ONLY valid JSON matching the schema defined in the system prompt.
"""
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", NODE_ANALYSIS_SYSTEM),
        ("user", NODE_ANALYSIS_USER_TEMPLATE),
    ]
)
# print(f"PROMPT: {prompt}")

def build_chain(llm: ChatOpenAI):
    return prompt | llm | StrOutputParser()


# -----------------------------
# Optional: use tools to enrich docs/edges
# -----------------------------
def enrich_with_tools(node, llm_feedback: dict):
    """
    Example of how you might call tools based on the model's feedback.
    Here we just derive simple queries from the node label.
    """
    label = node.get("label", "")
    category = node.get("category", "")

    #Web search for missing connections
    ws_query = f"Azure AI Foundry {label} {category} architecture dependencies"
    ws_result = web_search(ws_query)
    
    #Microsoft Docs search for more precise docs
    docs_query = f"site:learn.microsoft.com Azure AI Foundry {label}"
    docs_result = ms_docs_search(docs_query)

    return {
        "web_search": ws_result,
        "ms_docs_search": docs_result,
    }

def cleanup(model, manager):
    # Cleanup
    model.unload()
    manager.stop_web_service()
    print("Model unloaded and web service stopped.")
    sys.exit(0)


# -----------------------------
# Main loop
# -----------------------------
def main():
    # 1. Load graph
    log("GRAPH", f"Loading graph from {GRAPH_PATH}")
    nodes, G = load_graph(GRAPH_PATH)
    # print(f"Loaded {len(nodes)} nodes, {G.number_of_edges()} edges.")
    log(
        "GRAPH",
        f"Loaded {len(nodes)} nodes and {G.number_of_edges()} edges"
    )

    # 2. Compute Louvain communities
    partition = compute_louvain_communities(G)
    attach_communities_to_nodes(nodes, partition)
    print(f"Computed {len(set(partition.values()))} communities.")

    # 3. Init Foundry Local + LangChain LLM
    manager, model, llm = init_foundry_and_llm()
    llm_chain = build_chain(llm)

    diagnostics = compute_graph_diagnostics(G)
    log(
        "GRAPH", 
        f"Graph diagnostics: \n isolated_nodes: '{diagnostics["isolated_nodes"]}' \n components's nodes: '{len(diagnostics["components"])}' \n giant_component's nodes: {len(diagnostics["giant_component"])} \n secondary_components: {diagnostics["secondary_components"]}"
    )

    node_lookup = {
        n["id"]: n
        for n in nodes
        }

    #### STANDALONE nodes
    isolated_results = []
    for node_id in diagnostics["isolated_nodes"]:
        node = node_lookup[node_id]
        isolated_results.append(
            investigate_isolated_node(
                llm_chain,
                node,
                G
            )
        )

    save_investigation("isolated_nodes_analysis.json", isolated_results)

    #### Communities
    community_results = []
    for component in diagnostics["secondary_components"]:
        result = investigate_component(
            llm_chain,
            component,
            node_lookup,
            G
        )
        community_results.append(result)

    save_investigation("disconnected_communities_analysis.json", community_results)

    cleanup(model, manager)

    # Analyze each node
    updated_nodes = []
    for node in nodes:
        print(f"\n=== Analyzing node {node['id']} - {node.get('label', '')} ===")
        raw_result = analyze_node(llm_chain, node, G)
        print("Model raw result:")
        print(raw_result)

        # Try to parse JSON from model output
        try:
            feedback = json.loads(raw_result)
        except json.JSONDecodeError:
            print("Could not parse model output as JSON; keeping raw text.")
            feedback = {"raw": raw_result}

        # Optionally call tools to enrich docs/edges
        tool_enrichment = enrich_with_tools(node, feedback)
        
        #Attach feedback + tool enrichment to node for now
        node["_analysis"] = feedback
        node["_tool_enrichment"] = tool_enrichment

        updated_nodes.append(node)

    # Persist updated graph (versioned)
    out_path = GRAPH_PATH.with_name(GRAPH_PATH.stem + "_analyzed.json")
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(updated_nodes, f, indent=2, ensure_ascii=False)
        print(f"\nSaved analyzed graph to {out_path}")
    
    cleanup(model, manager)

if __name__ == "__main__":
    main()
