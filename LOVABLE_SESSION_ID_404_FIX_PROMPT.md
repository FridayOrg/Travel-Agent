Paste the text below into your Lovable project's AI chat exactly as-is.

--------------------------------------------------------------------------------

Fix this bug now: "Sorry — I could not reach the travel service. Request failed (404)"
appears when clicking a button, typing, or using voice input, especially soon after
the app loads.

ROOT CAUSE (confirmed): the app is calling
POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/static-answer
(or another /api/session/{session_id}/... endpoint) with a session_id that is
missing, empty, or the literal string "undefined" — meaning the request fires
before a session has been created, or a component lost track of the session_id.
I tested the backend directly with the same input and it returns 200 with correct
data, so the backend is not the problem — this is purely a frontend state bug.

DO THIS, EXACTLY:

1. Create ONE global session store (React Context, Zustand, or whatever state
   solution this app already uses — pick the one already in use, don't add a new
   one). It holds: sessionId (string | null), sessionReady (boolean).

2. At the top of the app (App root / a top-level provider that wraps EVERYTHING,
   not inside any individual screen or button component), on first mount:
   - call POST https://travel-agent-mw5e.onrender.com/api/session
   - on success, store the returned "session_id" into the global store and set
     sessionReady = true
   - on failure, retry automatically (e.g. retry up to 3 times with a short delay)
     and only show an error state if all retries fail

3. While sessionReady is false, the entire chat UI (all buttons, the text input,
   the mic button) must be disabled or show a loading/skeleton state. The user
   must be physically unable to click, type-submit, or record voice before
   sessionReady is true. This is the actual fix — it closes the race condition
   that causes the 404.

4. Find EVERY place in the codebase that currently calls any
   /api/session/{session_id}/... endpoint (static-answer, message, hotel-details,
   stt, tts, images, hotel-cards, state — all of them). Replace any local,
   component-scoped, prop-drilled, or duplicated session_id variable in each of
   these call sites with a read from the ONE global store created in step 1. Do
   not leave any call site with its own separate copy of session_id.

5. Add a safety net: if any of these calls ever comes back 404 with
   {"detail": "Unknown session_id"}, treat that as "the session expired" —
   automatically call POST /api/session again, store the new session_id, and
   retry the original request once. Never show the raw "Request failed (404)"
   text to the user.

6. After implementing, verify it yourself: simulate reloading the app and
   immediately interacting (click a button / type / start voice recording)
   before the destination cards have finished loading. Confirm no 404 occurs
   and the interaction either queues until session is ready or the input was
   correctly disabled until then.

Do not stop at a partial fix (e.g. only fixing the INTAKE screen) — this must
apply globally, to every screen and every input method, since session_id is
shared app-wide state, not per-screen state.
