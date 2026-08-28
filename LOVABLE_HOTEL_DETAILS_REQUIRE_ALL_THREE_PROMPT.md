Paste the text below into your Lovable project's AI chat exactly as-is.

--------------------------------------------------------------------------------

Fix the hotel-details screen (shown after the itinerary is confirmed): it must require
ALL THREE fields — Number of travellers, Budget, and Dates — to be filled in before hotel
search runs. Selecting/answering just one (or two) of them must NOT trigger hotel search
or move past this screen.

REQUIRED BEHAVIOR

1. Show all three question groups together on one screen:
   - "How many travellers?" — buttons: "2 Adults", "2 Adults + 1 Kid", "Other" (Other reveals
     Adults/Kids number inputs)
   - "What's your budget range per night?" — buttons: "Budget", "Mid-range", "Luxury", "Other"
     (Other reveals a free-text input)
   - A check-in/check-out date range picker
2. Clicking a button (or typing/speaking an answer) for ANY ONE of the three only
   selects/fills in that one field locally — it must NOT trigger hotel search or leave this
   screen. The other two fields stay exactly as they were.
3. Every answer (click, typed text, or voice) calls:
     POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/static-answer
     Body: { "text": "<the clicked option or typed/spoken text>" }
   Response: { "resolved": {...whichever of "adults"+"kids", "budget_level", "checkin"+
     "checkout" this answer resolved...}, "missing": [...whichever of "travellers",
     "budget_level", "dates" are still unresolved...], "reply": string|null, ...state }
   Merge "resolved" into local state (accumulate — never discard a field already answered
   by a previous click). Note: the backend also persists resolved fields itself, but you
   still need to track "missing" locally to know when to stop showing this screen.
4. As long as "missing" is non-empty, stay on this screen. Do not call hotel search, do not
   show any assistant reply, do not navigate away.
5. Only once ALL THREE are filled in (travellers AND budget AND dates), finalize: call
     POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/hotel-details
     Body: { "adults": number, "kids": number, "budget_level": string,
             "checkin": "YYYY-MM-DD", "checkout": "YYYY-MM-DD" }
   This is what actually triggers the real hotel search — use a 5+ minute client-side
   timeout and show a clear loading state, since this can take a while (cold start + live
   hotel API + AI reasoning). Its response contains the real "reply" with curated hotel
   picks — THAT is what should be shown as the next assistant message, and only then should
   the screen advance to showing hotel cards (stage becomes "HOTEL_SEARCH").
6. Audit whatever code currently handles a click/answer on this screen and fix it to follow
   steps 2-5 exactly — this must hold no matter which field is answered first, second, or
   third, and no matter whether by click, typed text, or voice.

VERIFY: click/fill only "Number of travellers", confirm nothing happens except that field
appearing filled in. Answer only "Budget" next, confirm still nothing advances or searches.
Only after the third field (Dates) is filled in should hotel search run and real hotel
recommendations appear.
