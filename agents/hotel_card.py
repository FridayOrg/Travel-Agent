"""Builds hotel recommendation cards from real LiteAPI data only.

Deliberately not an LLM step: hotel content detail (name, real photos, star rating, guest
sentiment, named facilities, description) and live rates (price, taxes/fees, board/meal plan,
cancellation policy) are both fetched for the exact same hotel_id, so every field shown is
grounded and correctly tied to that one property. A field that LiteAPI didn't actually return
is simply omitted (None) — never guessed or filled in.
"""
import re

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _strip_html(text):
    if not text:
        return None
    text = _TAG_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text).strip()
    return text or None


def build_hotel_card(detail: dict, rates: dict = None) -> dict:
    d = (detail or {}).get("data") or {}
    if not d:
        return None

    images = [img["url"] for img in (d.get("hotelImages") or []) if img.get("url")][:5]
    if not images and d.get("main_photo"):
        images = [d["main_photo"]]

    facilities = d.get("hotelFacilities") or [
        f.get("name") for f in (d.get("facilities") or []) if f.get("name")
    ]

    guest_rating = d.get("rating") or None
    if not guest_rating:
        categories = ((d.get("sentiment_analysis") or {}).get("categories")) or []
        scores = [c.get("rating") for c in categories if isinstance(c.get("rating"), (int, float))]
        if scores:
            guest_rating = round(sum(scores) / len(scores), 1)

    card = {
        "hotel_id": d.get("id"),
        "name": d.get("name"),
        "city": d.get("city"),
        "address": d.get("address"),
        "star_rating": d.get("starRating"),
        "guest_rating": guest_rating,
        "review_count": d.get("reviewCount"),
        "description": _strip_html(d.get("hotelDescription")),
        "facilities": facilities[:5],
        "images": images,
        "price": None,
    }

    rate_list = ((rates or {}).get("raw") or {}).get("data") or []
    if rate_list:
        room = (rate_list[0].get("roomTypes") or [{}])[0]
        rate = (room.get("rates") or [{}])[0]
        retail = rate.get("retailRate") or {}
        total = (retail.get("total") or [{}])[0]
        cancel = rate.get("cancellationPolicies") or {}
        cancel_infos = cancel.get("cancelPolicyInfos") or []

        card["price"] = {
            "amount": total.get("amount"),
            "currency": total.get("currency"),
            "room_name": rate.get("name"),
            "board_name": rate.get("boardName"),
            "taxes_and_fees": [
                {
                    "description": t.get("description"),
                    "amount": t.get("amount"),
                    "included": t.get("included"),
                }
                for t in (retail.get("taxesAndFees") or [])
            ],
            "refundable": (
                cancel.get("refundableTag") == "RFN" if cancel.get("refundableTag") else None
            ),
            "cancellation_deadline": cancel_infos[0].get("cancelTime") if cancel_infos else None,
        }

    return card
