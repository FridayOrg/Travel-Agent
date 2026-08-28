Paste the text below into your Lovable project's AI chat exactly as-is.

--------------------------------------------------------------------------------

Fix this bug now: on the initial intake screen (destination / traveller type / month
buttons), clicking just ONE button already produces a full assistant reply and
advances the conversation, instead of waiting until all three questions have been
answered.

ROOT CAUSE (confirmed): I tested the backend directly with a single field
("London" only, no traveller type or month) and it correctly returned
{"resolved": {"destination": "London"}, "missing": ["travellers", "month"],
"reply": null, "stage": "INTAKE", ...} — it does NOT finalize or advance on a
partial answer. This proves the backend is working correctly; the app is either
calling the wrong endpoint on a single click, or treating a response as "done"
when it shouldn't.

HOW THIS SCREEN IS SUPPOSED TO WORK

1. Every button click (or typed/voice answer) on this screen calls
   POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/static-answer
   with { "text": "<the clicked option or typed/spoken text>" }.
2. The response looks like:
   { "resolved": {...whichever of destination/travellers/month this answer resolved...},
     "missing": [...whichever of "destination", "travellers", "month" are still unset...],
     "reply": string | null,
     ...state }
3. Merge "resolved" into local app state (don't discard previously answered fields —
   accumulate across multiple clicks/messages, same as the destination/traveller-type/
   month combined form already does visually).
4. Only when "missing" comes back as an EMPTY array should the app finalize: call
   POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/intake
   with { "destination": ..., "traveler_type": ..., "month": ... } (note the field
   is "traveler_type", not "travellers_type" or "travellers"), using the accumulated
   values. This call's response includes the real "reply" — that's what should
   trigger showing the assistant's first message and moving off this screen.
5. While "missing" is non-empty, do NOT show any assistant reply and do NOT advance
   the screen/stage — just visually reflect which options are now selected/filled in
   (like the buttons already do) and keep waiting for the rest.
6. Audit the current code path for this screen: find whichever click handler is
   currently causing a full reply/advance after only one answer, and fix it to follow
   steps 1-5 above exactly. This must work the same way regardless of whether the
   traveller answers by clicking a button, typing, or using voice input for any of
   the three fields, in any order.
