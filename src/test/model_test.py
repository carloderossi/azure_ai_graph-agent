from foundry_local_sdk import Configuration, FoundryLocalManager
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

APP_NAME = "cdr-foundry-local"
MODEL_ID = "phi-4-mini" 

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

# Start OpenAI-compatible endpoint
manager.start_web_service()
base_url = f"{manager.urls[0]}/v1"

# LangChain LLM
llm = ChatOpenAI(
    base_url=base_url,
    api_key="none",
    model=model.id,
)

