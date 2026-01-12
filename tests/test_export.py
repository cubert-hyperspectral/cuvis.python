"""
Tests for cuvis.Export module.

Mirrors functionality from Example 4 notebook (Exporters) related to
exporting measurements in various formats: SessionFile, TIFF, ENVI, View.
"""

import pytest
import cuvis


def test_cube_exporter_creation(temp_output_dir):
    """Test CubeExporter can be created."""
    save_args = cuvis.SaveArgs(export_dir=str(temp_output_dir))
    exporter = cuvis.CubeExporter(save_args)
    assert exporter is not None


def test_cube_export_workflow(
    processing_context_from_session, test_measurement, temp_output_dir
):
    """Test export measurement as SessionFile (.cu3s)."""
    # Process measurement first
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.Raw
    pc.apply(test_measurement)

    # Export as SessionFile
    save_args = cuvis.SaveArgs(export_dir=str(temp_output_dir))
    exporter = cuvis.CubeExporter(save_args)
    exporter.apply(test_measurement)
    exporter.flush()

    # Verify output file was created
    output_files = list(temp_output_dir.glob("*.cu3s"))
    assert len(output_files) > 0, "No .cu3s files were created"


def test_tiff_exporter_creation(temp_output_dir):
    """Test TiffExporter can be created."""
    settings = cuvis.TiffExportSettings(export_dir=str(temp_output_dir))
    exporter = cuvis.TiffExporter(settings)
    assert exporter is not None


def test_tiff_export_workflow(
    processing_context_from_session, test_measurement, temp_output_dir
):
    """Test export measurement as TIFF."""
    # Process measurement first
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.Raw
    pc.apply(test_measurement)

    # Export as TIFF
    settings = cuvis.TiffExportSettings(
        export_dir=str(temp_output_dir), format=cuvis.TiffFormat.MultiChannel
    )
    exporter = cuvis.TiffExporter(settings)
    exporter.apply(test_measurement)
    exporter.flush()

    # Verify output file was created
    output_files = list(temp_output_dir.glob("*.tif*"))
    assert len(output_files) > 0, "No TIFF files were created"


def test_tiff_export_different_formats(
    processing_context_from_session, test_measurement, temp_output_dir
):
    """Test TIFF export with different format modes."""
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.Raw
    pc.apply(test_measurement)

    # Test MultiPage format
    multipage_dir = temp_output_dir / "multipage"
    multipage_dir.mkdir()
    settings = cuvis.TiffExportSettings(
        export_dir=str(multipage_dir), format=cuvis.TiffFormat.MultiPage
    )
    exporter = cuvis.TiffExporter(settings)
    exporter.apply(test_measurement)
    exporter.flush()
    assert len(list(multipage_dir.glob("*.tif*"))) > 0


def test_envi_exporter_creation(temp_output_dir):
    """Test EnviExporter can be created."""
    settings = cuvis.EnviExportSettings(export_dir=str(temp_output_dir))
    exporter = cuvis.EnviExporter(settings)
    assert exporter is not None


def test_envi_export_workflow(
    processing_context_from_session, test_measurement, temp_output_dir
):
    """Test export measurement as ENVI format (.hdr + .bin)."""
    # Process measurement first
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.Raw
    pc.apply(test_measurement)

    # Export as ENVI
    settings = cuvis.EnviExportSettings(export_dir=str(temp_output_dir))
    exporter = cuvis.EnviExporter(settings)
    exporter.apply(test_measurement)
    exporter.flush()

    # Verify output files were created (.hdr and/or .bin)
    hdr_files = list(temp_output_dir.glob("*.hdr"))
    bin_files = list(temp_output_dir.glob("*.bin"))
    raw_files = list(temp_output_dir.glob("*.raw"))

    # ENVI format should create at least header files
    assert len(hdr_files) > 0 or len(bin_files) > 0 or len(raw_files) > 0, (
        "No ENVI files were created"
    )


def test_view_exporter_creation(temp_output_dir, rgb_userplugin_path):
    """Test ViewExporter can be created."""
    settings = cuvis.ViewExportSettings(
        export_dir=str(temp_output_dir), userplugin=rgb_userplugin_path
    )
    exporter = cuvis.ViewExporter(settings)
    assert exporter is not None


def test_view_export_workflow(
    processing_context_from_session,
    test_measurement,
    temp_output_dir,
    rgb_userplugin_path,
):
    """Test export measurement as View (RGB visualization)."""
    # Process measurement first
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.Raw
    pc.apply(test_measurement)

    # Export as View
    settings = cuvis.ViewExportSettings(
        export_dir=str(temp_output_dir), userplugin=rgb_userplugin_path
    )
    exporter = cuvis.ViewExporter(settings)
    exporter.apply(test_measurement)
    exporter.flush()

    # Verify output was created
    output_files = list(temp_output_dir.glob("*.*"))
    assert len(output_files) > 0


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__]))
