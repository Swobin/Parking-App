import sys
import os
from datetime import datetime, timedelta

CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if BACKEND_DIR not in sys.path:
	sys.path.insert(0, BACKEND_DIR)

import notification_manager as nm


def test_schedule_5_min_warning():
	"""When a session has 5 minutes remaining, a 5-minute warning is scheduled."""
	manager = nm.NotificationManager()

	session_id = 42
	now = datetime.now()
	expiry = now + timedelta(minutes=5)

	scheduled = manager.handle_timer_tick(session_id, now, expiry)

	assert scheduled is True
	notes = manager.get_notifications(session_id)
	assert len(notes) == 1
	assert notes[0]["message"] == "5_min_warning"


def test_user_click_i_have_left_clears_queue():
	"""Clicking 'I have left' ends the session and clears the notification queue."""
	manager = nm.NotificationManager()

	session_id = 99
	# Pre-schedule a notification
	manager.schedule_notification(session_id, datetime.now(), "test")
	assert len(manager.get_notifications(session_id)) == 1

	result = manager.user_clicked_i_have_left(session_id)

	assert result == {"session_id": session_id, "ended": True}
	assert manager.get_notifications(session_id) == []
