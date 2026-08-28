INTAKE_QUESTIONS = [
    {
        "id": "destination",
        "question": "Where would you like to go?",
        "options": ["Dubai", "London", "Other"],
        "allow_other": True,
        "free_text": False,
    },
    {
        "id": "travellers",
        "question": "Who are you travelling with?",
        "options": ["Family", "Friends", "Solo", "Couple"],
        "allow_other": False,
        "free_text": False,
    },
    {
        "id": "month",
        "question": "When are you planning to travel?",
        "options": ["Aug-Sep", "Oct-Nov", "Dec-Jan", "Other"],
        "allow_other": True,
        "free_text": False,
    },
]

HOTEL_TRAVELLERS_QUESTION = {
    "id": "hotel_travellers",
    "question": "How many travellers?",
    "options": ["2 Adults", "2 Adults + 1 Kid", "Other"],
    "allow_other": True,
}

HOTEL_BUDGET_QUESTION = {
    "id": "hotel_budget",
    "question": "What's your budget range per night?",
    "options": ["Budget", "Mid-range", "Luxury", "Other"],
    "allow_other": True,
}

HOTEL_DATES_QUESTION = {
    "id": "hotel_dates",
    "question": "What are your check-in and check-out dates?",
    "type": "date_range",
}

# Shown together as one combined form (same batching pattern as INTAKE_QUESTIONS) instead of
# three sequential single-question screens.
HOTEL_DETAILS_QUESTIONS = [HOTEL_TRAVELLERS_QUESTION, HOTEL_BUDGET_QUESTION, HOTEL_DATES_QUESTION]

STATIC_STAGES = {"INTAKE", "HOTEL_DETAILS"}
