import json
from datetime import date, timedelta

import streamlit as st

from orchestrator import Orchestrator
from static_stages import INTAKE_QUESTIONS, HOTEL_TRAVELLERS_QUESTION, HOTEL_BUDGET_QUESTION
from tools.voice import speech_to_text, text_to_speech
from config import ELEVENLABS_API_KEY

st.set_page_config(page_title="AI Travel Advisor", page_icon="🧳")

title_col, speaker_col = st.columns([5, 1])
with title_col:
    st.title("🧳 AI Travel Advisor")

if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = Orchestrator()
    st.session_state.messages = []
    st.session_state.speak_replies = False
    st.session_state.last_voice_id = None
    st.session_state.awaiting_other_input = False
    st.session_state.intake_answers = {}

with speaker_col:
    if ELEVENLABS_API_KEY:
        st.session_state.speak_replies = st.toggle(
            "🔊", value=st.session_state.speak_replies, help="Speak replies aloud"
        )
    else:
        st.caption("🔇")

orch = st.session_state.orchestrator
ctx = orch.context

OTHER_TRIGGERS = ("other", "somewhere else", "elsewhere", "specify")


def is_other_option(option: str) -> bool:
    lo = option.strip().lower()
    return any(t in lo for t in OTHER_TRIGGERS)


def parse_clarifying_question(text):
    text = (text or "").strip()
    if not (text.startswith("{") and text.endswith("}")):
        return None
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
    if (
        isinstance(data, dict)
        and data.get("type") == "clarifying_question"
        and isinstance(data.get("question"), str)
        and isinstance(data.get("options"), list)
        and all(isinstance(o, str) for o in data.get("options", []))
    ):
        return data
    return None


def add_message(role, content, audio=None):
    st.session_state.messages.append({"role": role, "content": content, "audio": audio})


def speak(text):
    if st.session_state.speak_replies and ELEVENLABS_API_KEY:
        try:
            return text_to_speech(text)
        except Exception:
            return None
    return None


def handle_user_message(user_text: str):
    """For LLM-driven stages (DESTINATION_SPOTS, HOTEL_SEARCH, BOOKING)."""
    add_message("user", user_text)
    with st.spinner("Thinking..."):
        reply = orch.send(user_text)
    cq = parse_clarifying_question(reply)
    audio = speak(cq["question"] if cq else reply)
    add_message("assistant", reply, audio)
    st.rerun()


def render_text_or_voice_input(key: str, placeholder: str = "Type or speak your answer...") -> str | None:
    """Renders a text box + mic side by side; returns the finalized answer (from typed Submit or a
    fresh voice transcription) or None if nothing's been submitted yet."""
    if ELEVENLABS_API_KEY:
        text_col, mic_col = st.columns([5, 1])
        with text_col:
            typed = st.text_input(
                "Please specify", key=f"{key}_text", label_visibility="collapsed", placeholder=placeholder,
            )
        with mic_col:
            audio = st.audio_input("mic", key=f"{key}_audio", label_visibility="collapsed")
    else:
        typed = st.text_input(
            "Please specify", key=f"{key}_text", label_visibility="collapsed", placeholder=placeholder,
        )
        audio = None

    if audio is not None:
        audio_bytes = audio.getvalue()
        last_key = f"{key}_last_audio"
        if audio_bytes != st.session_state.get(last_key):
            st.session_state[last_key] = audio_bytes
            with st.spinner("Transcribing..."):
                try:
                    transcribed = speech_to_text(audio_bytes, filename="mic.wav")
                except Exception as e:
                    transcribed = ""
                    st.error(f"Transcription failed: {e}")
            if transcribed.strip():
                return transcribed.strip()

    if st.button("Submit", key=f"{key}_submit") and typed.strip():
        return typed.strip()
    return None


def enter_llm_stage_and_render(stage: str):
    with st.spinner("Thinking..."):
        reply = orch.enter_llm_stage(stage)
    cq = parse_clarifying_question(reply)
    audio = speak(cq["question"] if cq else reply)
    add_message("assistant", reply, audio)
    st.rerun()


# ----- Chat history (LLM-generated messages only) -----
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        cq = parse_clarifying_question(msg["content"]) if msg["role"] == "assistant" else None
        is_last = i == len(st.session_state.messages) - 1

        if cq and is_last and st.session_state.awaiting_other_input:
            st.markdown(f"**{cq['question']}**")
            other_text = render_text_or_voice_input(f"other_{i}")
            if other_text:
                st.session_state.awaiting_other_input = False
                handle_user_message(other_text)
        elif cq and is_last:
            st.markdown(f"**{cq['question']}**")
            option_cols = st.columns(len(cq["options"]))
            for j, option in enumerate(cq["options"]):
                with option_cols[j]:
                    if st.button(option, key=f"cq_{i}_{j}", use_container_width=True):
                        if is_other_option(option):
                            st.session_state.awaiting_other_input = True
                            st.rerun()
                        else:
                            handle_user_message(option)
        elif cq:
            st.markdown(f"**{cq['question']}**")
        else:
            st.markdown(msg["content"])

        if msg.get("audio"):
            st.audio(msg["audio"], format="audio/mp3")

with st.sidebar:
    st.caption(f"Stage: `{ctx.stage}`")
    if ctx.profile:
        st.json(ctx.profile)
    if ctx.destination:
        st.write(f"**Destination:** {ctx.destination}")
    if ctx.selected_hotel_name:
        st.write(f"**Hotel:** {ctx.selected_hotel_name}")
    if not ELEVENLABS_API_KEY:
        st.divider()
        st.caption("Voice disabled — add ELEVENLABS_API_KEY to .env to enable it.")


# ----- Stage 1: INTAKE (batch of 4 questions, shown together) -----
def render_intake_form():
    st.markdown("**Let's get started — a few quick questions:**")
    answers = st.session_state.intake_answers

    for q in INTAKE_QUESTIONS:
        qid = q["id"]
        st.markdown(f"**{q['question']}**")

        if qid in answers:
            st.caption(f"✓ {answers[qid]}")
            continue

        if q["free_text"]:
            val = render_text_or_voice_input(f"intake_{qid}")
            if val:
                answers[qid] = val
                st.rerun()
            continue

        other_active_key = f"intake_other_active_{qid}"
        if st.session_state.get(other_active_key):
            other_val = render_text_or_voice_input(f"intake_other_{qid}")
            if other_val:
                answers[qid] = other_val
                st.session_state[other_active_key] = False
                st.rerun()
        else:
            option_cols = st.columns(len(q["options"]))
            for j, opt in enumerate(q["options"]):
                with option_cols[j]:
                    if st.button(opt, key=f"intake_{qid}_{j}", use_container_width=True):
                        if q["allow_other"] and is_other_option(opt):
                            st.session_state[other_active_key] = True
                            st.rerun()
                        else:
                            answers[qid] = opt
                            st.rerun()

    if len(answers) == len(INTAKE_QUESTIONS):
        ctx.destination = answers["destination"]
        ctx.profile["destination"] = answers["destination"]
        ctx.profile["travellers_type"] = answers["travellers"]
        ctx.profile["month"] = answers["month"]

        summary = (
            f"Destination: {answers['destination']}, Travelling with: {answers['travellers']}, "
            f"When: {answers['month']}"
        )
        add_message("user", summary)
        enter_llm_stage_and_render("DESTINATION_SPOTS")


# ----- Stage: HOTEL_TRAVELLERS -----
def finish_hotel_travellers(adults: int, kids: int, label: str):
    ctx.adults = adults
    ctx.kids = kids
    ctx.stage = "HOTEL_BUDGET"
    add_message("user", label)
    st.rerun()


def render_hotel_travellers_question():
    q = HOTEL_TRAVELLERS_QUESTION
    st.markdown(f"**{q['question']}**")

    if st.session_state.get("hotel_travellers_other_active"):
        adults = st.number_input("Adults", min_value=1, max_value=10, value=2, key="hotel_other_adults")
        kids = st.number_input("Kids", min_value=0, max_value=10, value=0, key="hotel_other_kids")
        if st.button("Submit", key="hotel_travellers_other_submit"):
            finish_hotel_travellers(int(adults), int(kids), f"{int(adults)} Adults + {int(kids)} Kid(s)")
    else:
        option_cols = st.columns(len(q["options"]))
        for j, opt in enumerate(q["options"]):
            with option_cols[j]:
                if st.button(opt, key=f"hoteltrav_{j}", use_container_width=True):
                    if opt == "Other":
                        st.session_state.hotel_travellers_other_active = True
                        st.rerun()
                    elif opt == "2 Adults":
                        finish_hotel_travellers(2, 0, opt)
                    elif opt == "2 Adults + 1 Kid":
                        finish_hotel_travellers(2, 1, opt)


# ----- Stage: HOTEL_BUDGET -----
def finish_hotel_budget(budget_label: str):
    ctx.profile["budget_level"] = budget_label
    ctx.stage = "HOTEL_DATES"
    add_message("user", budget_label)
    st.rerun()


def render_hotel_budget_question():
    q = HOTEL_BUDGET_QUESTION
    st.markdown(f"**{q['question']}**")

    if st.session_state.get("hotel_budget_other_active"):
        other_val = render_text_or_voice_input("hotel_budget_other")
        if other_val:
            st.session_state.hotel_budget_other_active = False
            finish_hotel_budget(other_val)
    else:
        option_cols = st.columns(len(q["options"]))
        for j, opt in enumerate(q["options"]):
            with option_cols[j]:
                if st.button(opt, key=f"hotelbudget_{j}", use_container_width=True):
                    if opt == "Other":
                        st.session_state.hotel_budget_other_active = True
                        st.rerun()
                    else:
                        finish_hotel_budget(opt)


# ----- Stage: HOTEL_DATES -----
def render_hotel_dates_picker():
    st.markdown("**What are your check-in and check-out dates?**")
    default_start = date.today() + timedelta(days=30)
    default_end = default_start + timedelta(days=5)
    picked = st.date_input(
        "Dates", value=(default_start, default_end), key="hotel_dates_picker",
        label_visibility="collapsed",
    )
    if isinstance(picked, tuple) and len(picked) == 2:
        checkin, checkout = picked
        if st.button("Confirm dates", key="hotel_dates_submit"):
            ctx.checkin = checkin.isoformat()
            ctx.checkout = checkout.isoformat()
            add_message("user", f"{ctx.checkin} to {ctx.checkout}")
            enter_llm_stage_and_render("HOTEL_SEARCH")
    else:
        st.caption("Pick both a check-in and check-out date.")


# ----- Chat input row for LLM-driven stages -----
def render_chat_input():
    def _submit_text():
        text = st.session_state.get("chat_text_box", "").strip()
        if text:
            st.session_state.pending_message = text
            st.session_state.chat_text_box = ""

    if ELEVENLABS_API_KEY:
        input_col, mic_col, send_col = st.columns([7, 1, 1], gap="small")
        with input_col:
            st.text_input(
                "Message", key="chat_text_box", label_visibility="collapsed",
                placeholder="Tell me about your trip...", on_change=_submit_text,
            )
        with mic_col:
            audio_input = st.audio_input("🎤", label_visibility="collapsed")
        with send_col:
            st.button("➤", on_click=_submit_text, use_container_width=True)
    else:
        st.text_input(
            "Message", key="chat_text_box", label_visibility="collapsed",
            placeholder="Tell me about your trip...", on_change=_submit_text,
        )
        audio_input = None

    if audio_input is not None:
        audio_bytes = audio_input.getvalue()
        if audio_bytes != st.session_state.last_voice_id:
            st.session_state.last_voice_id = audio_bytes
            with st.spinner("Transcribing..."):
                try:
                    transcribed = speech_to_text(audio_bytes, filename="mic.wav")
                except Exception as e:
                    transcribed = ""
                    st.error(f"Transcription failed: {e}")
            if transcribed:
                handle_user_message(transcribed)

    if st.session_state.get("pending_message"):
        pending = st.session_state.pop("pending_message")
        handle_user_message(pending)


# ----- Dispatch on stage -----
if ctx.stage == "INTAKE":
    render_intake_form()
elif ctx.stage == "HOTEL_TRAVELLERS":
    render_hotel_travellers_question()
elif ctx.stage == "HOTEL_BUDGET":
    render_hotel_budget_question()
elif ctx.stage == "HOTEL_DATES":
    render_hotel_dates_picker()
else:
    render_chat_input()
