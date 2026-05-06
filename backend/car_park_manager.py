from flask_restful import Resource, reqparse
from marshmallow import Schema, fields, validate

from modules import get_database_connection


class CarParkSchema(Schema):
    carpark_id = fields.String()
    name = fields.String()
    longitude = fields.Method("get_longitude")
    latitude = fields.Method("get_latitude")
    spaces = fields.Integer(validate=validate.Range(min=0))
    price = fields.Float(validate=validate.Range(min=0), allow_none=True)
    distance = fields.Float(validate=validate.Range(min=0))
    avg_rating = fields.Float(validate=validate.Range(min=0))

    def get_longitude(self, obj):
        location = obj.get("location") or {}
        coordinates = location.get("coordinates") if isinstance(location, dict) else None
        if isinstance(coordinates, list) and len(coordinates) == 2:
            return coordinates[0]
        return None

    def get_latitude(self, obj):
        location = obj.get("location") or {}
        coordinates = location.get("coordinates") if isinstance(location, dict) else None
        if isinstance(coordinates, list) and len(coordinates) == 2:
            return coordinates[1]
        return None


class CarPark(Resource):
    def get(self):
        supabase = get_database_connection()
        response = supabase.table("carpark").select("name", "space_type", "location", "carpark_id").execute()
        if response.data:
            car_park_data = response.data[0]
            return {
                "data": CarParkSchema().dump(car_park_data)
            }, 200
        return {
            "data": [{"name": "No car parks found"}]
        }, 200

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str, required=True)
        parser.add_argument("spaces", type=int, required=True)
        parser.add_argument("location", type=float, required=True)
        args = parser.parse_args()

        supabase = get_database_connection()
        response = supabase.table("carParks").insert({
            "name": args["name"],
            "spaces": args["spaces"],
            "location": args["location"]
        }).execute()

        if not response.data:
            return {
                "error": "Failed to create car park"
            }, 500

        return {
            "data": CarParkSchema().dump(response.data[0])
        }, 201