from . import cuvis_il
from .Measurement import Measurement
from .Viewer import Viewer, ImageData
from .cuvis_aux import SDKException
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

    def set_acquisition_context(self, base: AcquisitionContext=None) -> None:
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

    def set_processing_context(self, base: ProcessingContext=None) -> None:
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

    def set_exporter(self, base: Exporter=None) -> None:
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

    def set_viewer(self, base: Viewer=None) -> None:
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

    def set_session_file(self, base: SessionFile=None, skipDroppedFrames: bool=True) -> None:
        if base is not None:
            if cuvis_il.status_ok != cuvis_il.cuvis_worker_set_session_file(
                    self._handle, skipDroppedFrames, base._handle):
                raise SDKException()
            self._session_file_set = True
        else:
            if cuvis_il.status_ok != cuvis_il.cuvis_worker_set_session_file(
                    self._handle, skipDroppedFrames, 0):
                raise SDKException()
            self._session_file_set = False
        pass

    def ingest_mesu(self, mesu: Measurement) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_ingest_mesu(
                self._handle, mesu):
            raise SDKException()
        pass

    def query_session_progress(self):
        frames_read = cuvis_il.new_p_int()
        frames_total = cuvis_il.new_p_int()
        if cuvis_il.status_ok != \
                cuvis_il.cuvis_worker_query_session_progress(self._handle,
                                                             frames_read,
                                                             frames_total):
            raise SDKException()
        return {"frames_read": cuvis_il.p_int_value(frames_read), "frames_total":  cuvis_il.p_int_value(frames_total)}


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
    def queue_limits(self) -> Tuple[int,int]:
        val_hard = cuvis_il.new_p_int()
        val_soft = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_queue_limits(
                self._handle, val_hard, val_soft):
            raise SDKException()
        return (cuvis_il.p_int_value(val_hard), cuvis_il.p_int_value(val_soft))


    @queue_limits.setter
    def queue_limits(self, val: Tuple[int,int] ) -> None:
        hard_limit, soft_limit = val
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_set_queue_limits(
                self._handle, hard_limit, soft_limit):
            raise SDKException()
        pass

    @property
    def queue_used(self) -> int:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_queue_used(
                self._handle, val):
            raise SDKException()
        return cuvis_il.p_int_value(val)
    
    @property
    def drop_behaviour(self) -> bool:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_get_drop_behavior(
                self._handle, val):
            raise SDKException()
        return bool(cuvis_il.p_int_value(val))

    @drop_behaviour.setter
    def drop_behaviour(self, can_drop: bool) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_worker_set_drop_behavior(
                self._handle, can_drop):
            raise SDKException()
        pass


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
