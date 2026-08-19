from .FileWriteSettings import SaveArgs
import datetime
from pathlib import Path

from ._cuvis_il import cuvis_il
from .cuvis_aux import (
    SDKException,
    SessionData,
    Capabilities,
    MeasurementFlags,
    SensorInfo,
    GPSData,
    _utc_from_epoch_ms,
)
from .cuvis_types import DataFormat, ProcessingMode, ReferenceType
from .cube_utils import ImageData, CudaImageData
from . import cuda


import cuvis.cuvis_types as internal


class Measurement(object):
    capture_time: datetime.datetime  # read-only
    measurement_flags: MeasurementFlags  # read-only
    path: str  # read-only
    comment: str
    factory_calibration: datetime.datetime | None  # read-only
    assembly: str  # read-only
    integration_time: int  # read-only
    averages: int  # read-only
    distance: float  # read-only
    serial_number: str  # read-only
    product_name: str  # read-only
    processing_mode: ProcessingMode  # read-only
    name: str
    session_info: SessionData  # read-only
    frame_id: int  # read-only

    # When False, refresh() skips fetching image data to the host via
    # cuvis_measurement_get_data_image. That host fetch moves a GPU-processed cube
    # into host memory and frees the device copy, which makes the same-process CUDA
    # path (get_cube_cuda) unavailable. Set False before processing when you intend
    # to read the cube as CUDA device memory. Default True preserves normal behaviour.
    _refresh_images = True

    def __init__(self, base: int | str | Path):
        self._handle = None
        self._session = None

        if isinstance(base, int):
            self._handle = base
        elif isinstance(base, str) or isinstance(base, Path):
            base = Path(base)
            if not base.exists():
                raise FileNotFoundError(
                    "Could not open Measurement. File does not exists."
                )

            _ptr = cuvis_il.new_p_int()
            if cuvis_il.status_ok != cuvis_il.cuvis_measurement_load(str(base), _ptr):
                raise SDKException()
            self._handle = cuvis_il.p_int_value(_ptr)
        else:
            raise ValueError("Could not open Measurement! Unknown Input")
        self.refresh()
        pass

    def _refresh_metadata(self):
        _metaData = cuvis_il.cuvis_mesu_metadata_allocate()
        if cuvis_il.status_ok != cuvis_il.cuvis_measurement_get_metadata(
            self._handle, _metaData
        ):
            raise SDKException

        self._capture_time = _utc_from_epoch_ms(_metaData.capture_time)
        self._measurement_flags = MeasurementFlags(_metaData.measurement_flags)
        self._path = _metaData.path
        self._comment = _metaData.comment
        try:
            self._factory_calibration = _utc_from_epoch_ms(
                _metaData.factory_calibration
            )
        except OverflowError:
            self._factory_calibration = None
        self._assembly = _metaData.assembly
        self._averages = _metaData.averages
        self._distance = _metaData.distance
        self._integration_time = _metaData.integration_time
        self._serial_number = _metaData.serial_number
        self._product_name = _metaData.product_name
        self._processing_mode = internal.__ProcessingMode__[_metaData.processing_mode]
        self._name = _metaData.name
        self._session_info = SessionData(
            _metaData.session_info_name,
            _metaData.session_info_session_no,
            _metaData.session_info_sequence_no,
        )
        self._frame_id = _metaData.measurement_frame_id
        cuvis_il.cuvis_mesu_metadata_free(_metaData)

    def refresh(self) -> None:
        self.data = {}
        self._refresh_metadata()
        pcount = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_measurement_get_data_count(
            self._handle, pcount
        ):
            raise SDKException()
        for ind in range(cuvis_il.p_int_value(pcount)):
            pType = cuvis_il.new_p_cuvis_data_type_t()
            key = cuvis_il.cuvis_measurement_get_data_info_swig(
                self._handle, pType, ind
            )
            cdtype = cuvis_il.p_cuvis_data_type_t_value(pType)
            if cdtype == cuvis_il.data_type_image:
                if not Measurement._refresh_images:
                    # Skip the host fetch so a GPU-processed cube stays in device
                    # memory and remains reachable via get_cube_cuda.
                    continue
                data = cuvis_il.cuvis_imbuffer_t()
                cuvis_il.cuvis_measurement_get_data_image(self._handle, key, data)
                # t0 = datetime.datetime.now()
                self.data.update(
                    {
                        key: ImageData(
                            img_buf=data,
                            dformat=DataFormat[data.__getattribute__("format")],
                        )
                    }
                )
                # print("image loading time: {}".format(
                # datetime.datetime.now() - t0))
            elif cdtype == cuvis_il.data_type_string:
                val = cuvis_il.cuvis_measurement_get_data_string_swig(self._handle, key)
                self.data.update({key: val})
            elif cdtype == cuvis_il.data_type_gps:
                gps = cuvis_il.cuvis_gps_t()
                cuvis_il.cuvis_measurement_get_data_gps(self._handle, key, gps)
                self.data.update({key: GPSData._from_internal(gps)})
            elif cdtype == cuvis_il.data_type_sensor_info:
                info = cuvis_il.cuvis_sensor_info_t()
                cuvis_il.cuvis_measurement_get_data_sensor_info(self._handle, key, info)
                self.data.update({key: SensorInfo._from_internal(info)})
            else:
                # The C API reports entries it cannot hand out with an empty key,
                # so they need a distinct one here or they overwrite each other.
                self.data.update(
                    {
                        key
                        or "unsupported_data_{}_{}".format(
                            cdtype, ind
                        ): "Not Implemented!"
                    }
                )

    def save(self, saveargs: SaveArgs) -> None:
        ge, sa = saveargs._get_internal()
        if cuvis_il.status_ok != cuvis_il.cuvis_measurement_save(
            self._handle, ge.export_dir, sa
        ):
            raise SDKException()
        pass

    @property
    def capture_time(self) -> datetime.datetime:
        """Timezone-aware UTC instant; comparing it against a naive datetime raises TypeError."""
        return self._capture_time

    @property
    def measurement_flags(self) -> MeasurementFlags:
        return self._measurement_flags

    @property
    def path(self) -> str:
        return self._path

    @property
    def comment(self) -> str:
        return self._comment

    @comment.setter
    def comment(self, comment: str) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_measurement_set_comment(
            self._handle, comment
        ):
            raise SDKException()
        self._refresh_metadata()
        pass

    @property
    def factory_calibration(self) -> datetime.datetime | None:
        """The calibration day, or None if the SDK reported a value datetime cannot hold.

        Timezone-aware UTC, but only the day carries meaning. The SDK stores the day as
        midnight in the local time of the machine that wrote the file, so the time
        component is an artifact of that machine and the day can be off by one when the
        file is read in another timezone.
        """
        return self._factory_calibration

    @property
    def assembly(self) -> str:
        return self._assembly

    @property
    def integration_time(self) -> int:
        return self._integration_time

    @property
    def averages(self) -> int:
        return self._averages

    @property
    def distance(self) -> float:
        return self._distance

    @property
    def serial_number(self) -> str:
        return self._serial_number

    @property
    def product_name(self) -> str:
        return self._product_name

    @property
    def processing_mode(self) -> ProcessingMode:
        return self._processing_mode

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_measurement_set_name(
            self._handle, name
        ):
            raise SDKException()
        self._refresh_metadata()
        pass

    @property
    def session_info(self) -> SessionData:
        return self._session_info

    @property
    def frame_id(self) -> int:
        return self._frame_id

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
        if "cube" in self.data:
            return self.data.get("cube")
        if self._session is not None:
            # try fallback if session is known
            if self._session._pc is None:
                from .ProcessingContext import ProcessingContext

                self._session._pc = ProcessingContext(self._session)
            self._session._pc.apply(self)
            return self.data.get("cube", None)
        raise ValueError(
            "This Measurement does not have a cube saved. Consider reprocessing with a Processing Context."
        )

    def get_cube_cuda(self, key: str = "cube") -> CudaImageData:
        """Image data as a device-resident CUDA buffer for same-process, zero-copy use.

        .. code-block:: python3

            from cuvis import cuda

            if cuda.capabilities().same_process:
                cuda.enable()                       # BEFORE loading or processing
                tensor = mesu.get_cube_cuda().to_torch()

        Returns a :class:`cuvis.CudaImageData` wrapping a CUVIS_CUDA_MEM handle; read it
        with ``.to_torch()`` (DLPack, which ties the buffer lifetime to the tensor) or
        through ``__cuda_array_interface__`` (which does not, so keep the CudaImageData
        alive). No host copy is made.

        The cube must still be on the device, which it is only when `cuda.enable` was
        called before it was processed; the host fetch in `refresh` otherwise moves it to
        host memory and frees the device copy.

        :param key: which image entry to read, `"cube"` unless the measurement carries
            several.
        :raises cuvis.UnavailableSDKFunction: the installed cuvis library provides no
            CUDA support; call `cuda.capabilities` first to avoid this.
        :raises cuvis.cuvis_aux.SDKException: the image data is not device-backed.
        """
        cuda.require_device()
        buf = cuvis_il.cuvis_cuda_imbuffer_t()
        if cuvis_il.status_ok != cuvis_il.cuvis_measurement_get_data_image_cuda(
            self._handle, key, buf
        ):
            raise SDKException()
        return CudaImageData(buf)

    def get_cube_cuda_ipc(self, key: str = "cube", backend: int = 0) -> CudaImageData:
        """Image data as a shareable CUDA buffer for cross-process use.

        Producer side; the consumer opens the payload with :mod:`cuvis_ipc`, which needs
        no SDK of its own.

        .. code-block:: python3

            cimg = mesu.get_cube_cuda_ipc()         # keep alive until the consumer is done
            send(cimg.export_payload())            # descriptor + geometry, one blob

            # ... in the consumer process, no cuvis installed ...
            import cuvis_ipc
            with cuvis_ipc.open(payload) as cube:
                tensor = cube.to_torch()

        Fetches the device buffer with `get_cube_cuda` and creates an IPC export on it,
        filling `.descriptor` with the transportable bytes. The returned object is the
        in-process pin, since legacy IPC carries no cross-process refcount: drop it and
        the consumer is reading freed device memory.

        :param key: which image entry to read.
        :param backend: which mechanism to export with, one of `cuvis.cuda.BACKEND_NONE`
            (auto), `BACKEND_POOL`, `BACKEND_LEGACY` or `BACKEND_VMM`. `cuda.capabilities`
            reports which of them this device supports.
        :raises cuvis.UnavailableSDKFunction: the installed cuvis library provides no
            CUDA IPC support.
        :raises cuvis.cuvis_aux.SDKException: the requested backend is unavailable on
            this device.
        """
        cimg = self.get_cube_cuda(key)
        cimg.make_ipc(backend)
        return cimg

    def get_cube(self, key: str = "cube") -> Union[ImageData, CudaImageData]:
        """Cube through whichever mode is active, so one call site serves both.

        .. code-block:: python3

            cube = mesu.get_cube()      # CudaImageData after cuda.enable(), else ImageData

        With CUDA mode on (`cuvis.cuda.enable`) this is `get_cube_cuda` and raises when
        the device path is unavailable. There is deliberately no silent fallback to the
        host: a zero-copy path that quietly degrades to two copies is worse than an error,
        because the cost is invisible.

        :param key: which image entry to read.
        :return: `CudaImageData` in CUDA mode, otherwise the host `ImageData`.
        """
        if cuda.is_enabled():
            return self.get_cube_cuda(key)
        return self.cube

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
            self._handle, _ptr
        ):
            raise SDKException()
        return Capabilities(cuvis_il.p_int_value(_ptr))

    @property
    def calibration_id(self) -> str:
        _id = cuvis_il.cuvis_measurement_get_calib_id_swig(self._handle)
        return _id

    @property
    def data_count(self) -> int:
        out = cuvis_il.new_p_int()
        cuvis_il.cuvis_measurement_get_data_count(self._handle, out)
        return cuvis_il.p_int_value(out)

    def clear_cube(self) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_measurement_clear_cube(self._handle):
            raise SDKException()
        pass

    def clear_implicit_reference(self, ref_type: ReferenceType) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_measurement_clear_implicit_reference(
            self._handle, internal.__CuvisReferenceType__[ref_type]
        ):
            raise SDKException()

    def deepcopy(self):
        _ptr = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_measurement_deep_copy(
            self._handle, _ptr
        ):
            raise SDKException()
        copy = Measurement(cuvis_il.p_int_value(_ptr))
        return copy

    def __del__(self):
        if self._handle is None:
            return
        _ptr = cuvis_il.new_p_int()
        self.clear_cube()
        cuvis_il.p_int_assign(_ptr, self._handle)
        cuvis_il.cuvis_measurement_free(_ptr)
        self._handle = cuvis_il.p_int_value(_ptr)
        pass

    def __deepcopy__(self, memo):
        return self.deepcopy()

    def __copy__(self, memo):
        """This functions is not permitted due to the class only keeping a handle, that is managed by the cuvis sdk."""
        raise TypeError("Shallow copying is not supported for Measurement")
