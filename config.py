import os
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.environ.get("Tavily_API_KEY") or os.environ.get("TAVILY_API_KEY")
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
# Separate key for the booking agent so its quota doesn't contend with the other agents'
# shared free-tier quota (booking is the last, most time-sensitive step in the flow).
BOOKING_GEMINI_API_KEY = os.environ.get("BOOKING_GEMINI_API_KEY") or GEMINI_API_KEY
# Separate key for speech-to-text (Gemini's own audio transcription, replacing ElevenLabs STT)
# so its usage doesn't contend with the other agents' shared quota either.
STT_GEMINI_API_KEY = os.environ.get("STT_GEMINI_API_KEY") or GEMINI_API_KEY
# Separate key for the answer-matcher (classify_intent / match_intake / match_hotel_details /
# answer_side_question) — this is the highest-frequency Gemini call in the whole app, since it
# runs on every single button click, typed answer, or voice answer during INTAKE and
# HOTEL_DETAILS, so isolating its quota matters more than almost anything else here.
ANSWER_MATCHER_GEMINI_API_KEY = os.environ.get("ANSWER_MATCHER_GEMINI_API_KEY") or GEMINI_API_KEY
LITEAPI_API_KEY = os.environ.get("LITEAPI_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")


def check_keys():
    status = {
        "TAVILY_API_KEY": bool(TAVILY_API_KEY),
        "GEMINI_API_KEY": bool(GEMINI_API_KEY),
        "LITEAPI_API_KEY": bool(LITEAPI_API_KEY),
        "ELEVENLABS_API_KEY": bool(ELEVENLABS_API_KEY),
    }
    return status
