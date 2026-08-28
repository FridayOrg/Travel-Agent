import requests
from config import LITEAPI_API_KEY

RATES_URL = "https://api.liteapi.travel/v3.0/hotels/rates"
PREBOOK_URL = "https://book.liteapi.travel/v3.0/rates/prebook"
BOOK_URL = "https://book.liteapi.travel/v3.0/rates/book"


def _headers():
    return {"X-API-Key": LITEAPI_API_KEY, "Content-Type": "application/json"}


def get_hotel_rates(
    hotel_id: str,
    check_in: str,
    check_out: str,
    adults: int = 2,
    guest_nationality: str = "US",
    currency: str = "EUR",
) -> dict:
    """Get real, live room rates and offers for one specific hotel. Returns raw data,
    including an offerId per rate needed for the next (prebook) step.

    Args:
      hotel_id: the LiteAPI hotel id from a prior search_hotels result
      check_in: check-in date, YYYY-MM-DD
      check_out: check-out date, YYYY-MM-DD
      adults: number of adult guests
      guest_nationality: guest's ISO 2-letter country code
      currency: 3-letter currency code for pricing
    """
    print(f"  [TOOL CALL] get_hotel_rates(hotel_id={hotel_id!r}, check_in={check_in!r}, "
          f"check_out={check_out!r}, adults={adults})")

    if not LITEAPI_API_KEY:
        return {"error": "LITEAPI_API_KEY is not configured — do not invent rates."}

    resp = requests.post(
        RATES_URL,
        headers=_headers(),
        json={
            "hotelIds": [hotel_id],
            "occupancies": [{"adults": adults}],
            "currency": currency,
            "guestNationality": guest_nationality,
            "checkin": check_in,
            "checkout": check_out,
        },
        timeout=20,
    )
    resp.raise_for_status()
    return {"raw": resp.json(), "source": "liteapi.travel (live)"}


def prebook_rate(offer_id: str) -> dict:
    """Lock in a specific rate offer and get the final confirmed price before booking.
    Returns a prebookId required for the next (book) step. Does not charge anything.

    Args:
      offer_id: the offerId from a get_hotel_rates result
    """
    print(f"  [TOOL CALL] prebook_rate(offer_id={offer_id!r})")

    if not LITEAPI_API_KEY:
        return {"error": "LITEAPI_API_KEY is not configured — do not invent a prebook result."}

    resp = requests.post(
        PREBOOK_URL,
        headers=_headers(),
        json={"offerId": offer_id, "usePaymentSdk": False},
        timeout=20,
    )
    resp.raise_for_status()
    return {"raw": resp.json(), "source": "liteapi.travel (live)"}


def complete_booking(
    prebook_id: str,
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
) -> dict:
    """Complete the (sandbox — no real charge) booking. Only call this after the traveller has
    explicitly confirmed they want to book, with the final price already shown to them.

    Args:
      prebook_id: the prebookId from a prebook_rate result
      first_name: guest first name
      last_name: guest last name
      email: guest email
      phone: guest phone number
    """
    print(f"  [TOOL CALL] complete_booking(prebook_id={prebook_id!r}, guest={first_name} {last_name})")

    if not LITEAPI_API_KEY:
        return {"error": "LITEAPI_API_KEY is not configured — do not invent a booking confirmation."}

    resp = requests.post(
        BOOK_URL,
        headers=_headers(),
        json={
            "prebookId": prebook_id,
            "holder": {"firstName": first_name, "lastName": last_name, "email": email, "phone": phone},
            "guests": [
                {"occupancyNumber": 1, "firstName": first_name, "lastName": last_name, "email": email}
            ],
            "payment": {"method": "ACC_CREDIT_CARD"},
        },
        timeout=20,
    )
    resp.raise_for_status()
    return {"raw": resp.json(), "source": "liteapi.travel (live, sandbox — not a real charge)"}
