from tavily import TavilyClient
from config import TAVILY_API_KEY

_client = None


def _get_client():
    global _client
    if _client is None:
        if not TAVILY_API_KEY:
            raise RuntimeError("TAVILY_API_KEY is missing from .env")
        _client = TavilyClient(api_key=TAVILY_API_KEY)
    return _client


def web_search(query: str, max_results: int = 5) -> dict:
    """Live web search. Returns raw results (title, url, content snippet) — no invented facts."""
    print(f"  [TOOL CALL] web_search(query={query!r})")
    client = _get_client()
    response = client.search(query=query, max_results=max_results, search_depth="advanced")
    results = [
        {"title": r.get("title"), "url": r.get("url"), "snippet": r.get("content")}
        for r in response.get("results", [])
    ]
    return {"query": query, "results": results, "source": "tavily.com (live)"}


if __name__ == "__main__":
    import json
    result = web_search("best neighborhoods to stay in Istanbul for nightlife and food")
    print(json.dumps(result, indent=2))
