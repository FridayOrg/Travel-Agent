"""Resolves typed or voice-transcribed free text into the same structured answers a button
click would produce, for the static (non-LLM) question stages: INTAKE, HOTEL_DETAILS.

Deliberately a narrow, closed-set classification call — not an open-ended chat turn — so it
stays reliable for fields that must never be silently skipped (the same reliability concern
that made these stages static forms in the first place). Reads its valid option sets straight
from static_stages.py, the same source of truth the frontend's buttons are built from, so a
future static question automatically gets matching for free.
"""
import json
import re

from google.genai import types

from llm import get_client, MODEL, today_context
from static_stages import INTAKE_QUESTIONS, HOTEL_TRAVELLERS_QUESTION, HOTEL_BUDGET_QUESTION
from tools.search import web_search

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _ask_matcher(instructions: str) -> dict:
    client = get_client()
    resp = client.models.generate_content(model=MODEL, contents=instructions)
    raw = (resp.text or "").strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        return {}
    try:
        return json.loads(raw[start:end + 1])
    except json.JSONDecodeError:
        return {}


def classify_intent(text: str, pending_question: str) -> str:
    """Classifies free text against the currently pending static question into exactly one of:
    - "answer": an attempt to answer the pending question (even if oddly worded/synonymous)
    - "question": a genuine informational question/side comment not requiring any earlier
      decision to change (e.g. "what's the weather like there?")
    - "change_request": a request to change or revisit something ALREADY DECIDED earlier in the
      conversation that is NOT the current pending question — e.g. a different destination, or
      regenerating/modifying the itinerary. ("actually make it 3 adults" while being asked the
      travellers question is just answering differently, NOT a change_request — this label is
      only for requests about something from an earlier stage.)
    Kept as a small, fast, single-word classification call — not the heavier field-matching or
    question-answering calls, which only run after this decides which path applies.
    """
    prompt = f"""A traveller is currently being asked: "{pending_question}"

They said: {json.dumps(text)}

Classify what they mean, choosing exactly one:
- "answer" — attempting to answer the pending question above (even inexactly).
- "question" — asking something informational (facts, weather, prices, general questions) that
  doesn't require changing any earlier trip decision.
- "change_request" — asking to change or revisit something ALREADY DECIDED earlier in the
  conversation that isn't the current pending question — e.g. a different destination, or
  regenerating/modifying the itinerary.

Respond with ONLY one word: answer, question, or change_request"""
    client = get_client()
    resp = client.models.generate_content(model=MODEL, contents=prompt)
    label = (resp.text or "").strip().lower()
    if "change" in label:
        return "change_request"
    if "question" in label:
        return "question"
    return "answer"


def handle_change_request(text: str, orchestrator) -> tuple[str, str]:
    """Routes a mid-flow "change something already decided" request back into the consultative
    destination_spots agent (which already knows how to modify an itinerary or change_destination
    — see agents/destination_spots.py), carrying the traveller's actual request as the opener
    instead of the normal canned greeting. Returns (reply, new_stage)."""
    opener = (
        f"While filling out hotel details, the traveller just said: {json.dumps(text)}\n\n"
        "This means they want to change or revisit something already decided (a different "
        "destination, the itinerary, etc.) rather than continue with hotel details right now. "
        "Address their request directly — if they want a different destination, call "
        "change_destination and then help plan for the new place; if they want the itinerary "
        "changed, revise it. Once whatever they need is resolved and they've explicitly "
        "confirmed they're ready (the usual itinerary confirmation), they'll automatically move "
        "back into the hotel questions."
    )
    reply = orchestrator.enter_llm_stage("DESTINATION_SPOTS", opener_override=opener)
    return reply, orchestrator.context.stage


def match_intake(text: str) -> dict:
    """Returns {"destination": str|None, "travellers": str|None, "month": str|None}.
    destination/month always resolve to something (a preset or the literal value stated,
    matching the "Other" free-text button behaviour) unless truly not mentioned at all.
    travellers only resolves to one of the 4 presets, or None if unclear/not mentioned."""
    fields_desc = {q["id"]: q["options"] for q in INTAKE_QUESTIONS}
    prompt = f"""{today_context()}

A traveller typed or spoke this instead of clicking a button: {json.dumps(text)}

IMPORTANT: only extract a field if they are STATING their own preference/choice for it. If they
are instead ASKING a question (e.g. "what's the weather like in Dubai?", "how much would Dubai
cost?", "is Dubai safe in October?") or just mentioning a place/time/group in passing while
asking about something else, that does NOT count as stating a preference — return null for that
field even though the word appears in their message. A mention only counts if they are telling
you that's their actual choice (e.g. "Dubai", "I want to go to Dubai", "let's do Dubai").

Extract up to three fields from it:
- "destination": if they are STATING a destination preference, return it. If it matches one of
  {fields_desc['destination'][:-1]} use that exact preset spelling; otherwise return the actual
  place name they said verbatim. Return null if no destination preference is being stated.
- "travellers": must be exactly one of {fields_desc['travellers']} (match synonyms, e.g. "just me"
  -> "Solo", "my partner and I" -> "Couple", "my parents and kids" -> "Family"). Return null if
  not being stated or genuinely unclear.
- "month": if they are STATING a travel timeframe preference, return it. If it clearly matches
  one of {fields_desc['month'][:-1]}, use that exact preset spelling; otherwise return the actual
  month/timeframe they said verbatim (e.g. "next March" -> "March"). Return null if no timing
  preference is being stated.

Respond with ONLY a JSON object: {{"destination": ..., "travellers": ..., "month": ...}}
No other text."""
    data = _ask_matcher(prompt)
    return {
        "destination": data.get("destination") or None,
        "travellers": data.get("travellers") if data.get("travellers") in fields_desc["travellers"] else None,
        "month": data.get("month") or None,
    }


def match_hotel_details(text: str) -> dict:
    """Returns {"adults": int|None, "kids": int, "budget_level": str|None,
    "checkin": "YYYY-MM-DD"|None, "checkout": "YYYY-MM-DD"|None} — resolves whichever of the
    three combined hotel-detail questions (travellers, budget, dates) the traveller addressed in
    one utterance, the same batched-extraction pattern as match_intake."""
    travellers_options = HOTEL_TRAVELLERS_QUESTION["options"]
    budget_options = HOTEL_BUDGET_QUESTION["options"]
    prompt = f"""{today_context()}

A traveller typed or spoke this instead of using the hotel-details form: {json.dumps(text)}

The form asks THREE things together — how many travellers, budget range per night, and
check-in/check-out dates. Extract whichever of these they actually stated (they may address
one, two, or all three in one message):

- "adults" / "kids": number of adult and child travellers they mean (e.g. presets like
  {travellers_options[:-1]} map to specific counts, or work out actual numbers from something
  like "3 adults and 2 kids" or "just the two of us"). null for adults if not stated at all.
- "budget_level": if it clearly matches one of {budget_options[:-1]}, use that exact preset
  spelling; otherwise return their own budget description verbatim. null if not stated at all.
- "checkin" / "checkout": calendar dates (resolve relative phrases like "next month" against
  today's real date above; nearest future occurrence for a bare month/day). null for either if
  not stated at all.

Respond with ONLY a JSON object: {{"adults": int or null, "kids": int (0 if not mentioned),
"budget_level": string or null, "checkin": "YYYY-MM-DD" or null, "checkout": "YYYY-MM-DD" or null}}
No other text."""
    data = _ask_matcher(prompt)
    adults = data.get("adults")
    checkin = data.get("checkin")
    checkout = data.get("checkout")
    return {
        "adults": adults if isinstance(adults, int) and adults > 0 else None,
        "kids": data.get("kids") if isinstance(data.get("kids"), int) else 0,
        "budget_level": data.get("budget_level") or None,
        "checkin": checkin if isinstance(checkin, str) and _DATE_RE.match(checkin) else None,
        "checkout": checkout if isinstance(checkout, str) and _DATE_RE.match(checkout) else None,
    }


def answer_side_question(text: str, pending_question: str, context) -> str:
    """When free text during a static stage doesn't resolve to an answer for the pending
    question, the traveller is very likely asking something else instead (a real question, a
    side comment) — this gives it a real, grounded reply (web_search-backed, never invented)
    rather than just re-showing the form silently. Always ends by steering back to the pending
    question so the flow isn't lost.
    """
    known_bits = []
    if getattr(context, "destination", None):
        known_bits.append(f"Destination so far: {context.destination}")
    if getattr(context, "profile", None):
        for k, v in context.profile.items():
            if v:
                known_bits.append(f"{k}: {v}")
    known = "\n".join(known_bits) or "Nothing collected yet."

    client = get_client()
    prompt = f"""{today_context()}

You are a travel consultant chatbot. The traveller is currently being asked this question by
the app's guided form: "{pending_question}"

What they just said instead of answering it: {json.dumps(text)}

What's already known about their trip so far:
{known}

If what they said is a genuine question or side comment (not an attempt to answer the pending
question), answer it briefly and honestly — use web_search if it needs a real fact you don't
already know (never invent specifics like prices, dates, or facts). If it doesn't look like a
real question either (e.g. unclear noise), just say so plainly. Either way, end your reply by
gently steering them back to the pending question above, in your own natural words.

Keep the whole reply SHORT — 2-4 sentences."""

    chat = client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(tools=[web_search]),
    )
    resp = chat.send_message(prompt)
    return (resp.text or "").strip() or "I'm not sure I follow — could you let me know your answer to the question above?"
