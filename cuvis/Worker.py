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
from .doc import copydoc

from dataclasses import dataclass
from typing import Callable, Awaitable


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

    @copydoc(cuvis_il.cuvis_worker_set_acq_cont)
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

    @copydoc(cuvis_il.cuvis_worker_set_proc_cont)
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

    @copydoc(cuvis_il.cuvis_worker_set_exporter)
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

    @copydoc(cuvis_il.cuvis_worker_set_viewer)
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

    @copydoc(cuvis_il.cuvis_worker_ingest_session_file)
    def ingest_session_file(self, session: SessionFile, frame_selection: str = 'all') -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_ingest_session_file(
                self._handle, session._handle, frame_selection):
            raise SDKException()

    @copydoc(cuvis_il.cuvis_worker_ingest_mesu)
    def ingest_mesu(self, mesu: Measurement) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_ingest_mesu(
                self._handle, mesu._handle):
            raise SDKException()
        pass

    @property
    @copydoc(cuvis_il.cuvis_worker_query_session_progress)
    def query_session_progress(self) -> float:
        val = cuvis_il.new_p_double()
        if cuvis_il.status_ok != \
                cuvis_il.cuvis_worker_query_session_progress(self._handle,
                                                             val):
            raise SDKException()
        return cuvis_il.p_double_value(val)

    @copydoc(cuvis_il.cuvis_worker_has_next_result)
    def has_next_result(self) -> bool:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_has_next_result(
                self._handle, val):
            raise SDKException()
        return cuvis_il.p_int_value(val) != 0

    @copydoc(cuvis_il.cuvis_worker_get_next_result)
    def get_next_result(self, timeout) -> WorkerResult:
        ptr_mesu = cuvis_il.new_p_int()
        ptr_view = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_next_result(
                self._handle, ptr_mesu, ptr_view, timeout):
            raise SDKException()
        mesu = Measurement(cuvis_il.p_int_value(ptr_mesu))
        if self._viewer_set:
            view = Viewer._create_view_data(None, cuvis_il.p_int_value(ptr_view))
        else:
            view = None
        return WorkerResult(mesu, view)

    async def get_next_result_async(self, timeout: int) -> WorkerResult:
        poll_intervall = 100
        ptr_mesu = cuvis_il.new_p_int()
        ptr_view = cuvis_il.new_p_int()

        tries = 0
        while tries * poll_intervall < timeout:
            if self.has_next_result():
                await a.sleep(0)
                if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_next_result(
                        self._handle, ptr_mesu, ptr_view, 100):
                    raise SDKException()
                break
            else:
                tries += 1
                await a.sleep(poll_intervall / 1000)
        mesu = Measurement(cuvis_il.p_int_value(ptr_mesu))
        if self._viewer_set:
            view = Viewer._create_view_data(None, cuvis_il.p_int_value(ptr_view))
        else:
            view = None
        return WorkerResult(mesu, view)

    @property
    @copydoc(cuvis_il.cuvis_worker_get_input_queue_limit)
    def input_queue_limit(self) -> int:
        val = cuvis_il.new_p_ulong()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_input_queue_limit(
                self._handle, val):
            raise SDKException()
        return cuvis_il.p_ulong_value(val)

    @property
    @copydoc(cuvis_il.cuvis_worker_get_mandatory_queue_limit)
    def mandatory_queue_limit(self) -> int:
        val = cuvis_il.new_p_ulong()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_mandatory_queue_limit(
                self._handle, val):
            raise SDKException()
        return cuvis_il.p_ulong_value(val)

    @property
    @copydoc(cuvis_il.cuvis_worker_get_supplementary_queue_limit)
    def supplementary_queue_limit(self) -> int:
        val = cuvis_il.new_p_ulong()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_supplementary_queue_limit(
                self._handle, val):
            raise SDKException()
        return cuvis_il.p_ulong_value(val)

    @property
    @copydoc(cuvis_il.cuvis_worker_get_output_queue_limit)
    def output_queue_limit(self) -> int:
        val = cuvis_il.new_p_ulong()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_output_queue_limit(
                self._handle, val):
            raise SDKException()
        return cuvis_il.p_ulong_value(val)

    @property
    @copydoc(cuvis_il.cuvis_worker_get_queue_used)
    def queue_used(self) -> int:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_queue_used(
                self._handle, val):
            raise SDKException()
        return cuvis_il.p_int_value(val)

    @property
    @copydoc(cuvis_il.cuvis_worker_get_can_drop_results)
    def can_drop_results(self) -> bool:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_can_drop_results(
                self._handle, val):
            raise SDKException()
        return bool(cuvis_il.p_int_value(val))

    @property
    @copydoc(cuvis_il.cuvis_worker_get_can_skip_measurements)
    def can_skip_measurements(self) -> bool:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_can_skip_measurements(
                self._handle, val):
            raise SDKException()
        return bool(cuvis_il.p_int_value(val))

    @property
    @copydoc(cuvis_il.cuvis_worker_get_can_skip_supplementary)
    def can_skip_supplementary(self) -> bool:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_can_skip_supplementary(
                self._handle, val):
            raise SDKException()
        return bool(cuvis_il.p_int_value(val))

    @property
    @copydoc(cuvis_il.cuvis_worker_is_processing_mandatory)
    def is_processing_mandatory(self) -> bool:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_is_processing_mandatory(
                self._handle, val):
            raise SDKException()
        return bool(cuvis_il.p_int_value(val))

    @property
    @copydoc(cuvis_il.cuvis_worker_is_processing)
    def is_processing(self) -> bool:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_is_processing(
                self._handle, val):
            raise SDKException()
        return bool(cuvis_il.p_int_value(val))

    @property
    @copydoc(cuvis_il.cuvis_worker_get_threads_busy)
    def threads_busy(self) -> int:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_threads_busy(
                self._handle, val):
            raise SDKException()
        return cuvis_il.p_int_value(val)

    @property
    @copydoc(cuvis_il.cuvis_worker_get_state)
    def state(self) -> WorkerState:
        val = cuvis_il.cuvis_worker_state_t()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_state(
                self._handle, val):
            raise SDKException()
        return WorkerState._from_internal(val)

    @copydoc(cuvis_il.cuvis_worker_start)
    def start_processing(self) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_start(
                self._handle):
            raise SDKException()

    @copydoc(cuvis_il.cuvis_worker_stop)
    def stop_processing(self) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_stop(
                self._handle):
            raise SDKException()

    @copydoc(cuvis_il.cuvis_worker_drop_all_queued)
    def drop_all_queued(self) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_drop_all_queued(
                self._handle):
            raise SDKException()

    def register_worker_callback(self, callback: Callable[[WorkerResult], Awaitable[None]]) -> None:
        self.reset_worker_callback()
        poll_time = 0.001

        async def _internal_worker_loop():
            while True:
                if self.has_next_result():
                    try:
                        workerContainer = await self.get_next_result_async(1000)
                        task = a.create_task(callback(workerContainer))
                    except (Exception, SDKException):
                        pass
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

    def __deepcopy__(self, memo):
        '''This functions is not permitted due to the class only keeping a handle, that is managed by the cuvis sdk.'''
        raise TypeError('Deep copying is not supported for Worker')

    def __copy__(self):
        '''This functions is not permitted due to the class only keeping a handle, that is managed by the cuvis sdk.'''
        raise TypeError('Shallow copying is not supported for Worker')
