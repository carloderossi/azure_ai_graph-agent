from foundry_local_sdk import Configuration, FoundryLocalManager

def ask_question(messages, client, model):
    print(f"Messages {messages} - client {client} - model {model}")
    try:
        for chunk in client.complete_streaming_chat(messages):
            # Skip chunks with no choices
            if not chunk.choices:
                continue
            choice = chunk.choices[0]
            # Skip chunks with no delta
            delta = getattr(choice, "delta", None)
            if delta is None:
                continue

            # Extract content safely
            content = getattr(delta, "content", None)
            if not content:
                continue

            print(content, end="", flush=True)
    except Exception as e:            
        print(e)
    print()
    # Clean up
    model.unload()
    print("Model unloaded.")


def load_model(manager, MODEL_NAME):
    print(f"Loading {MODEL_NAME}...")
    model = manager.catalog.get_model(MODEL_NAME)
    # model.download(
    #     lambda progress: print(
    #         f"\rDownloading model: {progress:.2f}%",
    #         end="",
    #         flush=True,
    #     )
    # )
    print()
    model.load()
    print(f"Model '{model.info.name}' loaded and ready.\n")

    # Get a chat client
    client = model.get_chat_client()    
    return model, client

def main():
    # Initialize the Foundry Local SDK
    config = Configuration(app_name="foundry_local_samples")
    FoundryLocalManager.initialize(config)
    manager = FoundryLocalManager.instance

    # Download and register all execution providers.
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

    # Select and load a model from the catalog
    MODEL1_NAME = "phi-4-mini-reasoning" #"deepseek-r1-7b" #"qwen2.5-0.5b"
    MODEL2_NAME = "qwen2.5-7b"
    print(f"\nDownloading and loading models: '{MODEL1_NAME}' '{MODEL2_NAME}' ...")

    USER_QUERY = "What is the golden ratio?"
    print(f"User query: {USER_QUERY}")

    # Create the conversation messages
    messages = [
        {"role": "user", "content": USER_QUERY}
    ]


    model1, client1 = load_model(manager, MODEL1_NAME)
    ask_question(messages, client1, model1)
    
    # model2, client2 = load_model(manager, MODEL2_NAME)
    # ask_question(messages, client2, model2)


if __name__ == "__main__":
    main()