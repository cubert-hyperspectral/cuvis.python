from cuvis_il import cuvis_il
from .Calibration import Calibration
from .FileWriteSettings import ProcessingArgs
from .Measurement import Measurement
from .SessionFile import SessionFile
from .cuvis_aux import SDKException
from .cuvis_types import ReferenceType, ProcessingMode

import cuvis.cuvis_types as internal

from typing import Union

import dataclasses

class ProcessingContext(object):
    def __init__(self, base: Union[Calibration, SessionFile, Measurement]):
        self._handle = None
        self._modeArgs = ProcessingArgs()

        if isinstance(base, Calibration):
            _ptr = cuvis_il.new_p_int()
            if cuvis_il.status_ok != cuvis_il.cuvis_proc_cont_create_from_calib(
                    base._handle, _ptr):
                raise SDKException()
            self._handle = cuvis_il.p_int_value(_ptr)
        elif isinstance(base, SessionFile):
            _ptr = cuvis_il.new_p_int()
            if cuvis_il.status_ok != \
                    cuvis_il.cuvis_proc_cont_create_from_session_file(
                        base._handle, _ptr):
                raise SDKException()
            self._handle = cuvis_il.p_int_value(_ptr)
        elif isinstance(base, Measurement):
            _ptr = cuvis_il.new_p_int()
            if cuvis_il.status_ok != cuvis_il.cuvis_proc_cont_create_from_mesu(
                    base._handle, _ptr):
                raise SDKException()
            self._handle = cuvis_il.p_int_value(_ptr)
        else:
            raise SDKException(
                "could not interpret input of type {}.".format(type(base)))
        pass

    def apply(self, mesu: Measurement) -> Measurement:
        if isinstance(mesu, Measurement):
            if cuvis_il.status_ok != cuvis_il.cuvis_proc_cont_apply(
                    self._handle, mesu._handle):
                raise SDKException()
            mesu.refresh()
            return mesu
        else:
            raise SDKException(
                "Can only apply ProcessingContext to Measurement!")
        pass

    def set_reference(self, mesu: Measurement, refType: ReferenceType) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_proc_cont_set_reference(
                self._handle, mesu._handle,
                internal.__CuvisReferenceType__[refType]):
            raise SDKException()
        pass

    def clear_reference(self, refType: ReferenceType) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_proc_cont_clear_reference(
                self._handle, internal.__CuvisReferenceType__[refType]):
            raise SDKException()
        pass

    def get_reference(self, refType: ReferenceType) -> Measurement:

        has_ref = self.has_reference(refType)
        if not has_ref:
            return None
        _ptr = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_proc_cont_get_reference(
                self._handle, _ptr,
                internal.__CuvisReferenceType__[refType]):
            raise SDKException()
        return Measurement(cuvis_il.p_int_value(_ptr))

    def has_reference(self, refType: ReferenceType) -> bool:
        _ptr = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_proc_cont_has_reference(
                self._handle, internal.__CuvisReferenceType__[refType],
                _ptr):
            raise SDKException()
        return bool(cuvis_il.p_int_value(_ptr))

    @property
    def processing_mode(self) -> ProcessingMode:
        return self._modeArgs.processing_mode

    @processing_mode.setter
    def processing_mode(self, pMode: ProcessingMode) -> None:
        self._modeArgs.processing_mode = pMode
        if cuvis_il.status_ok != cuvis_il.cuvis_proc_cont_set_args(
                self._handle, self._modeArgs._get_internal()):
            raise SDKException()
        pass

    def set_processing_args(self, pa: ProcessingArgs) -> None:
        self._modeArgs = dataclasses.replace(pa)
        if cuvis_il.status_ok != cuvis_il.cuvis_proc_cont_set_args(
                self._handle, self._modeArgs._get_internal()):
            raise SDKException()
        pass

    def get_processing_args(self) -> ProcessingArgs:
        return dataclasses.replace(self._modeArgs)

    def is_capable(self, mesu: Measurement, pa: ProcessingArgs) -> bool:
        args = pa._get_internal()
        _ptr = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_proc_cont_is_capable(
                self._handle, mesu._handle, args, _ptr):
            raise SDKException()
        return bool(cuvis_il.p_int_value(_ptr))

    def calc_distance(self, distMM: int) -> bool:
        if cuvis_il.status_ok != cuvis_il.cuvis_proc_cont_calc_distance(
                self._handle, distMM):
            raise SDKException()
        return True

    @property
    def calibration_id(self) -> str:
        _id = cuvis_il.cuvis_proc_cont_get_calib_id_swig(self._handle)
        return _id

    def __del__(self):
        _ptr = cuvis_il.new_p_int()
        cuvis_il.p_int_assign(_ptr, self._handle)
        cuvis_il.cuvis_proc_cont_free(_ptr)
        self._handle = cuvis_il.p_int_value(_ptr)
        pass