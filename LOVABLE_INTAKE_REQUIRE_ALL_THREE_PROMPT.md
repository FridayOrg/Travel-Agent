Paste the text below into your Lovable project's AI chat exactly as-is.

--------------------------------------------------------------------------------

Fix the initial intake screen: it must require ALL THREE fields — Destination,
Traveller type, and Month — to be selected before the conversation advances.
Right now selecting/clicking just one (or two) of them already produces a full
assistant reply and moves past this screen, which is wrong.

REQUIRED BEHAVIOR

1. Show all three question groups together on one screen (as already designed):
   Destination buttons, Traveller type buttons, Month buttons — each with an
   "Other" option that reveals a text input.
2. Clicking a button (or typing/speaking an answer) for ANY ONE of the three only
   selects/fills in that one field locally — it must NOT trigger a reply or leave
   this screen. The other two fields stay exactly as they were.
3. Every answer (click, typed text, or voice) calls:
     POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/static-answer
     Body: { "text": "<the clicked option or typed/spoken text>" }
   Response: { "resolved": {...whichever field(s) this answer matched...},
     "missing": [...whichever of "destination", "travellers", "month" are still
     unset...], "reply": string|null, ...state }
   Merge "resolved" into local state (accumulate — never discard a field that was
   already answered by a previous click).
4. As long as "missing" is non-empty, stay on this screen. Do not show any
   assistant reply, do not navigate away, do not call any other endpoint.
5. Only once ALL THREE are filled in (destination AND traveller type AND month —
   check this from your own accumulated local state, not just one response's
   "missing" field, since a single answer may only resolve one field) should you
   finalize: call
     POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/intake
     Body: { "destination": string, "traveler_type": string, "month": string }
   (field name is exactly "traveler_type" — not "travellers_type" or "travellers").
   This call's response contains the real "reply" — THAT is what should be shown
   as the assistant's first message, and only then should the screen advance to
   the chat/itinerary stage.
6. Audit whatever code currently handles a click on this screen and fix it to
   follow steps 2-5 exactly — this must hold no matter which field is answered
   first, second, or third, and no matter whether by click, typed text, or voice.

VERIFY: reload the app, click only "Destination", confirm nothing happens except
that button appearing selected. Click only "Traveller type" next, confirm still
nothing advances. Only after clicking "Month" (the third/last field) should the
assistant's welcome reply appear and the screen advance.
