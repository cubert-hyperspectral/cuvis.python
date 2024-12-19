from typing import Union
from .FileWriteSettings import SaveArgs
import datetime
import os
import numpy as np

from ._cuvis_il import cuvis_il
from .cuvis_aux import SDKException, SessionData, Capabilities, MeasurementFlags, SensorInfo, GPSData
from .cuvis_types import DataFormat, ProcessingMode, ReferenceType
from .cube_utils import ImageData


import cuvis.cuvis_types as internal
base_datetime = datetime.datetime(1970, 1, 1)


class Measurement(object):
    capture_time: datetime.datetime
    measurement_flags: MeasurementFlags
    path: str
    comment: str
    factory_calibration: datetime.datetime
    assembly: str
    integration_time: int
    averages: int
    distance: float
    serial_number: str
    product_name: str
    processing_mode: ProcessingMode
    name: str
    session_info: SessionData
    frame_id: int

    def __init__(self, base: Union[int, str]):
        self._handle = None
        self._session = None

        if isinstance(base, int):
            self._handle = base
        elif isinstance(base, str) and os.path.exists(base):
            _ptr = cuvis_il.new_p_int()
            if cuvis_il.status_ok != cuvis_il.cuvis_measurement_load(base,
                                                                     _ptr):
                raise SDKException()
            self._handle = cuvis_il.p_int_value(_ptr)
        else:
            raise SDKException(
                "Could not open Measurement! Either handle not"
                " available or file not found!")
        self.refresh()
        pass

    def _refresh_metadata(self):
        _metaData = cuvis_il.cuvis_mesu_metadata_allocate()
        if cuvis_il.status_ok != cuvis_il.cuvis_measurement_get_metadata(
                self._handle, _metaData):
            raise SDKException

        self.capture_time = base_datetime + datetime.timedelta(
            milliseconds=_metaData.capture_time)
        self.measurement_flags = MeasurementFlags(_metaData.measurement_flags)
        self.path = _metaData.path
        self.comment = _metaData.comment
        try:
            self.factory_calibration = base_datetime + datetime.timedelta(
                milliseconds=_metaData.factory_calibration)
        except OverflowError:
            self.factory_calibration = None
        self.assembly = _metaData.assembly
        self.averages = _metaData.averages
        self.distance = _metaData.distance
        self.integration_time = _metaData.integration_time
        self.serial_number = _metaData.serial_number
        self.product_name = _metaData.product_name
        self.processing_mode = internal.__ProcessingMode__[
            _metaData.processing_mode]
        self.name = _metaData.name
        self.session_info = SessionData(_metaData.session_info_name,
                                        _metaData.session_info_session_no,
                                        _metaData.session_info_sequence_no)
        self.frame_id = _metaData.measurement_frame_id
        cuvis_il.cuvis_mesu_metadata_free(_metaData)

    def refresh(self) -> None:
        self.data = {}
        self._refresh_metadata()
        pcount = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_measurement_get_data_count(
                self._handle, pcount):
            raise SDKException()
        for ind in range(cuvis_il.p_int_value(pcount)):
            pType = cuvis_il.new_p_cuvis_data_type_t()
            key = cuvis_il.cuvis_measurement_get_data_info_swig(self._handle,
                                                                pType, ind)
            cdtype = cuvis_il.p_cuvis_data_type_t_value(pType)
            if cdtype == cuvis_il.data_type_image:
                data = cuvis_il.cuvis_imbuffer_t()
                cuvis_il.cuvis_measurement_get_data_image(self._handle,
                                                          key,
                                                          data)
                # t0 = datetime.datetime.now()
                self.data.update({key: ImageData(img_buf=data,
                                                 dformat=DataFormat[
                                                     data.__getattribute__(
                                                         "format")])})
                # print("image loading time: {}".format(
                # datetime.datetime.now() - t0))
            elif cdtype == cuvis_il.data_type_string:
                val = cuvis_il.cuvis_measurement_get_data_string_swig(
                    self._handle, key)
                self.data.update({key: val})
            elif cdtype == cuvis_il.data_type_gps:
                gps = cuvis_il.cuvis_gps_t()
                cuvis_il.cuvis_measurement_get_data_gps(self._handle, key,
                                                        gps)
                self.data.update({key: GPSData._from_internal(gps)})
            elif cdtype == cuvis_il.data_type_sensor_info:
                info = cuvis_il.cuvis_sensor_info_t()
                cuvis_il.cuvis_measurement_get_data_sensor_info(self._handle,
                                                                key, info)
                self.data.update({key: SensorInfo._from_internal(info)})
            else:
                self.data.update({key: "Not Implemented!"})

    def save(self, saveargs: SaveArgs) -> None:
        ge, sa = saveargs._get_internal()
        if cuvis_il.status_ok != cuvis_il.cuvis_measurement_save(
                self._handle, ge.export_dir, sa):
            raise SDKException()
        pass

    def set_name(self, name: str) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_measurement_set_name(
                self._handle, name):
            raise SDKException()
        self._refresh_metadata()
        pass

    @property
    def cube(self) -> ImageData:
        """
        Retrieves or processes the 'cube' data for this Measurement.

        This property prioritizes convenience over strict design principles:
        - Attempts to retrieve the 'cube' from `self.data`.
        - Lazily initializes a `ProcessingContext` if a session is available but uninitialized.
        - May trigger expensive processing and modify internal state during property access.

        While functional, this approach introduces side effects and tight coupling, making it less
        predictable and not the cleanest solution. Suitable for specific workflows where these
        trade-offs are acceptable.

        Raises
        ------
        ValueError
            If the 'cube' is not available and processing is not possible.

        Returns
        -------
        ImageData
            The 'cube' data, either retrieved from `self.data` or generated through processing.
        """
        if 'cube' in self.data:
            return self.data.get('cube')
        if self._session is not None:
            # try fallback if session is known
            if self._session._pc is None:
                from .ProcessingContext import ProcessingContext
                self._session._pc = ProcessingContext(self._session)
            self._session._pc.apply(self)
            return self.data.get('cube', None)
        raise ValueError(
            "This Measurement does not have a cube saved. Consider reprocessing with a Processing Context.")

    @property
    def thumbnail(self):
        thumb = [val for key, val in self.data.items() if "view" in key]
        if len(thumb) == 0:
            print("No thumbnail available. Use cube instead!")
            return None
        elif len(thumb) == 1:
            return thumb[0]
        elif len(thumb) > 1:
            shapes = [th.array.shape for th in thumb]
            return thumb[shapes.index(min(shapes))]

    @property
    def capabilities(self) -> Capabilities:
        _ptr = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_measurement_get_capabilities(
                self._handle, _ptr):
            raise SDKException()
        return Capabilities(cuvis_il.p_int_value(_ptr))

    @property
    def calibration_id(self) -> str:
        _id = cuvis_il.cuvis_measurement_get_calib_id_swig(self._handle)
        return _id

    def set_comment(self, comment: str) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_measurement_set_comment(
                self._handle, comment):
            raise SDKException()
        self._refresh_metadata()
        pass

    @property
    def data_count(self) -> int:
        out = cuvis_il.new_p_int()
        cuvis_il.cuvis_measurement_get_data_count(self._handle, out)
        return cuvis_il.p_int_value(out)

    def clear_cube(self) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_measurement_clear_cube(
                self._handle):
            raise SDKException()
        pass

    def clear_implicit_reference(self, ref_type: ReferenceType) -> None:
        if cuvis_il.status_ok != \
                cuvis_il.cuvis_measurement_clear_implicit_reference(
                    self._handle, internal.__CuvisReferenceType__[ref_type]):
            raise SDKException()

    def deepcopy(self):
        _ptr = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_measurement_deep_copy(
                self._handle, _ptr):
            raise SDKException()
        copy = Measurement(cuvis_il.p_int_value(_ptr))
        return copy

    def __del__(self):
        _ptr = cuvis_il.new_p_int()
        self.clear_cube()
        cuvis_il.p_int_assign(_ptr, self._handle)
        cuvis_il.cuvis_measurement_free(_ptr)
        self._handle = cuvis_il.p_int_value(_ptr)
        pass
