"""
Tests for cuvis.Worker module.

Mirrors functionality from Example 5 notebook (Record Video) related to
worker pipeline management, processing, and result retrieval.
"""

import pytest
import cuvis


def test_worker_creation():
    """Test Worker can be created."""
    settings = cuvis.WorkerSettings()
    worker = cuvis.Worker(settings)
    assert worker is not None


def test_worker_settings_configuration():
    """Test WorkerSettings can be configured."""
    settings = cuvis.WorkerSettings(mandatory_queue_size=10, output_queue_size=5)
    assert settings is not None


def test_worker_set_processing_context(processing_context_from_session):
    """Test setting ProcessingContext on Worker."""
    settings = cuvis.WorkerSettings()
    worker = cuvis.Worker(settings)

    # Set processing context
    worker.set_processing_context(processing_context_from_session)

    # Worker should indicate processing is set
    assert hasattr(worker, "_processing_set")


def test_worker_set_exporter(temp_output_dir):
    """Test setting exporter on Worker."""
    settings = cuvis.WorkerSettings()
    worker = cuvis.Worker(settings)

    # Create and set exporter
    save_args = cuvis.SaveArgs(export_dir=str(temp_output_dir))
    exporter = cuvis.CubeExporter(save_args)
    worker.set_exporter(exporter)

    # Worker should accept the exporter
    assert hasattr(worker, "_exporter_set")


@pytest.mark.slow
def test_worker_pipeline_session_file(
    test_session_file, processing_context_from_session, temp_output_dir
):
    """Test Worker pipeline with SessionFile ingestion."""
    # Setup worker
    settings = cuvis.WorkerSettings(output_queue_size=5)
    worker = cuvis.Worker(settings)

    # Set processing context
    pc: cuvis.ProcessingContext = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.Raw
    worker.set_processing_context(pc)

    # Set exporter
    save_args = cuvis.SaveArgs(export_dir=str(temp_output_dir))
    exporter = cuvis.CubeExporter(save_args)
    worker.set_exporter(exporter)

    # Start processing
    worker.start_processing()

    try:
        # Ingest session file (only first measurement)
        worker.ingest_session_file(test_session_file, frame_selection="0")

        # Check for results
        result = worker.get_next_result(timeout=5000)
        assert isinstance(result, cuvis.WorkerResult)
        assert isinstance(result.mesu, cuvis.Measurement)
    finally:
        # Clean up
        worker.stop_processing()
        worker.drop_all_queued()


def test_worker_state_queries():
    """Test Worker state query methods."""
    settings = cuvis.WorkerSettings()
    worker = cuvis.Worker(settings)

    # Query various states
    assert isinstance(worker.is_processing, bool)
    assert isinstance(worker.queue_used, int)
    assert isinstance(worker.input_queue_limit, int)


def test_worker_has_next_result():
    """Test Worker has_next_result method."""
    settings = cuvis.WorkerSettings()
    worker = cuvis.Worker(settings)

    # Before any processing, should return False
    assert worker.has_next_result() is False


@pytest.mark.slow
def test_worker_start_stop_processing(processing_context_from_session):
    """Test Worker start and stop processing."""
    settings = cuvis.WorkerSettings()
    worker = cuvis.Worker(settings)

    # Set processing context
    worker.set_processing_context(processing_context_from_session)

    # Start processing
    worker.start_processing()
    assert worker.is_processing is True

    # Stop processing
    worker.stop_processing()
    assert worker.is_processing is False
