from ._cuvis_il import cuvis_il
from .Measurement import ImageData, Measurement
from .cuvis_aux import SDKException
from .cuvis_types import CUVIS_imbuffer_format

from .FileWriteSettings import ViewerSettings

from typing import Union


class Viewer(object):
    def __init__(self, settings: Union[int, ViewerSettings]):
        self._handle = None
        if isinstance(settings, int):
            self._handle = settings
        elif isinstance(settings, ViewerSettings):
            _ptr = cuvis_il.new_p_int()
            if cuvis_il.status_ok != cuvis_il.cuvis_viewer_create(
                    _ptr, settings._get_internal()):
                raise SDKException()
            self._handle = cuvis_il.p_int_value(_ptr)
        else:
            raise SDKException(
                "Could not open ViewerSettings of type {}!".format(
                    type(settings)))
        pass

    def _create_view_data(self, new_handle: int) -> Union[dict[str, ImageData], ImageData]:

        _ptr = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_view_get_data_count(
                new_handle, _ptr):
            raise SDKException()

        dataCount = cuvis_il.p_int_value(_ptr)

        view_array = {}

        for i in range(dataCount):
            view_data = cuvis_il.cuvis_view_data_t()
            if cuvis_il.status_ok != cuvis_il.cuvis_view_get_data(
                    new_handle, i, view_data):
                raise SDKException()

            view_array[view_data.id] = ImageData(img_buf=view_data.data,
                                                 dformat=view_data.data.format)

        if len(view_array.keys()) == 1:
            # if only one value is available, do not wrap in dictionary
            return list(view_array.values())[0]
        else:
            return view_array

    def apply(self, mesu: Measurement) -> dict[str, ImageData]:
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

    def __deepcopy__(self, memo):
        '''This functions is not permitted due to the class only keeping a handle, that is managed by the cuvis sdk.'''
        raise TypeError('Deep copying is not supported for Viewer')

    def __copy__(self):
        '''This functions is not permitted due to the class only keeping a handle, that is managed by the cuvis sdk.'''
        raise TypeError('Shallow copying is not supported for Viewer')
