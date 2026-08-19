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
    Image data of a measurement: a NumPy array together with the metadata that
    gives its axes meaning.

    Instances come from :attr:`cuvis.Measurement.data`, keyed by what the SDK calls
    the data frame. There is no need to construct one directly; :meth:`from_array`
    exists for the cases where a plain array has to be dressed back up.

    .. code-block:: python3

        mesu = cuvis.SessionFile(path)[0]
        cube = mesu.data["cube"]                    # a hyperspectral cube
        point = mesu.data["PointSpectrumQMini"]     # a point spectrometer reading

    :attr:`array` is always three dimensional, laid out as
    ``(height, width, channels)``, whatever the spatial extent is. A point
    spectrometer such as the QMini covers a single pixel and therefore arrives as
    ``(1, 1, channels)`` rather than as a bare vector. :attr:`is_spectrum`
    recognises that case and :attr:`spectrum` hands out the one dimensional band
    vector:

    .. code-block:: python3

        point.is_spectrum        # True
        point.spectrum           # ndarray, shape (2500,)
        cube.is_spectrum         # False

    :attr:`wavelength` is the centre wavelength in nm of every band, as a list with
    one entry per channel. Not every image has them: previews, info layers and other
    single band images carry none, and then :attr:`wavelength` is ``None``. Code that
    reads it must handle that, which is also why :meth:`__getitem__` may hand back
    ``None`` in place of a wavelength list.

    Slicing keeps the metadata in step with the data, see :meth:`__getitem__`.
    Arithmetic works element-wise on :attr:`array` and preserves the metadata as long
    as the geometry survives:

    .. code-block:: python3

        normalised = point / point.spectrum.max()   # ImageData, wavelengths intact
        difference = cube - dark_cube               # ImageData
        np.mean(cube)                               # plain scalar

    The class is not an ndarray subclass. ``np.asarray(image)`` gives the underlying
    array without copying and is the way to reach anything not offered here, such as
    comparisons or ``astype``:

    .. code-block:: python3

        mask = np.asarray(cube) > 500
        as_float = np.asarray(cube, dtype=np.float32)

    :ivar array: The image data, shaped ``(height, width, channels)``, or ``None``
        for an empty instance.
    :ivar width: Number of pixels along the horizontal axis, 1 for a point spectrum.
    :ivar height: Number of pixels along the vertical axis, 1 for a point spectrum.
    :ivar channels: Number of spectral bands, the length of the third array axis.
    :ivar wavelength: Centre wavelength in nm per band, or ``None`` when the SDK
        supplied no band information.
    """

    def __init__(self, img_buf=None, dformat=None):
        """
        Wrap an image buffer handed out by the SDK.

        Called by :class:`cuvis.Measurement` while it reads a measurement; there is
        rarely a reason to call it directly. Without arguments an empty instance is
        created, whose :attr:`array` is ``None`` and which cannot be indexed.

        :param img_buf: The ``cuvis_imbuffer_t`` to read, or ``None`` for an empty
            instance.
        :param dformat: The buffer's data format, as taken from the SDK.
        :raises TypeError: if `img_buf` is not an image buffer, or `dformat` is
            missing for one that is.
        :raises SDKException: if the buffer holds a data format this wrapper cannot
            read.
        """
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
        """Shape of :attr:`array`, ``(height, width, channels)``, or ``None`` when empty."""
        return None if self.array is None else self.array.shape

    @property
    def dtype(self):
        """Element type of :attr:`array`, or ``None`` when empty."""
        return None if self.array is None else self.array.dtype

    @property
    def is_spectrum(self) -> bool:
        """
        Whether this covers a single pixel, as a point spectrometer reading does.

        True when :attr:`array` covers a single pixel, which is the layout the SDK
        uses for a QMini and other point measurements. Derived from the array rather
        than from :attr:`width` and :attr:`height`, so it cannot disagree with what
        :attr:`spectrum` hands out.
        """
        return self.shape is not None and self.shape[:2] == (1, 1)

    @property
    def spectrum(self) -> np.ndarray:
        """
        The band vector of a single pixel measurement, one dimensional.

        Shortcut for the common point spectrometer case, equivalent to
        ``image.array.reshape(-1)``. For an image covering several pixels, index a
        pixel first, for example ``values, wavelengths = cube[y, x]``.

        .. code-block:: python3

            point = mesu.data["PointSpectrumQMini"]
            plt.plot(point.wavelength, point.spectrum)

        :return: A view on :attr:`array` of shape ``(channels,)``.
        :raises ValueError: if this instance is empty or covers more than one pixel.
        """
        if self.array is None:
            raise ValueError("Image array is not initialized.")
        if not self.is_spectrum:
            raise ValueError(
                "Not a single pixel measurement ({}x{}); index a pixel first, "
                "for example image[y, x].".format(self.shape[1], self.shape[0]))
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
        Slice or index the image data, keeping the wavelengths in step.

        The key is handed to :attr:`array` unchanged, so any NumPy indexing applies.
        What comes back depends only on how many dimensions the result has:

        ==================  ==========================================================
        Result dimensions   Returned
        ==================  ==========================================================
        3                   A new :class:`ImageData` over the selected bands
        1                   A ``(values, wavelengths)`` tuple
        anything else       The plain NumPy result, 2-D array or scalar
        ==================  ==========================================================

        .. code-block:: python3

            pixel, wavelengths = cube[100, 50]      # spectrum of one pixel, plus its wavelengths
            values, wavelengths = point[0, 0]       # the same for a QMini point spectrum
            bands = cube[:, :, 10:20]               # ImageData over bands 10 to 19
            one_band = cube[:, :, 10]               # 2-D ndarray, one band
            value = point[0, 0, 10]                 # scalar

        The wavelengths of the result are worked out from the band part of the key,
        which is understood for slices, integers, index lists and boolean masks, with
        ``...`` expanded first. They are ``None`` whenever they cannot be trusted:
        for an image that carries none to begin with, and for a key exotic enough
        that the selected bands cannot be identified. Wrong wavelengths are never
        invented to fill the gap, so check before using them.

        :param key: Any NumPy indexing key.
        :return: An :class:`ImageData`, a ``(values, wavelengths)`` tuple, or the
            plain NumPy result, as per the table above.
        :raises ValueError: if this instance is empty.
        """
        if self.array is None:
            raise ValueError("Image array is not initialized.")

        sliced_array = self.array[key]
        bands = self._band_indices(key)

        if np.ndim(sliced_array) == 3:
            return ImageData.from_array(
                sliced_array,
                wavelength=self._wavelengths_at(bands, sliced_array.shape[-1]))
        if np.ndim(sliced_array) == 1:
            return sliced_array, self._wavelengths_at(bands, len(sliced_array))
        return sliced_array

    def _band_indices(self, key) -> Optional[Sequence[int]]:
        """
        The band indices a key selects, in the order they appear in the result.

        None for a key whose effect on the band axis cannot be determined, in which
        case the wavelengths are dropped rather than guessed.
        """
        if not isinstance(key, tuple):
            key = (key,)
        at_ellipsis = next((i for i, part in enumerate(key) if part is Ellipsis), None)
        if at_ellipsis is not None:
            key = (key[:at_ellipsis]
                   + (slice(None),) * (4 - len(key))
                   + key[at_ellipsis + 1:])
        band_key = key[2] if len(key) >= 3 else slice(None)

        if isinstance(band_key, slice):
            return range(*band_key.indices(self.channels))
        if isinstance(band_key, (int, np.integer)):
            return range(band_key % self.channels, band_key % self.channels + 1)
        if isinstance(band_key, (list, tuple, np.ndarray)):
            selected = np.asarray(band_key)
            if selected.dtype == bool:
                selected = np.flatnonzero(selected)
            return [int(band) % self.channels for band in selected.ravel()]
        return None

    def _wavelengths_at(self, bands: Optional[Sequence[int]],
                        expected: int) -> Optional[list]:
        """The wavelengths of the selected bands, or None if they do not line up."""
        if self.wavelength is None or bands is None or len(bands) != expected:
            return None
        return [self.wavelength[band] for band in bands]

    def _wrap(self, result):
        """Keep the metadata when an operation preserved the image geometry."""
        # A boolean result is a mask, not image data; wavelengths would not describe it.
        if (isinstance(result, np.ndarray) and result.shape == self.array.shape
                and result.dtype != bool):
            return ImageData.from_array(
                result, self.width, self.height, self.channels, self.wavelength)
        return result

    def __array__(self, dtype=None, copy=None) -> np.ndarray:
        """
        Hand :attr:`array` to NumPy, so ``np.asarray(image)`` and every function
        built on it accept an :class:`ImageData` directly.

        :param dtype: Element type to convert to, or ``None`` to keep the current one.
        :param copy: ``True`` to force a copy. The default shares memory with
            :attr:`array` where the dtype allows it.
        :raises ValueError: if this instance is empty.
        """
        if self.array is None:
            raise ValueError("Image array is not initialized.")
        array = np.asarray(self.array, dtype=dtype)
        return array.copy() if copy else array

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        """
        Apply a NumPy ufunc to the underlying arrays, rewrapping the result.

        This is what makes ``image + 1`` and ``np.sqrt(image)`` return an
        :class:`ImageData` with the metadata carried over. Operations that change the
        geometry, reductions such as ``np.sum`` above all, return the plain NumPy
        result instead, because the metadata would no longer describe it. NumPy
        functions that are not ufuncs go through :meth:`__array__` and therefore
        always return plain arrays.
        """
        if "out" in kwargs:
            kwargs["out"] = tuple(_unwrap(out) for out in kwargs["out"])
        return self._wrap(
            getattr(ufunc, method)(*(_unwrap(i) for i in inputs), **kwargs))

    def to_numpy(self) -> np.ndarray:
        """
        The underlying array, shaped ``(height, width, channels)``.

        Returns the array itself rather than a copy, so writing to it writes through
        to this instance. Use ``np.asarray(image, dtype=...)`` to convert, or
        :attr:`spectrum` for the one dimensional form of a point measurement.
        """
        return self.array

    @classmethod
    def from_array(cls, array: np.ndarray, width: int = None, height: int = None,
                   channels: int = None, wavelength=None):
        """
        Build an :class:`ImageData` around an existing array.

        For results computed outside this class that should travel on as image data,
        and for tests. Measurements produce their own instances.

        .. code-block:: python3

            reflectance = ImageData.from_array(values, wavelength=cube.wavelength)

        :param array: The image data, ``(height, width, channels)``. Lower
            dimensional input is reshaped to that layout: a ``(channels,)`` band
            vector becomes a single pixel spectrum, a ``(height, width)`` image
            becomes a single band.
        :param width: Pixels along the horizontal axis. Taken from the array if omitted.
        :param height: Pixels along the vertical axis. Taken from the array if omitted.
        :param channels: Number of bands. Taken from the array if omitted.
        :param wavelength: Centre wavelength in nm per band. Leave it out when there
            is none; it is stored as given and never validated against `channels`.
        :return: A new :class:`ImageData` sharing memory with `array`.
        """
        array = np.asarray(array)
        if array.ndim == 1:
            array = array.reshape(1, 1, -1)
        elif array.ndim == 2:
            array = array[:, :, np.newaxis]

        instance = cls()
        instance.array = array
        instance.height = array.shape[0] if height is None else height
        instance.width = array.shape[1] if width is None else width
        instance.channels = array.shape[2] if channels is None else channels
        instance.wavelength = wavelength
        instance._img_buf = None
        return instance


def _binary_op(op, reflected=False):
    """Build one arithmetic dunder that delegates to the underlying array."""

    def apply(self, other):
        operands = (_unwrap(other), self.array) if reflected else (self.array, _unwrap(other))
        return self._wrap(op(*operands))

    name = op.__name__.strip("_")
    apply.__name__ = "__{}{}__".format("r" if reflected else "", name)
    apply.__doc__ = (
        "Element-wise {} on the underlying array, against a scalar, an array or "
        "another ImageData. Returns an ImageData with the metadata carried over "
        "when the geometry is unchanged, otherwise the plain NumPy result.".format(name))
    return apply


# Arithmetic operators, so that measurements can be combined directly rather than
# through their arrays. Comparisons are deliberately left out; use np.asarray().
for _op in (operator.add, operator.sub, operator.mul, operator.truediv,
            operator.floordiv, operator.mod, operator.pow):
    for _reflected in (False, True):
        _method = _binary_op(_op, _reflected)
        setattr(ImageData, _method.__name__, _method)

ImageData.__neg__ = lambda self: self._wrap(-self.array)
ImageData.__abs__ = lambda self: self._wrap(abs(self.array))

del _op, _reflected, _method
