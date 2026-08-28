import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trip_context import TripContext
from agents import booking
from tools.hotels import search_hotels
from llm import send_with_retry


def main():
    context = TripContext()
    context.profile = {
        "origin_location": "Mumbai, India",
        "travel_scope": "different country",
        "dates": "September, 5 days",
        "duration_days": 5,
        "budget_level": "mid-range",
        "party": "couple",
        "purpose": "relaxation",
        "climate_style": "warm coastal",
        "food_nightlife_culture": "food and nightlife",
        "luxury_vs_value": "mid-range",
        "notes": "",
    }
    context.destination = "Valencia, Spain"
    context.destination_reason = "warm, relaxed, good food"
    context.checkin = "2026-09-10"
    context.checkout = "2026-09-15"
    context.adults = 2

    results = search_hotels("Valencia", "ES", context.checkin, context.checkout, context.adults)
    hotels = results.get("raw", {}).get("data", [])[:3]
    context.known_hotels = {h["id"]: h.get("name") for h in hotels}
    first_id, first_name = next(iter(context.known_hotels.items()))
    context.selected_hotel_id = first_id
    context.selected_hotel_name = first_name

    print(f"Selected hotel: {first_name} ({first_id})\n")

    chat = booking.make_agent(context)
    reply = send_with_retry(chat, "Please find rates and show me the price.")
    print(f"AGENT: {reply.text}\n")


if __name__ == "__main__":
    main()
