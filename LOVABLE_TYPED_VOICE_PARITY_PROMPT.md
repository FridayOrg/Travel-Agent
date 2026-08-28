Paste the text below into your Lovable project's AI chat.

--------------------------------------------------------------------------------

Fix a bug: during the guided intake/hotel question stages, clicking a suggestion button works,
but typing the equivalent answer or using voice input does nothing — the flow doesn't advance.

Good news: the matching intelligence now lives in the backend, so this frontend fix is simple —
no fuzzy-matching logic needs to be built here at all.

WHEN THIS APPLIES
Only during these stages (the ones with buttons instead of a free chat box): INTAKE (the
destination/travellers/month quiz), HOTEL_TRAVELLERS, HOTEL_BUDGET, HOTEL_DATES.
(Every other stage already goes through the normal /message chat endpoint, which the LLM agent
already understands regardless of button vs. typed vs. voice input — no change needed there.)

THE FIX
Whenever the user types text and submits, or a voice transcription completes, while the app is
in one of the four stages above:

1. Call this new endpoint instead of blocking the input or doing nothing:
   POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/static-answer
   Body: { "text": string }  — the raw typed or transcribed text, unmodified.

2. Response shape:
   {
     "resolved": { ...whichever fields the backend confidently matched from this one message... },
     "missing": [ ...ids of fields still unresolved... ],
     "reply": string | null,   // present only when resolution advanced into an LLM stage
     ...state (same "stage"/"profile"/etc. fields the other endpoints already return)
   }

3. Handle the response per stage:

   - INTAKE: "resolved" may contain any of "destination", "travellers", "month" (partial is
     fine — e.g. the user might only mention the destination). Merge whatever's present into
     the SAME accumulated-answers state you already use for button clicks (the one that
     currently waits for all three before calling POST .../intake). Once all three are present
     (from any combination of clicks, typing, or voice), call POST .../intake exactly as you
     already do. If "missing" is non-empty, just keep showing the intake form as-is (the
     buttons for the still-missing fields) — no special UI needed, the user can click, type, or
     speak the rest.

   - HOTEL_TRAVELLERS / HOTEL_BUDGET: single-field stages. If "missing" is empty, the backend
     already applied the answer AND advanced "stage" for you (same as if the matching button had
     been clicked) — just re-render based on the new "stage" value, same as after any other
     stage-advancing call. If "missing" is non-empty, nothing changed server-side; show a brief
     "Sorry, I didn't catch that — please pick an option or try rephrasing" and let them retry.

   - HOTEL_DATES: needs both "checkin" and "checkout" resolved together (e.g. "check in October
     10th, leaving the 15th"). If "missing" is empty, "reply" will be populated and "stage" will
     have advanced to HOTEL_SEARCH — render "reply" as the next chat message exactly like after
     the date-picker submission. If "missing" is non-empty, ask the user to state (or pick) the
     missing date(s).

4. Voice input: whatever your existing speech-to-text transcription produces should go through
   this exact same path — treat a completed voice transcription as equivalent to submitted typed
   text and call the same endpoint the same way. There should be no separate code path for voice
   vs. typed text at any of these four stages.

Do not implement any client-side keyword/fuzzy matching yourselves — the backend already does
this via a narrow, reliable classification step (agents/answer_matcher.py) so mandatory fields
are never silently skipped. The frontend's only job is: route text to the right endpoint for the
current stage, and handle the response the same way you already handle button-click responses.
