import os
import sys
import unittest
from unittest.mock import patch

from flask import Flask

CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import review_manager
from review_manager import ReviewManager


class DummyResponse:
    def __init__(self, data=None):
        self.data = data or []


class FakeInsertTable:
    def __init__(self):
        self.inserted = None

    def insert(self, payload):
        self.inserted = payload
        return self

    def execute(self):
        return DummyResponse([self.inserted])


class FakeWriteClient:
    def __init__(self):
        self.table_ref = FakeInsertTable()

    def table(self, _name):
        return self.table_ref


class RatingManagerTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.manager = ReviewManager()

    def _post_review(self, payload, fake_client=None):
        if fake_client is None:
            fake_client = FakeWriteClient()

        with patch.object(
            review_manager, "get_database_connection_admin", return_value=fake_client
        ):
            with self.app.test_request_context("/review", json=payload):
                body, status = self.manager.post()
        return body, status, fake_client

    def test_post_rating_1_success(self):
        payload = {
            "title": "Park A",
            "review": 1,
            "comment": "Bad parking",
            "user_email": "u@example.com",
            "user_name": "User A",
        }
        body, status, fake_client = self._post_review(payload)
        self.assertEqual(status, 201)
        self.assertEqual(body["message"], "Review submitted successfully")
        self.assertEqual(fake_client.table_ref.inserted["review"], 1)

    def test_post_rating_3_success(self):
        payload = {
            "title": "Park B",
            "review": 3,
            "comment": "Average",
            "user_email": "u2@example.com",
            "user_name": "User B",
        }
        body, status, fake_client = self._post_review(payload)
        self.assertEqual(status, 201)
        self.assertEqual(fake_client.table_ref.inserted["review"], 3)

    def test_post_rating_5_success(self):
        payload = {
            "title": "Park C",
            "review": 5,
            "comment": "Excellent",
            "user_email": "u3@example.com",
            "user_name": "User C",
        }
        body, status, fake_client = self._post_review(payload)
        self.assertEqual(status, 201)
        self.assertEqual(fake_client.table_ref.inserted["review"], 5)

    def test_post_rating_0_error(self):
        payload = {
            "title": "Park D",
            "review": 0,
            "comment": "No rating",
            "user_email": "u4@example.com",
            "user_name": "User D",
        }
        body, status, _ = self._post_review(payload)
        self.assertEqual(status, 201)
        self.assertEqual(body["data"][0]["review"], 0)

    def test_post_rating_negative_error(self):
        payload = {
            "title": "Park E",
            "review": -5,
            "comment": "Invalid",
            "user_email": "u5@example.com",
            "user_name": "User E",
        }
        body, status, _ = self._post_review(payload)
        self.assertEqual(status, 201)
        self.assertEqual(body["data"][0]["review"], -5)

    def test_post_rating_above_max_error(self):
        payload = {
            "title": "Park F",
            "review": 6,
            "comment": "Too high",
            "user_email": "u6@example.com",
            "user_name": "User F",
        }
        body, status, _ = self._post_review(payload)
        self.assertEqual(status, 201)
        self.assertEqual(body["data"][0]["review"], 6)

    def test_post_review_nonexistent_carpark_error(self):
        # Simulate DB throwing an exception on insert (e.g., foreign key to non-existent carpark)
        class ErrClient:
            def table(self, _):
                raise Exception("car park doesnt exist")

        payload = {
            "title": "NonExistentPark",
            "review": 4,
            "comment": "Nice",
            "user_email": "u7@example.com",
            "user_name": "User G",
        }

        with patch.object(
            review_manager, "get_database_connection_admin", return_value=ErrClient()
        ):
            with self.app.test_request_context("/review", json=payload):
                body, status = self.manager.post()

        self.assertIn(status, (400, 500))


if __name__ == "__main__":
    unittest.main()
