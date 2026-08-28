Paste the text below into your Lovable project's AI chat exactly as-is.

--------------------------------------------------------------------------------

Fix two screens so each one only proceeds once ALL of its fields are answered — right
now answering just one field on either screen already triggers a reply and advances,
which is wrong.

====================================================================
SCREEN 1 — INITIAL INTAKE (Destination / Traveller type / Month)
====================================================================

REQUIRED BEHAVIOR

1. Show all three question groups together on one screen: Destination buttons,
   Traveller type buttons, Month buttons — each with an "Other" option that reveals a
   text input.
2. Clicking a button (or typing/speaking an answer) for ANY ONE of the three only
   selects/fills in that one field locally — it must NOT trigger a reply or leave this
   screen. The other two fields stay exactly as they were.
3. Every answer (click, typed text, or voice) calls:
     POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/static-answer
     Body: { "text": "<the clicked option or typed/spoken text>" }
   Response: { "resolved": {...whichever field(s) this answer matched...},
     "missing": [...whichever of "destination", "travellers", "month" are still
     unset...], "reply": string|null, ...state }
   Merge "resolved" into local state (accumulate — never discard a field already
   answered by a previous click).
4. As long as "missing" is non-empty, stay on this screen. Do not show any assistant
   reply, do not navigate away, do not call any other endpoint.
5. Only once ALL THREE are filled in (check this from your own accumulated local
   state, not just one response's "missing", since a single answer may only resolve
   one field), finalize: call
     POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/intake
     Body: { "destination": string, "traveler_type": string, "month": string }
   (field name is exactly "traveler_type" — not "travellers_type" or "travellers").
   This call's response contains the real "reply" — show THAT as the assistant's first
   message, and only then advance to the chat/itinerary stage.
6. Audit the current click handler for this screen and fix it to follow steps 2-5
   exactly, regardless of which field is answered first/second/third, and regardless
   of click vs typed vs voice input.

====================================================================
SCREEN 2 — HOTEL DETAILS (Travellers / Budget / Dates, after itinerary confirmed)
====================================================================

REQUIRED BEHAVIOR

1. Show all three question groups together on one screen:
   - "How many travellers?" — buttons: "2 Adults", "2 Adults + 1 Kid", "Other" (Other
     reveals Adults/Kids number inputs)
   - "What's your budget range per night?" — buttons: "Budget", "Mid-range", "Luxury",
     "Other" (Other reveals a free-text input)
   - A check-in/check-out date range picker
2. Answering ANY ONE of the three only fills that field locally — it must NOT trigger
   hotel search or leave this screen. The other two fields stay exactly as they were.
3. Every answer (click, typed text, or voice) calls:
     POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/static-answer
     Body: { "text": "<the clicked option or typed/spoken text>" }
   Response: { "resolved": {...whichever of "adults"+"kids", "budget_level", "checkin"+
     "checkout" this answer resolved...}, "missing": [...whichever of "travellers",
     "budget_level", "dates" are still unresolved...], "reply": string|null, ...state }
   Merge "resolved" into local state (accumulate). The backend also persists resolved
   fields itself, but you still need to track "missing" locally to know when to stop
   showing this screen.
4. As long as "missing" is non-empty, stay on this screen. Do not call hotel search, do
   not show any assistant reply, do not navigate away.
5. Only once ALL THREE are filled in (travellers AND budget AND dates), finalize: call
     POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/hotel-details
     Body: { "adults": number, "kids": number, "budget_level": string,
             "checkin": "YYYY-MM-DD", "checkout": "YYYY-MM-DD" }
   This triggers the real hotel search — use a 5+ minute client-side timeout and show a
   clear loading state (cold start + live hotel API + AI reasoning can take a while).
   Its response's "reply" is the curated hotel picks — show THAT as the next assistant
   message, and only then advance the screen (stage becomes "HOTEL_SEARCH").
6. Audit the current click/answer handler for this screen and fix it to follow steps
   2-5 exactly, regardless of which field is answered first/second/third, and
   regardless of click vs typed vs voice input.

====================================================================
VERIFY BOTH
====================================================================

Screen 1: reload the app, click only "Destination" — confirm nothing happens except
that button appearing selected. Click only "Traveller type" next — still nothing
advances. Only after the third field (Month) should the welcome reply appear and the
screen advance.

Screen 2: after confirming an itinerary, fill in only "Number of travellers" — confirm
nothing happens except that field appearing filled. Answer only "Budget" next — still
no search triggered. Only after the third field (Dates) should hotel search run and
real hotel recommendations appear.
