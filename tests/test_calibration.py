"""
Tests for cuvis.Calibration module.

Covers the CalibrationInfo fields read from the bundled test session.
"""

import datetime


def test_calibration_info_calibration_date_is_datetime(test_calibration):
    """Test the calibration date is converted instead of returned as raw epoch milliseconds."""
    assert isinstance(test_calibration.info.calibration_date, datetime.datetime)


def test_calibration_info_calibration_date_is_utc_aware(test_calibration):
    """Test the calibration date is a timezone-aware UTC datetime (see cuvis.pyil#29)."""
    calibration_date = test_calibration.info.calibration_date
    assert calibration_date.tzinfo is not None
    assert calibration_date.utcoffset() == datetime.timedelta(0)


def test_calibration_info_calibration_date_day(test_calibration):
    """Test the calibration date lands on the expected day.

    The SDK derives this value as midnight on the calibration day in the host's
    standard local time, so the instant shifts with the machine running the test
    and only the day can be pinned portably. Standard offsets span UTC-12 to
    UTC+14, which bounds the deviation at 14 hours.
    """
    assert abs(
        test_calibration.info.calibration_date
        - datetime.datetime(2023, 7, 27, tzinfo=datetime.timezone.utc)
    ) <= datetime.timedelta(hours=14)
