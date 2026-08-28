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

STATIC_STAGES = {"INTAKE", "HOTEL_TRAVELLERS", "HOTEL_BUDGET", "HOTEL_DATES"}
