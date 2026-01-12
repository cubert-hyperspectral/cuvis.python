"""
Tests for cuvis.SessionFile module.

Mirrors functionality from Example 2 notebook (Load Measurement) related to
SessionFile loading, iteration, and metadata access.
"""

import pytest
import cuvis


def test_session_file_load(test_session_file):
    """Test SessionFile loads successfully."""
    assert test_session_file is not None


def test_session_file_size(test_session_file):
    """Test SessionFile reports correct size."""
    size = test_session_file.get_size()
    assert isinstance(size, int)
    assert size >= 1  # At least one measurement


def test_session_file_len(test_session_file):
    """Test SessionFile supports len()."""
    length = len(test_session_file)
    assert isinstance(length, int)
    assert length >= 1


def test_session_file_iteration(test_session_file):
    """Test SessionFile is iterable."""
    count = 0
    for mesu in test_session_file:
        assert isinstance(mesu, cuvis.Measurement)
        count += 1
    assert count >= 1


def test_session_file_indexing(test_session_file):
    """Test SessionFile supports indexing."""
    mesu = test_session_file[0]
    assert isinstance(mesu, cuvis.Measurement)


def test_session_file_get_measurement(test_session_file):
    """Test SessionFile.get_measurement() method."""
    mesu = test_session_file.get_measurement(0)
    assert isinstance(mesu, cuvis.Measurement)


# def test_session_file_fps(test_session_file):
#     """Test SessionFile FPS property."""
#     fps = test_session_file.fps
#     assert isinstance(fps, (int, float))
#     assert fps >= 0


def test_session_file_operation_mode(test_session_file):
    """Test SessionFile operation mode."""
    mode = test_session_file.operation_mode
    assert isinstance(mode, cuvis.OperationMode)


def test_session_file_hash(test_session_file):
    """Test SessionFile hash property."""
    hash_val = test_session_file.hash
    assert isinstance(hash_val, str)
    assert len(hash_val) > 0
