Paste the text below into your Lovable project's AI chat. This extends the static-answer
integration you already built.

--------------------------------------------------------------------------------

Extend the handling of POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/static-answer
one more time. A traveller can now, while on a button-based stage (INTAKE, HOTEL_TRAVELLERS,
HOTEL_BUDGET, HOTEL_DATES), ask to change something already decided earlier — e.g. "actually
can we go to Singapore instead" or "can you change the itinerary" — instead of answering the
current question or asking an unrelated question.

When this happens, the response's "stage" field will have jumped back to a completely different
(non-static) stage — typically "DESTINATION_SPOTS" — and "reply" will contain the agent's real
response to their request. Handle this exactly like any other stage transition you already
support elsewhere in the app: switch away from whatever static form was showing, render "reply"
as a normal AI chat message, and show the free-text chat input for that new stage going forward
(same as after the normal INTAKE→DESTINATION_SPOTS transition).

Important: "reply" in this case may itself contain an embedded clarifying_question JSON block
(the same {"type": "clarifying_question", ...} format documented earlier), possibly with some
plain text before it. Run it through your existing clarifying_question parsing/button-rendering
logic exactly as you already do for normal chat replies — no special-casing needed beyond
routing based on the new "stage" value.

The traveller will naturally end up back at the hotel questions on their own later (once they
reconfirm the itinerary through the normal flow) — nothing else needs to be done for that.
