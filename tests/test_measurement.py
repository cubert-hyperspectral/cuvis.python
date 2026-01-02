"""
Tests for cuvis.Measurement module.

Mirrors functionality from Example 2 notebook (Load Measurement) related to
measurement data access, properties, and metadata.
"""

import pytest
import datetime
import cuvis


def test_measurement_metadata_attributes(aquarium_measurement):
    """Test Measurement has expected metadata attributes."""
    assert hasattr(aquarium_measurement, 'capture_time')
    assert hasattr(aquarium_measurement, 'integration_time')
    assert hasattr(aquarium_measurement, 'serial_number')
    assert hasattr(aquarium_measurement, 'product_name')


def test_measurement_capture_time(aquarium_measurement):
    """Test capture time is a datetime object."""
    capture_time = aquarium_measurement.capture_time
    assert isinstance(capture_time, datetime.datetime)


def test_measurement_integration_time(aquarium_measurement):
    """Test integration time is positive."""
    integration_time = aquarium_measurement.integration_time
    assert isinstance(integration_time, (int, float))
    assert integration_time > 0


def test_measurement_serial_number(aquarium_measurement):
    """Test serial number is a string."""
    serial = aquarium_measurement.serial_number
    assert isinstance(serial, str)
    assert len(serial) > 0


def test_measurement_product_name(aquarium_measurement):
    """Test product name is a string."""
    product = aquarium_measurement.product_name
    assert isinstance(product, str)
    assert len(product) > 0


def test_measurement_data_dict(aquarium_measurement):
    """Test measurement data dictionary exists."""
    assert hasattr(aquarium_measurement, 'data')
    assert isinstance(aquarium_measurement.data, dict)


def test_measurement_capabilities(aquarium_measurement):
    """Test measurement capabilities."""
    cap = aquarium_measurement.capabilities
    assert isinstance(cap, cuvis.Capabilities)


def test_measurement_comment_get_set(aquarium_measurement):
    """Test comment property getter/setter."""
    original = aquarium_measurement.comment
    test_comment = "Test comment for pytest"
    aquarium_measurement.comment = test_comment
    assert aquarium_measurement.comment == test_comment
    # Restore original
    aquarium_measurement.comment = original


def test_measurement_name_get_set(aquarium_measurement):
    """Test name property getter/setter."""
    original = aquarium_measurement.name
    test_name = "Test name for pytest"
    aquarium_measurement.name = test_name
    assert aquarium_measurement.name == test_name
    # Restore original
    aquarium_measurement.name = original


def test_measurement_deepcopy(aquarium_measurement):
    """Test measurement can be deep copied."""
    copy = aquarium_measurement.deepcopy()
    assert isinstance(copy, cuvis.Measurement)
    assert copy._handle != aquarium_measurement._handle
    # Verify copy has same metadata
    assert copy.capture_time == aquarium_measurement.capture_time
    assert copy.integration_time == aquarium_measurement.integration_time
