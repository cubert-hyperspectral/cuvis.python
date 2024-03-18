try:
    from cuvis_il import cuvis_il
except:
    import cuvis_il
from .Measurement import ImageData, Measurement
from .cuvis_aux import SDKException
from .cuvis_types import CUVIS_imbuffer_format

from .FileWriteSettings import ViewExportSettings

from typing import Union, Dict

class Viewer(object):
    def __init__(self, settings: Union[int,ViewExportSettings]):
        self._handle = None
        if isinstance(settings, int):
            self._handle = settings
        if isinstance(settings, ViewExportSettings):
            _ptr = cuvis_il.new_p_int()
            if cuvis_il.status_ok != cuvis_il.cuvis_viewer_create(
                    _ptr, settings._get_internal()[1]):
                raise SDKException()
            self._handle = cuvis_il.p_int_value(_ptr)
        else:
            raise SDKException(
                "Could not open ViewerSettings of type {}!".format(
                    type(settings)))
        pass

    def _create_view_data(self,new_handle: int) -> Dict[str,ImageData]:

        _ptr = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_view_get_data_count(
                new_handle, _ptr):
            raise SDKException()

        dataCount = cuvis_il.p_int_value(_ptr)

        view_array = {}

        for i in range(dataCount):
            view_data = cuvis_il.cuvis_view_data_t()
            if cuvis_il.status_ok != cuvis_il.cuvis_view_get_data(
                new_handle, view_data):
                raise SDKException()
        
            if view_data.data.format == CUVIS_imbuffer_format["imbuffer_format_uint8"]:
                view_data[view_data.id]= ImageData(img_buf=view_data.data,
                                 dformat=view_data.data.format)
            else:
                raise SDKException("Unsupported viewer bit depth!")
        # TODO when is a good point to release the view
        # cuvis_il.cuvis_view_free(_ptr)
        return view_array

    def apply(self, mesu: Measurement) -> Dict[str,ImageData]:
        _ptr = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_viewer_apply(self._handle,
                mesu._handle, _ptr):
            raise SDKException()
        currentView = cuvis_il.p_int_value(_ptr)

        return self._create_view_data(currentView)

    def __del__(self):
        _ptr = cuvis_il.new_p_int()
        cuvis_il.p_int_assign(_ptr, self._handle)
        cuvis_il.cuvis_viewer_free(_ptr)
        self._handle = cuvis_il.p_int_value(_ptr)
