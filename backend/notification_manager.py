from datetime import datetime, timedelta


class NotificationManager:
    """Minimal notification manager used for unit testing notification logic.

    in-memory so tests can run without external services. It models scheduling a 5-minute warning and clearing
    notifications when the user ends a session.
    """

    def __init__(self):
        self.queue = {}  # session_id -> list of notification dicts

    def schedule_notification(self, session_id: int, notify_time: datetime, message: str = "expiry_warning"):
        self.queue.setdefault(session_id, []).append({"time": notify_time, "message": message})

    def get_notifications(self, session_id: int):
        return list(self.queue.get(session_id, []))

    def clear_notifications(self, session_id: int):
        self.queue.pop(session_id, None)

    def handle_timer_tick(self, session_id: int, current_time: datetime, expiry_time: datetime) -> bool:
        """Called periodically to check whether a warning should be scheduled.

        Returns True if a notification was scheduled on this tick.
        """
        if expiry_time - current_time <= timedelta(minutes=5):
            if not self.get_notifications(session_id):
                self.schedule_notification(session_id, current_time, "5_min_warning")
                return True
        return False

    def user_clicked_i_have_left(self, session_id: int):
        """Simulate the user ending the session by clicking 'I have left'.

        Clears any pending notifications and returns a small result dict.
        """
        self.clear_notifications(session_id)
        return {"session_id": session_id, "ended": True}
