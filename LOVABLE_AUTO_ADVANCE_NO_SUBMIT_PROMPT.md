Paste the text below into your Lovable project's AI chat exactly as-is. This REPLACES the
earlier "require an explicit Submit click" instruction — that is no longer wanted.

--------------------------------------------------------------------------------

Fix both multi-question screens (initial intake: Destination/Traveller type/Month, and
hotel-details: Travellers/Budget/Dates) so they proceed automatically the moment all of
that screen's fields have a value — from ANY combination of button clicks, typed text, or
voice — WITHOUT requiring the user to click Submit. Right now it's stopping and waiting
for an explicit Submit click even after every field is already answered — remove that
wait entirely.

REQUIRED BEHAVIOR (both screens)

1. Clicking a button still only selects/highlights that field's value locally (unchanged).
2. Typed or spoken text still calls
     POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/static-answer
     Body: { "text": "<typed/spoken text>" }
   and merges "resolved" into the same local state a button click would (unchanged).
3. After EVERY answer (a button click OR a resolved text/voice answer), immediately check:
   are ALL of this screen's required fields now filled in local state?
   - If NO: do nothing further — stay on the screen, no reply shown, no API call beyond
     the static-answer above.
   - If YES: immediately (no click needed, no waiting) call the screen's finalize
     endpoint using the accumulated values:
       Intake screen: POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/intake
         Body: { "destination": string, "traveler_type": string, "month": string }
       Hotel-details screen: POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/hotel-details
         Body: { "adults": number, "kids": number, "budget_level": string, "checkin": "YYYY-MM-DD", "checkout": "YYYY-MM-DD" }
         (use a 5+ minute timeout with a loading state — this triggers the real hotel search)
   Show that call's "reply" as the next assistant message and advance the screen.
4. Prevent duplicate finalize calls: once the finalize call has fired for a screen, don't
   fire it again even if another answer comes in right after (e.g. from a slightly delayed
   voice transcript) — track a simple "already finalized this screen" flag per screen.
5. The Submit button may remain visible for anyone who wants to press it manually once all
   fields are filled, but it must NOT be required — auto-advance on the last field being
   filled, whichever way it was filled, is the primary path now.
6. This must work no matter which field is answered first/second/third, and no matter the
   mix of click vs typed vs voice across the three fields on either screen.

VERIFY

Screen 1: click Destination, then Traveller type, then type or speak the Month answer as
the last one — confirm the welcome reply appears immediately once that third answer
resolves, with no Submit click involved. Try a different order and a different mix
(e.g. type Destination, click Traveller type, click Month) — same result each time.

Screen 2: same check — mix clicks and typed/spoken answers for travellers/budget/dates,
confirm hotel search fires automatically the instant the third field is filled, no Submit
click needed.
