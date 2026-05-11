from datetime import datetime, timedelta


class ExtensionService:
    """Service to calculate extensions, price, and enforce max stay limits.

    This is a small, test-oriented implementation --> add time to a session, calculate price, enforce a
    maximum allowed stay, and provide time-remaining calculations.
    """

    def __init__(self, hourly_rate: float = 2.5, max_total_seconds: int = 24 * 3600):
        self.hourly_rate = hourly_rate
        self.max_total_seconds = max_total_seconds

    def calculate_price(self, add_seconds: int) -> float:
        hours = add_seconds / 3600.0
        return round(self.hourly_rate * hours, 2)

    def calculate_new_expiry(self, current_expiry: datetime, add_seconds: int) -> datetime:
        return current_expiry + timedelta(seconds=add_seconds)

    def extend_session(self, now: datetime, current_expiry: datetime, add_seconds: int):
        """Attempt to extend a session. Returns (new_expiry, price) or raises ValueError if max exceeded."""
        if add_seconds < 0:
            raise ValueError("Cannot add negative time")

        new_expiry = self.calculate_new_expiry(current_expiry, add_seconds)

        # Enforce max total stay measured from 'now' to new_expiry
        total_seconds = int((new_expiry - now).total_seconds())
        if total_seconds > self.max_total_seconds:
            raise ValueError("Maximum stay exceeded")

        price = self.calculate_price(add_seconds)
        return new_expiry, price

    def time_remaining(self, now: datetime, expiry: datetime) -> int:
        """Returns remaining seconds (0 if expired)."""
        diff = int((expiry - now).total_seconds())
        return max(0, diff)
