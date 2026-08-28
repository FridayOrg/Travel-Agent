Paste the text below into your Lovable project's AI chat.

--------------------------------------------------------------------------------

BUG: "Sorry — I could not reach the travel service. Request failed (404)"

This happens when the app calls POST /api/session/{session_id}/static-answer
(or any other /api/session/{session_id}/... endpoint) with a session_id that is
missing, empty, or the literal string "undefined" — i.e. the request goes out
before a session has actually been created, or the app lost track of the
session_id it was given earlier. I confirmed the backend itself is working
correctly (tested live with the exact same input and got a valid 200 response
with resolved fields) — this is purely a frontend state/timing bug, not a
backend issue, and it affects typed input, button clicks, and voice input
equally (whichever happens to fire first, before the session exists).

REQUIRED FIX

1. On app load (before showing any input, buttons, or chat), call
   POST https://travel-agent-mw5e.onrender.com/api/session ONCE, wait for the
   response, and store the returned "session_id" in app state (not just a
   local variable inside one component — it needs to be available to every
   screen/stage that makes a backend call).
2. Disable/block ALL input (buttons, text box, mic) until that session_id is
   confirmed present in state. Show a brief loading state on first load if
   needed, rather than letting the user submit anything before the session
   exists.
3. Every subsequent call to any /api/session/{session_id}/... endpoint
   (static-answer, message, hotel-details, stt, tts, images, hotel-cards,
   state) must read session_id from that shared app state — audit every
   call site and make sure none of them have a stale, hardcoded, or
   uninitialized session_id.
4. If a call ever does come back 404 with "Unknown session_id" (e.g. the
   session expired or the backend restarted), automatically create a new
   session (repeat step 1) and either retry the request or prompt the user
   to restart — don't just show a raw error.
5. Verify by reproducing the original bug: reload the app, and as fast as
   possible try clicking a button, typing, or using voice input before the
   destinations/buttons have finished rendering — confirm it no longer
   404s, because input is now blocked until session_id is ready.
