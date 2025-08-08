from datetime import datetime

import pytest

from analyse import get_flux_tariff
from datetime_util import local_tz


@pytest.mark.parametrize(
    "dt,expected",
    [
        # FLUX: 02:00 - 04:59
        (datetime(2024, 1, 1, 2, 0, tzinfo=local_tz), "FLUX"),
        (datetime(2024, 1, 1, 4, 30, tzinfo=local_tz), "FLUX"),
        # PEAK: 16:00 - 18:59
        (datetime(2024, 1, 1, 16, 0, tzinfo=local_tz), "PEAK"),
        (datetime(2024, 1, 1, 18, 30, tzinfo=local_tz), "PEAK"),
        # DAY: all other times
        (datetime(2024, 1, 1, 1, 30, tzinfo=local_tz), "DAY"),
        (datetime(2024, 1, 1, 5, 0, tzinfo=local_tz), "DAY"),
        (datetime(2024, 1, 1, 15, 30, tzinfo=local_tz), "DAY"),
        (datetime(2024, 1, 1, 19, 0, tzinfo=local_tz), "DAY"),
        (datetime(2024, 1, 1, 23, 30, tzinfo=local_tz), "DAY"),
    ],
)
def test_get_flux_tariff_not_bst(dt, expected):
    assert get_flux_tariff(dt) == expected


@pytest.mark.parametrize(
    "dt,expected",
    [
        # FLUX: 02:00 - 04:59
        (datetime(2024, 6, 1, 2, 0, tzinfo=local_tz), "FLUX"),
        (datetime(2024, 6, 1, 4, 30, tzinfo=local_tz), "FLUX"),
        # PEAK: 16:00 - 18:59
        (datetime(2024, 6, 1, 16, 0, tzinfo=local_tz), "PEAK"),
        (datetime(2024, 6, 1, 18, 30, tzinfo=local_tz), "PEAK"),
        # DAY: all other times
        (datetime(2024, 6, 1, 1, 30, tzinfo=local_tz), "DAY"),
        (datetime(2024, 6, 1, 5, 0, tzinfo=local_tz), "DAY"),
        (datetime(2024, 6, 1, 15, 30, tzinfo=local_tz), "DAY"),
        (datetime(2024, 6, 1, 19, 0, tzinfo=local_tz), "DAY"),
        (datetime(2024, 6, 1, 23, 30, tzinfo=local_tz), "DAY"),
    ],
)
def test_get_flux_tariff_bst(dt, expected):
    assert get_flux_tariff(dt) == expected
