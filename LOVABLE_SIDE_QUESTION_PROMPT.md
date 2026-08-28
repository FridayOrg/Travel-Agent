Paste the text below into your Lovable project's AI chat. This extends the static-answer
integration you already built.

--------------------------------------------------------------------------------

Update the handling of POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/static-answer
(used during the INTAKE/HOTEL_TRAVELLERS/HOTEL_BUDGET/HOTEL_DATES stages).

The "reply" field in its response can now also be populated in a case that previously didn't
happen: when the user typed or spoke a genuine QUESTION or side comment instead of an answer
(e.g. "what's the weather like there?" while still on the destination question). In that case:
- "resolved" may be empty or partial (whatever, if anything, could still be extracted)
- "missing" lists what's still needed
- "reply" contains a real answer to their question, ending with a steer back to the pending question
- the stage has NOT advanced — you're still on the same static question

Handle this by: rendering "reply" as a normal AI chat message (same as any other assistant
reply) whenever it's non-null, REGARDLESS of whether "missing" is empty or the stage advanced.
Keep showing the current static question's form/buttons underneath it exactly as before — don't
clear or replace them, since the user still needs to answer. This means "reply" being present is
no longer a signal that only means "we moved to the next stage" — check the "stage" field itself
(or whether "missing" is empty) to decide if you also need to swap which form is showing, fully
independent of whether "reply" has text to display.
