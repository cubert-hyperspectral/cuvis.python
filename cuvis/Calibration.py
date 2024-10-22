import os
from pathlib import Path

from ._cuvis_il import cuvis_il
from .SessionFile import SessionFile
from .cuvis_aux import SDKException, Capabilities, CalibrationInfo
from .cuvis_types import OperationMode

import cuvis.cuvis_types as internal

from typing import Union


class Calibration(object):

    def __init__(self, base: Union[Path, str, SessionFile]):
        self._handle = None
        _ptr = cuvis_il.new_p_int()
        if isinstance(base, SessionFile):
            retval = cuvis_il.cuvis_calib_create_from_session_file(
                base._handle, _ptr)
        elif (isinstance(base, Path) and base.is_dir()) or os.path.exists(base):
            retval = cuvis_il.cuvis_calib_create_from_path(str(base), _ptr)
        else:
            raise SDKException(
                "Could not interpret input of type '{}'.".format(type(base)))
        if cuvis_il.status_ok != retval:
            raise SDKException()
        self._handle = cuvis_il.p_int_value(_ptr)

    def get_capabilities(self, operation_mode: OperationMode) -> Capabilities:

        _ptr = cuvis_il.new_p_int()

        if cuvis_il.status_ok != cuvis_il.cuvis_calib_get_capabilities(
                self._handle, internal.__CuvisOperationMode__[operation_mode], _ptr):
            raise SDKException()
        return Capabilities(cuvis_il.p_int_value(_ptr))

    @property
    def info(self) -> CalibrationInfo:
        ret = cuvis_il.cuvis_calibration_info_t()
        if cuvis_il.status_ok != cuvis_il.cuvis_calib_get_info(
                self._handle, ret):
            raise SDKException()
        return CalibrationInfo(
            ret.model_name,
            ret.serial_no,
            ret.calibration_date,
            ret.annotation_name,
            ret.unique_id,
            ret.file_path)

    @property
    def id(self) -> str:
        _id = cuvis_il.cuvis_calib_get_id_swig(self._handle)
        return _id

    def __del__(self):
        _ptr = cuvis_il.new_p_int()
        cuvis_il.p_int_assign(_ptr, self._handle)
        cuvis_il.cuvis_calib_free(_ptr)
