"""
Pytest configuration and fixtures for cuvis.python integration tests.

This module provides shared fixtures for testing the CUVIS SDK Python wrapper.
All fixtures use the real SDK (integration testing, not mocked).
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import os
import gc
import cuvis


@pytest.fixture(scope="session")
def sdk_initialized():
    """
    Initialize SDK once per test session.

    Uses CUVIS_SETTINGS environment variable if set, otherwise uses current directory.
    """
    settings_path = os.environ.get("CUVIS_SETTINGS", ".")
    cuvis.init(settings_path=settings_path)
    yield
    gc.collect()
    # cuvis.shutdown()


@pytest.fixture(scope="session")
def test_data_dir():
    """Path to test data directory containing Aquarium.cu3s."""
    return Path(__file__).parent / "test_data"


@pytest.fixture(scope="session")
def rgb_userplugin_path(test_data_dir):
    """
    Path to RGB user plugin file (00_RGB.xml).

    Skips tests if the file is not found.
    """
    plugin_path = test_data_dir / "00_RGB.xml"
    if not plugin_path.exists():
        pytest.skip(f"RGB user plugin not found: {plugin_path}")
    return str(plugin_path)


@pytest.fixture(scope="session")
def aquarium_session_file(test_data_dir, sdk_initialized):
    """
    Load Aquarium.cu3s SessionFile once per session.

    Skips tests if the file is not found.
    """
    session_path = test_data_dir / "Aquarium.cu3s"
    if not session_path.exists():
        pytest.skip(f"Test data not found: {session_path}")
    session = cuvis.SessionFile(str(session_path))
    yield session
    del session
    gc.collect()


@pytest.fixture
def aquarium_measurement(aquarium_session_file):
    """
    Get first measurement from Aquarium session.

    Function-scoped to ensure each test gets a fresh measurement reference.
    """
    return aquarium_session_file.get_measurement(0)


@pytest.fixture
def processing_context_from_session(aquarium_session_file):
    """
    Create ProcessingContext from SessionFile.

    Function-scoped to ensure each test gets a fresh context.
    """
    return cuvis.ProcessingContext(aquarium_session_file)


@pytest.fixture
def temp_output_dir():
    """
    Temporary directory for export outputs.

    Automatically cleaned up after test completes.
    """
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def simulated_acquisition_context(aquarium_session_file, sdk_initialized):
    """
    Create simulated AcquisitionContext from SessionFile.

    Session-scoped since acquisition context initialization can be slow.
    """
    acq = cuvis.AcquisitionContext(aquarium_session_file, simulate=True)
    yield acq
    del acq
    gc.collect()
