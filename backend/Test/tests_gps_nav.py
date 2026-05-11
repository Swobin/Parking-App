import os
import sys
from flask import Flask

CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if BACKEND_DIR not in sys.path:
	sys.path.insert(0, BACKEND_DIR)

import search_manager
from search_manager import SearchManager


class DummyResponse:
	def __init__(self, data=None, error=None):
		self.data = data or []
		self.error = error


class FakeSupabaseTable:
	def __init__(self, data):
		self._data = data

	def select(self, *_args, **_kwargs):
		return self

	def execute(self):
		return DummyResponse(data=self._data)


class FakeSupabaseClient:
	def __init__(self, data):
		self._data = data

	def table(self, _name):
		return FakeSupabaseTable(self._data)


def test_enable_location_returns_nearest_carparks(monkeypatch):
	sample_data = [
		{"carpark_id": 1, "name": "Near One", "location": {"coordinates": [-1.0, 50.0]}},
		{"carpark_id": 2, "name": "Far One", "location": {"coordinates": [-5.0, 55.0]}},
	]
	fake_client = FakeSupabaseClient(sample_data)
	monkeypatch.setattr(search_manager, "get_database_connection_admin", lambda: fake_client)

	app = Flask(__name__)
	manager = SearchManager()

	with app.test_request_context("/search?query=&minDistance=0&maxDistance=100&longitude=-1.0&latitude=50.0"):
		result, status = manager.get()

	assert status == 200
	assert any(r["name"] == "Near One" for r in result)
	assert all(r["name"] != "Far One" for r in result)


def test_no_gps_sync_prompts_manual_search():
	app = Flask(__name__)
	manager = SearchManager()

	# Omit latitude/lattitude to simulate denied GPS
	with app.test_request_context("/search?query=test&minDistance=0&maxDistance=5&longitude=0"):
		result, status = manager.get()

	assert status == 400
	assert "Either latitude or lattitude is required" in result["error"]


def test_navigate_to_location_go_triggers_search(monkeypatch):
	sample_data = [
		{"carpark_id": 10, "name": "Target A", "location": {"coordinates": [10.0, 10.0]}},
	]
	fake_client = FakeSupabaseClient(sample_data)
	monkeypatch.setattr(search_manager, "get_database_connection_admin", lambda: fake_client)

	app = Flask(__name__)
	manager = SearchManager()

	# Simulate user clicking 'go' with a target location
	with app.test_request_context("/search?query=Target&minDistance=0&maxDistance=50&longitude=10.0&latitude=10.0"):
		result, status = manager.get()

	assert status == 200
	assert len(result) >= 1
	assert result[0]["name"] == "Target A"
