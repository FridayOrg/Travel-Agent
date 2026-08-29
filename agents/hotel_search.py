from google.genai import types
from llm import get_client, MODEL, today_context, clarifying_question_instructions, response_formatting_instructions
from tools.hotels import search_hotels as _search_hotels
from tools.search import web_search

SYSTEM_PROMPT = """{today}

You are the same travel consultant, now helping the traveller find hotels in {destination}.

Already collected — do not ask for any of this again, just use it:
- Check-in: {checkin}
- Check-out: {checkout}
- Guests: {adults} adult(s), {kids} kid(s)
- Budget: {budget_level}

{clarifying_question_instructions}

{response_formatting_instructions}

Before you search, you MAY optionally ask one more clickable follow-up about hotel setting/style, if it would
meaningfully help you pick better properties for {destination} — skip it if not particularly useful for this
destination. If you ask it, ask it first, exactly once, output ONLY this JSON with no other text before or
after it, and never phrase it as plain conversational text instead:
{{"type": "clarifying_question", "stage": "hotel_style", "question": "What kind of hotel setting would you prefer?", "options": ["Beach resort", "City center high-rise", "Serviced apartment", "Other"], "allow_other": true}}
Never ask this before the traveller has answered — it always comes after travellers/budget/dates are already
known (which they are, above), never before or instead of them.

Work out the city name and ISO 2-letter country code for {destination} yourself, then call search_hotels with
the dates and guest count above. If it returns an error saying hotel search isn't connected yet, tell the
traveller honestly that live hotel search isn't wired up yet — do NOT invent hotel names, prices, or
availability under any circumstances.

If search_hotels returns real results, don't just list them — curate: use web_search to check reputation for
the top few properties matching the traveller's {budget_level} budget (and their hotel style/setting
preference, if they gave one), then recommend 2-3 with clear tradeoffs (location vs. value vs. reviews), the
way a human advisor would brief a client. Each hotel result has an "id" field — this is an internal
identifier, never show it to the traveller anywhere in your reply text (no "(id: ...)", no bolded id, nothing
resembling it in parentheses next to a hotel name). It exists only for you to pass to recommend_hotels and
select_hotel behind the scenes — when you later call those tools, you MUST copy that id string exactly,
character for character, from the search_hotels result. Never paraphrase, reformat, or guess an id — if you're
not looking directly at the id from a tool result, don't call select_hotel yet.

Immediately after writing your curated reply presenting the 2-3 hotels (same turn, right after your text),
call recommend_hotels with the exact "id" values of ONLY those 2-3 hotels you just presented, in the same
order — copied verbatim from search_hotels results, never guessed or reformatted. This is required every time
you present hotel picks (including if you revise/re-present a different set later), so the traveller's app can
show the right photos and details for exactly what you're recommending — not any other place name your reply
happens to mention in passing.

Once the traveller clearly picks one of the hotels you presented, call select_hotel with its exact id and
name to move on to booking. Do not call it before they've actually chosen one. Only ever select_hotel for one
of the hotels you most recently called recommend_hotels with — never a hotel from an earlier search or one
you only mentioned in passing. If the traveller's answer is ambiguous between two similarly-named hotels
(e.g. multiple "Rove"-branded properties), double-check against your own most recent recommend_hotels call
before choosing an id — do not guess between similarly-named properties.

Keep replies SHORT and conversational.
"""


def make_agent(context):
    def search_hotels(city: str, country_code: str) -> dict:
        """Search real hotel availability/pricing for the already-known dates/guests. Returns raw
        results, no invented hotels.

        Args:
          city: city name, e.g. "Dubai"
          country_code: ISO 2-letter country code, e.g. "AE"
        """
        result = _search_hotels(city, country_code, context.checkin, context.checkout, context.adults)

        # Merge into (never overwrite) the accumulated map — this can be called more than once per
        # turn (e.g. Gemini retrying a tool-calling turn after a transient error), and each call can
        # return a different subset/order of hotels. Overwriting would drop hotels the model already
        # named in earlier tool results but didn't re-fetch, breaking the later name->id lookup used
        # to attach real images/cards to whatever the reply actually recommends.
        for hotel in (result.get("raw") or {}).get("data") or []:
            hotel_id = hotel.get("id")
            if hotel_id:
                context.known_hotels[hotel_id] = hotel.get("name")
                context.known_hotels_raw[hotel_id] = {
                    "name": hotel.get("name"),
                    "main_photo": hotel.get("main_photo"),
                    "thumbnail": hotel.get("thumbnail"),
                    "city": hotel.get("city"),
                }

        return result

    def recommend_hotels(hotel_ids: list[str]) -> str:
        """Call right after presenting your curated 2-3 hotel picks in your reply text, with the
        exact ids (from search_hotels) of exactly those hotels, in the order presented. This is
        what drives the traveller's app to show the right photos/details — never skip it, and
        never include an id for a place you only mentioned in passing (a neighbourhood, landmark,
        restaurant) rather than actually recommending as a place to stay.

        Args:
          hotel_ids: exact "id" values, copied verbatim from search_hotels results, of only the
            hotels just presented as picks — not any other place named in the reply.
        """
        known = getattr(context, "known_hotels", {}) or {}
        valid = [hid for hid in hotel_ids if hid in known]
        if valid:
            context.current_hotel_ids = valid
            return f"Recommended hotels set: {valid}"
        return "None of those ids matched known_hotels from the last search_hotels call — not applied."

    def select_hotel(hotel_id: str, hotel_name: str) -> str:
        """Call once the traveller has clearly chosen one of the hotels you presented.

        Args:
          hotel_id: the exact "id" field of the chosen hotel, copied verbatim from a search_hotels result
          hotel_name: the chosen hotel's name
        """
        known = getattr(context, "known_hotels", {}) or {}
        # Only the 2-3 hotels actually recommended THIS turn are valid choices — known_hotels can
        # hold 100+ entries accumulated across every search_hotels call this session (including
        # similarly-named properties, e.g. multiple "Rove"-branded hotels), so validating against
        # the full pool let a wrong-but-known id slip through when the model mismatched a hotel
        # name to a different hotel's id. Restricting to current_hotel_ids catches that instead of
        # silently booking the wrong property.
        recommended = getattr(context, "current_hotel_ids", None) or []
        candidates = {hid: known.get(hid) for hid in recommended} or known

        if hotel_id not in candidates:
            match = next(
                (hid for hid in candidates if candidates.get(hid) and candidates[hid].lower() == hotel_name.lower()),
                None,
            )
            if match:
                print(f"  [WARN] select_hotel got id {hotel_id!r} for {hotel_name!r} not in the "
                      f"recommended set; corrected to real id {match!r}.")
                hotel_id = match
            else:
                print(f"  [WARN] select_hotel got id {hotel_id!r} / name {hotel_name!r}, not among "
                      f"the hotels actually recommended this turn ({candidates}) — rejecting.")
                return (
                    f"That id/name isn't one of the hotels you just recommended (current picks: "
                    f"{candidates}). Re-check which exact hotel the traveller means and use its "
                    f"exact id from that set — do not select_hotel for a hotel from a different, "
                    f"earlier search result."
                )
        elif candidates.get(hotel_id) and candidates[hotel_id].lower() != hotel_name.lower():
            # id is a valid recommended hotel, but the name passed doesn't match — use the real
            # name for that id rather than trusting a possibly-mismatched name argument.
            print(f"  [WARN] select_hotel name {hotel_name!r} doesn't match known name "
                  f"{candidates[hotel_id]!r} for id {hotel_id!r}; using the known name.")
            hotel_name = candidates[hotel_id]

        context.selected_hotel_id = hotel_id
        context.selected_hotel_name = hotel_name
        context.stage = "BOOKING"
        return f"Hotel selected: {hotel_name}."

    client = get_client()
    chat = client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT.format(
                today=today_context(),
                destination=context.destination,
                checkin=context.checkin,
                checkout=context.checkout,
                adults=context.adults,
                kids=context.kids,
                budget_level=context.profile.get("budget_level"),
                clarifying_question_instructions=clarifying_question_instructions("hotel_style"),
                response_formatting_instructions=response_formatting_instructions(),
            ),
            tools=[search_hotels, web_search, recommend_hotels, select_hotel],
        ),
    )
    return chat
