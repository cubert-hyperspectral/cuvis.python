import os
from pathlib import Path

try:
    from cuvis_il import cuvis_il
except ImportError as e:
    if e.msg.startswith('DLL'):
        raise
    import cuvis_il
from .SessionFile import SessionFile
from .cuvis_aux import SDKException, Capabilities
from .cuvis_types import OperationMode

from typing import Union

class Calibration(object):

    def __init__(self, base: Union[Path, str, SessionFile]):
        self._handle = None

        if isinstance(Path(base), Path) and os.path.exists(Path(base)):
            _ptr = cuvis_il.new_p_int()
            if cuvis_il.status_ok != cuvis_il.cuvis_calib_create_from_path(
                    base, _ptr):
                raise SDKException()
            self._handle = cuvis_il.p_int_value(_ptr)
        elif isinstance(base, SessionFile):
            _ptr = cuvis_il.new_p_int()
            if cuvis_il.status_ok != \
                    cuvis_il.cuvis_calib_create_from_session_file(
                        base._handle, _ptr):
                raise SDKException()
        else:
            raise SDKException(
                "Could not interpret input of type {}.".format(type(base)))
        pass


    def get_capabilities(self, operation_mode: OperationMode) -> Capabilities:

        _ptr = cuvis_il.new_p_int()

        if cuvis_il.status_ok != cuvis_il.cuvis_calib_get_capabilities(
                self._handle, operation_mode, _ptr):
            raise SDKException()
        return Capabilities(cuvis_il.p_int_value(_ptr))

    @property
    def id(self) -> str:
        _id = cuvis_il.cuvis_calib_get_id_swig(self._handle)
        return _id

    def __del__(self):
        _ptr = cuvis_il.new_p_int()
        cuvis_il.p_int_assign(_ptr, self._handle)
        cuvis_il.cuvis_calib_free(_ptr)
        pass
