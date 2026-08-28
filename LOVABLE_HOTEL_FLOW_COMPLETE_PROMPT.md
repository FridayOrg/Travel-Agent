Paste the text below into your Lovable project's AI chat exactly as-is. This REPLACES any
earlier instructions about hotel-travellers/hotel-budget/hotel-dates screens — those
endpoints no longer exist.

--------------------------------------------------------------------------------

Fix the hotel flow end-to-end: after the itinerary is confirmed, the traveller should see a
form to enter travellers/budget/dates, then real hotel recommendations with photos, then be
able to select one — none of this is currently showing. Implement all of the following exactly.

IMPORTANT: if any part of the current code references these endpoints, DELETE that code —
they no longer exist and will 404:
  POST /api/session/{id}/hotel-travellers
  POST /api/session/{id}/hotel-budget
  POST /api/session/{id}/hotel-dates
They have been replaced by ONE combined step described below.

STEP 1 — STAGE "HOTEL_DETAILS" (after the itinerary is confirmed)

When state.stage is "HOTEL_DETAILS", show ONE combined form with three questions together
(same pattern as the initial intake form):
  1. "How many travellers?" — buttons: "2 Adults", "2 Adults + 1 Kid", "Other" (Other reveals
     two number inputs: Adults, Kids)
  2. "What's your budget range per night?" — buttons: "Budget", "Mid-range", "Luxury", "Other"
     (Other reveals a free-text input)
  3. A check-in/check-out date range picker

Every answer (button click, typed text, or voice) on this screen — for any of the three
questions, in any order — calls:
  POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/static-answer
  Body: { "text": "<answer text>" }
  Response: { "resolved": {...whichever of "adults"+"kids", "budget_level", "checkin"+
    "checkout" this answer resolved...}, "missing": [...whichever of "travellers",
    "budget_level", "dates" are still unresolved...], "reply": string|null, ...state }

Keep showing the form and merging "resolved" into local state until "missing" is empty. The
backend also persists resolved fields itself as they come in, so you don't need to worry about
losing progress across turns — but you DO need to check "missing" each time to know whether to
keep showing the form.

Once all three are known (either from "missing": [] on a static-answer response, or once
you've collected all three via buttons yourself), call:
  POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/hotel-details
  Body: { "adults": number, "kids": number, "budget_level": string,
          "checkin": "YYYY-MM-DD", "checkout": "YYYY-MM-DD" }
  Response: { "reply": string, ...state } — this triggers the real hotel search, can take up
  to a few minutes on a slow day (Render free-tier cold start + live hotel API + AI reasoning).
  Use a 5+ minute client-side timeout on this call and show a clear loading state — do not
  treat "still loading" as an error before then.

Once this responds, "stage" will be "HOTEL_SEARCH" and "reply" contains the agent's curated
hotel recommendations — show it as the next chat message, then proceed to Step 2.

STEP 2 — STAGE "HOTEL_SEARCH" (showing real hotel cards with photos)

Whenever state.stage is "HOTEL_SEARCH" (after step 1, and after every subsequent message while
still in this stage), call:
  GET https://travel-agent-mw5e.onrender.com/api/session/{session_id}/hotel-cards
  Response: { "cards": [ { hotel_id, name, city, address, star_rating, guest_rating,
    review_count, description, facilities: string[], images: string[],
    price: { amount, currency, room_name, board_name, taxes_and_fees: [...], refundable,
    cancellation_deadline } | null }, ... ] }

Render each card with: main image (images[0]), name, star_rating, guest_rating (out of 10) +
review_count, address, a short excerpt of description, a few facilities as tags/chips, and the
price (amount + currency, room_name, board_name) if present. Never invent or placeholder any
field — only show what the API actually returned, and omit price if it's null.

Each card MUST have a "Select Hotel" button. Clicking it sends:
  POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/message
  Body: { "text": "I'll go with {name}." }   (use the card's exact "name")
Treat this exactly like a normal chat message — show it as a user message bubble, then show
the response's "reply" as the next assistant message. The backend will move state.stage to
"BOOKING" once the selection is confirmed.

Also optionally call GET .../images (mode "hotels") for a supplementary photo gallery beside
the chat — same auth/session pattern, entries have {label, images: [{url, caption,
source_title}]}. This is optional polish; the hotel-cards images above are the primary source
and are required.

STEP 3 — STAGE "BOOKING"

Continue as normal free-text chat (rate confirmation, guest details, final "yes, book it").
When the reply is exactly {"type": "booking_form"} (no other text), show a structured form
(Name, Email, Phone) instead of a chat bubble, and submit the filled values as a normal chat
message once submitted. Once state.booking_confirmed becomes true, show a closing message:
"Your booking is confirmed! Have a wonderful trip. Happy journey! ✈️"

VERIFY: walk through the whole flow yourself after implementing — confirm an itinerary, fill
in the combined hotel-details form (mixing a button click and a typed answer), confirm real
hotel cards with actual photos and prices appear, click "Select Hotel" on one, and confirm it
proceeds into booking.
