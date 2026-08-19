"""
Tests for cuvis.cuvis_aux helpers.

Covers the shared epoch conversion and the GPSData timestamp, which the bundled
test session carries no record for.
"""

import datetime
from types import SimpleNamespace

import pytest

from cuvis.cuvis_aux import GPSData, _utc_from_epoch_ms

CAPTURE_TIME_MS = 1700824385356
CAPTURE_TIME = datetime.datetime(
    2023, 11, 24, 11, 13, 5, 356000, tzinfo=datetime.timezone.utc
)


@pytest.mark.parametrize(
    "milliseconds, expected",
    [
        (0, datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)),
        (CAPTURE_TIME_MS, CAPTURE_TIME),
    ],
    ids=["epoch", "capture_time"],
)
def test_utc_from_epoch_ms(milliseconds, expected):
    """Test epoch milliseconds convert to the expected timezone-aware UTC datetime."""
    assert _utc_from_epoch_ms(milliseconds) == expected
    assert _utc_from_epoch_ms(milliseconds).utcoffset() == datetime.timedelta(0)


def test_gps_data_time_is_utc_aware():
    """Test the GPS timestamp is a timezone-aware UTC datetime (see cuvis.pyil#29)."""
    gps = GPSData._from_internal(
        SimpleNamespace(
            longitude=9.9937, latitude=48.4011, altitude=478.0, time=CAPTURE_TIME_MS
        )
    )
    assert gps.time.tzinfo is not None
    assert gps.time.utcoffset() == datetime.timedelta(0)
    assert gps.time == CAPTURE_TIME
