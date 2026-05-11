import os
import sys
from flask import Flask

CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import search_manager
from search_manager import SearchManagerAll


class DummyResponse:
    def __init__(self, data=None, error=None):
        self.data = data or []
        self.error = error


class FakeSupabaseTable:
    def __init__(self, response):
        self._response = response

    def select(self, *_args, **_kwargs):
        return self

    def execute(self):
        return self._response


class FakeSupabaseClient:
    def __init__(self, response):
        self._response = response

    def table(self, _name):
        return FakeSupabaseTable(self._response)


def test_search_all_returns_carparks(monkeypatch):
    sample = [
        {"carpark_id": 1, "name": "A Lot"},
        {"carpark_id": 2, "name": "B Lot"},
    ]

    resp = DummyResponse(data=sample)
    fake_client = FakeSupabaseClient(resp)

    monkeypatch.setattr(search_manager, "get_database_connection_admin", lambda: fake_client)

    manager = SearchManagerAll()
    result, status = manager.get()

    assert status == 200
    assert isinstance(result, list)
    assert len(result) == 2


def test_search_all_handles_db_error(monkeypatch):
    resp = DummyResponse(data=None, error="connection failed")
    fake_client = FakeSupabaseClient(resp)

    monkeypatch.setattr(search_manager, "get_database_connection_admin", lambda: fake_client)

    manager = SearchManagerAll()
    result, status = manager.get()

    assert status == 500
    assert "Failed to fetch car parks" in result["error"]
