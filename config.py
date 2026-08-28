import os
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.environ.get("Tavily_API_KEY") or os.environ.get("TAVILY_API_KEY")
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
# Separate key for the booking agent so its quota doesn't contend with the other agents'
# shared free-tier quota (booking is the last, most time-sensitive step in the flow).
BOOKING_GEMINI_API_KEY = os.environ.get("BOOKING_GEMINI_API_KEY") or GEMINI_API_KEY
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
