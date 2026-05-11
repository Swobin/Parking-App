import os
import sys
from flask import Flask

CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import user_manager as um
import authentication_manager as am
import user_manager


class DummyResponse:
    def __init__(self, data=None, error=None):
        self.data = data or []
        self.error = error


class FakeTable:
    def __init__(self, response=None):
        self._response = response or DummyResponse()
        self._inserted = None

    def select(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def order(self, *args, **kwargs):
        return self

    def insert(self, payload):
        # simulate returning inserted row and allow chaining to execute()
        self._inserted = payload
        self._response = DummyResponse(data=[payload])
        return self

    def update(self, payload):
        self._response = DummyResponse(data=[{"user_id": 77}])
        return self

    def delete(self):
        return self

    def execute(self):
        return self._response


class FakeAdminClient:
    def __init__(self, response=None):
        self._response = response or DummyResponse()

    def table(self, name):
        return FakeTable(self._response)


class FakeClient:
    def __init__(self, response=None):
        self._response = response or DummyResponse()

    def table(self, name):
        return FakeTable(self._response)


def test_normalise_vehicle_type_variants():
    assert um._normalise_vehicle_type(None) == "CAR"
    assert um._normalise_vehicle_type("personal") == "CAR"
    assert um._normalise_vehicle_type("WORK") == "PCV"
    assert um._normalise_vehicle_type("ev") == "EV"
    assert um._normalise_vehicle_type("unknown") == "CAR"


def test_get_user_success(monkeypatch):
    fake_user = {"result": True, "user_id": 7, "first_name": "A", "last_name": "B", "email": "a@b.com", "payment_token": '[{"id":"tok_1"}]'}

    monkeypatch.setattr(um, "auth_getUser", lambda email=None: fake_user)

    vehicle_rows = [{"vehicle_id": 1, "registration": "ABC123", "type": "CAR"}]
    fake_db = FakeClient(DummyResponse(data=vehicle_rows))
    monkeypatch.setattr(user_manager, "get_database_connection", lambda: fake_db)

    body, status = um.get_user("a@b.com")
    assert status == 200
    assert body["result"] is True
    assert body["vehicles"] == vehicle_rows
    assert isinstance(body["payment_methods"], list)


def test_get_user_not_found(monkeypatch):
    monkeypatch.setattr(um, "auth_getUser", lambda email=None: {"result": False})
    body, status = um.get_user("missing@x.com")
    assert status == 404
    assert body["result"] is False


def test_add_vehicle_success(monkeypatch):
    monkeypatch.setattr(um, "auth_getUser", lambda email=None: {"result": True, "user_id": 5})
    fake_admin = FakeAdminClient()
    monkeypatch.setattr(user_manager, "get_database_connection_admin", lambda: fake_admin)

    body, status = um.add_vehicle("a@b.com", " ab123 ", "personal")
    assert status == 201
    assert body["result"] is True
    assert body["vehicle"]["registration"] == "AB123"


def test_add_vehicle_invalid_registration(monkeypatch):
    monkeypatch.setattr(um, "auth_getUser", lambda email=None: {"result": True, "user_id": 5})
    fake_admin = FakeAdminClient()
    monkeypatch.setattr(user_manager, "get_database_connection_admin", lambda: fake_admin)

    body, status = um.add_vehicle("a@b.com", " ", "CAR")
    assert status == 400
    assert body["result"] is False


def test_delete_vehicle_success(monkeypatch):
    monkeypatch.setattr(um, "auth_getUser", lambda email=None: {"result": True, "user_id": 9})
    fake_admin = FakeAdminClient(DummyResponse(data=[]))
    monkeypatch.setattr(user_manager, "get_database_connection_admin", lambda: fake_admin)

    body, status = um.delete_vehicle("x@y.com", 12)
    assert status == 200
    assert body["result"] is True


def test_update_user_success(monkeypatch):
    # Simulate update returning data with user_id
    resp = DummyResponse(data=[{"user_id": 77}])
    fake_admin = FakeAdminClient(resp)
    monkeypatch.setattr(user_manager, "get_database_connection_admin", lambda: fake_admin)

    body, status = um.update_user("New", "Name", email="old@x.com", updated_email="new@x.com")
    assert status == 200
    assert body["result"] is True
    assert body["email"] == "new@x.com"
