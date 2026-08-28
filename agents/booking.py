from google.genai import types
from llm import get_booking_client, MODEL, today_context, clarifying_question_instructions, response_formatting_instructions
from tools.booking import (
    get_hotel_rates as _get_hotel_rates,
    prebook_rate as _prebook_rate,
    complete_booking as _complete_booking,
)
from tools.weather import get_weather

SYSTEM_PROMPT = """{today}

You are the same travel consultant, now finalizing the booking for {hotel_name} in {destination}
(check-in {checkin}, check-out {checkout}, {adults} adult(s)). This is a SANDBOX/test booking — no real
payment is ever taken, but treat the flow with the same care as a real one so the traveller can trust it.

Traveller profile:
{profile}

Other hotels from the same search that were shown to the traveller, in case the chosen one has no live rates
for these dates (id -> name): {other_hotels}

{clarifying_question_instructions}

{response_formatting_instructions}

Follow this exact sequence, one step at a time, confirming with the traveller as you go:

1. Call get_hotel_rates for the chosen hotel and these dates. Default to currency "USD" and guest_nationality
   "US" unless the traveller has told you where they're from — if they mention their home location at any
   point in the conversation, use that to pick the right 3-letter ISO currency code and 2-letter ISO
   nationality code instead. If it returns no offers, don't just stop and
   ask — automatically try the other hotels listed above (get_hotel_rates again with a different id) until
   one returns real offers, then tell the traveller plainly which hotel you ended up finding availability for
   and why ("X had no availability for those dates, so I checked Y instead"). Only ask the traveller to pick
   a different hotel themselves if none of the listed alternatives have rates either.
2. Present the price and room/rate details clearly (room name, board/meal plan, total price in the
   traveller's home currency) for whichever hotel actually has offers. Each offer has a short offer_id like
   "R1" — use that short id exactly as given when you call prebook_rate, never invent your own id.
3. Then ask this exact clickable question — never skip it, and never ask for guest details before it:
   {{"type": "clarifying_question", "stage": "hotel_confirm", "question": "Are you happy with this hotel?", "options": ["Yes, continue", "Choose another hotel"]}}
   - If they choose "Choose another hotel", call return_to_hotel_search — do not ask for guest details or
     call any other tool first.
   - If they choose "Yes, continue" (or otherwise clearly confirm), output ONLY this exact JSON and nothing
     else, with no other text before or after it, to hand off to the booking form:
     {{"type": "booking_form"}}
     Do not ask for the traveller's name/email/phone yourself in plain text — the booking form collects it.
4. Once you receive a message with the traveller's name, email, and phone (it will arrive as a follow-up
   message after the booking form), call prebook_rate with the offer_id from step 2 to lock in the final
   price. It returns a short prebook_id like "P1" — use that exact short id for the next step. Tell the
   traveller the confirmed total and ask them to explicitly confirm ("yes, book it") before going further.
5. ONLY after they clearly say yes, call complete_booking with that prebook_id and their details.
6. Once booked, confirm the booking reference clearly, and close warmly with a couple of quick, genuinely
   useful tips for the trip (you may use get_weather for a packing tip) — like a real travel agent would after
   securing a booking.

Never call complete_booking without an explicit "yes"/"confirm"/"book it" from the traveller after seeing the
final price. Never invent a price, offer_id, prebook_id, or booking reference — every number must come from a
tool result this turn. If any tool returns an error, say so plainly instead of making something up.

Keep replies SHORT and conversational.
"""


def make_agent(context):
    context.offer_lookup = {}
    context.prebook_lookup = {}

    def get_hotel_rates(
        hotel_id: str,
        check_in: str,
        check_out: str,
        currency: str,
        guest_nationality: str,
        adults: int = 2,
    ) -> dict:
        """Get real room rates/offers for one hotel, priced in the traveller's home currency.
        Returns a short list of options, each with a short offer_id to use in prebook_rate — never
        the raw provider offer string.

        Args:
          hotel_id: the hotel id (from search_hotels or the alternatives list)
          check_in: check-in date, YYYY-MM-DD
          check_out: check-out date, YYYY-MM-DD
          currency: 3-letter ISO currency code matching the traveller's home currency if known,
            e.g. "INR", "GBP", "USD", "EUR" — otherwise default to "USD"
          guest_nationality: 2-letter ISO country code matching the traveller's home country if known,
            otherwise default to "US"
          adults: number of adult guests
        """
        result = _get_hotel_rates(hotel_id, check_in, check_out, adults, guest_nationality, currency)
        if "error" in result:
            return result

        options = []
        for hotel in (result.get("raw") or {}).get("data") or []:
            for room in hotel.get("roomTypes") or []:
                offer_id = room.get("offerId")
                if not offer_id:
                    continue
                short_id = f"R{len(context.offer_lookup) + 1}"
                context.offer_lookup[short_id] = offer_id
                for rate in room.get("rates") or []:
                    total = ((rate.get("retailRate") or {}).get("total") or [{}])[0]
                    options.append({
                        "offer_id": short_id,
                        "hotel_id": hotel_id,
                        "room_name": rate.get("name"),
                        "board": rate.get("boardName"),
                        "price": total.get("amount"),
                        "currency": total.get("currency"),
                    })
                break  # one offer alias per room type is enough detail for the model

        if not options:
            return {"offers": [], "note": "No available offers for this hotel/these dates."}
        return {"offers": options, "source": "liteapi.travel (live)"}

    def prebook_rate(offer_id: str) -> dict:
        """Lock in a rate offer and get the final confirmed price before booking. Returns a short
        prebook_id to use in complete_booking.

        Args:
          offer_id: the short offer_id (e.g. "R1") from a get_hotel_rates result
        """
        real_offer_id = context.offer_lookup.get(offer_id)
        if not real_offer_id:
            return {"error": f"Unknown offer_id {offer_id!r} — use an offer_id exactly as given by get_hotel_rates."}

        result = _prebook_rate(real_offer_id)
        if "error" in result:
            return result

        data = (result.get("raw") or {}).get("data") or {}
        short_id = f"P{len(context.prebook_lookup) + 1}"
        context.prebook_lookup[short_id] = data.get("prebookId")

        return {
            "prebook_id": short_id,
            "hotel_id": data.get("hotelId"),
            "checkin": data.get("checkin"),
            "checkout": data.get("checkout"),
            "currency": data.get("currency"),
            "total_price": data.get("price"),
            "source": "liteapi.travel (live)",
        }

    def complete_booking(prebook_id: str, first_name: str, last_name: str, email: str, phone: str) -> dict:
        """Complete the (sandbox — no real charge) booking. Only call after the traveller has
        explicitly confirmed they want to book, with the final price already shown to them.

        Args:
          prebook_id: the short prebook_id (e.g. "P1") from a prebook_rate result
          first_name: guest first name
          last_name: guest last name
          email: guest email
          phone: guest phone number
        """
        real_prebook_id = context.prebook_lookup.get(prebook_id)
        if not real_prebook_id:
            return {"error": f"Unknown prebook_id {prebook_id!r} — use a prebook_id exactly as given by prebook_rate."}

        result = _complete_booking(real_prebook_id, first_name, last_name, email, phone)
        if "error" in result:
            return result

        data = (result.get("raw") or {}).get("data") or {}
        context.booking_confirmation = data.get("bookingId") or data
        return {
            "booking_id": data.get("bookingId"),
            "status": data.get("status"),
            "source": "liteapi.travel (live, sandbox — not a real charge)",
        }

    def return_to_hotel_search() -> str:
        """Call when the traveller wants to choose a different hotel instead of this one
        (answers "Choose another hotel"). Do not call this after guest details have been
        collected — only right after presenting the price/room, before the booking form."""
        context.selected_hotel_id = None
        context.selected_hotel_name = None
        context.stage = "HOTEL_SEARCH"
        return "Returning to hotel recommendations."

    other_hotels = {
        hid: name
        for hid, name in (context.known_hotels or {}).items()
        if hid != context.selected_hotel_id
    }

    client = get_booking_client()
    chat = client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT.format(
                today=today_context(),
                hotel_name=context.selected_hotel_name,
                destination=context.destination,
                checkin=context.checkin,
                checkout=context.checkout,
                adults=context.adults,
                profile=context.profile,
                other_hotels=other_hotels or "none",
                clarifying_question_instructions=clarifying_question_instructions("hotel_confirm"),
                response_formatting_instructions=response_formatting_instructions(),
            ),
            tools=[get_hotel_rates, prebook_rate, complete_booking, get_weather, return_to_hotel_search],
        ),
    )
    return chat
