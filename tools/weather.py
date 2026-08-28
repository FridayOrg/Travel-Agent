import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def geocode_city(city: str) -> dict | None:
    resp = requests.get(GEOCODE_URL, params={"name": city, "count": 1}, timeout=10)
    resp.raise_for_status()
    results = resp.json().get("results")
    if not results:
        return None
    r = results[0]
    return {"name": r["name"], "country": r.get("country"), "lat": r["latitude"], "lon": r["longitude"]}


def get_weather(city: str) -> dict:
    """Real-time + forecast weather for a city. Returns raw data, no invented values."""
    print(f"  [TOOL CALL] get_weather(city={city!r})")
    place = geocode_city(city)
    if not place:
        return {"error": f"Could not find location: {city}"}

    resp = requests.get(
        FORECAST_URL,
        params={
            "latitude": place["lat"],
            "longitude": place["lon"],
            "current": "temperature_2m,weather_code,wind_speed_10m",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
            "forecast_days": 7,
            "timezone": "auto",
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    return {
        "location": place,
        "current": data.get("current"),
        "daily_forecast": data.get("daily"),
        "source": "open-meteo.com (live)",
    }


if __name__ == "__main__":
    import json
    result = get_weather("Istanbul")
    print(json.dumps(result, indent=2))
