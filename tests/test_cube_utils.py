"""
Unit tests for the ImageData helper.

These build ImageData from plain arrays, so they cover the point spectrum layout
(1, 1, channels) produced by a QMini without needing such a measurement at hand.
"""

import numpy as np
import pytest

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
