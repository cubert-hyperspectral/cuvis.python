from ._cuvis_il import cuvis_il
from .Measurement import Measurement
from .cuvis_aux import SDKException
from .cuvis_types import AsyncResult

import asyncio as a

from typing import Optional, Union
from datetime import timedelta


def _to_ms(value: Union[int, timedelta]) -> int:
    if isinstance(value, timedelta):
        return int(value / timedelta(milliseconds=1))
    elif isinstance(value, int):
        return value
    else:
        raise SDKException('Unknown type for converting to ms')


class AsyncMesu(object):
    def __init__(self, handle):
        self._handle = handle

    pass

    def get(self, timeout_ms: Union[int, timedelta]) -> tuple[Optional[Measurement], AsyncResult]:
        """

        """
        _ptr = cuvis_il.new_p_int()
        _pmesu = cuvis_il.new_p_int()
        cuvis_il.p_int_assign(_ptr, self._handle)
        res = cuvis_il.cuvis_async_capture_get(
            _ptr, _to_ms(timeout_ms), _pmesu)

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

    def __await__(self) -> Optional[Measurement]:
        async def _wait_for_return():
            _status_ptr = cuvis_il.new_p_cuvis_status_t()
            while True:
                if cuvis_il.status_ok != cuvis_il.cuvis_async_capture_status(self._handle, _status_ptr):
                    raise SDKException()
                status = cuvis_il.p_cuvis_status_t_value(_status_ptr)
                if status == cuvis_il.status_ok:
                    return self.get(0)[0]
                else:
                    await a.sleep(10.0 / 1000)
        return _wait_for_return().__await__()

    def __del__(self):
        _ptr = cuvis_il.new_p_int()
        cuvis_il.p_int_assign(_ptr, self._handle)
        cuvis_il.cuvis_async_capture_free(_ptr)
        self._handle = cuvis_il.p_int_value(_ptr)

    def __deepcopy__(self, memo):
        '''This functions is not permitted due to the class only keeping a handle, that is managed by the cuvis sdk.'''
        raise TypeError('Deep copying is not supported for AsyncMesu')

    def __copy__(self):
        '''This functions is not permitted due to the class only keeping a handle, that is managed by the cuvis sdk.'''
        raise TypeError(
            'Shallow copying is not supported for AsyncMesu')


class Async(object):
    def __init__(self, handle):
        self._handle = handle

    def get(self, timeout_ms: Union[int, timedelta]) -> AsyncResult:
        """

        """
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
        async def _wait_for_return():
            _status_ptr = cuvis_il.new_p_cuvis_status_t()
            while True:
                if cuvis_il.status_ok != cuvis_il.cuvis_async_call_status(self._handle, _status_ptr):
                    raise SDKException()
                status = cuvis_il.p_cuvis_status_t_value(_status_ptr)
                if status == cuvis_il.status_ok:
                    return self.get(0)
                else:
                    await a.sleep(10.0 / 1000)
        return _wait_for_return().__await__()

    def __del__(self):
        _ptr = cuvis_il.new_p_int()
        cuvis_il.p_int_assign(_ptr, self._handle)
        cuvis_il.cuvis_async_call_free(_ptr)
        self._handle = cuvis_il.p_int_value(_ptr)

    def __deepcopy__(self, memo):
        '''This functions is not permitted due to the class only keeping a handle, that is managed by the cuvis sdk.'''
        raise TypeError('Deep copying is not supported for Async')

    def __copy__(self):
        '''This functions is not permitted due to the class only keeping a handle, that is managed by the cuvis sdk.'''
        raise TypeError(
            'Shallow copying is not supported for Async')
