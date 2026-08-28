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


def search_place_images(query: str, max_results: int = 4) -> list[dict]:
    """Live image search for a real place/attraction/hotel. Returns real, source-attributed
    image URLs pulled from actual indexed web pages — never generated or generic stock images.
    """
    print(f"  [TOOL CALL] search_place_images(query={query!r})")
    client = _get_client()
    response = client.search(
        query=query,
        max_results=max_results,
        search_depth="basic",
        include_images=True,
        include_image_descriptions=True,
    )
    images = response.get("images") or []
    return [
        {
            "url": img.get("url"),
            "caption": img.get("description"),
            "source_title": img.get("title"),
        }
        for img in images
        if img.get("url")
    ][:max_results]


if __name__ == "__main__":
    import json
    print(json.dumps(search_place_images("Burj Khalifa Dubai"), indent=2))
