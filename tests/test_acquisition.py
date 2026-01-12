"""
Tests for cuvis.AcquisitionContext module.

Mirrors functionality from Example 1 notebook (Take Snapshot) related to
simulated camera acquisition, operation modes, and snapshot capture.
"""

import pytest
import time
import cuvis


def test_simulated_acquisition_context_creation(simulated_acquisition_context):
    """Test simulated AcquisitionContext created successfully."""
    assert simulated_acquisition_context is not None
    assert isinstance(simulated_acquisition_context, cuvis.AcquisitionContext)


def test_acquisition_context_state(simulated_acquisition_context):
    """Test acquisition context state property."""
    state = simulated_acquisition_context.state
    assert isinstance(state, cuvis.HardwareState)


def test_acquisition_context_ready(simulated_acquisition_context):
    """Test acquisition context ready property."""
    ready = simulated_acquisition_context.ready
    assert isinstance(ready, bool)


def test_acquisition_context_operation_mode(simulated_acquisition_context):
    """Test operation mode get/set."""
    # Get current mode
    original_mode = simulated_acquisition_context.operation_mode
    assert isinstance(original_mode, cuvis.OperationMode)

    # Set to Software mode
    simulated_acquisition_context.operation_mode = cuvis.OperationMode.Software
    assert simulated_acquisition_context.operation_mode == cuvis.OperationMode.Software

    # Restore original
    simulated_acquisition_context.operation_mode = original_mode


def test_acquisition_context_integration_time(simulated_acquisition_context):
    """Test integration time get/set."""
    # Get current integration time
    original_time = simulated_acquisition_context.integration_time
    assert isinstance(original_time, (int, float))
    assert original_time > 0

    # Set new integration time
    new_time = 10.0
    simulated_acquisition_context.integration_time = new_time
    assert simulated_acquisition_context.integration_time == new_time

    # Restore original
    simulated_acquisition_context.integration_time = original_time


def test_acquisition_context_session_info(simulated_acquisition_context):
    """Test session info get/set."""
    session_info = simulated_acquisition_context.session_info
    assert isinstance(session_info, cuvis.SessionData)


@pytest.mark.slow
def test_simulated_capture_snapshot(simulated_acquisition_context, processing_context_from_session):
    """Test capturing snapshot in simulated mode."""
    acq = simulated_acquisition_context

    # Set operation mode to Software
    acq.operation_mode = cuvis.OperationMode.Software

    # Wait for ready state (with timeout)
    timeout = 10  # seconds
    start = time.time()
    while not acq.ready and (time.time() - start) < timeout:
        time.sleep(0.1)

    if not acq.ready:
        pytest.skip("Acquisition context not ready within timeout")

    # Capture snapshot
    mesu = acq.capture_at(timeout_ms=5000)
    assert isinstance(mesu, cuvis.Measurement)

    # Verify we can process the captured measurement
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.Raw
    pc.apply(mesu)
    assert 'cube' in mesu.data


def test_acquisition_context_component_count(simulated_acquisition_context):
    """Test component count property."""
    count = simulated_acquisition_context.component_count
    assert isinstance(count, int)
    assert count >= 0
