"""
Tests for cuvis.General module.

Mirrors functionality from Example notebooks related to SDK initialization,
version information, and configuration.
"""

import pytest
import logging
import cuvis


def test_sdk_version(sdk_initialized):
    """Test SDK version retrieval."""
    version = cuvis.version()
    assert isinstance(version, str)
    assert len(version) > 0
    # Version should contain some numbers
    assert any(char.isdigit() for char in version)


def test_sdk_version_via_sdk_version_function(sdk_initialized):
    """Test SDK version via sdk_version() alias."""
    version = cuvis.General.sdk_version()
    assert isinstance(version, str)
    assert len(version) > 0


def test_wrapper_version(sdk_initialized):
    """Test wrapper version retrieval."""
    version = cuvis.General.wrapper_version()
    assert isinstance(version, str)
    assert "3.5.0" in version  # Current wrapper version


# def test_sdk_initialization_and_shutdown():
#    """Test SDK can be initialized and shut down multiple times."""
#    cuvis.init()
#    cuvis.shutdown()
#    cuvis.init()
#    cuvis.shutdown()


def test_log_level_setting(sdk_initialized):
    """Test log level can be set."""
    # Test with logging constants
    cuvis.set_log_level(logging.INFO)
    cuvis.set_log_level(logging.DEBUG)
    cuvis.set_log_level(logging.WARNING)

    # Test with string input
    cuvis.set_log_level("debug")
    cuvis.set_log_level("info")
    cuvis.set_log_level("warning")
