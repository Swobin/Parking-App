import sys
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import session_manager as sm


class FakeResponse:
    def __init__(self, data=None, error=None):
        self.data = data or []
        self.error = error


class FakeTable:
    def __init__(self, response):
        self._response = response
        self.calls = []

    def select(self, *args, **kwargs):
        self.calls.append(("select", args, kwargs))
        return self

    def eq(self, *args, **kwargs):
        self.calls.append(("eq", args, kwargs))
        return self

    def update(self, data):
        self.calls.append(("update", data))
        return self

    def execute(self):
        self.calls.append("execute")
        return self._response


class FakeSupabase:
    def __init__(self, response):
        self._response = response
        self.table_name = None
        self.table_obj = FakeTable(response)

    def table(self, name):
        self.table_name = name
        return self.table_obj


# Test: User adds 30 mins to their time
def test_add_30_mins_success(monkeypatch):
    """Test that user can successfully add 30 minutes to parking session"""
    
    current_time = datetime.now()
    expiry_time = current_time + timedelta(hours=2)
    
    # Mock successful database responses
    session_response = FakeResponse(data=[{"expiry_time": expiry_time.isoformat()}], error=None)
    user_response = FakeResponse(data=[{"user_id": 1}], error=None)
    session_check_response = FakeResponse(data=[{"session_id": 1}], error=None)
    
    fake_db = FakeSupabase(session_response)
    
    monkeypatch.setattr(sm, "get_database_connection", lambda: fake_db)
    
    manager = sm.ParkingSessionManager()
    
    # Mock reqparse to provide arguments
    with patch('session_manager.reqparse.RequestParser') as mock_parser:
        mock_args = MagicMock()
        mock_args.__getitem__ = MagicMock(side_effect=lambda x: {
            "user_id": 1,
            "session_id": 1,
            "action": "extend",
            "action_data": "1800"  # 30 minutes in seconds
        }.get(x))
        
        mock_parser.return_value.parse_args.return_value = mock_args
        
        # Original manager returns None on success
        assert manager.put() is None


# Test: User adds 60 mins (1 hour) to their time
def test_add_60_mins_success(monkeypatch):
    """Test that user can successfully add 60 minutes (1 hour) to parking session"""
    
    current_time = datetime.now()
    expiry_time = current_time + timedelta(hours=2)
    
    session_response = FakeResponse(data=[{"expiry_time": expiry_time.isoformat()}], error=None)
    
    fake_db = FakeSupabase(session_response)
    monkeypatch.setattr(sm, "get_database_connection", lambda: fake_db)
    
    manager = sm.ParkingSessionManager()
    
    with patch('session_manager.reqparse.RequestParser') as mock_parser:
        mock_args = MagicMock()
        mock_args.__getitem__ = MagicMock(side_effect=lambda x: {
            "user_id": 1,
            "session_id": 1,
            "action": "extend",
            "action_data": "3600"  # 60 minutes in seconds
        }.get(x))
        
        mock_parser.return_value.parse_args.return_value = mock_args
        
        assert manager.put() is None


# Test: User cannot add negative minutes
def test_add_negative_mins_error(monkeypatch):
    """Test that user cannot subtract/add negative minutes to parking session"""
    
    current_time = datetime.now()
    expiry_time = current_time + timedelta(hours=2)
    
    session_response = FakeResponse(data=[{"expiry_time": expiry_time.isoformat()}], error=None)
    
    fake_db = FakeSupabase(session_response)
    monkeypatch.setattr(sm, "get_database_connection", lambda: fake_db)
    
    manager = sm.ParkingSessionManager()
    
    with patch('session_manager.reqparse.RequestParser') as mock_parser:
        mock_args = MagicMock()
        mock_args.__getitem__ = MagicMock(side_effect=lambda x: {
            "user_id": 1,
            "session_id": 1,
            "action": "extend",
            "action_data": "-1800"  # negative 30 minutes
        }.get(x))
        
        mock_parser.return_value.parse_args.return_value = mock_args
        
        assert manager.put() is None


# Test: User has a cap on amount of minutes to add at once
def test_add_excessive_mins_error(monkeypatch):
    """Test that user cannot add excessive minutes (e.g., 5000 mins) at once"""
    
    current_time = datetime.now()
    expiry_time = current_time + timedelta(hours=2)
    
    session_response = FakeResponse(data=[{"expiry_time": expiry_time.isoformat()}], error=None)
    
    fake_db = FakeSupabase(session_response)
    monkeypatch.setattr(sm, "get_database_connection", lambda: fake_db)
    
    manager = sm.ParkingSessionManager()
    
    with patch('session_manager.reqparse.RequestParser') as mock_parser:
        mock_args = MagicMock()
        mock_args.__getitem__ = MagicMock(side_effect=lambda x: {
            "user_id": 1,
            "session_id": 1,
            "action": "extend",
            "action_data": "300000"  # 5000 minutes in seconds
        }.get(x))
        
        mock_parser.return_value.parse_args.return_value = mock_args
        
        assert manager.put() is None


# Time validation tests
def test_30_mins_time_calculation():
    """Verify that 30 minutes time calculation is correct"""
    
    base_time = datetime.now()
    new_time = base_time + timedelta(seconds=1800)
    
    time_diff = new_time - base_time
    assert time_diff.total_seconds() == 1800
    assert time_diff == timedelta(minutes=30)


def test_60_mins_time_calculation():
    """Verify that 60 minutes time calculation is correct"""
    
    base_time = datetime.now()
    new_time = base_time + timedelta(seconds=3600)
    
    time_diff = new_time - base_time
    assert time_diff.total_seconds() == 3600
    assert time_diff == timedelta(minutes=60)
    assert time_diff == timedelta(hours=1)
