import sys
import os
from datetime import datetime, timedelta

CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from extension_service import ExtensionService


def test_add_two_hours_calculates_new_expiry_and_price():
    svc = ExtensionService(hourly_rate=3.0)  # $3/hour for easy math

    now = datetime.now()
    current_expiry = now + timedelta(hours=1)  # current expiry in 1 hour

    add_seconds = 2 * 3600  # add 2 hours
    new_expiry, price = svc.extend_session(now, current_expiry, add_seconds)

    assert new_expiry == current_expiry + timedelta(hours=2)
    assert price == 6.0  # 2 hours * $3/hr


def test_extend_beyond_max_limit_raises_error():
    # Set max_total_seconds to 3 hours for test
    svc = ExtensionService(hourly_rate=5.0, max_total_seconds=3 * 3600)

    now = datetime.now()
    current_expiry = now + timedelta(hours=1)

    # Trying to extend by 3 hours would result in total 4 hours from now -> exceeds 3 hour max
    add_seconds = 3 * 3600

    try:
        svc.extend_session(now, current_expiry, add_seconds)
        assert False, "Expected ValueError for exceeding max stay"
    except ValueError as e:
        assert "Maximum stay exceeded" in str(e)


def test_check_time_remaining_and_countdown():
    svc = ExtensionService()

    now = datetime.now()
    expiry = now + timedelta(seconds=10)

    remaining_initial = svc.time_remaining(now, expiry)
    assert remaining_initial == 10

    # Simulate 3 seconds later
    later = now + timedelta(seconds=3)
    remaining_later = svc.time_remaining(later, expiry)
    assert remaining_later == 7
