Paste the text below into your Lovable project's AI chat exactly as-is.

--------------------------------------------------------------------------------

Fix this bug: clicking "Select Hotel" on a hotel card sometimes selects a DIFFERENT
hotel than the one that was actually clicked (e.g. clicking "Select Hotel" on card #2
in the list results in card #1's hotel being selected/booked instead).

ROOT CAUSE (likely): the hotel cards are rendered from an array (from
GET /api/session/{id}/hotel-cards), and each card's "Select Hotel" button's click
handler is not correctly bound to THAT specific card's own hotel — it's probably
referencing a shared/stale variable (e.g. a loop variable captured incorrectly, or
a single "selectedHotel" state variable that doesn't get set per-card before the
click fires), so every button ends up sending the same (often first) hotel's name
regardless of which card the user actually clicked.

REQUIRED FIX

1. Find the code that renders the hotel-cards list (from GET .../hotel-cards) and
   each card's "Select Hotel" button.
2. Make sure each card's button handler is bound directly to THAT card's own data —
   e.g. an inline handler like `onClick={() => handleSelectHotel(card.name)}` inside
   the .map() over cards, using the loop's own `card` variable, not a variable from
   outer scope or a shared piece of state set separately.
3. When clicked, it must send EXACTLY that card's "name" field:
     POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/message
     Body: { "text": "I'll go with {card.name}." }
4. Verify: render the hotel cards, click "Select Hotel" on the SECOND or THIRD card
   specifically (not the first), and confirm the chat message and the resulting
   booking flow reference that exact hotel — not the first one in the list.
5. Also double check the same pattern isn't present anywhere else multiple similar
   cards/buttons are rendered from a list (e.g. destination cards, if applicable) —
   fix the same root cause everywhere it appears, not just this one screen.
