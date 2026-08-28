Paste the text below into your Lovable project's AI chat exactly as-is. This REPLACES any
earlier instructions that said to call the backend on every single button click — that is
wrong. Only Submit should trigger backend processing.

--------------------------------------------------------------------------------

Fix both multi-question screens (the initial intake screen, and the hotel-details screen)
so that clicking an option only SELECTS it locally — it must NOT call the backend or
process anything yet. Only clicking the Submit button, once all questions on that screen
have an answer, should send everything to the backend and process the result.

====================================================================
SCREEN 1 — INITIAL INTAKE (Destination / Traveller type / Month)
====================================================================

1. Clicking a Destination button, a Traveller type button, or a Month button (or filling
   in the "Other" text field for any of them) ONLY updates local component state to mark
   that option as selected/highlighted. Do NOT call any API endpoint on these clicks.
2. If the traveller instead types or speaks a free-text answer in the chat box for any of
   these three questions, call
     POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/static-answer
     Body: { "text": "<typed/spoken text>" }
   to interpret it, and merge whatever comes back in "resolved" into the same local
   selection state as a button click would (so typed/voice answers behave identically to
   clicking the matching button).
3. Show a Submit button. Keep it disabled until all three fields (destination, traveller
   type, month) have a value in local state (from a button click, typed text, or voice).
4. When Submit is clicked, call:
     POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/intake
     Body: { "destination": string, "traveler_type": string, "month": string }
   (field name is exactly "traveler_type"). Show the response's "reply" as the assistant's
   first message and advance to the chat/itinerary stage.
5. Nothing should be sent to the backend, and no assistant reply should appear, until
   Submit is actually clicked.

====================================================================
SCREEN 2 — HOTEL DETAILS (Travellers / Budget / Dates, after itinerary confirmed)
====================================================================

1. Clicking a Travellers button, a Budget button, or picking dates in the date-range
   picker (or filling in "Other" text) ONLY updates local component state. Do NOT call
   any API endpoint on these interactions.
2. If the traveller instead types or speaks a free-text answer, call
     POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/static-answer
     Body: { "text": "<typed/spoken text>" }
   and merge whatever comes back in "resolved" into the same local selection state.
3. Show a Submit button. Keep it disabled until all three fields (travellers, budget,
   dates) have a value in local state.
4. When Submit is clicked, call:
     POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/hotel-details
     Body: { "adults": number, "kids": number, "budget_level": string,
             "checkin": "YYYY-MM-DD", "checkout": "YYYY-MM-DD" }
   Use a 5+ minute client-side timeout and show a clear loading state — this triggers the
   real hotel search. Show the response's "reply" (curated hotel picks) as the next
   assistant message, then advance the screen (stage becomes "HOTEL_SEARCH").
5. Nothing should be sent to the backend, and hotel search must not run, until Submit is
   actually clicked.

====================================================================
VERIFY BOTH
====================================================================

Screen 1: click Destination, then Traveller type, then Month one at a time — confirm
nothing happens after each click except that option becoming visually selected, and
Submit only becomes enabled after all three. Click Submit — confirm only then does the
assistant's welcome reply appear.

Screen 2: same check — select travellers, then budget, then dates one at a time, confirm
nothing happens until Submit is clicked, and only then does hotel search run.
