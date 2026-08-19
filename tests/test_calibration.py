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


def test_calibration_info_calibration_date_value(test_calibration):
    """Test the calibration date has the expected exact UTC value."""
    assert test_calibration.info.calibration_date == datetime.datetime(
        2023, 7, 26, 23, 0, tzinfo=datetime.timezone.utc
    )
