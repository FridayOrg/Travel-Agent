Paste the text below into your Lovable project's AI chat exactly as-is.

--------------------------------------------------------------------------------

Fix hotel price display so it's consistent everywhere: the same hotel must show the exact
same price in the listing and after it's selected, with the per-night rate as the primary
figure and the total computed from it.

DATA SOURCE (unchanged): GET /api/session/{session_id}/hotel-cards returns, per hotel:
  "price": { "amount": number, "currency": string, "nights": number,
             "price_per_night": number, "room_name": string, "board_name": string,
             "refundable": boolean, ... }
  - "amount" is the TOTAL for the whole stay (all "nights") — this is the authoritative total.
  - "price_per_night" is amount / nights, already computed server-side.
The booking chat replies (after selecting a hotel) state the SAME total and per-night figures
in text, sourced from the exact same rate — the backend already guarantees these two numbers
never differ for the same hotel/dates (verified). Your job is to display both consistently.

DISPLAY RULES

1. On the hotel listing card, show the per-night price as the primary figure:
     "$104.23 USD/night · Deluxe Twin Atrium View · Room Only · Non-refundable"
   using price.price_per_night, price.currency, price.room_name, price.board_name, and a
   short label derived from price.refundable.

2. After the user selects a hotel, display it using the EXACT SAME price.price_per_night
   value already shown on the listing card for that hotel — never re-fetch, re-derive, round
   differently, or otherwise produce a different number for the per-night rate at this point.

3. Compute and show the total as price_per_night × nights (this will already match
   price.amount from the API — use whichever is more convenient, they must always agree):
     "$104.23 USD/night × 3 nights = $312.69 USD total"

4. "nights" always comes from price.nights (itself derived from the user's actual selected
   check-in/check-out dates) — never hardcode or guess a night count.

5. Use the same currency (price.currency) everywhere this hotel's price appears — listing,
   selection confirmation, and any booking summary.

6. If the traveller changes their number of nights via a fresh hotel-details/date change that
   re-triggers a real backend search (POST .../hotel-details), that naturally returns fresh
   card data (possibly a different per-night rate, since real hotel pricing varies by date) —
   treat that as an entirely new listing and display its own price.price_per_night from
   scratch. This rule is about NOT independently recalculating or drifting the price for
   dates that haven't changed — it doesn't mean per-night rates never legitimately change
   when the traveller picks different dates.

7. Never show two different numbers for the same hotel/same dates at any point in the flow —
   listing, hotel_confirm question, and the final booking summary must all match exactly.

VERIFY: view a hotel listing, note its per-night price, select that hotel, and confirm the
selection screen shows the identical per-night price and a total that's exactly
per_night × nights — matching the listing card precisely, in the same currency.
