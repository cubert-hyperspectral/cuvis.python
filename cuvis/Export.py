from _cuvis_il import cuvis_il
from .cuvis_aux import SDKException

from .Measurement import Measurement
from .FileWriteSettings import GeneralExportSettings, EnviExportSettings, TiffExportSettings, ViewExportSettings, SaveArgs

class Exporter(object):
    def __init__(self):
        self._handle = None
        pass

    def __del__(self):
        _ptr = cuvis_il.new_p_int()
        cuvis_il.p_int_assign(_ptr, self._handle)
        cuvis_il.cuvis_exporter_free(_ptr)
        pass

    def apply(self, mesu: Measurement) -> Measurement:
        if cuvis_il.status_ok != cuvis_il.cuvis_exporter_apply(self._handle,
                                                               mesu._handle):
            raise SDKException()
        mesu.refresh()
        return mesu

    @property
    def queue_used(self) -> int:
        _ptr = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_exporter_get_queue_used(
                self._handle, _ptr):
            raise SDKException()
        return cuvis_il.p_int_value(_ptr)


class CubeExporter(Exporter):
    def __init__(self, fs: SaveArgs):
        super().__init__()
        _ptr = cuvis_il.new_p_int()
        ge, fs = fs._get_internal()
        if cuvis_il.status_ok != cuvis_il.cuvis_exporter_create_cube(_ptr, ge,
                                                                     fs):
            raise SDKException()
        self._handle = cuvis_il.p_int_value(_ptr)
        pass


class TiffExporter(Exporter):
    def __init__(self, fs: TiffExportSettings):
        super().__init__()
        _ptr = cuvis_il.new_p_int()
        ge, fs = fs._get_internal()
        if cuvis_il.status_ok != cuvis_il.cuvis_exporter_create_tiff(_ptr, ge,
                                                                     fs):
            raise SDKException()
        self._handle = cuvis_il.p_int_value(_ptr)
        pass


class EnviExporter(Exporter):
    def __init__(self, ge: EnviExportSettings):
        super().__init__()
        _ptr = cuvis_il.new_p_int()
        ge, _ = ge._get_internal()
        if cuvis_il.status_ok != cuvis_il.cuvis_exporter_create_envi(_ptr, ge):
            raise SDKException()
        self._handle = cuvis_il.p_int_value(_ptr)
        pass


class ViewExporter(Exporter):
    def __init__(self, fs: ViewExportSettings):
        super().__init__()
        _ptr = cuvis_il.new_p_int()
        ge, fs = fs._get_internal()
        if cuvis_il.status_ok != cuvis_il.cuvis_exporter_create_view(_ptr, ge,
                                                                     fs):
            raise SDKException()
        self._handle = cuvis_il.p_int_value(_ptr)
        pass
