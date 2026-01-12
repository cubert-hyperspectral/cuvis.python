"""
Tests for cuvis.Measurement module.

Mirrors functionality from Example 2 notebook (Load Measurement) related to
measurement data access, properties, and metadata.
"""

import pytest
import datetime
import cuvis


def test_measurement_metadata_attributes(test_measurement):
    """Test Measurement has expected metadata attributes."""
    assert hasattr(test_measurement, "capture_time")
    assert hasattr(test_measurement, "integration_time")
    assert hasattr(test_measurement, "serial_number")
    assert hasattr(test_measurement, "product_name")


def test_measurement_capture_time(test_measurement):
    """Test capture time is a datetime object."""
    capture_time = test_measurement.capture_time
    assert isinstance(capture_time, datetime.datetime)


def test_measurement_integration_time(test_measurement):
    """Test integration time is positive."""
    integration_time = test_measurement.integration_time
    assert isinstance(integration_time, (int, float))
    assert integration_time > 0


def test_measurement_serial_number(test_measurement):
    """Test serial number is a string."""
    serial = test_measurement.serial_number
    assert isinstance(serial, str)
    assert len(serial) > 0


def test_measurement_product_name(test_measurement):
    """Test product name is a string."""
    product = test_measurement.product_name
    assert isinstance(product, str)
    assert len(product) > 0


def test_measurement_data_dict(test_measurement):
    """Test measurement data dictionary exists."""
    assert hasattr(test_measurement, "data")
    assert isinstance(test_measurement.data, dict)


def test_measurement_capabilities(test_measurement):
    """Test measurement capabilities."""
    cap = test_measurement.capabilities
    assert isinstance(cap, cuvis.Capabilities)


def test_measurement_comment_get_set(test_measurement):
    """Test comment property getter/setter."""
    original = test_measurement.comment
    test_comment = "Test comment for pytest"
    test_measurement.comment = test_comment
    assert test_measurement.comment == test_comment
    # Restore original
    test_measurement.comment = original


def test_measurement_name_get_set(test_measurement):
    """Test name property getter/setter."""
    original = test_measurement.name
    test_name = "Test name for pytest"
    test_measurement.name = test_name
    assert test_measurement.name == test_name
    # Restore original
    test_measurement.name = original


def test_measurement_deepcopy(test_measurement):
    """Test measurement can be deep copied."""
    copy = test_measurement.deepcopy()
    assert isinstance(copy, cuvis.Measurement)
    assert copy._handle != test_measurement._handle
    # Verify copy has same metadata
    assert copy.capture_time == test_measurement.capture_time
    assert copy.integration_time == test_measurement.integration_time
