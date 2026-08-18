from typing import Optional, Sequence, Union
from ._cuvis_il import cuvis_il
import numpy as np
import operator
from .cuvis_aux import SDKException

_IMBUF_READERS = {
    1: cuvis_il.cuvis_read_imbuf_uint8,
    2: cuvis_il.cuvis_read_imbuf_uint16,
    3: cuvis_il.cuvis_read_imbuf_uint32,
    4: cuvis_il.cuvis_read_imbuf_float32,
}


def _unwrap(value):
    return value.array if isinstance(value, ImageData) else value


class ImageData(object):
    """
    An image or spectrum returned by a measurement, as a NumPy array plus its metadata.

    The array is always three dimensional, (height, width, channels), whatever the
    spatial extent is. A point spectrometer such as the QMini therefore arrives as
    (1, 1, channels); :attr:`is_spectrum` identifies that case and :attr:`spectrum`
    gives the one dimensional vector.

    Not every image carries wavelengths. Previews and info layers do not, in which
    case :attr:`wavelength` is None.
    """

    def __init__(self, img_buf=None, dformat=None):
        self._img_buf = None
        self.array = None
        self.width = None
        self.height = None
        self.channels = None
        self.wavelength = None

        if img_buf is None:
            return

        if not isinstance(img_buf, cuvis_il.cuvis_imbuffer_t):
            raise TypeError(
                "Wrong data type for image buffer: {}".format(type(img_buf)))

        if dformat is None:
            raise TypeError("Missing format for reading image buffer")

        read = _IMBUF_READERS.get(img_buf.format)
        if read is None:
            raise SDKException()

        # Keep a reference to the underlying buffer so the NumPy array
        # remains valid for the lifetime of this ImageData instance.
        self._img_buf = img_buf
        self.array = read(img_buf)
        self.width = img_buf.width
        self.height = img_buf.height
        self.channels = img_buf.channels

        if img_buf.wavelength is not None:
            self.wavelength = [
                cuvis_il.p_unsigned_int_getitem(img_buf.wavelength, z)
                for z in range(self.channels)]

    @property
    def shape(self) -> Optional[tuple]:
        return None if self.array is None else self.array.shape

    @property
    def dtype(self):
        return None if self.array is None else self.array.dtype

    @property
    def is_spectrum(self) -> bool:
        """True for a single pixel measurement, such as a point spectrometer."""
        return self.width == 1 and self.height == 1

    @property
    def spectrum(self) -> np.ndarray:
        """
        The one dimensional band vector of a single pixel measurement.

        :raises ValueError: if this image covers more than one pixel.
        """
        if self.array is None:
            raise ValueError("Image array is not initialized.")
        if not self.is_spectrum:
            raise ValueError(
                "Not a single pixel measurement ({}x{}); index a pixel first, "
                "for example image[y, x].".format(self.width, self.height))
        return self.array.reshape(-1)

    def __repr__(self) -> str:
        if self.array is None:
            return "ImageData(empty)"
        return "ImageData({}x{}x{}, {}, wavelength={})".format(
            self.width, self.height, self.channels, self.array.dtype,
            "no" if self.wavelength is None else
            "{}..{} nm".format(self.wavelength[0], self.wavelength[-1]))

    def __getitem__(self, key) -> Union[np.ndarray, tuple, "ImageData", np.generic]:
        """
        Slice or index the image data.

        The result follows the dimensionality of the slice: a three dimensional
        result stays an :class:`ImageData` carrying the matching wavelengths, a band
        vector comes back as (values, wavelengths), and anything else is returned as
        the plain NumPy result.

        Example:
            pixel, wavelengths = image_data[100, 50]  # Single pixel spectrum plus wavelengths
            values, wavelengths = point_spectrum[0, 0]  # Same for a QMini point spectrum
            band_slice = image_data[:, :, 10:20]  # Subset of Image and Bands results in a new ImageData object
            single_channel = image_data[:,:,10] # Single Channel returns a normal numpy array
        """
        if self.array is None:
            raise ValueError("Image array is not initialized.")

        sliced_array = self.array[key]
        bands = self._band_indices(key)

        if np.ndim(sliced_array) == 3:
            return ImageData.from_array(
                sliced_array, wavelength=self._wavelengths_at(bands))
        if np.ndim(sliced_array) == 1 and len(bands) == len(sliced_array):
            return sliced_array, self._wavelengths_at(bands)
        return sliced_array

    def _band_indices(self, key) -> Sequence[int]:
        """The band indices a key selects, in the order they appear in the result."""
        band_key = key[2] if isinstance(key, tuple) and len(key) == 3 else slice(None)
        if isinstance(band_key, slice):
            return range(*band_key.indices(self.channels))
        if isinstance(band_key, (int, np.integer)):
            return range(band_key % self.channels, band_key % self.channels + 1)
        return range(self.channels)

    def _wavelengths_at(self, bands: Sequence[int]) -> Optional[list]:
        if self.wavelength is None:
            return None
        return [self.wavelength[band] for band in bands]

    def _wrap(self, result):
        """Keep the metadata when an operation preserved the image geometry."""
        if isinstance(result, np.ndarray) and result.shape == self.array.shape:
            return ImageData.from_array(
                result, self.width, self.height, self.channels, self.wavelength)
        return result

    def __array__(self, dtype=None, copy=None) -> np.ndarray:
        if self.array is None:
            raise ValueError("Image array is not initialized.")
        array = np.asarray(self.array, dtype=dtype)
        return array.copy() if copy else array

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        if "out" in kwargs:
            kwargs["out"] = tuple(_unwrap(out) for out in kwargs["out"])
        return self._wrap(
            getattr(ufunc, method)(*(_unwrap(i) for i in inputs), **kwargs))

    def to_numpy(self) -> np.ndarray:
        """
        Returns the spectral data as a NumPy array.
        """
        return self.array

    @classmethod
    def from_array(cls, array: np.ndarray, width: int = None, height: int = None,
                   channels: int = None, wavelength=None):
        """
        Creates an ImageData instance from a NumPy array and metadata.

        Any dimension left out is taken from the array itself, which is assumed to
        be laid out as (height, width, channels).
        """
        array = np.asarray(array)
        shape = array.shape + (1,) * (3 - array.ndim)

        instance = cls()
        instance.array = array
        instance.height = shape[0] if height is None else height
        instance.width = shape[1] if width is None else width
        instance.channels = shape[2] if channels is None else channels
        instance.wavelength = wavelength
        instance._img_buf = None
        return instance


def _binary_op(op, reflected=False):
    def apply(self, other):
        operands = (_unwrap(other), self.array) if reflected else (self.array, _unwrap(other))
        return self._wrap(op(*operands))

    name = op.__name__.strip("_")
    apply.__name__ = "__{}{}__".format("r" if reflected else "", name)
    apply.__doc__ = "Element-wise {} on the underlying array.".format(name)
    return apply


for _op in (operator.add, operator.sub, operator.mul, operator.truediv,
            operator.floordiv, operator.mod, operator.pow):
    for _reflected in (False, True):
        _method = _binary_op(_op, _reflected)
        setattr(ImageData, _method.__name__, _method)

ImageData.__neg__ = lambda self: self._wrap(-self.array)
ImageData.__abs__ = lambda self: self._wrap(abs(self.array))

del _op, _reflected, _method
