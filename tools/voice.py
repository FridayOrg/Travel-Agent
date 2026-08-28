import requests
from config import ELEVENLABS_API_KEY

TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
STT_URL = "https://api.elevenlabs.io/v1/speech-to-text"

DEFAULT_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"  # "George" — warm, friendly narrator voice


def text_to_speech(text: str, voice_id: str = DEFAULT_VOICE_ID) -> bytes:
    """Convert agent reply text to spoken audio (mp3 bytes) via ElevenLabs."""
    if not ELEVENLABS_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY is missing from .env")

    resp = requests.post(
        TTS_URL.format(voice_id=voice_id),
        headers={"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"},
        json={"text": text, "model_id": "eleven_flash_v2_5"},  # low-latency model for near-instant playback
        timeout=30,
    )
    resp.raise_for_status()
    return resp.content


def speech_to_text(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    """Transcribe recorded microphone audio to text via ElevenLabs Scribe."""
    if not ELEVENLABS_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY is missing from .env")

    resp = requests.post(
        STT_URL,
        headers={"xi-api-key": ELEVENLABS_API_KEY},
        data={"model_id": "scribe_v1"},
        files={"file": (filename, audio_bytes)},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json().get("text", "")


if __name__ == "__main__":
    audio = text_to_speech("Connection ok, this is a live test of the voice output.")
    with open("tts_test.mp3", "wb") as f:
        f.write(audio)
    print(f"Wrote {len(audio)} bytes to tts_test.mp3")
