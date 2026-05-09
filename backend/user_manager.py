import json
from urllib.parse import unquote

from flask import request
from flask_restful import Resource
from modules import get_database_connection, get_database_connection_admin
from authentication_manager import getUser as auth_getUser

    


def get_user(email):
    try:
        user = auth_getUser(email=email)
        if user and user.get("result") is True:
            supabase = get_database_connection()
            print(user.get("user_id"))
            vehicle_response = (
                supabase.table("vehicle")
                .select("vehicle_id, registration, type")
                .eq("user_id", user.get("user_id"))
                .order("vehicle_id", desc=False)
                .execute()
            )
            print(f"Fetched vehicles for user {email}: {vehicle_response.data}")
            vehicles = vehicle_response.data if vehicle_response and vehicle_response.data else []
            payment_methods = []

            payment_token = user.get("payment_token")
            if payment_token:
                try:
                    parsed = json.loads(payment_token)
                    if isinstance(parsed, list):
                        payment_methods = parsed
                except Exception:
                    payment_methods = []

            return {
                "process": "Get User",
                "user_id": user.get("user_id"),
                "name": user.get("first_name") or user.get("name"),
                "lastname": user.get("last_name") or user.get("lastname"),
                "email": user.get("email"),
                "vehicles": vehicles,
                "payment_methods": payment_methods,
                "result": True,
            }, 200

        return {
            "process": "Get User",
            "user_id": None,
            "name": None,
            "lastname": None,
            "email": email,
            "vehicles": [],
            "payment_methods": [],
            "error": "User not found",
            "result": False,
        }, 404
    except Exception as e:
        print(f"Error occurred while fetching user: {e}")
        return {
            "process": "Get User",
            "user_id": None,
            "name": None,
            "lastname": None,
            "email": email, 
            "vehicles": [],
            "payment_methods": [],
            "error": "User not found",
            "result": False
        }, 404


def _normalise_vehicle_type(raw_type):
    if not raw_type:
        return "CAR"

    normalised = str(raw_type).upper().strip()
    allowed = {"CAR", "MOTORCYCLE", "LORRY", "EV", "PCV"}
    if normalised in allowed:
        return normalised

    aliases = {
        "PERSONAL": "CAR",
        "WORK": "PCV",
        "FAMILY": "CAR",
        "OTHER": "CAR",
    }
    return aliases.get(normalised, "CAR")


def add_vehicle(email, registration, vehicle_type):
    """Add a single vehicle for a user."""
    try:
        user = auth_getUser(email=email)
        if not user or user.get("result") is not True:
            return {
                "process": "Add Vehicle",
                "result": False,
                "error": "User not found",
            }, 404

        user_id = user.get("user_id")

        supabase = get_database_connection_admin()

        registration = (registration or "").strip().upper()
        if not registration:
            return {
                "process": "Add Vehicle",
                "result": False,
                "error": "Registration cannot be empty",
            }, 400

        vehicle_type = _normalise_vehicle_type(vehicle_type)

        response = supabase.table("vehicle").insert(
            {
                "user_id": user_id,
                "registration": registration,
                "type": vehicle_type,
            }
        ).execute()

        if hasattr(response, 'error') and response.error:
            print(f"Error adding vehicle: {response.error}")
            return {
                "process": "Add Vehicle",
                "result": False,
                "error": str(response.error),
            }, 400

        if response.data:
            print(f"Added vehicle {registration} for user {email}")
            return {
                "process": "Add Vehicle",
                "result": True,
                "vehicle": response.data[0],
            }, 201

        return {
            "process": "Add Vehicle",
            "result": False,
            "error": "Failed to insert vehicle",
        }, 400

    except Exception as e:
        print(f"Error adding vehicle: {e}")
        return {
            "process": "Add Vehicle",
            "result": False,
            "error": str(e),
        }, 400


def delete_vehicle(email, vehicle_id):
    """Delete a vehicle for a user."""
    try:
        user = auth_getUser(email=email)
        if not user or user.get("result") is not True:
            return {
                "process": "Delete Vehicle",
                "result": False,
                "error": "User not found",
            }, 404

        user_id = user.get("user_id")

        supabase = get_database_connection_admin()

        response = (
            supabase.table("vehicle")
            .delete()
            .eq("user_id", user_id)
            .eq("vehicle_id", vehicle_id)
            .execute()
        )

        print(f"Deleted vehicle {vehicle_id} for user {email}")
        return {
            "process": "Delete Vehicle",
            "result": True,
        }, 200

    except Exception as e:
        print(f"Error deleting vehicle: {e}")
        return {
            "process": "Delete Vehicle",
            "result": False,
            "error": str(e),
        }, 400


def update_user(name, lastname, email=None, updated_email=None, vehicles=None, payment_methods=None):
    supabase = get_database_connection_admin()

    payment_methods = payment_methods or []
    vehicles = vehicles or []

    update_payload = {
        "first_name": name,
        "last_name": lastname,
        "payment_token": json.dumps(payment_methods),
    }
    if updated_email and updated_email != email:
        update_payload["email"] = updated_email

    response = (
        supabase.table("User")
        .update(update_payload)
        .eq("email", email)
        .execute()
    )
    print(f"Updating user: {name} {lastname}, email: {email}")
    if response or response.data:
        return {
            "process": "Update User",
            "user_id": response.data[0].get("user_id"),
            "name": name,
            "lastname": lastname,
            "email": updated_email or email,
            "result": True,
            }, 200

    if vehicles is not None:
        user_id = response.data[0].get("user_id")

        supabase.table("vehicle").delete().eq("user_id", user_id).execute()

        for vehicle in vehicles:
            registration = (vehicle.get("vrm") or vehicle.get("registration") or "").strip().upper()
            if not registration:
                continue

            vehicle_type = _normalise_vehicle_type(vehicle.get("type"))
            supabase.table("vehicle").insert(
                {
                    "user_id": user_id,
                    "registration": registration,
                    "type": vehicle_type,
                }
            ).execute()
            return {
                "process": "Update User",
                "user_id": user_id,
                "name": name,
                "lastname": lastname,
                "email": updated_email or email,
                "result": True,
            }, 200


    return {
        "process": "Update User",
        "result": False
    }, 404



class UserResource(Resource):
    def get(self, email):
        email = unquote(email)
        return get_user(email)

    def put(self, email):
        email = unquote(email)
        body = request.get_json(silent=True) or {}

        name = body.get("name")
        lastname = body.get("lastname")

        if name is None or lastname is None:
            return {
                "process": "Update User",
                "result": False,
                "error": "name and lastname are required",
            }, 400

        return update_user(
            name=name,
            lastname=lastname,
            email=email,
            updated_email=body.get("email"),
            vehicles=body.get("vehicles", []),
            payment_methods=body.get("payment_methods", []),
        )


class VehicleResource(Resource):
    def post(self, email):
        """Add a new vehicle for a user."""
        email = unquote(email)
        body = request.get_json(silent=True) or {}

        registration = body.get("registration")
        vehicle_type = body.get("type")

        if not registration:
            return {
                "process": "Add Vehicle",
                "result": False,
                "error": "registration is required",
            }, 400

        return add_vehicle(
            email=email,
            registration=registration,
            vehicle_type=vehicle_type or "CAR",
        )

    def delete(self, email):
        """Delete a vehicle for a user."""
        email = unquote(email)
        body = request.get_json(silent=True) or {}

        vehicle_id = body.get("vehicle_id")

        if vehicle_id is None:
            return {
                "process": "Delete Vehicle",
                "result": False,
                "error": "vehicle_id is required",
            }, 400

        return delete_vehicle(email=email, vehicle_id=vehicle_id)



