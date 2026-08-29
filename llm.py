import re
import time
from datetime import date

from google import genai
from google.genai import errors
from config import GEMINI_API_KEY, BOOKING_GEMINI_API_KEY, STT_GEMINI_API_KEY, ANSWER_MATCHER_GEMINI_API_KEY

MODEL = "gemini-flash-lite-latest"


def today_context() -> str:
    """Inject the real current date so agents don't guess/assume a stale year when
    reasoning about dates or searching for date-sensitive facts (festivals, seasons, events)."""
    return f"Today's real date is {date.today().strftime('%A, %B %d, %Y')}."


def clarifying_question_instructions(stage: str) -> str:
    return f"""When you need to ask the traveller something that has a small, clear set of likely answers, do
NOT ask in plain free text. Instead, output ONLY a JSON object in this exact format, with no other text before
or after it:

{{"type": "clarifying_question", "stage": "{stage}", "question": "<the question text>", "options": ["<option 1>", "<option 2>", "<option 3>", "<option 4>"]}}

Example:
{{"type": "clarifying_question", "stage": "{stage}", "question": "Who are you travelling with?", "options": ["Solo", "Partner", "Friends", "Family"]}}

Rules:
- Only use this JSON format for questions with a small number of clear, mutually exclusive answers (2-5 options).
- For open-ended questions (budget in exact figures, specific interests, anything that doesn't bucket cleanly),
  ask normally in plain conversational text instead — do not force everything into this format.
- When you use the JSON format, output ONLY the JSON — no greeting, no explanation, no text before or after it,
  and never mix plain text with a JSON block in the same turn.
- Keep the exact keys "type", "stage", "question", "options" every time — do not rename or restructure them,
  and always set "stage" to exactly "{stage}".
- Never use this format for anything except a genuine multiple-choice question to the traveller — never for
  your own destination/hotel recommendations or any other content."""

def response_formatting_instructions() -> str:
    return """Formatting rules for every reply you write (not just clarifying questions):
- Wrap every named place, attraction, neighbourhood, or specific experience you mention in **bold**
  markdown (e.g. **Burj Park**, **Love Lake**, **Global Village**, **yacht cruise**). Do this
  consistently for every such name, every time — never leave a real place name unbolded.
- If your reply ends with a direct question to the traveller (an invitation to continue), wrap
  ONLY that final question in double hashes instead of asterisks, e.g. ##<your question here>##.
  The question itself must always be about what you just said THIS turn — e.g. if you were
  discussing hotels, ask about choosing/continuing with a hotel, not about building an itinerary;
  if you were discussing spots/activities, ask about the itinerary. Never reuse a stock question
  from a different stage of the conversation just because it sounds like a natural closer — write
  a fresh one that actually fits what you just told them. Use this exact ## marker (not ** bold)
  for that one closing question, and never use it for anything else. If your reply doesn't end in
  a direct question, don't add one artificially — just omit the ## marker that turn.
- Never use the ## marker for the structured {"type": "clarifying_question", ...} JSON format
  described above — that has its own separate rendering and must never be mixed with prose or
  ## markers in the same message."""


_client = None
_booking_client = None
_stt_client = None
_answer_matcher_client = None


def get_client():
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is missing from .env")
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def get_booking_client():
    """Separate Gemini client/API key for the booking agent, so its quota doesn't contend
    with the other agents sharing GEMINI_API_KEY — booking is the last, most time-sensitive
    step in the flow, right when a traveller is trying to finish checking out."""
    global _booking_client
    if _booking_client is None:
        if not BOOKING_GEMINI_API_KEY:
            raise RuntimeError("BOOKING_GEMINI_API_KEY (or GEMINI_API_KEY) is missing from .env")
        _booking_client = genai.Client(api_key=BOOKING_GEMINI_API_KEY)
    return _booking_client


def get_stt_client():
    """Separate Gemini client/API key for speech-to-text (replacing ElevenLabs STT), so voice
    transcription doesn't contend with the other agents' shared quota either."""
    global _stt_client
    if _stt_client is None:
        if not STT_GEMINI_API_KEY:
            raise RuntimeError("STT_GEMINI_API_KEY (or GEMINI_API_KEY) is missing from .env")
        _stt_client = genai.Client(api_key=STT_GEMINI_API_KEY)
    return _stt_client


def get_answer_matcher_client():
    """Separate Gemini client/API key for the answer-matcher (agents/answer_matcher.py) — the
    highest-frequency Gemini call in the app, since it runs on every button click, typed
    answer, or voice answer during INTAKE and HOTEL_DETAILS. Isolating its quota keeps a busy
    intake/hotel-details screen from starving (or being starved by) the other agents."""
    global _answer_matcher_client
    if _answer_matcher_client is None:
        if not ANSWER_MATCHER_GEMINI_API_KEY:
            raise RuntimeError("ANSWER_MATCHER_GEMINI_API_KEY (or GEMINI_API_KEY) is missing from .env")
        _answer_matcher_client = genai.Client(api_key=ANSWER_MATCHER_GEMINI_API_KEY)
    return _answer_matcher_client


def _call_with_retry(fn, max_retries: int = 8):
    """Runs fn() (a zero-arg callable making one Gemini API call), automatically waiting out
    free-tier 429 rate limits and retrying. Shared by every call site that talks to Gemini
    directly, so none of them can turn a transient rate limit into an unhandled 500."""
    for attempt in range(max_retries):
        try:
            return fn()
        except errors.ClientError as e:
            if getattr(e, "code", None) != 429 or attempt == max_retries - 1:
                raise
            delay = 15.0
            match = re.search(r"retryDelay['\"]?:\s*['\"]?(\d+(?:\.\d+)?)", str(e))
            if match:
                delay = float(match.group(1))
            time.sleep(delay + 1)
    raise RuntimeError("unreachable")


def send_with_retry(chat, message: str, max_retries: int = 8):
    """Send a chat message, automatically waiting out Gemini free-tier 429 rate limits."""
    return _call_with_retry(lambda: chat.send_message(message), max_retries)


def generate_with_retry(client, max_retries: int = 8, **kwargs):
    """client.models.generate_content(**kwargs), automatically waiting out Gemini free-tier
    429 rate limits — the generate_content equivalent of send_with_retry, for call sites that
    use a one-off client.models.generate_content call instead of a chat session."""
    return _call_with_retry(lambda: client.models.generate_content(**kwargs), max_retries)


if __name__ == "__main__":
    client = get_client()
    resp = client.models.generate_content(model=MODEL, contents="Say 'connection ok' and nothing else.")
    print(resp.text)
