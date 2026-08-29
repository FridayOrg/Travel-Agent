Paste the text below into your Lovable project's AI chat exactly as-is.

--------------------------------------------------------------------------------

Fix hotel card pricing: the card was showing the TOTAL price for the whole stay labeled
as "per night" (e.g. showing "$68 / per night" for a 3-night stay that actually costs
$68 total) — this made prices look far too low. GET /api/session/{session_id}/hotel-cards
now returns two explicit, separate price fields — use both correctly:

  "price": {
    "amount": number,          // TOTAL price for the entire stay (all nights) — NOT per night
    "currency": string,
    "nights": number,          // number of nights this total covers
    "price_per_night": number, // average nightly rate (amount / nights) — for reference only
    "room_name": string,
    "board_name": string,
    ...
  }

REQUIRED DISPLAY

On each hotel card, show BOTH clearly labeled, e.g.:
  "$133.13 total for 3 nights"
  "($44.38 / night)"
Never label "amount" as a nightly rate on its own — it is the full-stay total. If "nights"
or "price_per_night" is null (dates not resolved yet), just show the total amount without
a per-night line rather than guessing.

Apply the same fix anywhere else a hotel price is shown from this data (chat replies from
the booking step already state both the total and the per-night rate in text, per a
separate backend fix — this prompt covers the card/UI display specifically).

VERIFY: pick a multi-night stay, confirm the card shows a total price that matches the
number of nights actually selected, with the per-night figure shown as a clearly
secondary/smaller reference number, not the primary price.
