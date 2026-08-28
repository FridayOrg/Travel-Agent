import re

from trip_context import TripContext
from agents import destination_spots, hotel_search, booking
from llm import send_with_retry

_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def extract_places(text: str, limit: int = 3) -> list:
    """Pulls the **bolded** place/attraction names an agent's reply already names — these are
    real names grounded in that turn's web_search results, not a new generation step, so this is
    just parsing, not inventing anything."""
    seen = []
    for m in _BOLD_RE.findall(text or ""):
        name = m.strip().strip(":").strip()
        if name and name not in seen and len(name) > 2:
            seen.append(name)
        if len(seen) >= limit:
            break
    return seen


def match_recommended_hotels(text: str, known_hotels: dict, limit: int = 4) -> list:
    """Matches the bolded hotel names an agent's reply actually recommends against the real
    hotel ids from search_hotels, so the hotels shown as images are exactly the ones the reply
    is talking about — not just the first few results in the raw search response."""
    names = extract_places(text, limit=limit + 2)
    matched = []
    for name in names:
        for hotel_id, hotel_name in (known_hotels or {}).items():
            if hotel_name and (name.lower() in hotel_name.lower() or hotel_name.lower() in name.lower()):
                if hotel_id not in matched:
                    matched.append(hotel_id)
                break
        if len(matched) >= limit:
            break
    return matched

STAGE_AGENTS = {
    "DESTINATION_SPOTS": destination_spots.make_agent,
    "HOTEL_SEARCH": hotel_search.make_agent,
    "BOOKING": booking.make_agent,
}

STAGE_OPENERS = {
    "DESTINATION_SPOTS": (
        "The traveller's trip basics are set: destination {destination}, travelling with "
        "{travellers_type}, in {month}. Greet them briefly and suggest the best real "
        "spots/places to visit, grounded in web search — do not hallucinate."
    ),
    "HOTEL_SEARCH": (
        "All hotel search inputs are already collected (dates, guests, budget). Search real hotels "
        "now, cross-check reputation, and present curated picks with reasoning."
    ),
    "BOOKING": (
        "The traveller just picked their hotel. Greet them briefly, confirming which hotel, then get "
        "the real rates for it."
    ),
}


class Orchestrator:
    def __init__(self):
        self.context = TripContext()
        self._chat = None

    def _track_reply_entities(self, text: str) -> None:
        if self.context.stage == "DESTINATION_SPOTS":
            places = extract_places(text)
            if places:
                self.context.current_places = places
        elif self.context.stage == "HOTEL_SEARCH":
            hotel_ids = match_recommended_hotels(text, self.context.known_hotels)
            if hotel_ids:
                self.context.current_hotel_ids = hotel_ids

    def enter_llm_stage(self, stage: str) -> str:
        self.context.stage = stage
        self._chat = STAGE_AGENTS[stage](self.context)
        opener = STAGE_OPENERS[stage].format(
            destination=self.context.destination,
            travellers_type=self.context.profile.get("travellers_type"),
            month=self.context.profile.get("month"),
        )
        response = send_with_retry(self._chat, opener)
        text = (response.text or "").strip()
        self._track_reply_entities(text)
        return text

    def send(self, user_message: str) -> str:
        stage_before = self.context.stage
        response = send_with_retry(self._chat, user_message)
        text = response.text or ""

        if self.context.stage != stage_before and self.context.stage in STAGE_AGENTS:
            # A tool call inside this turn advanced to another LLM-backed stage (e.g. select_hotel ->
            # BOOKING) — rebuild the chat for the new stage and use its own opening reply instead of
            # the old agent's filler text, avoiding duplicate/overlapping messages.
            text = self.enter_llm_stage(self.context.stage)
        else:
            self._track_reply_entities(text)

        return text
