Paste the text below into your Lovable project's AI chat exactly as-is. This REPLACES both
earlier instructions about Submit behavior (the "always require Submit" one and the "never
require Submit" one) — this is the final, correct rule.

--------------------------------------------------------------------------------

Fix both multi-question screens (initial intake: Destination/Traveller type/Month, and
hotel-details: Travellers/Budget/Dates) with this exact rule:

- If the user answers a question by clicking a button, that answer is only selected/
  highlighted locally — clicking Submit is still required to finalize and move on.
- If the user answers a question by typing or speaking it, that answer is processed
  immediately — no Submit click is needed for that.

In other words: Submit is only a requirement for button-only answers. The moment a typed
or spoken answer is what completes the last remaining field on the screen, finalize
immediately and automatically — don't wait for a Submit click in that case, even if the
other fields on the same screen were filled by clicking buttons.

REQUIRED BEHAVIOR (both screens)

1. Clicking a button only selects/highlights that field's value locally — never finalizes
   anything by itself, and never fires a static-answer call for a plain button click.
2. Typed or spoken text always calls
     POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/static-answer
     Body: { "text": "<typed/spoken text>" }
   and merges "resolved" into the same local state a button click would.
3. After a typed/spoken answer resolves (step 2), immediately check: are ALL of this
   screen's required fields now filled (regardless of whether some were filled by button
   clicks earlier)?
   - If NO: stay on the screen, no further action.
   - If YES: immediately (no Submit click needed) call the screen's finalize endpoint —
     see step 5 below.
4. If the user instead finishes the screen purely by clicking buttons (the last field to
   get filled was a button click, not typed/spoken text), do NOT auto-finalize — wait for
   an explicit Submit button click. Keep the Submit button visible and enabled once all
   fields have a value, exactly as before.
5. Finalize endpoints (used either automatically after a completing typed/voice answer, or
   after a Submit click):
     Intake screen: POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/intake
       Body: { "destination": string, "traveler_type": string, "month": string }
     Hotel-details screen: POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/hotel-details
       Body: { "adults": number, "kids": number, "budget_level": string, "checkin": "YYYY-MM-DD", "checkout": "YYYY-MM-DD" }
       (use a 5+ minute timeout with a loading state — this triggers the real hotel search)
   Show the response's "reply" as the next assistant message and advance the screen.
6. Prevent duplicate finalize calls — once finalize has fired for a screen (whether via
   auto-advance or a Submit click), don't fire it again for that screen.
7. This must hold for any order/mix of fields — e.g. two fields answered by button plus
   the third by typing should auto-finalize (rule 3); three fields answered entirely by
   button should wait for Submit (rule 4); a field re-typed after already being set by a
   button should still trigger the auto-finalize check.

VERIFY

Screen 1: click Destination, click Traveller type, click Month — confirm it does NOT
auto-advance, and only proceeds after clicking Submit.
Then reload: click Destination, click Traveller type, then TYPE the Month answer —
confirm it auto-advances the instant the typed answer resolves, no Submit click.

Screen 2: same two checks — all-button entry waits for Submit; any entry that ends with a
typed/spoken answer completing the set auto-advances without Submit.
