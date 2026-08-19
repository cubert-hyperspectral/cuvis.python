"""
Tests for cuvis.AcquisitionContext module.

Mirrors functionality from Example 1 notebook (Take Snapshot) related to
simulated camera acquisition, operation modes, and snapshot capture.
"""

import pytest
import time
import cuvis
from cuvis.cuvis_aux import SDKException
from cuvis.cuvis_types import AsyncResult


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
def test_simulated_capture_snapshot(
    simulated_acquisition_context, processing_context_from_session
):
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
    assert "cube" in mesu.data


def test_acquisition_context_component_count(simulated_acquisition_context):
    """Test component count property."""
    count = simulated_acquisition_context.component_count
    assert isinstance(count, int)
    assert count >= 0


def _drain(acq):
    """Take the queued measurement back out, so the next test sees an empty queue."""
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            return acq.get_next_measurement(500)
        except SDKException:
            continue
    pytest.fail("the capture never reached the internal queue")


def _ready_software_context(acq):
    """A simulated context in Software mode, ready to be triggered."""
    acq.operation_mode = cuvis.OperationMode.Software
    deadline = time.time() + 10
    while not acq.ready and time.time() < deadline:
        time.sleep(0.1)
    if not acq.ready:
        pytest.skip("Acquisition context not ready within timeout")
    return acq


def _assert_queue_empty(acq):
    with pytest.raises(SDKException):
        acq.get_next_measurement(300)


def test_capture_to_internal_queues_the_measurement(
    simulated_acquisition_context, processing_context_from_session
):
    """to_internal=True hands the SDK a null result handle, which queues the capture.

    The queue is checked empty on both sides so the measurement cannot be anything but
    this capture, and the result is processed to prove it is a usable measurement rather
    than a handle the SDK never filled in.
    """
    acq = _ready_software_context(simulated_acquisition_context)
    _assert_queue_empty(acq)

    assert acq.capture(to_internal=True) is None

    mesu = _drain(acq)
    assert isinstance(mesu, cuvis.Measurement)
    _assert_queue_empty(acq)

    processing_context_from_session.processing_mode = cuvis.ProcessingMode.Raw
    processing_context_from_session.apply(mesu)
    assert mesu.cube.array.size > 0


def test_worker_receives_a_capture_from_the_internal_queue(
    simulated_acquisition_context, processing_context_from_session
):
    """The other consumer cuvis.h:1887 names for the internal queue."""
    acq = _ready_software_context(simulated_acquisition_context)
    _assert_queue_empty(acq)

    worker = cuvis.Worker(cuvis.WorkerSettings(output_queue_size=8))
    worker.set_acquisition_context(acq)
    processing_context_from_session.processing_mode = cuvis.ProcessingMode.Raw
    worker.set_processing_context(processing_context_from_session)
    worker.start_processing()
    try:
        assert acq.capture(to_internal=True) is None

        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                result = worker.get_next_result(1000)
            except SDKException:
                continue
            assert isinstance(result.mesu, cuvis.Measurement)
            return
        pytest.fail("the worker never saw the queued capture")
    finally:
        worker.stop_processing()
        worker.drop_all_queued()
        worker.set_acquisition_context(None)


def test_capture_returns_an_async_measurement_without_queueing_it(
    simulated_acquisition_context,
):
    """The other half of the same switch: a result handle means no queue entry.

    The async result is collected first, so the capture is known to have happened and an
    empty queue afterwards cannot be mistaken for a capture that never ran. Three windows
    rather than one, so a late delivery does not pass as an absence.
    """
    acq = _ready_software_context(simulated_acquisition_context)
    _assert_queue_empty(acq)

    mesu, result = acq.capture().get(5000)
    assert isinstance(mesu, cuvis.Measurement)
    assert result is AsyncResult.done

    for _ in range(3):
        _assert_queue_empty(acq)
