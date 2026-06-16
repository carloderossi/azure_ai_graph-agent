from foundry_local_sdk import Configuration, FoundryLocalManager
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate

from src.tools.graph import load_graph
from src.azure_ai_graph_agent.graph_agent import GRAPH_PATH, get_system_promt, get_user_context
from src.tools.llm_graph import analyze_node
from src.tools.search_tools import ms_docs_search

import json

## PS C:\Carlo\Azure\FoundryLocal\azure_ai_graph-agent> .venv\Scripts\activate 
# (azure_ai_graph-agent) PS C:\Carlo\Azure\FoundryLocal\azure_ai_graph-agent> python -m src.test.model_chat_test

APP_NAME = "cdr-foundry-local"
MODEL_ID = "phi-4-mini" ## "qwen3.5-2b-text"
### "qwen3.5-4b" a long useless philosofical answer
### "qwen3.5-2b-text"
## "phi-3-mini-128k" 
## "deepseek-r1-1.5b"  adds <think>....
# ### "phi-4-mini"  does not follow formatting instructions 
### "qwen2.5-coder-1.5b" same json issue as phi-4-mini
# ## "phi-3-mini-128k" same json issue as phi-4-mini
## BEST: "qwen3.5-2b-text"

config = Configuration(app_name=APP_NAME)
FoundryLocalManager.initialize(config)
manager = FoundryLocalManager.instance

# Download and register execution providers
manager.download_and_register_eps()

# Load model
model = manager.catalog.get_model(MODEL_ID)
model.download(
    lambda progress: print(
        f"\rDownloading model: {progress:.2f}%", end="", flush=True
    )
)
print()
model.load()
print(f"Model '{MODEL_ID}' loaded.")
print(f"Name: '{model.info.name}',\n Capabilities '{model.info.capabilities}',\n Modalities: {model.info.input_modalities},\n Publisher: {model.info.publisher},\n FileSize: {model.info.file_size_mb},\n ContextLength: {model.info.context_length}")

# Start OpenAI-compatible endpoint -NPU
manager.start_web_service()
base_url = f"{manager.urls[0]}/v1"

# LangChain LLM
llm = ChatOpenAI(
    base_url=base_url,
    api_key="none",
    model=model.id,
)

user_content = get_user_context()
system_prompt = get_system_promt()

#llm_chain = build_chain(llm)

#print(f"LLM CHAIN: \n{llm_chain}\n")

nodes, G = load_graph(GRAPH_PATH)
node = G.nodes["az000001"]##["az000231"]

raw_result = analyze_node(user_content, system_prompt, llm, node, G)

print("Model raw result:")
print(raw_result)

# Try to parse JSON from model output
try:
    feedback = json.loads(raw_result)
except json.JSONDecodeError as e:
    print("Could not parse model output as JSON; keeping raw text.", e)
    feedback = {"raw": raw_result}

model.unload()
manager.stop_web_service()
print("Model unloaded and web service stopped.")