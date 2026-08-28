"""Image Agent — retrieves real, verifiable images for destinations/attractions and hotels.

Deliberately NOT an LLM agent: there is no reasoning or generation step here, only grounded
lookups against real sources (LiteAPI's own per-hotel photos, Tavily's live image search).
This keeps zero hallucination risk in what actually gets shown to the traveller — if a source
has no real image for an entity, that entity gets an honest "no verified image" result instead
of a guess.
"""
from tools.images import search_place_images

_cache: dict[str, list[dict]] = {}


def _cached_search(query: str, max_results: int) -> list[dict]:
    key = query.strip().lower()
    if key not in _cache:
        _cache[key] = search_place_images(query, max_results=max_results)
    return _cache[key]


def get_destination_images(place_name: str, context_hint: str | None = None, max_results: int = 3) -> dict:
    """Real images for a destination or a specific attraction/place within it.

    Args:
      place_name: the exact place/attraction name (e.g. "Burj Khalifa", or a city like "Dubai")
      context_hint: extra disambiguating context, e.g. the destination city, so a search for an
        attraction doesn't collide with a same-named place elsewhere
    """
    query = place_name
    if context_hint and context_hint.strip().lower() not in place_name.lower():
        query = f"{place_name} {context_hint}"
    images = _cached_search(query, max_results)
    return {"label": place_name, "images": images}


def get_hotel_images(hotel_id: str, hotel_name: str, known_hotels_raw: dict, max_results: int = 2) -> dict:
    """Real images for one specific hotel property.

    Prioritizes LiteAPI's own photo data for that exact hotel_id (guaranteed to match the real
    property, since it's tied directly to the id LiteAPI itself returned) over a generic name
    search. Only falls back to a grounded web image search (hotel name + city, never a generic
    "hotels in <city>" query) if LiteAPI had no photo for that property.
    """
    raw = (known_hotels_raw or {}).get(hotel_id) or {}
    images = []
    if raw.get("main_photo"):
        images.append({"url": raw["main_photo"], "caption": hotel_name, "source_title": "liteapi.travel"})
    if raw.get("thumbnail") and raw.get("thumbnail") != raw.get("main_photo"):
        images.append({"url": raw["thumbnail"], "caption": hotel_name, "source_title": "liteapi.travel"})

    if not images:
        query = hotel_name + (f" {raw['city']}" if raw.get("city") else "")
        images = _cached_search(query, max_results)

    return {"label": hotel_name, "images": images[:max_results]}
