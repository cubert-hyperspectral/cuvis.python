import os
from pathlib import Path

from cuvis_il import cuvis_il
from .Measurement import Measurement
from .cuvis_aux import SDKException
from .cuvis_types import OperationMode, SessionItemType, ReferenceType

import cuvis.cuvis_types as internal

from typing import Union, Optional

class SessionFile(object):
    def __init__(self, base: Union[Path,str]):
        self._handle = None
        if isinstance(Path(base), Path) and os.path.exists(base):
            _ptr = cuvis_il.new_p_int()
            if cuvis_il.status_ok != cuvis_il.cuvis_session_file_load(base,
                                                                      _ptr):
                raise SDKException()
            self._handle = cuvis_il.p_int_value(_ptr)
        else:
            raise SDKException(
                "Could not open SessionFile File! File not found!")

    pass

    def get_measurement(self, frameNo: int, itemtype: SessionItemType = SessionItemType.no_gaps) ->  Optional[Measurement]:
        _ptr = cuvis_il.new_p_int()
        ret =  cuvis_il.cuvis_session_file_get_mesu(self._handle, frameNo, internal.__CuvisSessionItemType__[itemtype],
                _ptr)
        if cuvis_il.status_no_measurement == ret:
            return None
        if cuvis_il.status_ok != ret:
            raise SDKException()
        return Measurement(cuvis_il.p_int_value(_ptr))
    
    def get_reference(self, frameNo: int, reftype: ReferenceType) -> Measurement:
        _ptr = cuvis_il.new_p_int()
        ret = cuvis_il.cuvis_session_file_get_reference_mesu(
                self._handle, frameNo, internal.__CuvisSessionItemType__[reftype],
                _ptr)
        if cuvis_il.status_no_measurement == ret:
            return None
        if cuvis_il.status_ok != ret:
            raise SDKException()
        return Measurement(cuvis_il.p_int_value(_ptr))

    def get_size(self, itemtype: SessionItemType = SessionItemType.no_gaps) -> int:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_session_file_get_size(
                self._handle, internal.__CuvisSessionItemType__[itemtype], val):
            raise SDKException()
        return cuvis_il.p_int_value(val)

    @property
    def fps(self) -> float:
        val = cuvis_il.new_p_double()
        if cuvis_il.status_ok != cuvis_il.cuvis_session_file_get_fps(
                self._handle, val):
            raise SDKException()
        return cuvis_il.p_double_value(val)

    @property
    def operation_mode(self) -> OperationMode:
        val = cuvis_il.new_p_cuvis_operation_mode_t()
        if cuvis_il.status_ok != cuvis_il.cuvis_session_file_get_operation_mode(
                self._handle, val):
            raise SDKException()
        return internal.__OperationMode__[cuvis_il.p_cuvis_operation_mode_t_value(val)]
    
    @property
    def hash(self) -> str:
        return cuvis_il.cuvis_session_file_get_hash_swig(self._handle)
    
    # Python Magic Methods
    def __iter__(self):
        for i in range(len(self)):
            yield self[i]
        pass
        
    def __len__(self):
        return self.get_size()
    
    def __getitem__(self, key: int) -> Measurement:
        return self.get_measurement(key)

    def __del__(self):
        _ptr = cuvis_il.new_p_int()
        cuvis_il.p_int_assign(_ptr, self._handle)
        cuvis_il.cuvis_session_file_free(_ptr)
        self._handle = cuvis_il.p_int_value(_ptr)
