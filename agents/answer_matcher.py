"""Resolves typed or voice-transcribed free text into the same structured answers a button
click would produce, for the static (non-LLM) question stages: INTAKE, HOTEL_TRAVELLERS,
HOTEL_BUDGET, HOTEL_DATES.

Deliberately a narrow, closed-set classification call — not an open-ended chat turn — so it
stays reliable for fields that must never be silently skipped (the same reliability concern
that made these stages static forms in the first place). Reads its valid option sets straight
from static_stages.py, the same source of truth the frontend's buttons are built from, so a
future static question automatically gets matching for free.
"""
import json
import re

from llm import get_client, MODEL, today_context
from static_stages import INTAKE_QUESTIONS, HOTEL_TRAVELLERS_QUESTION, HOTEL_BUDGET_QUESTION


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


def match_intake(text: str) -> dict:
    """Returns {"destination": str|None, "travellers": str|None, "month": str|None}.
    destination/month always resolve to something (a preset or the literal value stated,
    matching the "Other" free-text button behaviour) unless truly not mentioned at all.
    travellers only resolves to one of the 4 presets, or None if unclear/not mentioned."""
    fields_desc = {q["id"]: q["options"] for q in INTAKE_QUESTIONS}
    prompt = f"""{today_context()}

A traveller typed or spoke this instead of clicking a button: {json.dumps(text)}

Extract up to three fields from it:
- "destination": if they name a place, return it. If it matches one of {fields_desc['destination'][:-1]}
  use that exact preset spelling; otherwise return the actual place name they said verbatim.
  Return null only if no destination is mentioned at all.
- "travellers": must be exactly one of {fields_desc['travellers']} (match synonyms, e.g. "just me"
  -> "Solo", "my partner and I" -> "Couple", "my parents and kids" -> "Family"). Return null if
  not mentioned or genuinely unclear.
- "month": if they name a timeframe, return it. If it clearly matches one of
  {fields_desc['month'][:-1]}, use that exact preset spelling; otherwise return the actual
  month/timeframe they said verbatim (e.g. "next March" -> "March"). Return null only if no
  timing is mentioned at all.

Respond with ONLY a JSON object: {{"destination": ..., "travellers": ..., "month": ...}}
No other text."""
    data = _ask_matcher(prompt)
    return {
        "destination": data.get("destination") or None,
        "travellers": data.get("travellers") if data.get("travellers") in fields_desc["travellers"] else None,
        "month": data.get("month") or None,
    }


def match_hotel_travellers(text: str) -> dict:
    """Returns {"adults": int|None, "kids": int}. None adults means no confident match."""
    options = HOTEL_TRAVELLERS_QUESTION["options"]
    prompt = f"""A traveller typed or spoke this instead of clicking a button: {json.dumps(text)}

They're answering "How many travellers?" (options shown were: {options}).
Extract the number of adults and number of kids/children they mean. "2 Adults" = 2 adults, 0
kids. "2 Adults + 1 Kid" = 2 adults, 1 kid. If they state different numbers (e.g. "3 adults and
2 kids", "just the two of us", "me, my wife and our daughter"), work out the actual counts.
Respond with ONLY a JSON object: {{"adults": <int or null if truly unclear>, "kids": <int, 0 if none mentioned>}}
No other text."""
    data = _ask_matcher(prompt)
    adults = data.get("adults")
    return {
        "adults": adults if isinstance(adults, int) and adults > 0 else None,
        "kids": data.get("kids") if isinstance(data.get("kids"), int) else 0,
    }


def match_hotel_budget(text: str) -> dict:
    """Returns {"budget_level": str|None} — always resolves to a preset or the traveller's own
    literal description (matching the "Other" free-text button), unless nothing budget-related
    was said at all."""
    options = HOTEL_BUDGET_QUESTION["options"]
    prompt = f"""A traveller typed or spoke this instead of clicking a button: {json.dumps(text)}

They're answering "What's your budget range per night?" (preset options were:
{options[:-1]}, or a custom description).
If it clearly matches one of {options[:-1]}, return that exact preset spelling. Otherwise, if
they described a budget in their own words, return their description verbatim. Return null only
if nothing budget-related was said at all.

Respond with ONLY a JSON object: {{"budget_level": ... or null}}
No other text."""
    data = _ask_matcher(prompt)
    return {"budget_level": data.get("budget_level") or None}


_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def match_hotel_dates(text: str) -> dict:
    """Returns {"checkin": "YYYY-MM-DD"|None, "checkout": "YYYY-MM-DD"|None}."""
    prompt = f"""{today_context()}

A traveller typed or spoke this instead of using a date picker: {json.dumps(text)}

They're stating their hotel check-in and check-out dates. Work out the actual calendar dates
they mean (resolve relative phrases like "next month" or "the second week of October" against
today's real date above; assume the nearest future occurrence for a bare month/day). Return
null for either field if it truly can't be determined.

Respond with ONLY a JSON object: {{"checkin": "YYYY-MM-DD" or null, "checkout": "YYYY-MM-DD" or null}}
No other text."""
    data = _ask_matcher(prompt)
    checkin = data.get("checkin")
    checkout = data.get("checkout")
    return {
        "checkin": checkin if isinstance(checkin, str) and _DATE_RE.match(checkin) else None,
        "checkout": checkout if isinstance(checkout, str) and _DATE_RE.match(checkout) else None,
    }
