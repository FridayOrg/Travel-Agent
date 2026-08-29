Paste the text below into your Lovable project's AI chat exactly as-is. This reinforces/
clarifies the earlier price-consistency prompt: both figures must ALWAYS be shown together,
not one collapsed or hidden behind the other.

--------------------------------------------------------------------------------

Everywhere a hotel price is shown (listing card, hotel_confirm selection screen, booking
summary), display BOTH of these together, always, not just one:
  1. The per-night price — price.price_per_night, price.currency
  2. The total for the stay — price.amount (or price_per_night × nights, they always match),
     with the number of nights shown explicitly (price.nights)

Example format (both lines visible together, every time a hotel's price appears):
  $104.23 USD/night
  $312.69 USD total for 3 nights

Or inline, if that fits the design better:
  $104.23 USD/night · $312.69 USD total (3 nights)

Never show only the per-night price without the total, and never show only the total
without the per-night rate and the night count — a traveller must always be able to see both
at a glance, on the listing card AND after selecting the hotel AND in the booking summary,
with identical numbers each time (per the earlier price-consistency rules).

VERIFY: check the listing card, the post-selection screen, and the booking summary — each
one must show both the per-night rate and the total-with-nights-count simultaneously, with
matching numbers across all three.
