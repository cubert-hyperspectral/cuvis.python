from typing import Union
from ._cuvis_il import cuvis_il
import numpy as np
from .cuvis_aux import SDKException


class ImageData(object):
    def __init__(self, img_buf=None, dformat=None):

        if img_buf is None:

            self.width = None
            self.height = None
            self.channels = None
            self.array = None
            self.wavelength = None
            self._img_buf = None

        elif isinstance(img_buf, cuvis_il.cuvis_imbuffer_t):
            # Keep a reference to the underlying buffer so the NumPy view
            # remains valid for the lifetime of this ImageData instance.
            self._img_buf = img_buf

            if dformat is None:
                raise TypeError("Missing format for reading image buffer")

            if img_buf.format == 1:
                self.array = cuvis_il.cuvis_read_imbuf_uint8(img_buf)
            elif img_buf.format == 2:
                self.array = cuvis_il.cuvis_read_imbuf_uint16(img_buf)
            elif img_buf.format == 3:
                self.array = cuvis_il.cuvis_read_imbuf_uint32(img_buf)
            elif img_buf.format == 4:
                self.array = cuvis_il.cuvis_read_imbuf_float32(img_buf)
            else:
                raise SDKException()

            self.width = img_buf.width
            self.height = img_buf.height
            self.channels = img_buf.channels

            if img_buf.wavelength is not None:
                self.wavelength = [
                    cuvis_il.p_unsigned_int_getitem(
                        img_buf.wavelength, z) for z
                    in
                    range(self.channels)]

            # print("got image of size {}.".format(self.array.shape))

        else:
            raise TypeError(
                "Wrong data type for image buffer: {}".format(type(img_buf)))

    def __getitem__(self, key) -> Union[np.ndarray, tuple[np.ndarray, np.ndarray], object]:
        """
        Enables slicing and indexing of the image data.
        Example:
            pixel, wavelengths = image_data[100, 50]  # Single pixel spectrum plus wavelengths
            band_slice = image_data[:, :, 10:20]  # Subset of Image and Bands results in a new ImageData object
            single_channel = image_data[:,:,10] # Single Channel returns a normal numpy array
        """
        if self.array is None:
            raise ValueError("Image array is not initialized.")
        sliced_array = self.array[key]

        if sliced_array.ndim == 1:
            start_band, end_band = self._get_band_range(key)
            return sliced_array, self.wavelength[start_band:end_band]
        elif sliced_array.ndim == 2:
            return sliced_array
        elif sliced_array.ndim == 3 and sliced_array.shape[-1] > 1:
            if self.wavelength is None:
                raise ValueError("Wavelength data is not available.")
            start_band, end_band = self._get_band_range(key)
            sliced_wavelength = self.wavelength[start_band:end_band]
            return ImageData.from_array(
                sliced_array,
                width=sliced_array.shape[1],
                height=sliced_array.shape[0],
                channels=sliced_array.shape[2],
                wavelength=sliced_wavelength,
            )

    def _get_band_range(self, key):
        """
        Helper method to determine the band range based on the slicing key.
        """
        if isinstance(key, tuple) and len(key) == 3:
            if isinstance(key[2], slice):
                start = key[2].start or 0
                stop = key[2].stop or self.channels
                return start, stop
            elif isinstance(key[2], int):
                return key[2], key[2] + 1
        return 0, self.channels

    def to_numpy(self) -> np.ndarray:
        """
        Returns the spectral data as a NumPy array.
        """
        return self.array

    @classmethod
    def from_array(cls, array: np.ndarray, width: int, height: int, channels: int, wavelength=None):
        """
        Creates an ImageData instance from a NumPy array and metadata.
        """
        instance = cls()
        instance.array = array
        instance.width = width
        instance.height = height
        instance.channels = channels
        instance.wavelength = wavelength
        instance._img_buf = None
        return instance
