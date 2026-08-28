Paste the text below into your Lovable project's AI chat. This is a BREAKING CHANGE to the
existing hotel-question screens — the old sequential endpoints/stages no longer exist.

--------------------------------------------------------------------------------

The backend has changed how hotel details are collected: instead of three sequential
screens (number of travellers, then budget, then dates, one at a time), they are now
collected together as ONE combined form — the same way the initial destination/travellers/
month intake screen already works.

WHAT CHANGED

- The stage names "HOTEL_TRAVELLERS", "HOTEL_BUDGET", and "HOTEL_DATES" no longer exist. There
  is now a single stage: "HOTEL_DETAILS".
- The endpoints POST /api/session/{id}/hotel-travellers, .../hotel-budget, and .../hotel-dates
  no longer exist. There is now one combined endpoint:
    POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/hotel-details
    Body: { "adults": number, "kids": number, "budget_level": string, "checkin": "YYYY-MM-DD", "checkout": "YYYY-MM-DD" }
    Response: { "reply": string, ...state } — same shape as the old hotel-dates endpoint (this
    call triggers the actual hotel search, same as before).

REQUIRED UI CHANGE

When "stage" is "HOTEL_DETAILS", show all three questions together on one screen (mirroring
however you already render the combined intake form):
  1. "How many travellers?" — buttons: "2 Adults", "2 Adults + 1 Kid", "Other" (Other reveals
     two number inputs: Adults, Kids)
  2. "What's your budget range per night?" — buttons: "Budget", "Mid-range", "Luxury", "Other"
     (Other reveals a free-text input for a custom description)
  3. A check-in/check-out date range picker

Let the user answer these three in any order, by any mix of clicking, typing, or voice (see the
unified-input-handling prompt from before — this screen is Category A, so typed/voice text still
routes to POST .../static-answer, not directly to this endpoint). Once all three have a value —
by whatever combination of button clicks, typed answers, or voice — call POST .../hotel-details
with all three collected values together, exactly once, to finalize and trigger hotel search.

STATIC-ANSWER BEHAVIOR FOR THIS COMBINED STAGE

POST .../static-answer during "HOTEL_DETAILS" now works like the intake form's partial-answer
pattern: a single utterance might resolve one, two, or all three fields at once (e.g. "2 adults,
mid-range, checking in October 10th to the 15th" resolves everything in one message). Its
"resolved" object will contain whichever of these keys got matched this turn: "adults"+"kids",
"budget_level", "checkin"+"checkout". Its "missing" array will contain whichever of "travellers",
"budget_level", "dates" are still unresolved (note: the backend already persists resolved fields
onto the session server-side as they come in across multiple turns, so you don't need to track
partial state yourself for this one — but you DO still need to detect when "missing" is empty vs
non-empty each time to know whether to keep showing the form or move on: once a response comes
back with "missing": [] and "stage" has changed to "HOTEL_SEARCH", treat it exactly like the old
hotel-dates transition — the "reply" field will have the curated hotel recommendations).

Everything else about static-answer (question / change_request handling) works the same as
already documented for this stage.
