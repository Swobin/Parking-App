import os
import sys
import time
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


def make_sample(n):
    # spread points around origin for quick distance checks
    return [
        {"carpark_id": i, "name": f"P{i}", "location": {"coordinates": [(-1.0 + (i % 100) * 0.001), (50.0 + (i % 100) * 0.001)]}}
        for i in range(n)
    ]


def test_search_latency_small(monkeypatch):
    sample = make_sample(50)
    fake = FakeSupabaseClient(sample)
    monkeypatch.setattr(search_manager, "get_database_connection_admin", lambda: fake)

    app = Flask(__name__)
    manager = SearchManager()

    start = time.perf_counter()
    with app.test_request_context("/search?query=&minDistance=0&maxDistance=20000&longitude=-1.0&latitude=50.0"):
        result, status = manager.get()
    duration = time.perf_counter() - start

    assert status == 200
    # Ensure it completes quickly for a small dataset
    assert duration < 0.5, f"Search took too long: {duration:.3f}s"


def test_search_latency_large(monkeypatch):
    sample = make_sample(2000)
    fake = FakeSupabaseClient(sample)
    monkeypatch.setattr(search_manager, "get_database_connection_admin", lambda: fake)

    app = Flask(__name__)
    manager = SearchManager()

    start = time.perf_counter()
    with app.test_request_context("/search?query=&minDistance=0&maxDistance=20000&longitude=-1.0&latitude=50.0"):
        result, status = manager.get()
    duration = time.perf_counter() - start

    assert status == 200
    # Larger dataset should still finish within a reasonable bound on CI/machines
    assert duration < 3.0, f"Large search took too long: {duration:.3f}s"
