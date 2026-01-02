# CUVIS Python SDK Tests

This directory contains integration tests for the cuvis.python wrapper, mirroring the functionality demonstrated in the 5 Jupyter notebook examples.

## Test Structure

- **conftest.py** - Pytest fixtures and configuration
- **test_general.py** - SDK initialization, version info
- **test_session_file.py** - SessionFile loading and iteration
- **test_measurement.py** - Measurement data access and properties
- **test_processing_context.py** - Processing modes and cube generation
- **test_export.py** - Export formats (SessionFile, TIFF, ENVI, View)
- **test_acquisition.py** - Simulated camera acquisition
- **test_worker.py** - Worker pipeline management
- **test_integration_workflows.py** - End-to-end workflows mirroring notebooks

## Prerequisites

1. **Install test dependencies:**
   ```bash
   pip install -e ".[test]"
   ```

2. **Set up test data:**
   - Place `Aquarium.cu3s` (with 1 measurement) in `tests/test_data/`
   - Ensure CUVIS SDK is installed and `CUVIS` environment variable is set

3. **Optional: Set CUVIS_SETTINGS environment variable:**
   ```bash
   export CUVIS_SETTINGS=/path/to/settings  # Linux/Mac
   set CUVIS_SETTINGS=C:\path\to\settings   # Windows
   ```

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run specific test file
```bash
pytest tests/test_session_file.py
pytest tests/test_processing_context.py
```

### Run with verbose output
```bash
pytest -v tests/
```

### Run in parallel (faster)
```bash
pytest -n auto tests/
```

### Run only fast tests (skip slow ones)
```bash
pytest -m "not slow" tests/
```

### Run only integration tests
```bash
pytest -m integration tests/
```

### Run with timeout (60s per test)
```bash
pytest --timeout=60 tests/
```

### Run specific test function
```bash
pytest tests/test_general.py::test_sdk_version
```

## Test Coverage

The tests mirror the 5 Jupyter notebook examples:

### Example 1: Take Snapshot
- **Files:** `test_acquisition.py`, `test_integration_workflows.py`
- Simulated camera initialization, software trigger, snapshot capture

### Example 2: Load Measurement
- **Files:** `test_session_file.py`, `test_measurement.py`, `test_integration_workflows.py`
- SessionFile loading, measurement metadata, cube data access

### Example 3: Reprocess
- **Files:** `test_processing_context.py`, `test_integration_workflows.py`
- Processing modes: Raw, DarkSubtract, Reflectance, SpectralRadiance
- Reference handling: Dark, White, Distance

### Example 4: Exporters
- **Files:** `test_export.py`, `test_integration_workflows.py`
- Export formats: SessionFile (.cu3s), TIFF, ENVI

### Example 5: Record Video
- **Files:** `test_worker.py`, `test_integration_workflows.py`
- Worker pipeline, SessionFile ingestion, result retrieval

## Test Markers

- `@pytest.mark.slow` - Tests that take longer (acquisition, worker)
- `@pytest.mark.integration` - End-to-end integration tests
- `@pytest.mark.skip` - Skipped tests (e.g., ViewExporter requires userplugin)

## Expected Runtime

- **Sequential:** 5-8 minutes
- **Parallel (`-n auto`):** 2-3 minutes

## Troubleshooting

### Test data not found
```
Error: Test data not found: tests/test_data/Aquarium.cu3s
```
**Solution:** Place the Aquarium.cu3s file in `tests/test_data/`

### CUVIS environment variable not set
```
Error: CUVIS environmental variable is not set!
```
**Solution:** Set the CUVIS environment variable to point to the SDK installation

### Acquisition context not ready
```
Skipped: Acquisition context not ready within timeout
```
**Solution:** This is expected in some environments. The test skips gracefully.

## CI/CD Integration

For CI/CD pipelines, use:
```bash
pytest -n auto --timeout=60 -m "not slow" tests/
```

This runs tests in parallel, with timeouts, and skips slow tests for faster feedback.

## Contributing

When adding new tests:
1. Follow the existing naming convention: `test_<module>_<functionality>.py`
2. Add docstrings explaining what notebook functionality is mirrored
3. Use appropriate markers (`@pytest.mark.slow`, `@pytest.mark.integration`)
4. Update this README if adding new test files
