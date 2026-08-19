from ._cuvis_il import cuvis_il
from .Measurement import Measurement
from .cuvis_aux import SDKException
from .cuvis_types import AsyncResult

import asyncio as a

from datetime import timedelta


def _to_ms(value: int | timedelta) -> int:
    if isinstance(value, timedelta):
        return int(value / timedelta(milliseconds=1))
    elif isinstance(value, int):
        return value
    else:
        raise SDKException("Unknown type for converting to ms")


# The SDK's own waits take a timeout in ms and treat 0 as "wait for ever".
_WAIT_FOREVER = 0


async def _wait_off_the_loop(blocking_get):
    """Run one of the SDK's blocking waits in a worker thread.

    The wrappers release the GIL for the duration of the call, so the thread parks in the
    SDK and the event loop keeps running. This is what makes the awaitables below real:
    they resume when the SDK is done, not when the next poll happens to come round.

    The cost is one pooled thread per outstanding wait, and a wait that never completes
    cannot be cancelled, because a thread blocked in C is not interruptible. Both go away
    only if the SDK hands out something the event loop can watch directly.
    """
    loop = a.get_running_loop()
    return await loop.run_in_executor(None, blocking_get, _WAIT_FOREVER)


class AsyncMesu(object):
    def __init__(self, handle):
        self._handle = handle

    pass

    def get(
        self, timeout_ms: int | timedelta
    ) -> tuple[Measurement | None, AsyncResult]:
        _ptr = cuvis_il.new_p_int()
        _pmesu = cuvis_il.new_p_int()
        cuvis_il.p_int_assign(_ptr, self._handle)
        res = cuvis_il.cuvis_async_capture_get(_ptr, _to_ms(timeout_ms), _pmesu)

        if res == cuvis_il.status_ok:
            return Measurement(cuvis_il.p_int_value(_pmesu)), AsyncResult.done
        elif res == cuvis_il.status_deferred:
            return None, AsyncResult.deferred
        elif res == cuvis_il.status_overwritten:
            return None, AsyncResult.overwritten
        elif res == cuvis_il.status_timeout:
            return None, AsyncResult.timeout
        else:
            raise SDKException()

    # Python Magic Methods

    def __await__(self) -> Measurement | None:
        async def _wait_for_return():
            mesu, _ = await _wait_off_the_loop(self.get)
            return mesu

        return _wait_for_return().__await__()

    def __del__(self):
        if self._handle is None:
            return
        _ptr = cuvis_il.new_p_int()
        cuvis_il.p_int_assign(_ptr, self._handle)
        cuvis_il.cuvis_async_capture_free(_ptr)
        self._handle = cuvis_il.p_int_value(_ptr)

    def __deepcopy__(self, memo):
        """This functions is not permitted due to the class only keeping a handle, that is managed by the cuvis sdk."""
        raise TypeError("Deep copying is not supported for AsyncMesu")

    def __copy__(self):
        """This functions is not permitted due to the class only keeping a handle, that is managed by the cuvis sdk."""
        raise TypeError("Shallow copying is not supported for AsyncMesu")


class Async(object):
    def __init__(self, handle):
        self._handle = handle

    def get(self, timeout_ms: int | timedelta) -> AsyncResult:
        _ptr = cuvis_il.new_p_int()
        cuvis_il.p_int_assign(_ptr, self._handle)
        res = cuvis_il.cuvis_async_call_get(_ptr, _to_ms(timeout_ms))

        if res == cuvis_il.status_ok:
            return AsyncResult.done
        elif res == cuvis_il.status_deferred:
            return AsyncResult.deferred
        elif res == cuvis_il.status_overwritten:
            return AsyncResult.overwritten
        elif res == cuvis_il.status_timeout:
            return AsyncResult.timeout
        else:
            raise SDKException()
        pass

    # Python Magic Methods

    def __await__(self) -> AsyncResult:
        return _wait_off_the_loop(self.get).__await__()

    def __del__(self):
        if self._handle is None:
            return
        _ptr = cuvis_il.new_p_int()
        cuvis_il.p_int_assign(_ptr, self._handle)
        cuvis_il.cuvis_async_call_free(_ptr)
        self._handle = cuvis_il.p_int_value(_ptr)

    def __deepcopy__(self, memo):
        """This functions is not permitted due to the class only keeping a handle, that is managed by the cuvis sdk."""
        raise TypeError("Deep copying is not supported for Async")

    def __copy__(self):
        """This functions is not permitted due to the class only keeping a handle, that is managed by the cuvis sdk."""
        raise TypeError("Shallow copying is not supported for Async")
