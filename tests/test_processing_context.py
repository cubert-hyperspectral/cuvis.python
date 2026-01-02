"""
Tests for cuvis.ProcessingContext module.

Mirrors functionality from Example 3 notebook (Reprocess) related to
processing modes, reference handling, and cube generation.
"""

import pytest
import cuvis


def test_processing_context_creation_from_session(processing_context_from_session):
    """Test ProcessingContext can be created from SessionFile."""
    assert processing_context_from_session is not None
    assert isinstance(processing_context_from_session, cuvis.ProcessingContext)


def test_processing_context_creation_from_measurement(processing_context_from_measurement):
    """Test ProcessingContext can be created from Measurement."""
    assert processing_context_from_measurement is not None
    assert isinstance(processing_context_from_measurement, cuvis.ProcessingContext)


def test_processing_mode_raw(processing_context_from_session, aquarium_measurement):
    """Test Raw processing mode generates cube."""
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.Raw
    pc.apply(aquarium_measurement)
    assert 'cube' in aquarium_measurement.data
    cube = aquarium_measurement.data['cube']
    assert cube is not None


def test_processing_mode_dark_subtract(processing_context_from_session, aquarium_measurement):
    """Test DarkSubtract processing mode generates cube."""
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.DarkSubtract
    pc.apply(aquarium_measurement)
    assert 'cube' in aquarium_measurement.data
    cube = aquarium_measurement.data['cube']
    assert cube is not None


def test_processing_mode_reflectance(processing_context_from_session, aquarium_measurement):
    """Test Reflectance processing mode generates cube."""
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.Reflectance
    pc.apply(aquarium_measurement)
    assert 'cube' in aquarium_measurement.data
    cube = aquarium_measurement.data['cube']
    assert cube is not None


def test_processing_mode_spectral_radiance(processing_context_from_session, aquarium_measurement):
    """Test SpectralRadiance processing mode generates cube."""
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.SpectralRadiance
    pc.apply(aquarium_measurement)
    assert 'cube' in aquarium_measurement.data
    cube = aquarium_measurement.data['cube']
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


def test_cube_property_access(processing_context_from_session, aquarium_measurement):
    """Test cube property convenience accessor."""
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.Raw
    pc.apply(aquarium_measurement)

    # Access cube via property
    cube = aquarium_measurement.cube
    assert cube is not None
    assert hasattr(cube, 'array')


def test_cube_data_shape(processing_context_from_session, aquarium_measurement):
    """Test cube has expected 3D shape (height, width, channels)."""
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.Raw
    pc.apply(aquarium_measurement)

    cube = aquarium_measurement.cube
    assert len(cube.array.shape) == 3  # 3D array: height, width, channels
    height, width, channels = cube.array.shape
    assert height > 0
    assert width > 0
    assert channels > 0  # Should have spectral channels


def test_cube_wavelength_access(processing_context_from_session, aquarium_measurement):
    """Test cube wavelength information is accessible."""
    pc = processing_context_from_session
    pc.processing_mode = cuvis.ProcessingMode.Raw
    pc.apply(aquarium_measurement)

    cube = aquarium_measurement.cube
    # Check if wavelength information is available
    assert hasattr(cube, 'wavelength')
    wavelength = cube.wavelength
    assert wavelength is not None
