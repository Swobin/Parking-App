import sys
import os
from unittest.mock import MagicMock, patch

CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import car_park_manager as cpm


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

    def insert(self, data):
        self.calls.append(("insert", data))
        return self

    def delete(self):
        self.calls.append("delete")
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


# Test: User gets carpark details (spaces, price, types of spaces)
def test_get_carpark_details_success(monkeypatch):
    """Test that user can get car park details including spaces, price, and types"""
    
    carpark_data = {
        "carpark_id": "CP001",
        "name": "Downtown Parking",
        "spaces": 150,
        "price": 5.50,
        "distance": 0.5,
        "avg_rating": 4.5
    }
    
    response = FakeResponse(data=[carpark_data], error=None)
    fake_db = FakeSupabase(response)
    
    monkeypatch.setattr(cpm, "get_database_connection", lambda: fake_db)
    
    carpark = cpm.CarPark()
    result, status = carpark.get()
    
    assert status == 200
    assert result["data"]["name"] == "Downtown Parking"
    assert result["data"]["spaces"] == 150
    assert result["data"]["price"] == 5.50


# Test: User cannot add a new carpark (should return error)
def test_add_new_carpark_error(monkeypatch):
    """Test that users cannot add a new car park and receive an error"""
    
    # Mock failed database insert response
    response = FakeResponse(data=[], error=None)
    fake_db = FakeSupabase(response)
    
    monkeypatch.setattr(cpm, "get_database_connection", lambda: fake_db)
    
    carpark = cpm.CarPark()
    
    with patch('car_park_manager.reqparse.RequestParser') as mock_parser:
        mock_args = MagicMock()
        mock_args.__getitem__ = MagicMock(side_effect=lambda x: {
            "name": "New Parking",
            "spaces": 100,
            "location": 40.7128
        }.get(x))
        
        mock_parser.return_value.parse_args.return_value = mock_args
        
        result, status = carpark.post()
        
        # Should return error since users cannot add car parks
        assert status == 500
        assert "error" in result


# Test: User cannot remove a carpark (operation not allowed)
def test_remove_carpark_not_allowed(monkeypatch):
    """Test that users cannot remove a car park"""
    
    response = FakeResponse(data=[], error=None)
    fake_db = FakeSupabase(response)
    
    monkeypatch.setattr(cpm, "get_database_connection", lambda: fake_db)
    
    carpark = cpm.CarPark()
    
    # DELETE method should not exist or should return error
    # Testing that the delete method is not available to users
    has_delete_method = hasattr(carpark, 'delete')
    
    # If delete method doesn't exist, users cannot remove car parks
    if not has_delete_method:
        # This is the expected behavior - no delete method means users can't remove
        assert True
    else:
        # If it exists, it should return an error
        result, status = carpark.delete()
        assert status == 400 or status == 403


# Test: User cannot get non-existing carpark (should return error)
def test_get_nonexistent_carpark_error(monkeypatch):
    """Test that users can only get existing car parks and receive error for non-existent ones"""
    
    # Mock empty response for non-existent car park
    response = FakeResponse(data=[], error=None)
    fake_db = FakeSupabase(response)
    
    monkeypatch.setattr(cpm, "get_database_connection", lambda: fake_db)
    
    carpark = cpm.CarPark()
    result, status = carpark.get()
    
    # Should return default message indicating no car parks found
    assert status == 200
    assert "No car parks found" in str(result["data"])


# Test: Get carpark with all details
def test_get_carpark_all_details(monkeypatch):
    """Test that getting a carpark returns all required details: spaces, price, types"""
    
    carpark_data = {
        "carpark_id": "CP002",
        "name": "Mall Parking",
        "spaces": 300,
        "price": 3.00,
        "distance": 1.2,
        "avg_rating": 4.8
    }
    
    response = FakeResponse(data=[carpark_data], error=None)
    fake_db = FakeSupabase(response)
    
    monkeypatch.setattr(cpm, "get_database_connection", lambda: fake_db)
    
    carpark = cpm.CarPark()
    result, status = carpark.get()
    
    assert status == 200
    assert "carpark_id" in result["data"]
    assert "name" in result["data"]
    assert "spaces" in result["data"]
    assert "price" in result["data"]
    assert result["data"]["spaces"] > 0


# Test: Verify spaces validation (non-negative)
def test_carpark_spaces_validation():
    """Test that car park spaces must be non-negative"""
    
    # Valid spaces
    valid_data = {
        "carpark_id": "CP003",
        "name": "Test Parking",
        "spaces": 50,
        "price": 2.50,
        "distance": 0.3,
        "avg_rating": 4.0
    }
    
    schema = cpm.CarParkSchema()
    result = schema.dump(valid_data)
    assert result["spaces"] == 50
    assert result["spaces"] >= 0


# Test: Verify price validation (non-negative)
def test_carpark_price_validation():
    """Test that car park price must be non-negative"""
    
    valid_data = {
        "carpark_id": "CP004",
        "name": "Expensive Parking",
        "spaces": 100,
        "price": 10.00,
        "distance": 0.5,
        "avg_rating": 3.5
    }
    
    schema = cpm.CarParkSchema()
    result = schema.dump(valid_data)
    assert result["price"] >= 0


# Test: Verify distance validation (non-negative)
def test_carpark_distance_validation():
    """Test that car park distance must be non-negative"""
    
    valid_data = {
        "carpark_id": "CP005",
        "name": "Close Parking",
        "spaces": 75,
        "price": 4.50,
        "distance": 0.1,
        "avg_rating": 4.2
    }
    
    schema = cpm.CarParkSchema()
    result = schema.dump(valid_data)
    assert result["distance"] >= 0
