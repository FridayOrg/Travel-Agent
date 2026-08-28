class TripContext:
    def __init__(self):
        self.stage = "INTAKE"
        self.profile = {}
        self.destination = None
        self.destination_reason = None
        self.trip_duration_days = None
        self.trip_duration_label = None
        self.itinerary_confirmed = False
        self.checkin = None
        self.checkout = None
        self.adults = None
        self.kids = 0
        self.known_hotels = {}
        self.known_hotels_raw = {}
        self.current_places = []
        self.current_hotel_ids = []
        self.selected_hotel_id = None
        self.selected_hotel_name = None
        self.offer_lookup = {}
        self.prebook_lookup = {}
        self.booking_confirmation = None

    def summary(self) -> str:
        return (
            f"stage={self.stage}, "
            f"destination={self.destination or 'none'}, "
            f"selected_hotel={self.selected_hotel_name or 'none'}, "
            f"booking={'confirmed' if self.booking_confirmation else 'none'}"
        )
