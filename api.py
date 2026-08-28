"""
HTTP API wrapping the existing multi-agent orchestrator (orchestrator.py, agents/*, tools/*)
for the Evara "Plan with AI" frontend. Agent logic itself is untouched — this is purely a
thin transport layer so the browser-based chat UI can drive the same orchestrator that the
Streamlit app (app.py) drives.

Run with: uvicorn api:app --port 8000 --reload
"""
import io
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from orchestrator import Orchestrator
from config import ELEVENLABS_API_KEY
from static_stages import INTAKE_QUESTIONS, HOTEL_TRAVELLERS_QUESTION, HOTEL_BUDGET_QUESTION

app = FastAPI(title="Evara Plan-with-AI backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSIONS: dict[str, Orchestrator] = {}


def get_orchestrator(session_id: str) -> Orchestrator:
    orch = SESSIONS.get(session_id)
    if orch is None:
        raise HTTPException(status_code=404, detail="Unknown session_id")
    return orch


class IntakeBody(BaseModel):
    destination: str
    traveler_type: str
    theme: str | None = None
    month: str | None = None


class MessageBody(BaseModel):
    text: str


class HotelTravellersBody(BaseModel):
    adults: int
    kids: int = 0


class HotelBudgetBody(BaseModel):
    budget_level: str


class HotelDatesBody(BaseModel):
    checkin: str
    checkout: str


class TtsBody(BaseModel):
    text: str


class StaticAnswerBody(BaseModel):
    text: str


def state_payload(orch: Orchestrator) -> dict:
    ctx = orch.context
    return {
        "stage": ctx.stage,
        "destination": ctx.destination,
        "profile": ctx.profile,
        "trip_duration_days": ctx.trip_duration_days,
        "selected_hotel_name": ctx.selected_hotel_name,
        "booking_confirmed": bool(ctx.booking_confirmation),
    }


@app.post("/api/session")
def create_session():
    session_id = uuid.uuid4().hex
    SESSIONS[session_id] = Orchestrator()
    return {"session_id": session_id, **state_payload(SESSIONS[session_id])}


@app.post("/api/session/{session_id}/intake")
def submit_intake(session_id: str, body: IntakeBody):
    orch = get_orchestrator(session_id)
    ctx = orch.context
    ctx.destination = body.destination
    ctx.profile["destination"] = body.destination
    ctx.profile["travellers_type"] = body.traveler_type
    ctx.profile["month"] = body.month or "not specified"
    if body.theme:
        ctx.profile["theme"] = body.theme
    reply = orch.enter_llm_stage("DESTINATION_SPOTS")
    return {"reply": reply, **state_payload(orch)}


@app.post("/api/session/{session_id}/message")
def send_message(session_id: str, body: MessageBody):
    orch = get_orchestrator(session_id)
    reply = orch.send(body.text)
    return {"reply": reply, **state_payload(orch)}


@app.post("/api/session/{session_id}/hotel-travellers")
def hotel_travellers(session_id: str, body: HotelTravellersBody):
    orch = get_orchestrator(session_id)
    ctx = orch.context
    ctx.adults = body.adults
    ctx.kids = body.kids
    ctx.stage = "HOTEL_BUDGET"
    return {**state_payload(orch)}


@app.post("/api/session/{session_id}/hotel-budget")
def hotel_budget(session_id: str, body: HotelBudgetBody):
    orch = get_orchestrator(session_id)
    ctx = orch.context
    ctx.profile["budget_level"] = body.budget_level
    ctx.stage = "HOTEL_DATES"
    return {**state_payload(orch)}


@app.post("/api/session/{session_id}/hotel-dates")
def hotel_dates(session_id: str, body: HotelDatesBody):
    orch = get_orchestrator(session_id)
    ctx = orch.context
    ctx.checkin = body.checkin
    ctx.checkout = body.checkout
    reply = orch.enter_llm_stage("HOTEL_SEARCH")
    return {"reply": reply, **state_payload(orch)}


@app.post("/api/session/{session_id}/static-answer")
def static_answer(session_id: str, body: StaticAnswerBody):
    """Lets typed or voice-transcribed free text work identically to clicking one of the
    static-stage buttons (INTAKE, HOTEL_TRAVELLERS, HOTEL_BUDGET, HOTEL_DATES). See
    agents/answer_matcher.py — a narrow, closed-set match against that stage's real options,
    not open-ended chat, so mandatory fields still can't be silently skipped.

    Response envelope:
      { "resolved": {...fields confidently matched from this one utterance...},
        "missing": [...ids of fields still unresolved...],
        "reply": str|None,     # a real message to show the traveller: present when resolution
                                # advanced into the next (LLM) stage, when the text was a genuine
                                # side question (answered, then steers back), or when it was a
                                # request to change something already decided (routed back into
                                # the destination_spots agent, whose own reply is returned here)
        ...state_payload }
    Every message is classified into exactly one of three intents first (agents/answer_matcher's
    classify_intent): "answer" (attempting to answer the pending question — handled by the
    per-stage matchers below, same as before), "question" (an unrelated informational
    question/side comment — answered directly via web-search-grounded answer_side_question,
    steering back to the pending question, stage unchanged), or "change_request" (asking to
    revisit something already decided earlier, e.g. a different destination or the itinerary —
    routed back into the destination_spots agent via handle_change_request, which owns modifying
    the itinerary or calling change_destination; the traveller returns to hotel questions once
    they reconfirm there, exactly like the normal itinerary-confirmation flow).

    For INTAKE specifically, "resolved" may be partial (e.g. just destination) — the caller
    should merge it into whatever's already been collected via buttons/prior free text and only
    finalize (call POST .../intake) once all three fields are present, exactly like the button
    flow already does. For the single-field hotel static stages, a resolved answer is applied
    and the stage advances immediately, same as the equivalent structured endpoint.
    """
    from agents import answer_matcher

    orch = get_orchestrator(session_id)
    ctx = orch.context
    text = body.text

    pending_questions = {
        "INTAKE": " / ".join(q["question"] for q in INTAKE_QUESTIONS),
        "HOTEL_TRAVELLERS": HOTEL_TRAVELLERS_QUESTION["question"],
        "HOTEL_BUDGET": HOTEL_BUDGET_QUESTION["question"],
        "HOTEL_DATES": "What are your check-in and check-out dates?",
    }
    if ctx.stage not in pending_questions:
        raise HTTPException(status_code=400, detail=f"Stage {ctx.stage!r} isn't a static question stage — use /message instead.")

    intent = answer_matcher.classify_intent(text, pending_questions[ctx.stage])

    if intent == "change_request":
        reply, new_stage = answer_matcher.handle_change_request(text, orch)
        return {"resolved": {}, "missing": [], "reply": reply, **state_payload(orch)}

    if intent == "question":
        reply = answer_matcher.answer_side_question(text, pending_questions[ctx.stage], ctx)
        missing = {
            "INTAKE": ["destination", "travellers", "month"],
            "HOTEL_TRAVELLERS": ["adults"],
            "HOTEL_BUDGET": ["budget_level"],
            "HOTEL_DATES": ["checkin", "checkout"],
        }[ctx.stage]
        return {"resolved": {}, "missing": missing, "reply": reply, **state_payload(orch)}

    # intent == "answer" — proceed with the existing per-stage structured matching.
    if ctx.stage == "INTAKE":
        matched = answer_matcher.match_intake(text)
        resolved = {k: v for k, v in matched.items() if v is not None}
        missing = [k for k, v in matched.items() if v is None]
        return {"resolved": resolved, "missing": missing, "reply": None, **state_payload(orch)}

    if ctx.stage == "HOTEL_TRAVELLERS":
        matched = answer_matcher.match_hotel_travellers(text)
        if matched["adults"] is None:
            return {"resolved": {}, "missing": ["adults"], "reply": None, **state_payload(orch)}
        ctx.adults = matched["adults"]
        ctx.kids = matched["kids"]
        ctx.stage = "HOTEL_BUDGET"
        return {"resolved": matched, "missing": [], "reply": None, **state_payload(orch)}

    if ctx.stage == "HOTEL_BUDGET":
        matched = answer_matcher.match_hotel_budget(text)
        if matched["budget_level"] is None:
            return {"resolved": {}, "missing": ["budget_level"], "reply": None, **state_payload(orch)}
        ctx.profile["budget_level"] = matched["budget_level"]
        ctx.stage = "HOTEL_DATES"
        return {"resolved": matched, "missing": [], "reply": None, **state_payload(orch)}

    matched = answer_matcher.match_hotel_dates(text)
    missing = [k for k, v in matched.items() if v is None]
    if missing:
        resolved = {k: v for k, v in matched.items() if v is not None}
        return {"resolved": resolved, "missing": missing, "reply": None, **state_payload(orch)}
    ctx.checkin = matched["checkin"]
    ctx.checkout = matched["checkout"]
    reply = orch.enter_llm_stage("HOTEL_SEARCH")
    return {"resolved": matched, "missing": [], "reply": reply, **state_payload(orch)}


@app.get("/api/session/{session_id}/state")
def get_state(session_id: str):
    return state_payload(get_orchestrator(session_id))


@app.get("/api/session/{session_id}/images")
def get_images(session_id: str):
    """Real, grounded images for whatever the traveller is currently looking at — destination
    spots while planning, hotel photos once hotel search/booking starts. See agents/image_agent.py
    — no image here is generated or generic; each is either LiteAPI's own photo for that exact
    hotel id, or a live web image-search result for that exact named place."""
    from agents.image_agent import get_destination_images, get_hotel_images

    orch = get_orchestrator(session_id)
    ctx = orch.context

    hotel_stages = ("HOTEL_TRAVELLERS", "HOTEL_BUDGET", "HOTEL_DATES", "HOTEL_SEARCH", "BOOKING")
    if ctx.stage in hotel_stages:
        if ctx.stage == "BOOKING" and ctx.selected_hotel_id:
            entries = [get_hotel_images(ctx.selected_hotel_id, ctx.selected_hotel_name, ctx.known_hotels_raw)]
        elif ctx.current_hotel_ids:
            entries = [
                get_hotel_images(hid, (ctx.known_hotels or {}).get(hid, ""), ctx.known_hotels_raw)
                for hid in ctx.current_hotel_ids
            ]
        else:
            entries = [
                get_hotel_images(hid, name, ctx.known_hotels_raw)
                for hid, name in list((ctx.known_hotels or {}).items())[:4]
            ]
        return {"mode": "hotels", "entries": entries}

    places = ctx.current_places or ([ctx.destination] if ctx.destination else [])
    entries = [get_destination_images(p, context_hint=ctx.destination) for p in places[:3]]
    return {"mode": "destination", "entries": entries}


@app.get("/api/session/{session_id}/hotel-cards")
def get_hotel_cards(session_id: str):
    """Rich hotel recommendation cards built entirely from real LiteAPI data — see
    agents/hotel_card.py. hotel_id ties detail and rates together so every field on a card
    belongs to that exact property; nothing here is invented or generic."""
    from tools.hotels import get_hotel_details
    from tools.booking import get_hotel_rates
    from agents.hotel_card import build_hotel_card

    orch = get_orchestrator(session_id)
    ctx = orch.context

    if ctx.stage == "BOOKING" and ctx.selected_hotel_id:
        ids = [ctx.selected_hotel_id]
    elif ctx.current_hotel_ids:
        ids = ctx.current_hotel_ids
    else:
        ids = list((ctx.known_hotels or {}).keys())[:4]

    cards = []
    for hotel_id in ids:
        detail = get_hotel_details(hotel_id)
        if "error" in detail:
            continue
        rates = None
        if ctx.checkin and ctx.checkout:
            rr = get_hotel_rates(hotel_id, ctx.checkin, ctx.checkout, ctx.adults or 2, "US", "USD")
            if "error" not in rr:
                rates = rr
        card = build_hotel_card(detail, rates)
        if card:
            cards.append(card)

    return {"cards": cards}


@app.post("/api/session/{session_id}/tts")
def tts(session_id: str, body: TtsBody):
    get_orchestrator(session_id)  # validates the session exists
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=503, detail="Voice output not configured")
    from tools.voice import text_to_speech

    audio_bytes = text_to_speech(body.text)
    return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg")
