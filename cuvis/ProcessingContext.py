from ._cuvis_il import cuvis_il
from .Calibration import Calibration
from .FileWriteSettings import ProcessingArgs
from .Measurement import Measurement
from .SessionFile import SessionFile
from .cube_utils import ImageData
from .cuvis_aux import SDKException
from .cuvis_types import ReferenceType, ProcessingMode

import cuvis.cuvis_types as internal


import dataclasses

import numpy as np

_SPECTRUM_REFERENCES = (ReferenceType.WhiteSpectrum, ReferenceType.TargetSpectrum)


def _spectrum_arrays(data: ImageData | tuple) -> tuple[np.ndarray, np.ndarray]:
    """(wavelengths_nm, values) as validated 1-d arrays out of an ImageData or a pair."""
    if isinstance(data, ImageData):
        if data.wavelength is None:
            raise ValueError("The spectrum ImageData carries no wavelengths.")
        wavelengths = np.asarray(data.wavelength).reshape(-1)
        values = np.asarray(data.array).reshape(-1)
    else:
        try:
            wavelengths, values = data
        except (TypeError, ValueError):
            raise TypeError(
                "A reference spectrum is an ImageData with wavelengths, or a"
                " (wavelengths, values) pair of one-dimensional arrays."
            )
        wavelengths = np.asarray(wavelengths).reshape(-1)
        values = np.asarray(values).reshape(-1)
    if wavelengths.size == 0 or wavelengths.size != values.size:
        raise ValueError(
            "A reference spectrum needs equally many wavelengths and values,"
            f" got {wavelengths.size} and {values.size}."
        )
    return np.ascontiguousarray(wavelengths, dtype=np.float32), values


class ProcessingContext(object):
    def __init__(
        self,
        base: Calibration | SessionFile | Measurement,
        load_references: bool = True,
    ):
        self._handle = None
        self._modeArgs = ProcessingArgs()

        if isinstance(base, Calibration):
            _ptr = cuvis_il.new_p_int()
            if cuvis_il.status_ok != cuvis_il.cuvis_proc_cont_create_from_calib(
                base._handle, _ptr
            ):
                raise SDKException()
            self._handle = cuvis_il.p_int_value(_ptr)
        elif isinstance(base, SessionFile):
            _ptr = cuvis_il.new_p_int()
            if cuvis_il.status_ok != cuvis_il.cuvis_proc_cont_create_from_session_file(
                base._handle, 1 if load_references else 0, _ptr
            ):
                raise SDKException()
            self._handle = cuvis_il.p_int_value(_ptr)
        elif isinstance(base, Measurement):
            _ptr = cuvis_il.new_p_int()
            if cuvis_il.status_ok != cuvis_il.cuvis_proc_cont_create_from_mesu(
                base._handle, 1 if load_references else 0, _ptr
            ):
                raise SDKException()
            self._handle = cuvis_il.p_int_value(_ptr)
        else:
            raise SDKException(
                "could not interpret input of type {}.".format(type(base))
            )
        pass

    def apply(self, mesu: Measurement) -> Measurement:
        if isinstance(mesu, Measurement):
            if cuvis_il.status_ok != cuvis_il.cuvis_proc_cont_apply(
                self._handle, mesu._handle
            ):
                raise SDKException()
            mesu.refresh()
            return mesu
        else:
            raise SDKException("Can only apply ProcessingContext to Measurement!")
        pass

    def set_reference(
        self,
        data: Measurement | ImageData | tuple,
        refType: ReferenceType,
        *,
        effective_bit_depth: int | None = None,
        integration_time: float = 0.0,
    ) -> None:
        """Set a reference for processing.

        The classic reference types take a Measurement. The two spectrum types take an
        ImageData carrying wavelengths, or a (wavelengths, values) pair of arrays, with
        wavelengths in nanometres:

        - TargetSpectrum: reflectance values in percent (0 to 100).
        - WhiteSpectrum: raw sensor counts (uint16); effective_bit_depth (1 to 16) is
          required, integration_time [ms] describes the recording.
        """
        if refType not in _SPECTRUM_REFERENCES:
            if effective_bit_depth is not None or integration_time:
                raise TypeError(
                    "Spectrum metadata only applies to WhiteSpectrum and TargetSpectrum references."
                )
            if not isinstance(data, Measurement):
                raise TypeError(f"Reference type {refType} takes a Measurement.")
            if cuvis_il.status_ok != cuvis_il.cuvis_proc_cont_set_reference(
                self._handle, data._handle, internal.__CuvisReferenceType__[refType]
            ):
                raise SDKException()
            return

        if isinstance(data, Measurement):
            raise TypeError(
                f"Reference type {refType} takes spectrum data"
                " (an ImageData with wavelengths, or a (wavelengths, values) pair)."
            )
        wavelengths, values = _spectrum_arrays(data)

        if refType is ReferenceType.TargetSpectrum:
            if effective_bit_depth is not None or integration_time:
                raise TypeError(
                    "Counts metadata does not apply to the target spectrum."
                )
            values = np.ascontiguousarray(values, dtype=np.float32)
            if (
                cuvis_il.status_ok
                != cuvis_il.cuvis_proc_cont_set_reference_target_spectrum_swig(
                    self._handle, wavelengths, values
                )
            ):
                raise SDKException()
            return

        if effective_bit_depth is None:
            raise ValueError(
                "A white counts spectrum needs effective_bit_depth (1 to 16)."
            )
        if values.min() < 0 or values.max() > 0xFFFF:
            raise ValueError("White spectrum counts must fit uint16 (0 to 65535).")
        values = np.ascontiguousarray(values, dtype=np.uint16)
        if (
            cuvis_il.status_ok
            != cuvis_il.cuvis_proc_cont_set_reference_white_spectrum_swig(
                self._handle,
                wavelengths,
                values,
                int(effective_bit_depth),
                float(integration_time),
            )
        ):
            raise SDKException()
        pass

    def clear_reference(self, refType: ReferenceType) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_proc_cont_clear_reference(
            self._handle, internal.__CuvisReferenceType__[refType]
        ):
            raise SDKException()
        pass

    def get_reference(self, refType: ReferenceType) -> Measurement:
        """The reference measurement, or None. Spectrum references are not measurements;
        for those use get_reference_spectrum."""
        has_ref = self.has_reference(refType)
        if not has_ref:
            return None
        _ptr = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_proc_cont_get_reference(
            self._handle, _ptr, internal.__CuvisReferenceType__[refType]
        ):
            raise SDKException()
        return Measurement(cuvis_il.p_int_value(_ptr))

    def get_reference_spectrum(self, refType: ReferenceType) -> ImageData:
        """The reference spectrum as an ImageData (shape 1 x 1 x channels, wavelengths in
        nanometres), or None when the slot is empty.

        Only ReferenceType.WhiteSpectrum and ReferenceType.TargetSpectrum are spectra;
        other types live in get_reference. The counts metadata passed to set_reference
        (effective_bit_depth, integration_time) is not returned; the C API
        does not expose it.
        """
        if refType is ReferenceType.TargetSpectrum:
            read = cuvis_il.cuvis_proc_cont_get_reference_target_spectrum_swig
        elif refType is ReferenceType.WhiteSpectrum:
            read = cuvis_il.cuvis_proc_cont_get_reference_white_spectrum_swig
        else:
            raise ValueError(
                f"Reference type {refType} is not a spectrum; use get_reference."
            )
        if not self.has_reference(refType):
            return None
        status, wavelengths, values = read(self._handle)
        if cuvis_il.status_ok != status:
            raise SDKException()
        return ImageData.from_array(
            values, wavelength=[float(wl) for wl in wavelengths]
        )

    def has_reference(self, refType: ReferenceType) -> bool:
        _ptr = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_proc_cont_has_reference(
            self._handle, internal.__CuvisReferenceType__[refType], _ptr
        ):
            raise SDKException()
        return bool(cuvis_il.p_int_value(_ptr))

    @property
    def processing_mode(self) -> ProcessingMode:
        return self._modeArgs.processing_mode

    @processing_mode.setter
    def processing_mode(self, pMode: ProcessingMode) -> None:
        self._modeArgs.processing_mode = pMode
        if cuvis_il.status_ok != cuvis_il.cuvis_proc_cont_set_args(
            self._handle, self._modeArgs._get_internal()
        ):
            raise SDKException()
        pass

    def set_processing_args(self, pa: ProcessingArgs) -> None:
        self._modeArgs = dataclasses.replace(pa)
        if cuvis_il.status_ok != cuvis_il.cuvis_proc_cont_set_args(
            self._handle, self._modeArgs._get_internal()
        ):
            raise SDKException()
        pass

    def get_processing_args(self) -> ProcessingArgs:
        return dataclasses.replace(self._modeArgs)

    def is_capable(self, mesu: Measurement, pa: ProcessingArgs) -> bool:
        args = pa._get_internal()
        _ptr = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_proc_cont_is_capable(
            self._handle, mesu._handle, args, _ptr
        ):
            raise SDKException()
        return bool(cuvis_il.p_int_value(_ptr))

    def calc_distance(self, distMM: float) -> bool:
        if cuvis_il.status_ok != cuvis_il.cuvis_proc_cont_calc_distance(
            self._handle, distMM
        ):
            raise SDKException()
        return True

    @property
    def calibration_id(self) -> str:
        _id = cuvis_il.cuvis_proc_cont_get_calib_id_swig(self._handle)
        return _id

    def __del__(self):
        if self._handle is None:
            return
        _ptr = cuvis_il.new_p_int()
        cuvis_il.p_int_assign(_ptr, self._handle)
        cuvis_il.cuvis_proc_cont_free(_ptr)
        self._handle = cuvis_il.p_int_value(_ptr)
        pass

    def __deepcopy__(self, memo):
        """This functions is not permitted due to the class only keeping a handle, that is managed by the cuvis sdk."""
        raise TypeError("Deep copying is not supported for ProcessingContext")

    def __copy__(self):
        """This functions is not permitted due to the class only keeping a handle, that is managed by the cuvis sdk."""
        raise TypeError("Shallow copying is not supported for ProcessingContext")
