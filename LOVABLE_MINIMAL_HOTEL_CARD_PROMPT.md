Paste the text below into your Lovable project's AI chat exactly as-is.

--------------------------------------------------------------------------------

Change how hotel options are displayed in the chat. Make each hotel card minimal and
text-only — no images anywhere in the chat for hotel results.

Data still comes from GET /api/session/{session_id}/hotel-cards, same as before:
  { "cards": [ { hotel_id, name, city, address, star_rating, guest_rating, review_count,
    description, facilities, images, price: { amount, currency, nights, price_per_night,
    room_name, board_name, taxes_and_fees, refundable, cancellation_deadline } }, ... ] }

SHOW ONLY, for each hotel:
  - Hotel name
  - Price (use price.amount as the total, formatted like "104.23 USD" — you can also show
    price.price_per_night alongside if there's room, but the total is the primary figure)
  - Room type (price.room_name)
  - Meal/board type (price.board_name)
  - Cancellation policy (a short label derived from price.refundable — e.g. "Non-refundable"
    if false, "Free cancellation" or similar if true; use price.cancellation_deadline if you
    want to show a date, but keep it short)
  - A "Select Hotel" button (unchanged — still sends { "text": "I'll go with {name}." } via
    POST /api/session/{session_id}/message)

Example layout for one card:

  Rove Dubai Marina

  104.23 USD · Deluxe Twin Atrium View · Room Only · Non-refundable

  [Select Hotel]

DO NOT display, even though the API returns them — simply ignore these fields in the UI:
  - images (no hotel photos anywhere in the chat for hotel results)
  - description
  - address / city
  - star_rating / guest_rating / review_count
  - facilities
  - any other field not listed in "SHOW ONLY" above

Remove any image loading/rendering code for hotel cards specifically (destination/attraction
images elsewhere in the app, if any, are unaffected — this only applies to hotel result
cards). Keep the card visually simple: a compact text block per hotel, not a large media card.

VERIFY: reach the hotel recommendation stage in a chat flow and confirm each hotel appears as
a plain text block with exactly name, price, room type, board type, cancellation policy, and
a Select Hotel button — no image, no description, no address, no star rating, no facilities.
