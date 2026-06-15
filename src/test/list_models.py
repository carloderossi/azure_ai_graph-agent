from foundry_local_sdk import Configuration, FoundryLocalManager

def list_models(manager):
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

    # list the models currently cached on the system
    cached = manager.catalog.get_cached_models()
    print("\nCached models:")
    print("Alias (name, capabilities, modalities, publisher, file size mb, context length)")
    for m in cached:
        print(f" - {m.info.alias} ({m.info.name}, {m.info.capabilities}, {m.info.input_modalities}, {m.info.publisher}, {m.info.file_size_mb}, {m.info.context_length})")

    print()
    # list the Foundry Local models available for download    
    available = manager.catalog.list_models()

    # sort alphabetically by alias
    available_sorted = sorted(available, key=lambda m: m.info.alias.lower())

    def fmt(n: int) -> str:
        return f"{n:,}".replace(",", "'")

    available = manager.catalog.list_models()
    available_sorted = sorted(available, key=lambda m: m.info.alias.lower())

    print("Available models:")
    print("Alias (name, capabilities, modalities, publisher, file size mb, context length)")
    for m in available_sorted:
        print(
            f" - {m.info.alias} "
            f"({m.info.name}, {m.info.capabilities}, {m.info.input_modalities}, " 
            f"{m.info.publisher}, {fmt(m.info.file_size_mb)}, {fmt(m.info.context_length)})"
        )


if __name__ == "__main__":
    # Initialize the Foundry Local SDK
    config = Configuration(app_name="foundry_local_samples") # C:\Users\carlo\.foundry_local_samples\cache\models\Microsoft
    FoundryLocalManager.initialize(config)
    manager = FoundryLocalManager.instance
    list_models(manager)
