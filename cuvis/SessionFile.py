
from pathlib import Path

from ._cuvis_il import cuvis_il
from .Measurement import Measurement, ImageData
from .cuvis_aux import SDKException
from .cuvis_types import OperationMode, SessionItemType, ReferenceType, CUVIS_imbuffer_format

import cuvis.cuvis_types as internal

from typing import Union, Optional


class SessionFile(object):
    def __init__(self, base: Union[Path, str]):
        base = Path(base)
        self._handle = None
        self._pc = None
        if base.exists():
            _ptr = cuvis_il.new_p_int()
            if cuvis_il.status_ok != cuvis_il.cuvis_session_file_load(str(base),
                                                                      _ptr):
                raise SDKException()
            self._handle = cuvis_il.p_int_value(_ptr)
        else:
            raise FileNotFoundError(
                "Could not open SessionFile File! File not found!")

    def get_measurement(self, frameNo: int = 0, itemtype: SessionItemType = SessionItemType.no_gaps) -> Optional[Measurement]:
        _ptr = cuvis_il.new_p_int()
        ret = cuvis_il.cuvis_session_file_get_mesu(self._handle, frameNo, internal.__CuvisSessionItemType__[itemtype],
                                                   _ptr)
        if cuvis_il.status_no_measurement == ret:
            return None
        if cuvis_il.status_ok != ret:
            raise SDKException()
        mesu = Measurement(cuvis_il.p_int_value(_ptr))
        mesu._session = self
        return mesu

    def get_reference(self, frameNo: int, reftype: ReferenceType) -> Optional[Measurement]:
        _ptr = cuvis_il.new_p_int()
        ret = cuvis_il.cuvis_session_file_get_reference_mesu(
            self._handle, frameNo, internal.__CuvisReferenceType__[reftype],
            _ptr)
        if cuvis_il.status_no_measurement == ret:
            return None
        if cuvis_il.status_ok != ret:
            raise SDKException()
        return Measurement(cuvis_il.p_int_value(_ptr))

    @property
    def thumbnail(self) -> ImageData:
        thumbnail_data = cuvis_il.cuvis_view_data_t()
        if cuvis_il.status_ok != cuvis_il.cuvis_session_file_get_thumbnail(self, thumbnail_data):
            raise SDKException()

        if thumbnail_data.data.format == CUVIS_imbuffer_format["imbuffer_format_uint8"]:
            return ImageData(img_buf=thumbnail_data.data,
                             dformat=thumbnail_data.data.format)
        else:
            raise SDKException("Unsupported viewer bit depth!")

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

    def __deepcopy__(self, memo):
        '''This functions is not permitted due to the class only keeping a handle, that is managed by the cuvis sdk.'''
        raise TypeError('Deep copying is not supported for SessionFile')

    def __copy__(self):
        '''This functions is not permitted due to the class only keeping a handle, that is managed by the cuvis sdk.'''
        raise TypeError('Shallow copying is not supported for SessionFile')
