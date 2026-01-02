"""
Tests for cuvis.SessionFile module.

Mirrors functionality from Example 2 notebook (Load Measurement) related to
SessionFile loading, iteration, and metadata access.
"""

import pytest
import cuvis


def test_session_file_load(aquarium_session_file):
    """Test SessionFile loads successfully."""
    assert aquarium_session_file is not None


def test_session_file_size(aquarium_session_file):
    """Test SessionFile reports correct size."""
    size = aquarium_session_file.get_size()
    assert isinstance(size, int)
    assert size >= 1  # At least one measurement


def test_session_file_len(aquarium_session_file):
    """Test SessionFile supports len()."""
    length = len(aquarium_session_file)
    assert isinstance(length, int)
    assert length >= 1


def test_session_file_iteration(aquarium_session_file):
    """Test SessionFile is iterable."""
    count = 0
    for mesu in aquarium_session_file:
        assert isinstance(mesu, cuvis.Measurement)
        count += 1
    assert count >= 1


def test_session_file_indexing(aquarium_session_file):
    """Test SessionFile supports indexing."""
    mesu = aquarium_session_file[0]
    assert isinstance(mesu, cuvis.Measurement)


def test_session_file_get_measurement(aquarium_session_file):
    """Test SessionFile.get_measurement() method."""
    mesu = aquarium_session_file.get_measurement(0)
    assert isinstance(mesu, cuvis.Measurement)


def test_session_file_fps(aquarium_session_file):
    """Test SessionFile FPS property."""
    fps = aquarium_session_file.fps
    assert isinstance(fps, (int, float))
    assert fps >= 0


def test_session_file_operation_mode(aquarium_session_file):
    """Test SessionFile operation mode."""
    mode = aquarium_session_file.operation_mode
    assert isinstance(mode, cuvis.OperationMode)


def test_session_file_hash(aquarium_session_file):
    """Test SessionFile hash property."""
    hash_val = aquarium_session_file.hash
    assert isinstance(hash_val, str)
    assert len(hash_val) > 0
