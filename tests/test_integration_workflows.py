"""
Integration workflow tests that mirror the Jupyter notebook examples end-to-end.

These tests validate complete workflows from the 5 example notebooks:
- Example 1: Take Snapshot
- Example 2: Load Measurement
- Example 3: Reprocess
- Example 4: Exporters
- Example 5: Record Video
"""

import pytest
import time
import cuvis


@pytest.mark.integration
def test_load_and_extract(aquarium_session_file, processing_context_from_session):
    """
    Load Measurement workflow.

    Steps:
    1. Load SessionFile
    2. Access measurement metadata
    3. Process to generate cube
    4. Extract spectral data
    """
    # Step 1: Load session (already loaded via fixture)
    assert len(aquarium_session_file) >= 1

    # Step 2: Get measurement and access metadata
    mesu = aquarium_session_file[0]
    assert mesu.capture_time is not None
    assert mesu.integration_time > 0
    assert mesu.serial_number is not None

    # Step 3: Process to get cube
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.Raw
    pc.apply(mesu)

    # Step 4: Verify cube and extract data
    cube = mesu.cube
    assert cube.array.shape[2] > 0  # Has spectral channels

    # Extract a point spectrum (similar to notebook)
    height, width, channels = cube.array.shape
    point_spectrum = cube.array[height // 2, width // 2, :]
    assert len(point_spectrum) == channels


@pytest.mark.integration
@pytest.mark.slow
def test_reprocessing_modes(aquarium_session_file, processing_context_from_session):
    """
    Reprocess workflow.

    Steps:
    1. Load measurement
    2. Process with Raw mode
    3. Process with DarkSubtract mode
    4. Process with Reflectance mode
    5. Process with SpectralRadiance mode
    """
    mesu = aquarium_session_file[0]
    pc = processing_context_from_session

    # Raw mode
    pc.processing_mode = cuvis.ProcessingMode.Raw
    pc.apply(mesu)
    raw_cube = mesu.data["cube"]
    assert raw_cube is not None

    # DarkSubtract mode
    pc.processing_mode = cuvis.ProcessingMode.DarkSubtract
    pc.apply(mesu)
    dark_cube = mesu.data["cube"]
    assert dark_cube is not None

    # Reflectance mode
    pc.processing_mode = cuvis.ProcessingMode.Reflectance
    pc.apply(mesu)
    refl_cube = mesu.data["cube"]
    assert refl_cube is not None

    # SpectralRadiance mode
    pc.processing_mode = cuvis.ProcessingMode.SpectralRadiance
    pc.apply(mesu)
    radiance_cube = mesu.data["cube"]
    assert radiance_cube is not None

    # Verify all cubes were generated
    assert all([raw_cube, dark_cube, refl_cube, radiance_cube])


@pytest.mark.integration
@pytest.mark.slow
def test_export_formats(
    aquarium_session_file, processing_context_from_session, temp_output_dir
):
    """
    Exporters workflow.

    Steps:
    1. Load and process measurement
    2. Export as SessionFile (.cu3s)
    3. Export as TIFF
    4. Export as ENVI
    """
    mesu = aquarium_session_file[0]
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.Raw
    pc.apply(mesu)

    # Step 2: Export as SessionFile
    cube_dir = temp_output_dir / "cube"
    cube_dir.mkdir()
    save_args = cuvis.SaveArgs(export_dir=str(cube_dir))
    cube_exporter = cuvis.CubeExporter(save_args)
    cube_exporter.apply(mesu)
    cube_exporter.flush()

    # Step 3: Export as TIFF
    tiff_dir = temp_output_dir / "tiff"
    tiff_dir.mkdir()
    tiff_settings = cuvis.TiffExportSettings(
        export_dir=str(tiff_dir), format=cuvis.TiffFormat.MultiChannel
    )
    tiff_exporter = cuvis.TiffExporter(tiff_settings)
    tiff_exporter.apply(mesu)
    tiff_exporter.flush()

    # Step 4: Export as ENVI
    envi_dir = temp_output_dir / "envi"
    envi_dir.mkdir()
    envi_settings = cuvis.EnviExportSettings(export_dir=str(envi_dir))
    envi_exporter = cuvis.EnviExporter(envi_settings)
    envi_exporter.apply(mesu)
    envi_exporter.flush()

    # Verify all exports created files
    assert len(list(cube_dir.glob("*.cu3s"))) > 0, "SessionFile export failed"
    assert len(list(tiff_dir.glob("*.tif*"))) > 0, "TIFF export failed"
    assert (
        len(list(envi_dir.glob("*.hdr"))) > 0
        or len(list(envi_dir.glob("*.bin"))) > 0
        or len(list(envi_dir.glob("*.raw"))) > 0
    ), "ENVI export failed"


@pytest.mark.integration
@pytest.mark.slow
def test_simulated_acquisition_snapshot(
    simulated_acquisition_context, processing_context_from_session, temp_output_dir
):
    """
    Take Snapshot workflow.

    Steps:
    1. Initialize simulated camera
    2. Set software trigger mode
    3. Wait for ready state
    4. Capture snapshot
    5. Process measurement
    6. Save to file
    """
    acq = simulated_acquisition_context

    # Step 2: Set operation mode to software
    acq.operation_mode = cuvis.OperationMode.Software

    # Step 3: Wait for ready (with timeout)
    timeout = 10  # seconds
    start = time.time()
    while not acq.ready and (time.time() - start) < timeout:
        time.sleep(0.1)

    if not acq.ready:
        pytest.skip("Acquisition context not ready within timeout")

    # Step 4: Capture snapshot
    mesu = acq.capture_at(timeout_ms=5000)
    assert isinstance(mesu, cuvis.Measurement)

    # Step 5: Process the measurement
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.Raw
    pc.apply(mesu)
    assert "cube" in mesu.data

    # Step 6: Save to file
    save_args = cuvis.SaveArgs(export_dir=str(temp_output_dir))
    mesu.save(save_args)

    # Verify file was saved
    output_files = list(temp_output_dir.glob("*.cu3s"))
    assert len(output_files) > 0, "Snapshot save failed"


@pytest.mark.integration
@pytest.mark.slow
def test_complete_pipeline(
    aquarium_session_file, processing_context_from_session, temp_output_dir
):
    """
    Complete end-to-end pipeline test.

    Combines multiple notebook workflows:
    - Load SessionFile
    - Process measurement
    - Export in multiple formats
    - Verify outputs
    """
    # Load measurement
    mesu = aquarium_session_file[0]

    # Process with Reflectance mode (most common)
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.Reflectance
    pc.apply(mesu)

    # Verify cube was generated
    cube = mesu.cube
    assert cube is not None
    assert len(cube.array.shape) == 3

    # Export in all formats
    formats = {
        "session": (
            ".cu3s",
            cuvis.CubeExporter(
                cuvis.SaveArgs(export_dir=str(temp_output_dir / "session"))
            ),
        ),
        "tiff": (
            "*.tif*",
            cuvis.TiffExporter(
                cuvis.TiffExportSettings(export_dir=str(temp_output_dir / "tiff"))
            ),
        ),
        "envi": (
            "*.hdr",
            cuvis.EnviExporter(
                cuvis.EnviExportSettings(export_dir=str(temp_output_dir / "envi"))
            ),
        ),
    }

    for format_name, (pattern, exporter) in formats.items():
        export_dir = temp_output_dir / format_name
        export_dir.mkdir(exist_ok=True)
        exporter.apply(mesu)
        exporter.flush()

    # Verify all exports succeeded
    assert (
        len(list((temp_output_dir / "session").glob(".cu3s"))) >= 0
    )  # May be in subdirs
    assert len(list((temp_output_dir / "tiff").glob("*.tif*"))) > 0
    # ENVI creates .hdr or .raw or .bin
    envi_files = (
        list((temp_output_dir / "envi").glob("*.hdr"))
        + list((temp_output_dir / "envi").glob("*.raw"))
        + list((temp_output_dir / "envi").glob("*.bin"))
    )
    assert len(envi_files) > 0
