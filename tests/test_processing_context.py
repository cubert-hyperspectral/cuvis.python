"""
Tests for cuvis.ProcessingContext module.

Mirrors functionality from Example 3 notebook (Reprocess) related to
processing modes, reference handling, and cube generation.
"""

import numpy as np
import pytest

import cuvis
from cuvis.cuvis_aux import SDKException


def test_processing_context_creation_from_session(processing_context_from_session):
    """Test ProcessingContext can be created from SessionFile."""
    assert processing_context_from_session is not None
    assert isinstance(processing_context_from_session, cuvis.ProcessingContext)


def test_processing_mode_raw(processing_context_from_session, test_measurement):
    """Test Raw processing mode generates cube."""
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.Raw
    pc.apply(test_measurement)
    assert "cube" in test_measurement.data
    cube = test_measurement.data["cube"]
    assert cube is not None


def test_processing_mode_dark_subtract(
    processing_context_from_session, test_measurement
):
    """Test DarkSubtract processing mode generates cube."""
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.DarkSubtract
    pc.apply(test_measurement)
    assert "cube" in test_measurement.data
    cube = test_measurement.data["cube"]
    assert cube is not None


def test_processing_mode_reflectance(processing_context_from_session, test_measurement):
    """Test Reflectance processing mode generates cube."""
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.Reflectance
    pc.apply(test_measurement)
    assert "cube" in test_measurement.data
    cube = test_measurement.data["cube"]
    assert cube is not None


def test_processing_mode_spectral_radiance(
    processing_context_from_session, test_measurement
):
    """Test SpectralRadiance processing mode generates cube."""
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.SpectralRadiance
    pc.apply(test_measurement)
    assert "cube" in test_measurement.data
    cube = test_measurement.data["cube"]
    assert cube is not None


def test_processing_context_has_reference(processing_context_from_session):
    """Test checking for references."""
    pc = processing_context_from_session
    # Check for Dark reference
    has_dark = pc.has_reference(cuvis.ReferenceType.Dark)
    assert isinstance(has_dark, bool)

    # Check for White reference
    has_white = pc.has_reference(cuvis.ReferenceType.White)
    assert isinstance(has_white, bool)


def test_processing_context_get_reference(processing_context_from_session):
    """Test getting reference measurements if available."""
    pc = processing_context_from_session

    # Try to get Dark reference if available
    if pc.has_reference(cuvis.ReferenceType.Dark):
        dark_ref = pc.get_reference(cuvis.ReferenceType.Dark)
        assert isinstance(dark_ref, cuvis.Measurement)

    # Try to get White reference if available
    if pc.has_reference(cuvis.ReferenceType.White):
        white_ref = pc.get_reference(cuvis.ReferenceType.White)
        assert isinstance(white_ref, cuvis.Measurement)


def test_cube_property_access(processing_context_from_session, test_measurement):
    """Test cube property convenience accessor."""
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.Raw
    pc.apply(test_measurement)

    # Access cube via property
    cube = test_measurement.cube
    assert cube is not None
    assert hasattr(cube, "array")


def test_cube_data_shape(processing_context_from_session, test_measurement):
    """Test cube has expected 3D shape (height, width, channels)."""
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.Raw
    pc.apply(test_measurement)

    cube = test_measurement.cube
    assert len(cube.array.shape) == 3  # 3D array: height, width, channels
    height, width, channels = cube.array.shape
    assert height > 0
    assert width > 0
    assert channels > 0  # Should have spectral channels


def test_cube_wavelength_access(processing_context_from_session, test_measurement):
    """Test cube wavelength information is accessible."""
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.Raw
    pc.apply(test_measurement)

    cube = test_measurement.cube
    # Check if wavelength information is available
    assert hasattr(cube, "wavelength")
    wavelength = cube.wavelength
    assert wavelength is not None


# --- reference spectra -----------------------------------------------------------------
# The counts metadata (effective_bit_depth, integration_time) cannot be asserted after a
# round trip: the C API stores it but exposes no getter for it.


def _flat_target(n=10):
    wavelengths = np.linspace(450.0, 900.0, n, dtype=np.float32)
    values = np.full(n, 100.0, dtype=np.float32)
    return wavelengths, values


def test_target_spectrum_round_trip(processing_context_from_session):
    """A target spectrum set from numpy arrays reads back through get_reference_spectrum."""
    pc = processing_context_from_session
    wavelengths, values = _flat_target()

    pc.set_reference((wavelengths, values), cuvis.ReferenceType.TargetSpectrum)
    assert pc.has_reference(cuvis.ReferenceType.TargetSpectrum)

    spectrum = pc.get_reference_spectrum(cuvis.ReferenceType.TargetSpectrum)
    assert isinstance(spectrum, cuvis.ImageData)
    np.testing.assert_allclose(
        np.asarray(spectrum.array).reshape(-1), values, rtol=1e-6
    )
    np.testing.assert_allclose(spectrum.wavelength, wavelengths, rtol=1e-6)

    pc.clear_reference(cuvis.ReferenceType.TargetSpectrum)
    assert not pc.has_reference(cuvis.ReferenceType.TargetSpectrum)
    assert pc.get_reference_spectrum(cuvis.ReferenceType.TargetSpectrum) is None


def test_white_counts_spectrum_round_trip(processing_context_from_session):
    """A white counts spectrum with its bit depth reads back; values stay uint16."""
    pc = processing_context_from_session
    wavelengths = np.linspace(450.0, 900.0, 8, dtype=np.float32)
    counts = np.linspace(100, 4000, 8).astype(np.uint16)

    pc.set_reference(
        (wavelengths, counts),
        cuvis.ReferenceType.WhiteSpectrum,
        effective_bit_depth=12,
        integration_time=10.0,
    )
    assert pc.has_reference(cuvis.ReferenceType.WhiteSpectrum)

    spectrum = pc.get_reference_spectrum(cuvis.ReferenceType.WhiteSpectrum)
    assert np.asarray(spectrum.array).reshape(-1).tolist() == counts.tolist()
    np.testing.assert_allclose(spectrum.wavelength, wavelengths, rtol=1e-6)

    pc.clear_reference(cuvis.ReferenceType.WhiteSpectrum)
    assert not pc.has_reference(cuvis.ReferenceType.WhiteSpectrum)


def test_target_spectrum_from_image_data(processing_context_from_session):
    """An ImageData built with from_array sets a target spectrum like the numpy pair."""
    pc = processing_context_from_session
    wavelengths, values = _flat_target()
    spectrum_in = cuvis.ImageData.from_array(values, wavelength=list(wavelengths))

    pc.set_reference(spectrum_in, cuvis.ReferenceType.TargetSpectrum)

    spectrum_out = pc.get_reference_spectrum(cuvis.ReferenceType.TargetSpectrum)
    np.testing.assert_allclose(
        np.asarray(spectrum_out.array).reshape(-1), values, rtol=1e-6
    )
    pc.clear_reference(cuvis.ReferenceType.TargetSpectrum)


def test_white_counts_spectrum_requires_bit_depth(processing_context_from_session):
    pc = processing_context_from_session
    wavelengths, values = _flat_target()
    with pytest.raises(ValueError, match="effective_bit_depth"):
        pc.set_reference(
            (wavelengths, values.astype(np.uint16)), cuvis.ReferenceType.WhiteSpectrum
        )


def test_spectrum_length_mismatch_rejected(processing_context_from_session):
    pc = processing_context_from_session
    with pytest.raises(ValueError, match="equally many"):
        pc.set_reference(
            (np.array([450.0, 500.0]), np.array([1.0])),
            cuvis.ReferenceType.TargetSpectrum,
        )


def test_spectrum_and_measurement_slots_do_not_mix(
    processing_context_from_session, test_measurement
):
    """A Measurement cannot land in a spectrum slot and vice versa, and get_reference
    does not serve spectrum slots."""
    pc = processing_context_from_session
    wavelengths, values = _flat_target()

    with pytest.raises(TypeError):
        pc.set_reference(test_measurement, cuvis.ReferenceType.TargetSpectrum)
    with pytest.raises(TypeError):
        pc.set_reference((wavelengths, values), cuvis.ReferenceType.Dark)
    with pytest.raises(TypeError):
        pc.set_reference(
            test_measurement, cuvis.ReferenceType.Dark, effective_bit_depth=12
        )
    with pytest.raises(ValueError):
        pc.get_reference_spectrum(cuvis.ReferenceType.Dark)

    pc.set_reference((wavelengths, values), cuvis.ReferenceType.TargetSpectrum)
    with pytest.raises(SDKException):
        pc.get_reference(cuvis.ReferenceType.TargetSpectrum)
    pc.clear_reference(cuvis.ReferenceType.TargetSpectrum)


@pytest.mark.slow
def test_flat_target_spectrum_keeps_reflectance_identical(
    processing_context_from_session, test_measurement
):
    """A flat 100 percent target spectrum must not change the reflectance cube."""
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.Reflectance

    pc.apply(test_measurement)
    plain = np.array(test_measurement.data["cube"].array, copy=True)

    wavelengths, values = _flat_target(64)
    pc.set_reference((wavelengths, values), cuvis.ReferenceType.TargetSpectrum)
    pc.apply(test_measurement)
    with_target = np.array(test_measurement.data["cube"].array, copy=True)
    pc.clear_reference(cuvis.ReferenceType.TargetSpectrum)

    # one count of tolerance: the reflectance kernel is parallel and not
    # bit-deterministic between runs, and a flat 100 percent target must only be
    # a no-op within uint16 rounding
    assert np.abs(plain.astype(np.int32) - with_target.astype(np.int32)).max() <= 1


def test_target_spectrum_scales_reflectance(
    processing_context_from_session, test_measurement
):
    """A flat 50 percent target spectrum halves every reflectance value."""
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.Reflectance
    pc.apply(test_measurement)
    base = np.array(test_measurement.data["cube"].array, copy=True)
    grid = np.asarray(test_measurement.data["cube"].wavelength, dtype=np.float32)

    pc.set_reference(
        (grid, np.full(grid.size, 50.0, dtype=np.float32)),
        cuvis.ReferenceType.TargetSpectrum,
    )
    pc.apply(test_measurement)
    halved = np.array(test_measurement.data["cube"].array, copy=True)
    pc.clear_reference(cuvis.ReferenceType.TargetSpectrum)

    mask = base > 200  # above the noise floor, so uint16 rounding stays below 1 percent
    ratio = halved[mask].astype(np.float64) / base[mask]
    assert abs(ratio.mean() - 0.5) < 0.005
    assert ratio.min() > 0.49 and ratio.max() < 0.51


def _padded_white(test_measurement, level):
    """A flat counts spectrum spanning past the cube grid, whose rounded ends may sit
    inside the calibration's float grid."""
    grid = np.asarray(test_measurement.data["cube"].wavelength, dtype=np.float32)
    wls = np.concatenate(([grid[0] - 10.0], grid, [grid[-1] + 10.0])).astype(np.float32)
    return wls, np.full(wls.size, level, dtype=np.uint16)


def test_white_spectrum_replaces_white_reference(
    processing_context_from_session, test_measurement
):
    """The two white sources are mutually exclusive: setting one clears the other, and
    reflectance uses whichever is set; four times the counts quarter the cube."""
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.Reflectance
    pc.apply(test_measurement)
    assert pc.has_reference(cuvis.ReferenceType.White)
    white_mesu = pc.get_reference(cuvis.ReferenceType.White)

    wls, counts = _padded_white(test_measurement, 1000)
    pc.set_reference(
        (wls, counts), cuvis.ReferenceType.WhiteSpectrum, effective_bit_depth=12
    )
    assert not pc.has_reference(cuvis.ReferenceType.White)
    assert pc.has_reference(cuvis.ReferenceType.WhiteSpectrum)

    pc.apply(test_measurement)
    from_1000 = np.array(test_measurement.data["cube"].array, copy=True)

    wls, counts = _padded_white(test_measurement, 4000)
    pc.set_reference(
        (wls, counts), cuvis.ReferenceType.WhiteSpectrum, effective_bit_depth=12
    )
    pc.apply(test_measurement)
    from_4000 = np.array(test_measurement.data["cube"].array, copy=True)

    mask = from_1000 > 200
    ratio = from_4000[mask].astype(np.float64) / from_1000[mask]
    assert abs(ratio.mean() - 0.25) < 0.005

    # and the other direction: restoring the white measurement clears the spectrum
    pc.set_reference(white_mesu, cuvis.ReferenceType.White)
    assert pc.has_reference(cuvis.ReferenceType.White)
    assert not pc.has_reference(cuvis.ReferenceType.WhiteSpectrum)


def test_spectra_survive_legacy_cu3_round_trip(
    processing_context_from_session, test_measurement, temp_output_dir
):
    """A measurement processed with both spectra keeps them through a legacy .cu3 save
    behind the SpectrumFileRefData indirection: one .cu3sp sidecar per slot beside the
    .cu3, never embedded, and the stored cube is bit-identical after reload."""
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.Reflectance
    pc.apply(test_measurement)
    grid = np.asarray(test_measurement.data["cube"].wavelength, dtype=np.float32)
    target = np.full(grid.size, 50.0, dtype=np.float32)
    pc.set_reference((grid, target), cuvis.ReferenceType.TargetSpectrum)
    wls, counts = _padded_white(test_measurement, 1000)
    pc.set_reference(
        (wls, counts), cuvis.ReferenceType.WhiteSpectrum, effective_bit_depth=12
    )
    pc.apply(test_measurement)
    expected = np.array(test_measurement.data["cube"].array, copy=True)

    # the CubeExporter is the one component that writes references in their link
    # forms; allow_session_file=False makes it produce a loose legacy .cu3
    exporter = cuvis.CubeExporter(
        cuvis.SaveArgs(
            export_dir=str(temp_output_dir),
            allow_overwrite=True,
            allow_session_file=False,
            allow_info_file=False,
            full_export=True,
        )
    )
    exporter.apply(test_measurement)
    exporter.flush()
    del exporter
    cu3 = list(temp_output_dir.glob("*.cu3"))
    assert len(cu3) == 1

    # the spectra land as sidecar files beside the other reference files, shared by
    # every measurement saved into the directory, never embedded into the measurement
    assert (temp_output_dir / "Calibration" / "target_spectrum_ref.cu3sp").is_file()
    assert (temp_output_dir / "Calibration" / "white_spectrum_ref.cu3sp").is_file()

    reloaded = cuvis.Measurement(str(cu3[0]))
    assert np.array_equal(np.asarray(reloaded.data["cube"].array), expected)
