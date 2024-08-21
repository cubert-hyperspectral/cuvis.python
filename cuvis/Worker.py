from ._cuvis_il import cuvis_il
from .Measurement import Measurement
from .Viewer import Viewer, ImageData
from .cuvis_aux import SDKException, WorkerState
from .AcquisitionContext import AcquisitionContext
from .ProcessingContext import ProcessingContext
from .Export import Exporter
from .SessionFile import SessionFile
from .Measurement import Measurement
from .FileWriteSettings import WorkerSettings

import asyncio as a

from dataclasses import dataclass
from typing import Callable, Awaitable, Tuple


@dataclass
class WorkerResult:
    mesu: Measurement
    view: ImageData


class Worker(object):
    def __init__(self, args: WorkerSettings):
        self._exporter_set = False
        self._acquisition_set = False
        self._processing_set = False
        self._viewer_set = False
        self._session_file_set = False

        self._worker_poll_task = None

        self._handle = None
        _ptr = cuvis_il.new_p_int()
        settings = args._get_internal()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_create(_ptr, settings):
            raise SDKException()
        self._handle = cuvis_il.p_int_value(_ptr)
        pass

    def set_acquisition_context(self, base: AcquisitionContext = None) -> None:
        if base is not None:
            if cuvis_il.status_ok != cuvis_il.cuvis_worker_set_acq_cont(
                    self._handle, base._handle):
                raise SDKException()
            self._acquisition_set = True
        else:
            if cuvis_il.status_ok != cuvis_il.cuvis_worker_set_acq_cont(
                    self._handle, 0):
                raise SDKException()
            self._acquisition_set = False
        pass

    def set_processing_context(self, base: ProcessingContext = None) -> None:
        if base is not None:
            if cuvis_il.status_ok != cuvis_il.cuvis_worker_set_proc_cont(
                    self._handle, base._handle):
                raise SDKException()
            self._processing_set = True
        else:
            if cuvis_il.status_ok != cuvis_il.cuvis_worker_set_proc_cont(
                    self._handle, 0):
                raise SDKException()
            self._processing_set = False
        pass

    def set_exporter(self, base: Exporter = None) -> None:
        if base is not None:
            if cuvis_il.status_ok != cuvis_il.cuvis_worker_set_exporter(
                    self._handle, base._handle):
                raise SDKException()
            self._exporter_set = True
        else:
            if cuvis_il.status_ok != cuvis_il.cuvis_worker_set_exporter(
                    self._handle, 0):
                raise SDKException()
            self._exporter_set = False
        pass

    def set_viewer(self, base: Viewer = None) -> None:
        if base is not None:
            if cuvis_il.status_ok != cuvis_il.cuvis_worker_set_viewer(
                    self._handle, base._handle):
                raise SDKException()
            self._viewer_set = True
        else:
            if cuvis_il.status_ok != cuvis_il.cuvis_worker_set_viewer(
                    self._handle, 0):
                raise SDKException()
            self._viewer_set = False
        pass

    def ingest_session_file(self, session: SessionFile, frame_selection: str = 'all') -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_set_session_file(
                self._handle, session._handle, frame_selection):
            raise SDKException()

    def ingest_mesu(self, mesu: Measurement) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_ingest_mesu(
                self._handle, mesu):
            raise SDKException()
        pass

    def query_session_progress(self) -> float:
        val = cuvis_il.new_p_double()
        if cuvis_il.status_ok != \
                cuvis_il.cuvis_worker_query_session_progress(self._handle,
                                                             val):
            raise SDKException()
        return val

    def has_next_result(self) -> bool:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_has_next_result(
                self._handle, val):
            raise SDKException()
        return cuvis_il.p_int_value(val) != 0

    def get_next_result(self, timeout) -> WorkerResult:
        this_mesu = cuvis_il.new_p_int()
        this_viewer = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_next_result(
                self._handle, this_mesu, this_viewer, timeout):
            raise SDKException()
        mesu = Measurement(cuvis_il.p_int_value(this_mesu))
        if self._viewer_set:
            view = Viewer(cuvis_il.p_int_value(this_viewer)).apply(this_mesu)
        else:
            view = None
        return WorkerResult(mesu, view)
        # return mesu

    async def get_next_result_async(self, timeout: int) -> WorkerResult:
        poll_intervall = 100
        this_mesu = cuvis_il.new_p_int()
        this_viewer = cuvis_il.new_p_int()

        tries = 0
        while tries * poll_intervall < timeout:
            if self.has_next_result():
                await a.sleep(0)
                if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_next_result(
                        self._handle, this_mesu, this_viewer, 100):
                    raise SDKException()
                break
            else:
                tries += 1
                await a.sleep(poll_intervall / 1000)
        mesu = Measurement(cuvis_il.p_int_value(this_mesu))
        if self._viewer_set:
            view = Viewer(cuvis_il.p_int_value(this_viewer)).apply(this_mesu)
        else:
            view = None
        return WorkerResult(mesu, view)

    @property
    def input_queue_limit(self) -> int:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_input_queue_limit(
                self._handle, val):
            raise SDKException()
        return bool(cuvis_il.p_int_value(val))

    @property
    def mandatory_queue_limit(self) -> int:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_mandatory_queue_limit(
                self._handle, val):
            raise SDKException()
        return bool(cuvis_il.p_int_value(val))

    @property
    def supplementary_queue_limit(self) -> int:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_supplementary_queue_limit(
                self._handle, val):
            raise SDKException()
        return bool(cuvis_il.p_int_value(val))

    @property
    def output_queue_limit(self) -> int:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_output_queue_limit(
                self._handle, val):
            raise SDKException()
        return bool(cuvis_il.p_int_value(val))

    @property
    def queue_used(self) -> int:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_queue_used(
                self._handle, val):
            raise SDKException()
        return bool(cuvis_il.p_int_value(val))

    @property
    def can_drop_results(self) -> bool:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_can_drop_results(
                self._handle, val):
            raise SDKException()
        return bool(cuvis_il.p_int_value(val))

    @property
    def can_skip_measurements(self) -> bool:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_can_skip_measurements(
                self._handle, val):
            raise SDKException()
        return bool(cuvis_il.p_int_value(val))

    @property
    def can_skip_supplementary(self) -> bool:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_can_skip_supplementary(
                self._handle, val):
            raise SDKException()
        return bool(cuvis_il.p_int_value(val))

    @property
    def is_processing_mandatory(self) -> bool:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_is_processing_mandatory(
                self._handle, val):
            raise SDKException()
        return bool(cuvis_il.p_int_value(val))

    @property
    def is_processing(self) -> bool:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_is_processing(
                self._handle, val):
            raise SDKException()
        return bool(cuvis_il.p_int_value(val))

    @property
    def threads_busy(self) -> int:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_threads_busy(
                self._handle, val):
            raise SDKException()
        return cuvis_il.p_int_value(val)

    @property
    def state(self) -> WorkerState:
        val = cuvis_il.cuvis_worker_state_t()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_state(
                self._handle, val):
            raise SDKException()
        return WorkerState._from_internal(val)

    def register_worker_callback(self, callback: Callable[[WorkerResult], Awaitable[None]]) -> None:
        self.reset_worker_callback()
        poll_time = 0.001

        async def _internal_worker_loop():
            while True:
                if self.has_next_result():
                    workerContainer = await self.get_next_result_async(1000)
                    task = a.create_task(callback(workerContainer))

                    # TODO limit number of created task objects like in the cpp wrapper
                else:
                    await a.sleep(poll_time)

        self._worker_poll_task = a.create_task(_internal_worker_loop())

    def reset_worker_callback(self) -> None:
        if self._worker_poll_task is not None:
            self._worker_poll_task.cancel()
            self._worker_poll_task = None

    def __del__(self):
        self.reset_worker_callback()
        _ptr = cuvis_il.new_p_int()
        cuvis_il.p_int_assign(_ptr, self._handle)
        cuvis_il.cuvis_worker_free(_ptr)
        self._handle = cuvis_il.p_int_value(_ptr)
