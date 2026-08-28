Paste the text below into your new Lovable project's AI chat.
Before pasting, replace `<BACKEND_URL>` with your deployed backend's public URL
(e.g. https://your-app.onrender.com) once it's hosted.

--------------------------------------------------------------------------------

Add an AI travel-planning chat feature to this app. There is already a working backend —
a FastAPI multi-agent travel advisor — hosted at `<BACKEND_URL>`. Do not build any AI logic
yourself; only build the frontend chat UI and wire it to these existing REST endpoints.

GENERAL RULES
- All requests/responses are JSON. Base URL: `<BACKEND_URL>`
- A conversation is a "session" — call POST /api/session once at the start to get a
  session_id, then include that session_id in every subsequent call's URL.
- Every endpoint that advances the conversation returns a common state shape:
  {
    "stage": string,              // current conversation stage, see STAGES below
    "destination": string|null,
    "profile": object,            // traveller profile fields collected so far
    "trip_duration_days": number|null,
    "selected_hotel_name": string|null,
    "booking_confirmed": boolean
  }
  Endpoints that also produce a chat reply add a "reply" field (string) to that same object.

ENDPOINTS

1. POST /api/session
   No body. Response: { "session_id": string, ...state }
   Call once when the chat UI first opens.

2. POST /api/session/{session_id}/intake
   Body: { "destination": string, "traveler_type": string, "month": string }
   Ask the user 3 questions first as clickable option buttons (not free text):
     - "Where would you like to go?" options: Dubai, London, Other (free text if Other)
     - "Who are you travelling with?" options: Family, Friends, Solo, Couple
     - "When are you planning to travel?" options: Aug-Sep, Oct-Nov, Dec-Jan, Other (free text if Other)
   Submit all three together as this call. Response: { "reply": string, ...state }
   Render "reply" as the AI's first chat message.

3. POST /api/session/{session_id}/message
   Body: { "text": string }
   Use this for every free-text chat turn after intake (the user typing in a normal chat box).
   Response: { "reply": string, ...state }

   IMPORTANT — the "reply" string sometimes contains ONLY a JSON object instead of plain text,
   in this exact shape:
     {"type": "clarifying_question", "stage": "...", "question": "...", "options": ["...", "..."], "allow_other": true|false}
   When you detect this (reply is valid JSON with "type": "clarifying_question"), render it as
   the question text plus clickable buttons for each option instead of plain text. When the user
   clicks one, send that option's exact label back via POST .../message as { "text": "<label>" }.
   If they click an option that means "other" (label contains "other"), show a text input instead
   and send whatever they type.

   There is also a second special reply marker, exactly this string with no other text:
     {"type": "booking_form"}
   When you see this, instead of showing chat text, render a small form with three fields:
   Full Name, Email, Phone — validate non-empty name, valid email format, and a valid phone
   number before allowing submit. On submit, send it as a normal chat message via
   POST .../message with text set to exactly:
     "My name is {name}. Email: {email}. Phone: {phone}."

4. POST /api/session/{session_id}/hotel-travellers
   Body: { "adults": number, "kids": number }
   Static question UI (buttons, not an LLM call): "How many travellers?" — options "2 Adults",
   "2 Adults + 1 Kid", "Other" (Other reveals two number inputs: Adults, Kids).
   Response: { ...state } (no "reply" field — just move to the next static question).

5. POST /api/session/{session_id}/hotel-budget
   Body: { "budget_level": string }
   Static question: "What's your budget range per night?" — options "Budget", "Mid-range",
   "Luxury", "Other" (Other reveals a text input for a custom description).
   Response: { ...state }

6. POST /api/session/{session_id}/hotel-dates
   Body: { "checkin": "YYYY-MM-DD", "checkout": "YYYY-MM-DD" }
   Static question: a date-range picker, not buttons — "What are your check-in and check-out
   dates?" Submitting this triggers the actual hotel search (can take up to a few minutes on a
   slow day, show a loading state), so use a generous client-side timeout (5+ minutes) here and
   on the /message endpoint, not the usual ~30s default, and don't treat "still loading" as an
   error until then. Response: { "reply": string, ...state }

7. GET /api/session/{session_id}/hotel-cards
   No body. Response: { "cards": [ { hotel_id, name, city, address, star_rating, guest_rating,
   review_count, description, facilities: string[], images: string[], price: { amount, currency,
   room_name, board_name, taxes_and_fees: [...], refundable, cancellation_deadline } | null }, ... ] }
   Call this whenever stage is "HOTEL_SEARCH" or "BOOKING" to render real hotel recommendation
   cards (image, name, location, star/guest rating, review count, facilities, price, meal plan,
   refundability). Never invent or use placeholder hotel data — every field comes from this
   endpoint or is omitted if null. Each card needs a "Select Hotel" button that sends
   { "text": "I'll go with {name}." } via POST .../message.

8. GET /api/session/{session_id}/images
   No body. Response: { "mode": "destination"|"hotels", "entries": [ { "label": string,
   "images": [ { "url": string, "caption": string|null, "source_title": string|null } ] }, ... ] }
   Optional: use this to show a supplementary photo gallery of the destination/attractions being
   discussed (mode "destination") or the hotels being recommended (mode "hotels") alongside the
   chat. Only display an entry once its images have actually loaded (preload and drop any URL
   that fails) — never show a broken image or an empty gallery card.

9. POST /api/session/{session_id}/tts (optional — only if you want voice playback)
   Body: { "text": string }. Response: audio/mpeg binary (an MP3). Play it directly as an <audio>
   source. Skip this endpoint entirely if voice output isn't wanted.

STAGES (value of "stage" in the state object) — use these to decide which UI to show:
  INTAKE -> DESTINATION_SPOTS -> HOTEL_TRAVELLERS -> HOTEL_BUDGET -> HOTEL_DATES ->
  HOTEL_SEARCH -> BOOKING
- INTAKE: show the 3-question intake form (call intake endpoint on submit).
- DESTINATION_SPOTS: normal free-text chat (agent suggests spots, asks trip duration, builds an
  itinerary, then asks "Are you okay with this itinerary?" as a clarifying_question).
- HOTEL_TRAVELLERS / HOTEL_BUDGET / HOTEL_DATES: show the matching static question UI described
  above instead of a free-text box.
- HOTEL_SEARCH: free-text chat + call GET hotel-cards to show real hotel recommendations. The
  agent will also ask "Are you happy with this hotel?" as a clarifying_question after a hotel is
  selected, and may hand off to the booking_form marker described in endpoint 3.
- BOOKING: free-text chat continues here (rate confirmation, final "yes, book it" confirmation).
  Once state.booking_confirmed becomes true, show a closing message:
  "Your booking is confirmed! Have a wonderful trip. Happy journey! ✈️"

Build a clean, on-brand chat UI (whatever this app's existing design language is) with a chat
message list, a text input, and inline buttons/forms for the structured steps above. Keep replies
left-aligned as AI messages and user input right-aligned, standard chat conventions. Do not
fabricate any hotel/destination facts — only render what the API actually returns.
