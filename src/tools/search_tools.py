import requests
import urllib.parse

# -----------------------------
# Tools 
# -----------------------------
def web_search(query: str):
    """
    Real web search using DuckDuckGo Instant Answer API.
    No API key required.
    Returns structured results with title + URL.
    """
    print(f"[web_search] query={query}")

    try:
        encoded = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_redirect=1&no_html=1"

        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        results = []

        # 1. Abstract (direct answer)
        if data.get("AbstractText"):
            results.append({
                "title": data.get("Heading", "Abstract"),
                "url": data.get("AbstractURL", ""),
                "snippet": data.get("AbstractText", "")
            })

        # 2. Related topics
        for item in data.get("RelatedTopics", []):
            if isinstance(item, dict) and "Text" in item and "FirstURL" in item:
                results.append({
                    "title": item.get("Text", ""),
                    "url": item.get("FirstURL", ""),
                    "snippet": item.get("Text", "")
                })

        return {
            "query": query,
            "results": results[:10]  # limit to 10
        }

    except Exception as e:
        return {
            "query": query,
            "error": str(e),
            "results": []
        }

def ms_docs_search(query: str):
    """
    Searches Microsoft Learn documentation using the public search API.
    Returns structured results with title + URL + description.
    """
    print(f"[ms_docs_search] query={query}")

    try:
        encoded = urllib.parse.quote(query)
        url = f"https://learn.microsoft.com/api/search?search={encoded}&locale=en-us"

        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("description", "")
            })

        return {
            "query": query,
            "results": results[:10]
        }

    except Exception as e:
        return {
            "query": query,
            "error": str(e),
            "results": []
        }
