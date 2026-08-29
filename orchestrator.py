import re

from trip_context import TripContext
from agents import destination_spots, hotel_search, booking
from llm import send_with_retry

_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")

_ORDINAL_WORDS = {
    "first": 1, "1st": 1, "one": 1,
    "second": 2, "2nd": 2, "two": 2,
    "third": 3, "3rd": 3, "three": 3,
    "fourth": 4, "4th": 4, "four": 4,
}


def _parse_bare_ordinal(text: str, count: int):
    """If the message is JUST a position reference (e.g. "1", "2", "the first one", "option 3",
    "#2") and nothing else, return that 1-based position (if within 1..count) — else None. Kept
    deliberately narrow: anything with extra words describing the hotel itself (a name, a
    preference) falls through to the LLM's own judgement instead of being force-matched here."""
    cleaned = re.sub(r"[.!?]+$", "", (text or "").strip().lower())
    cleaned = re.sub(r"^(the|option|number|no\.?|#)\s+", "", cleaned)
    cleaned = re.sub(r"\s+(one|option)$", "", cleaned)
    cleaned = cleaned.strip(" #")

    if cleaned.isdigit():
        n = int(cleaned)
        return n if 1 <= n <= count else None
    if cleaned in _ORDINAL_WORDS:
        n = _ORDINAL_WORDS[cleaned]
        return n if 1 <= n <= count else None
    return None


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
        # HOTEL_SEARCH: current_hotel_ids is set directly by the recommend_hotels tool call
        # (see agents/hotel_search.py) — deterministic, not guessed from bolded text in the
        # reply, since every place name gets bolded (neighbourhoods, landmarks, hotels alike)
        # and that made text-matching prone to picking up unrelated hotels.

    def enter_llm_stage(self, stage: str, opener_override: str = None) -> str:
        self.context.stage = stage
        self._chat = STAGE_AGENTS[stage](self.context)
        opener = opener_override or STAGE_OPENERS[stage].format(
            destination=self.context.destination,
            travellers_type=self.context.profile.get("travellers_type"),
            month=self.context.profile.get("month"),
        )
        response = send_with_retry(self._chat, opener)
        text = (response.text or "").strip()
        self._track_reply_entities(text)
        return text

    def send(self, user_message: str) -> str:
        # Deterministic shortcut: during HOTEL_SEARCH, a bare position reference ("1", "the
        # second one", "#3") always means that hotel's position in the list just presented
        # (current_hotel_ids, in the exact order recommend_hotels was called with) — resolve it
        # in code rather than trusting the LLM to map the number back to the right id, since
        # that mapping has been observed to go wrong (picking a different hotel than the
        # traveller's stated position, only "recovering" by coincidence via the no-availability
        # fallback). Anything not a clean bare position falls through to the LLM as normal.
        if self.context.stage == "HOTEL_SEARCH" and self.context.current_hotel_ids:
            ids = self.context.current_hotel_ids
            pos = _parse_bare_ordinal(user_message, len(ids))
            if pos:
                hotel_id = ids[pos - 1]
                hotel_name = (self.context.known_hotels or {}).get(hotel_id)
                if hotel_name:
                    self.context.selected_hotel_id = hotel_id
                    self.context.selected_hotel_name = hotel_name
                    return self.enter_llm_stage(
                        "BOOKING",
                        opener_override=(
                            f"The traveller selected hotel #{pos}, \"{hotel_name}\", from the list you "
                            "just presented. Greet them briefly confirming this hotel, then get the real "
                            "rates for it (call get_hotel_rates with its id)."
                        ),
                    )

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
