"""
Tests for the ImageData helper.

The first half builds ImageData from plain arrays, which is what lets the point
spectrum layout (1, 1, channels) of a QMini be covered without such a measurement
at hand. The second half runs the same behaviour against the committed test
measurement, so the contract is checked against data the SDK really produces.
"""

import numpy as np
import pytest

import cuvis
from cuvis import ImageData


@pytest.fixture
def spectrum():
    """A single pixel measurement, as a point spectrometer delivers it."""
    return ImageData.from_array(
        np.arange(2500, dtype=np.float32).reshape(1, 1, 2500),
        wavelength=list(range(200, 2700)))


@pytest.fixture
def cube():
    return ImageData.from_array(
        np.arange(4 * 3 * 5, dtype=np.uint16).reshape(4, 3, 5),
        wavelength=[100, 200, 300, 400, 500])


@pytest.fixture
def preview():
    """A single band image, which the SDK delivers without wavelengths."""
    return ImageData.from_array(np.zeros((4, 3, 1), dtype=np.uint8))


def test_from_array_derives_geometry(spectrum, cube):
    assert (spectrum.height, spectrum.width, spectrum.channels) == (1, 1, 2500)
    assert (cube.height, cube.width, cube.channels) == (4, 3, 5)


def test_from_array_reshapes_to_the_documented_layout():
    """array is always (height, width, channels), whatever came in."""
    from_vector = ImageData.from_array(np.arange(7))
    assert from_vector.array.shape == (1, 1, 7)
    assert from_vector.is_spectrum

    from_image = ImageData.from_array(np.zeros((4, 3)))
    assert from_image.array.shape == (4, 3, 1)
    assert (from_image.height, from_image.width, from_image.channels) == (4, 3, 1)


def test_spectrum_is_one_dimensional(spectrum):
    assert spectrum.is_spectrum
    assert spectrum.spectrum.shape == (2500,)
    np.testing.assert_array_equal(spectrum.spectrum, spectrum.array.ravel())


def test_spectrum_rejected_for_an_image(cube):
    assert not cube.is_spectrum
    with pytest.raises(ValueError):
        cube.spectrum


def test_pixel_access_returns_values_and_wavelengths(spectrum, cube):
    values, wavelength = spectrum[0, 0]
    assert values.shape == (2500,)
    assert len(wavelength) == 2500

    values, wavelength = cube[2, 1]
    assert values.shape == (5,)
    assert wavelength == [100, 200, 300, 400, 500]


def test_band_slice_stays_image_data(spectrum):
    sliced = spectrum[:, :, 10:20]
    assert isinstance(sliced, ImageData)
    assert sliced.channels == 10
    assert sliced.wavelength == list(range(210, 220))


def test_single_band_slice_stays_image_data(spectrum):
    """A width one band slice used to fall through every branch and return None."""
    sliced = spectrum[:, :, 10:11]
    assert isinstance(sliced, ImageData)
    assert sliced.array.shape == (1, 1, 1)
    assert sliced.wavelength == [210]


def test_scalar_index_returns_the_value(spectrum):
    """Indexing down to a scalar used to return None."""
    assert spectrum[0, 0, 5] == spectrum.array[0, 0, 5]


def test_strided_and_negative_band_slices(cube):
    sliced = cube[:, :, ::2]
    assert sliced.wavelength == [100, 300, 500]
    assert cube[:, :, -2:].wavelength == [400, 500]


def test_band_index_lists_and_masks(cube):
    assert cube[:, :, [0, 2]].wavelength == [100, 300]
    mask = np.array([True, False, True, False, False])
    assert cube[:, :, mask].wavelength == [100, 300]


def test_ellipsis_is_expanded_before_reading_the_band_axis(cube):
    assert cube[..., 1:3].wavelength == [200, 300]
    assert cube[1, 2, ...][1] == [100, 200, 300, 400, 500]


def test_wavelengths_are_dropped_rather_than_guessed(cube):
    """A slice down the spatial axis selects one band, not len(result) of them."""
    values, wavelength = cube[0, :, 2]
    assert values.shape == (3,)
    assert wavelength is None


def test_wavelength_is_none_without_band_information(preview):
    """Accessing wavelength used to raise AttributeError for such images."""
    assert preview.wavelength is None
    values, wavelength = preview[0, 0]
    assert wavelength is None
    assert isinstance(preview[:, :, 0:1], ImageData)


def test_numpy_conversion(spectrum):
    np.testing.assert_array_equal(np.asarray(spectrum), spectrum.array)
    assert np.mean(spectrum) == pytest.approx(spectrum.array.mean())


def test_arithmetic_preserves_metadata(spectrum):
    doubled = spectrum * 2
    assert isinstance(doubled, ImageData)
    assert doubled.channels == 2500
    assert doubled.wavelength == spectrum.wavelength
    np.testing.assert_array_equal(doubled.array, spectrum.array * 2)

    np.testing.assert_array_equal((spectrum - spectrum).array,
                                  np.zeros_like(spectrum.array))
    np.testing.assert_array_equal((2 * spectrum).array, spectrum.array * 2)
    np.testing.assert_array_equal((-spectrum).array, -spectrum.array)


def test_reduction_drops_the_wrapper(spectrum):
    assert not isinstance(np.sum(spectrum), ImageData)


def test_empty_image_data():
    empty = ImageData()
    assert empty.array is None
    assert empty.wavelength is None
    assert empty.shape is None
    with pytest.raises(ValueError):
        empty[0, 0]
    with pytest.raises(ValueError):
        np.asarray(empty)
    with pytest.raises(ValueError):
        empty.spectrum


# The same contract, against the measurement committed to the repository.


@pytest.fixture
def real_cube(processing_context_from_session, test_measurement):
    """The processed cube of the test measurement, with wavelengths."""
    processing_context_from_session.processing_mode = cuvis.ProcessingMode.Raw
    processing_context_from_session.apply(test_measurement)
    return test_measurement.cube


@pytest.fixture
def real_view(test_measurement):
    """The view image, which the SDK delivers without any band information."""
    return test_measurement.data["view"]


def test_real_cube_geometry_matches_its_metadata(real_cube):
    assert real_cube.array.ndim == 3
    assert real_cube.array.shape == (real_cube.height, real_cube.width, real_cube.channels)
    assert not real_cube.is_spectrum


def test_real_cube_wavelengths_line_up_with_the_bands(real_cube):
    assert len(real_cube.wavelength) == real_cube.channels
    assert real_cube.wavelength == sorted(real_cube.wavelength)


def test_real_cube_pixel_access(real_cube):
    values, wavelength = real_cube[real_cube.height // 2, real_cube.width // 2]
    assert values.shape == (real_cube.channels,)
    assert wavelength == real_cube.wavelength


def test_real_cube_band_slice_keeps_wavelengths_in_step(real_cube):
    sliced = real_cube[:, :, 2:5]
    assert isinstance(sliced, ImageData)
    assert sliced.channels == 3
    assert sliced.wavelength == real_cube.wavelength[2:5]
    np.testing.assert_array_equal(sliced.array, real_cube.array[:, :, 2:5])


def test_real_cube_single_band_slice_stays_image_data(real_cube):
    """This slice used to fall through every branch and return None."""
    sliced = real_cube[:, :, 0:1]
    assert isinstance(sliced, ImageData)
    assert sliced.wavelength == real_cube.wavelength[:1]


def test_real_cube_index_forms(real_cube):
    assert real_cube[:, :, 0].shape == (real_cube.height, real_cube.width)
    assert np.ndim(real_cube[0, 0, 0]) == 0
    assert real_cube[..., 1:3].wavelength == real_cube.wavelength[1:3]
    assert real_cube[:, :, [0, 2]].wavelength == [real_cube.wavelength[0],
                                                  real_cube.wavelength[2]]


def test_real_view_has_no_wavelengths(real_view):
    """Reading wavelength on such an image used to raise AttributeError."""
    assert real_view.wavelength is None
    assert real_view.channels == real_view.array.shape[2]

    values, wavelength = real_view[0, 0]
    assert values.shape == (real_view.channels,)
    assert wavelength is None
    assert real_view[:, :, 0:1].wavelength is None


def test_real_cube_arithmetic_preserves_metadata(real_cube):
    doubled = real_cube * 2
    assert isinstance(doubled, ImageData)
    assert doubled.wavelength == real_cube.wavelength
    assert doubled.shape == real_cube.shape
    np.testing.assert_array_equal(doubled.array, real_cube.array * 2)
    np.testing.assert_array_equal((real_cube - real_cube).array,
                                  np.zeros_like(real_cube.array))


def test_real_cube_numpy_interop(real_cube):
    assert np.asarray(real_cube) is real_cube.array
    assert np.asarray(real_cube, dtype=np.float32).dtype == np.float32
    assert np.mean(real_cube) == pytest.approx(real_cube.array.mean())


def test_real_pixel_spectrum_behaves_like_a_point_measurement(real_cube):
    """
    The committed measurement has no point spectrometer, so take a real pixel and
    check it works in the (1, 1, channels) layout a QMini arrives in.
    """
    values, wavelength = real_cube[10, 10]
    point = ImageData.from_array(values, wavelength=wavelength)

    assert point.is_spectrum
    assert point.array.shape == (1, 1, real_cube.channels)
    np.testing.assert_array_equal(point.spectrum, values)
    assert (point / 2)[0, 0][1] == wavelength
