import requests
from config import LITEAPI_API_KEY

SEARCH_URL = "https://api.liteapi.travel/v3.0/data/hotels"
DETAIL_URL = "https://api.liteapi.travel/v3.0/data/hotel"


def search_hotels(city: str, country_code: str, check_in: str, check_out: str, adults: int = 2) -> dict:
    """Search real hotel availability/pricing. Returns raw results, no invented hotels.

    Args:
      city: city name, e.g. "Valencia"
      country_code: ISO 2-letter country code, e.g. "ES"
      check_in: check-in date, YYYY-MM-DD
      check_out: check-out date, YYYY-MM-DD
      adults: number of adult guests
    """
    print(f"  [TOOL CALL] search_hotels(city={city!r}, country_code={country_code!r}, "
          f"check_in={check_in!r}, check_out={check_out!r}, adults={adults})")

    if not LITEAPI_API_KEY:
        return {
            "error": "LITEAPI_API_KEY is not configured — real hotel search is not connected yet. "
                     "Do not invent hotel names, prices, or availability; tell the traveller this "
                     "step isn't wired up yet."
        }

    try:
        resp = requests.get(
            SEARCH_URL,
            params={"cityName": city, "countryCode": country_code},
            headers={"X-API-Key": LITEAPI_API_KEY},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        # A transient network/timeout/upstream error, distinct from the "not configured" case
        # above — logged with the real cause so it's diagnosable, but reported to the model in
        # the same "don't invent data, tell the traveller honestly" shape it already expects.
        print(f"  [ERROR] search_hotels request failed: {e}")
        return {
            "error": f"Hotel search request failed ({type(e).__name__}) — likely a transient "
                     "network/upstream issue, not a missing configuration. Tell the traveller "
                     "honestly that the live hotel search hit a temporary issue and ask them to "
                     "try again in a moment — do not say it isn't wired up, and do not invent "
                     "hotel names, prices, or availability."
        }
    return {"city": city, "raw": data, "source": "liteapi.travel (live)"}


def get_hotel_details(hotel_id: str) -> dict:
    """Full real content for one specific hotel: description, all real photos, star rating,
    guest review sentiment, named facilities/amenities. Returns raw data, no invented hotels.

    Args:
      hotel_id: the exact LiteAPI hotel id
    """
    print(f"  [TOOL CALL] get_hotel_details(hotel_id={hotel_id!r})")

    if not LITEAPI_API_KEY:
        return {"error": "LITEAPI_API_KEY is not configured — hotel detail lookup is not connected yet."}

    try:
        resp = requests.get(
            DETAIL_URL,
            params={"hotelId": hotel_id},
            headers={"X-API-Key": LITEAPI_API_KEY},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json().get("data") or {}
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] get_hotel_details request failed: {e}")
        return {"error": f"Hotel detail request failed ({type(e).__name__}) — a transient network/upstream issue."}
    if not data:
        return {"error": f"No hotel detail found for hotel_id {hotel_id!r}."}
    return {"data": data, "source": "liteapi.travel (live)"}


if __name__ == "__main__":
    import json
    result = search_hotels("Valencia", "ES", "2026-09-10", "2026-09-15")
    print(json.dumps(result, indent=2))
