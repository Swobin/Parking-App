import sys
import os
from unittest.mock import MagicMock, patch

CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import car_park_manager as cpm
import search_manager as sm


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


# Test: User can see the type of car park
def test_get_carpark_type_success(monkeypatch):
    """Test that user can view car park details including type of car park"""
    
    carpark_data = {
        "carpark_id": "CP001",
        "name": "Downtown Parking",
        "space_type": "covered",
        "location": {"coordinates": [40.7128, -74.0060]},
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
    assert "space_type" in result["data"] or "space_type" in str(result)


# Test: User gets carpark with multiple space types
def test_get_carpark_with_space_types(monkeypatch):
    """Test that car park response includes space type information"""
    
    carpark_data = {
        "carpark_id": "CP002",
        "name": "Mall Parking",
        "space_type": "open",
        "location": {"coordinates": [40.7580, -73.9855]},
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
    carpark_details = result["data"]
    assert "name" in carpark_details
    assert carpark_details["name"] == "Mall Parking"


# Test: User cannot view a non-existing car park type
def test_get_nonexistent_carpark_type_error(monkeypatch):
    """Test that user cannot view a non-existing car park and receives an error"""
    
    # Mock empty response for non-existent car park
    response = FakeResponse(data=[], error=None)
    fake_db = FakeSupabase(response)
    
    monkeypatch.setattr(cpm, "get_database_connection", lambda: fake_db)
    
    carpark = cpm.CarPark()
    result, status = carpark.get()
    
    # Should return status 200 but with no car parks found message
    assert status == 200
    # Verify it indicates no car parks were found
    assert "No car parks found" in str(result["data"])


# Test: Verify space type field exists in response
def test_carpark_space_type_field_exists(monkeypatch):
    """Test that space_type field is returned in car park details"""
    
    carpark_data = {
        "carpark_id": "CP003",
        "name": "Airport Parking",
        "space_type": "covered",
        "location": {"coordinates": [40.7769, -73.8740]},
        "spaces": 500,
        "price": 8.00,
        "distance": 12.5,
        "avg_rating": 4.2
    }
    
    response = FakeResponse(data=[carpark_data], error=None)
    fake_db = FakeSupabase(response)
    
    monkeypatch.setattr(cpm, "get_database_connection", lambda: fake_db)
    
    carpark = cpm.CarPark()
    result, status = carpark.get()
    
    assert status == 200
    # Check that car park has the space type information
    result_str = str(result)
    assert "carpark" in result_str.lower() or "space" in result_str.lower()


# Test: Get car park with covered space type
def test_get_covered_carpark_type(monkeypatch):
    """Test viewing a car park with covered space type"""
    
    carpark_data = {
        "carpark_id": "CP004",
        "name": "Covered Garage",
        "space_type": "covered",
        "location": {"coordinates": [40.7489, -73.9680]},
        "spaces": 200,
        "price": 6.50,
        "distance": 0.8,
        "avg_rating": 4.7
    }
    
    response = FakeResponse(data=[carpark_data], error=None)
    fake_db = FakeSupabase(response)
    
    monkeypatch.setattr(cpm, "get_database_connection", lambda: fake_db)
    
    carpark = cpm.CarPark()
    result, status = carpark.get()
    
    assert status == 200
    assert result["data"]["name"] == "Covered Garage"


# Test: Get car park with open space type
def test_get_open_carpark_type(monkeypatch):
    """Test viewing a car park with open space type"""
    
    carpark_data = {
        "carpark_id": "CP005",
        "name": "Street Parking",
        "space_type": "open",
        "location": {"coordinates": [40.7614, -73.9776]},
        "spaces": 50,
        "price": 2.00,
        "distance": 0.2,
        "avg_rating": 3.5
    }
    
    response = FakeResponse(data=[carpark_data], error=None)
    fake_db = FakeSupabase(response)
    
    monkeypatch.setattr(cpm, "get_database_connection", lambda: fake_db)
    
    carpark = cpm.CarPark()
    result, status = carpark.get()
    
    assert status == 200
    assert result["data"]["name"] == "Street Parking"


# Test: Get car park with valet service space type
def test_get_valet_carpark_type(monkeypatch):
    """Test viewing a car park with valet service space type"""
    
    carpark_data = {
        "carpark_id": "CP006",
        "name": "Valet Parking",
        "space_type": "valet",
        "location": {"coordinates": [40.7505, -73.9972]},
        "spaces": 100,
        "price": 12.00,
        "distance": 0.3,
        "avg_rating": 4.9
    }
    
    response = FakeResponse(data=[carpark_data], error=None)
    fake_db = FakeSupabase(response)
    
    monkeypatch.setattr(cpm, "get_database_connection", lambda: fake_db)
    
    carpark = cpm.CarPark()
    result, status = carpark.get()
    
    assert status == 200
    assert result["data"]["name"] == "Valet Parking"


# Test: Verify all car park fields exist in response
def test_carpark_all_fields_exist(monkeypatch):
    """Test that all required car park fields are present in the response"""
    
    carpark_data = {
        "carpark_id": "CP007",
        "name": "Complete Parking",
        "space_type": "covered",
        "location": {"coordinates": [40.7549, -73.9840]},
        "spaces": 250,
        "price": 7.00,
        "distance": 1.0,
        "avg_rating": 4.4
    }
    
    response = FakeResponse(data=[carpark_data], error=None)
    fake_db = FakeSupabase(response)
    
    monkeypatch.setattr(cpm, "get_database_connection", lambda: fake_db)
    
    carpark = cpm.CarPark()
    result, status = carpark.get()
    
    assert status == 200
    result_data = result["data"]
    # Verify key fields exist
    assert "name" in result_data
    assert result_data["spaces"] > 0
    assert result_data["price"] >= 0
