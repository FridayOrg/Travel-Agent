Paste the text below into your Lovable project's AI chat exactly as-is.

--------------------------------------------------------------------------------

Update the chat text/voice input so the user never has to click the Send button to
submit a typed or spoken answer — only clicking the Send icon manually should remain
optional, not required. This applies everywhere the chat input bar is used, on every
default question, not just one screen.

IMPORTANT — this does NOT change how the default-question BUTTONS behave. Buttons
keep working exactly as already implemented (selecting a button only updates local
state; the screen still only finalizes/processes once ALL of that screen's questions
have a value, via the Submit button, per the existing flow). This change is only about
removing the need to click Send for TEXT and VOICE input specifically.

TEXT INPUT

1. Pressing Enter in the chat text box submits the typed text immediately — exactly as
   if the Send icon had been clicked. The Send icon can stay visible and clickable too
   (for anyone who prefers clicking it), but Enter must always work without it.
2. Do not use a typing-pause/debounce timer to guess when someone is "done typing" —
   that causes accidental partial submissions. Enter (or an explicit Send click) is
   the completion signal, exactly like today, just without requiring the click.
3. Prevent duplicate submissions: once a submission is in flight (waiting for the
   backend response), disable further Enter/Send submissions until it resolves, and
   never fire the same message twice.

VOICE INPUT

1. When the user stops recording (or recording auto-stops), wait for the transcription
   to finish (call to POST /api/session/{session_id}/stt as already implemented).
2. Once the final transcript text comes back, submit it automatically through the exact
   same path a typed Enter-submission would use — no extra tap/click required, no
   "review before sending" step.
3. If the transcript comes back empty, don't submit anything — show a small inline
   "Didn't catch that, try again" message (as already implemented), don't auto-retry.
4. Prevent duplicate submissions here too — while a transcription/submission is in
   flight, disable starting a new recording until it resolves.

HOW A TEXT/VOICE ANSWER IS PROCESSED (unchanged from the existing flow)

Whether it's typed (Enter) or spoken (auto-submitted transcript), it goes through the
exact same handling a button click's underlying answer would — call
POST /api/session/{session_id}/static-answer with { "text": "<the text>" }, merge
"resolved" into the screen's local state (same state buttons write into), and only
once ALL required fields for that screen have a value should the screen finalize
(call the appropriate POST .../intake or .../hotel-details, per the existing
Submit-button flow) — do not finalize early just because one text/voice answer came
in, same rule that already applies to button clicks.

VERIFY

- Type an answer and press Enter (don't click Send) — confirm it submits and updates
  the relevant field's selection state, without needing a Send click.
- Record a voice answer — confirm it submits automatically the moment transcription
  finishes, without any extra click.
- Confirm this works identically on every default-question screen (intake and
  hotel-details), not just one.
- Confirm rapid double-Enter or double-tapping the mic doesn't cause a duplicate
  submission.
- Confirm the screen still only finalizes once all of its required fields have a
  value — a single text/voice answer for just one field must not skip the others.
