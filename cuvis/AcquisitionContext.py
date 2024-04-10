try:
    from cuvis_il import cuvis_il
except:
    import cuvis_il
from .Async import Async, AsyncMesu
from .Calibration import Calibration
from .General import ComponentInfo
from .Measurement import Measurement
from .SessionFile import SessionFile
from .cuvis_aux import SDKException, SessionData
from .cuvis_types import HardwareState, OperationMode

from typing import Coroutine, Callable, Awaitable, Union, Iterable
from .doc import copydoc

import cuvis.cuvis_types as internal

import asyncio as a

class AcquisitionContext(object):
    def __init__(self, base: Union[Calibration, SessionFile], *, simulate: bool = False):
        self._handle = None
        self._simulate = simulate
        self._state_poll_task = None

        if isinstance(base, Calibration):
            _ptr = cuvis_il.new_p_int()
            if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_create_from_calib(
                    base._handle, _ptr):
                raise SDKException()
            self._handle = cuvis_il.p_int_value(_ptr)
        elif isinstance(base, SessionFile):
            _ptr = cuvis_il.new_p_int()
            if cuvis_il.status_ok != \
                    cuvis_il.cuvis_acq_cont_create_from_session_file(
                        base._handle, int(self._simulate), _ptr):
                raise SDKException()
            self._handle = cuvis_il.p_int_value(_ptr)
        else:
            raise SDKException(
                "Could not interpret input of type {}.".format(type(base)))
        pass


    @property
    @copydoc(cuvis_il.cuvis_acq_cont_get_state)
    def state(self) -> HardwareState:
        val = cuvis_il.new_p_cuvis_hardware_state_t()
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_get_state(
                self._handle, val):
            raise SDKException()
        return internal.__HardwareState__[ cuvis_il.p_cuvis_hardware_state_t_value(val)]


    @property
    @copydoc(cuvis_il.cuvis_acq_cont_get_component_count)
    def component_count(self) -> int:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_get_component_count(
                self._handle, val):
            raise SDKException()
        return cuvis_il.p_int_value(val)

    @copydoc(cuvis_il.cuvis_comp_online_get)
    def _get_component_online(self, idref: int) -> bool:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_comp_online_get(
                self._handle,idref, val):
            raise SDKException()
        return bool(cuvis_il.p_int_value(val))

    @copydoc(cuvis_il.cuvis_acq_cont_get_component_info)
    def _get_component_info(self, idref: int) -> ComponentInfo:
        ci = cuvis_il.cuvis_component_info_t()
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_get_component_info(
                self._handle, idref, ci):
            raise SDKException()
        return ComponentInfo._from_internal(ci)
    

    @property
    @copydoc(cuvis_il.cuvis_acq_cont_queue_size_get)
    def queue_size(self) -> int:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_queue_size_get(
                self._handle, val):
            raise SDKException()
        return cuvis_il.p_int_value(val)

    @queue_size.setter
    @copydoc(cuvis_il.cuvis_acq_cont_queue_size_set)
    def queue_size(self, val: int) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_queue_size_set(
                self._handle, val):
            raise SDKException()
        pass

    @copydoc(cuvis_il.cuvis_comp_gain_get)
    def _get_gain(self, idref: int) -> float:
        val = cuvis_il.new_p_double()
        if cuvis_il.status_ok != cuvis_il.cuvis_comp_gain_get(self._handle,
                                                              idref, val):
            raise SDKException()
        return cuvis_il.p_double_value(val)

    @copydoc(cuvis_il.cuvis_comp_gain_set)
    def _set_gain(self, idref: int, val: float) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_comp_gain_set(self._handle,
                                                              idref, float(val)):
            raise SDKException()
        pass

    @copydoc(cuvis_il.cuvis_comp_gain_set_async)
    def _set_gain_async(self, idref: int, val: float) -> Async:
        _pAsync = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_comp_gain_set_async(
                self._handle, idref, _pAsync, val):
            raise SDKException()
        return Async(cuvis_il.p_int_value(_pAsync))

    @property
    @copydoc(cuvis_il.cuvis_acq_cont_operation_mode_get)
    def operation_mode(self) -> OperationMode:
        val = cuvis_il.new_p_cuvis_operation_mode_t()
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_operation_mode_get(
                self._handle, val):
            raise SDKException()
        return  internal.__OperationMode__[cuvis_il.p_cuvis_operation_mode_t_value(val)]

    @operation_mode.setter
    @copydoc(cuvis_il.cuvis_acq_cont_operation_mode_set)
    def operation_mode(self, val: OperationMode) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_operation_mode_set(
                self._handle, internal.__CuvisOperationMode__[val]):
            raise SDKException()
        pass

    @copydoc(cuvis_il.cuvis_acq_cont_operation_mode_set_async)
    def set_operation_mode_async(self, val: OperationMode) -> Async:
        _pAsync = cuvis_il.new_p_int()
        if cuvis_il.status_ok != \
                cuvis_il.cuvis_acq_cont_operation_mode_set_async(
                    self._handle, _pAsync,
                    internal.__CuvisOperationMode__[val]):
            raise SDKException()
        return Async(cuvis_il.p_int_value(_pAsync))

    @property
    @copydoc(cuvis_il.cuvis_acq_cont_integration_time_get)
    def integration_time(self) -> float:
        val = cuvis_il.new_p_double()
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_integration_time_get(
                self._handle, val):
            raise SDKException()
        return cuvis_il.p_double_value(val)

    @integration_time.setter
    @copydoc(cuvis_il.cuvis_acq_cont_integration_time_set)
    def integration_time(self, val: float) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_integration_time_set(
                self._handle, float(val)):
            raise SDKException()
        pass

    @copydoc(cuvis_il.cuvis_acq_cont_integration_time_set_async)
    def set_integration_time_async(self, val: float) -> Async:
        _pAsync = cuvis_il.new_p_int()
        if cuvis_il.status_ok != \
                cuvis_il.cuvis_acq_cont_integration_time_set_async(
                    self._handle, _pAsync, float(val)):
            raise SDKException()
        return Async(cuvis_il.p_int_value(_pAsync))

    @copydoc(cuvis_il.cuvis_comp_integration_time_factor_get)
    def _get_integration_time_factor(self, idref: int) -> float:
        val = cuvis_il.new_p_double()
        if cuvis_il.status_ok != \
                cuvis_il.cuvis_comp_integration_time_factor_get(
                    self._handle, idref, val):
            raise SDKException()
        return cuvis_il.p_double_value(val)

    @copydoc(cuvis_il.cuvis_comp_integration_time_factor_set)
    def _set_integration_time_factor(self, idref: int, val: float) -> None:
        if cuvis_il.status_ok != \
                cuvis_il.cuvis_comp_integration_time_factor_set(
                    self._handle, idref, float(val)):
            raise SDKException()
        pass

    @copydoc(cuvis_il.cuvis_comp_integration_time_factor_set_async)
    def _set_integration_time_factor_async(self, idref: int, val: float) -> Async:
        _pasync = cuvis_il.new_p_int()
        if cuvis_il.status_ok != \
                cuvis_il.cuvis_comp_integration_time_factor_set_async(
                    self._handle, idref, _pasync, float(val)):
            raise SDKException()
        return Async(cuvis_il.p_int_value(_pasync))

    @copydoc(cuvis_il.cuvis_acq_cont_capture_async)
    def capture(self) -> AsyncMesu:
        _pasync = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_capture_async(
                self._handle, _pasync):
            raise SDKException()
        return AsyncMesu(cuvis_il.p_int_value(_pasync))

    @copydoc(cuvis_il.cuvis_acq_cont_capture)
    def capture_at(self, timeout_ms: int) -> Measurement:
        this_mesu = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_capture(
                self._handle, this_mesu, timeout_ms):
            raise SDKException()
        return Measurement(cuvis_il.p_int_value(this_mesu))

    @property
    @copydoc(cuvis_il.cuvis_acq_cont_fps_get)
    def fps(self) -> float:
        val = cuvis_il.new_p_double()
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_fps_get(
                self._handle, val):
            raise SDKException()
        return cuvis_il.p_double_value(val)

    @fps.setter
    @copydoc(cuvis_il.cuvis_acq_cont_fps_set)
    def fps(self, val: float) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_fps_set(
                self._handle, float(val)):
            raise SDKException()
        pass

    @copydoc(cuvis_il.cuvis_acq_cont_fps_set_async)
    def set_fps_async(self, val: float) -> Async:
        _pasync = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_fps_set_async(
                self._handle, _pasync, float(val)):
            raise SDKException()
        return Async(cuvis_il.p_int_value(_pasync))

    @copydoc(cuvis_il.cuvis_acq_cont_has_next_measurement)
    def has_next_measurement(self) -> bool:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_has_next_measurement(
                self._handle, val):
            raise SDKException()
        return cuvis_il.p_int_value(val) != 0

    @copydoc(cuvis_il.cuvis_acq_cont_get_next_measurement)
    def get_next_measurement(self, timeout_ms: int) -> Measurement:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_get_next_measurement(
                self._handle, val, timeout_ms):
            raise SDKException()
        return Measurement(cuvis_il.p_int_value(val))

    @property
    @copydoc(cuvis_il.cuvis_acq_cont_get_session_info)
    def session_info(self) -> SessionData:
        session = cuvis_il.cuvis_session_info_t()
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_get_session_info(
                self._handle, session):
            raise SDKException()
        return SessionData(session.name,
                           session.session_no,
                           session.sequence_no)

    @session_info.setter
    @copydoc(cuvis_il.cuvis_acq_cont_set_session_info)
    def session_info(self, val: SessionData) -> None:
        session = cuvis_il.cuvis_session_info_t()
        try:
            session.name = val.name
            session.sequence_no = val.sequence_number
            session.session_no = val.session_number
        except KeyError as e:
            raise ValueError(
                "Missing {} in SessionFile Info dictionary.".format(e))
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_set_session_info(
                self._handle, session):
            raise SDKException()
        pass

    @property
    @copydoc(cuvis_il.cuvis_acq_cont_queue_used_get)
    def queue_used(self) -> int:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_queue_used_get(
                self._handle, val):
            raise SDKException()
        return cuvis_il.p_int_value(val)

    @copydoc(cuvis_il.cuvis_comp_driver_queue_used_get)
    def _get_driver_queue_used(self, idref: int) -> int:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_comp_driver_queue_used_get(
                self._handle, idref, val):
            raise SDKException()
        return cuvis_il.p_int_value(val)

    @copydoc(cuvis_il.cuvis_comp_hardware_queue_used_get)
    def _get_hardware_queue_used(self, idref: int) -> int:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_comp_hardware_queue_used_get(
                self._handle, idref, val):
            raise SDKException()
        return cuvis_il.p_int_value(val)

    @copydoc(cuvis_il.cuvis_comp_driver_queue_size_get)
    def _get_driver_queue_size(self, idref: int) -> int:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_comp_driver_queue_size_get(
                self._handle, idref, val):
            raise SDKException()
        return cuvis_il.p_int_value(val)

    @copydoc(cuvis_il.cuvis_comp_hardware_queue_size_get)
    def _get_hardware_queue_size(self, idref: int) -> int:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_comp_hardware_queue_size_get(
                self._handle, val, idref):
            raise SDKException()
        return cuvis_il.p_int_value(val)

    @copydoc(cuvis_il.cuvis_comp_temperature_get)
    def _get_temperature(self, idref: int) -> float:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_comp_temperature_get(
                self._handle, idref, val):
            raise SDKException()
        return cuvis_il.p_int_value(val)

    @property
    @copydoc(cuvis_il.cuvis_acq_cont_average_get)
    def average(self) -> int:
        val = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_average_get(
                self._handle, val):
            raise SDKException()
        return cuvis_il.p_int_value(val)

    @average.setter
    @copydoc(cuvis_il.cuvis_acq_cont_average_set)
    def average(self, avg: int) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_average_set(
                self._handle, avg):
            raise SDKException()
        pass

    @copydoc(cuvis_il.cuvis_acq_cont_average_set_async)
    def set_average_async(self, avg: int) -> Async:
        _pasync = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_average_set_async(
                self._handle, _pasync, avg):
            raise SDKException()
        return Async(cuvis_il.p_int_value(_pasync))

    @copydoc(cuvis_il.cuvis_acq_cont_continuous_set)
    def set_continuous(self, val: bool) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_continuous_set(
                self._handle, int(val)):
            raise SDKException()
        pass

    @copydoc(cuvis_il.cuvis_acq_cont_continuous_set_async)
    def set_continuous_async(self, val: bool) -> Async:
        _pasync = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_continuous_set_async(
                self._handle, _pasync, int(val)):
            raise SDKException()
        return Async(cuvis_il.p_int_value(_pasync))

    @property
    @copydoc(cuvis_il.cuvis_acq_cont_bandwidth_get)
    def bandwidth(self) -> int:
        _ptr = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_bandwidth_get(
                self._handle, _ptr):
            raise SDKException()
        return cuvis_il.p_int_value(_ptr)

    @property
    @copydoc(cuvis_il.cuvis_acq_cont_auto_exp_get)
    def auto_exp(self) -> bool :
        _ptr = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_auto_exp_get(
                self._handle, _ptr):
            raise SDKException()
        return bool(cuvis_il.p_int_value(_ptr))

    @auto_exp.setter
    @copydoc(cuvis_il.cuvis_acq_cont_auto_exp_set)
    def auto_exp(self, val: bool) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_auto_exp_set(
                self._handle, int(val)):
            raise SDKException()
        pass

    @copydoc(cuvis_il.cuvis_acq_cont_auto_exp_set_async)
    def set_auto_exp_async(self, val: bool) -> Async:
        _pasync = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_auto_exp_set_async(
                self._handle, _pasync, int(val)):
            raise SDKException()
        return Async(cuvis_il.p_int_value(_pasync))
    
    @property
    @copydoc(cuvis_il.cuvis_acq_cont_auto_exp_comp_get)
    def auto_exp_comp(self) -> float :
        _ptr = cuvis_il.new_p_double()
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_auto_exp_comp_get(
                self._handle, _ptr):
            raise SDKException()
        return bool(cuvis_il.p_double_value(_ptr))

    @auto_exp_comp.setter
    @copydoc(cuvis_il.cuvis_acq_cont_auto_exp_comp_set)
    def auto_exp_comp(self, val: float) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_auto_exp_comp_set(
                self._handle, float(val)):
            raise SDKException()
        pass

    @copydoc(cuvis_il.cuvis_acq_cont_auto_exp_comp_set_async)
    def set_auto_exp_comp_async(self, val: float) -> Async:
        _pasync = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_auto_exp_comp_set_async(
                self._handle, _pasync, float(val)):
            raise SDKException()
        return Async(cuvis_il.p_int_value(_pasync))

    @property
    @copydoc(cuvis_il.cuvis_acq_cont_preview_mode_get)
    def preview_mode(self) -> bool:
        _ptr = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_preview_mode_get(
                self._handle, _ptr):
            raise SDKException()
        return bool(cuvis_il.p_int_value(_ptr))

    @preview_mode.setter
    @copydoc(cuvis_il.cuvis_acq_cont_preview_mode_set)
    def preview_mode(self, val: bool) -> None:
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_preview_mode_set(
                self._handle, val):
            raise SDKException()
        return

    @copydoc(cuvis_il.cuvis_acq_cont_preview_mode_set_async)
    def set_preview_mode_async(self, val: bool) -> Async:
        _pasync = cuvis_il.new_p_int()
        if cuvis_il.status_ok != cuvis_il.cuvis_acq_cont_preview_mode_set_async(
                self._handle, _pasync, int(val)):
            raise SDKException()
        return Async(cuvis_il.p_int_value(_pasync))
    
    def register_state_change_callback(self, callback: Callable[[HardwareState, list[tuple[str,bool]]], Awaitable[None]]) -> None:
        """

        """
        self.reset_state_change_callback()
        
        async def _internal_state_loop():
                poll_time = 0.5
                last_state = HardwareState.Offline
                last_component_states = [(cmp.info.display_name, False)  
                             for cmp in self.components()]
                first_pending = True
                while True:
                    state_changed = first_pending
                    first_pending = False

                    current_state = self.state
                    if last_state != current_state:
                        state_changed = True
                        last_state = current_state
                    for i, cmp in enumerate(self.components()):
                        comp_state = cmp.online()
                        last_comp_state = last_component_states[i][1]

                        if comp_state != last_comp_state:
                            state_changed = True
                            last_component_states[i] = last_component_states[i][0] , comp_state

                    if state_changed:
                        await callback(last_state, last_component_states)
                    else:
                        await a.sleep(poll_time)

        self._state_poll_task = a.create_task(_internal_state_loop())

    def reset_state_change_callback(self) -> None:
        """

        """
        if self._state_poll_task is not None:
            self._state_poll_task.cancel()
            self._state_poll_task = None




        

    def components(self):
        """
        Returns an iterator over all components
        """
        for i in range(0, self.component_count):
            yield Component(self,i)
        pass

    def __del__(self):
        _ptr = cuvis_il.new_p_int()
        cuvis_il.p_int_assign(_ptr, self._handle)
        cuvis_il.cuvis_acq_cont_free(_ptr)
        self._handle = cuvis_il.p_int_value(_ptr)


class Component:
    """

    """
    def __init__(self, acq: AcquisitionContext, idx: int):
        self._acq = acq
        self._idx = idx
        self.info = acq._get_component_info(idx)

    @property
    @copydoc(cuvis_il.cuvis_comp_online_get)
    def online(self) -> bool:
        return self._acq._get_component_online(self._idx)
    
    @property
    @copydoc(cuvis_il.cuvis_comp_temperature_get)
    def temperature(self) -> float:
        return self._acq._get_temperature(self._idx)
    
    @property
    @copydoc(cuvis_il.cuvis_comp_gain_get)
    def gain(self) -> float:
        return self._acq._get_gain(self._idx)
    
    @gain.setter
    @copydoc(cuvis_il.cuvis_comp_gain_set)
    def gain(self, val: float) -> None:
        return self._acq._set_gain(self._idx, val)
    
    @property
    @copydoc(cuvis_il.cuvis_comp_integration_time_factor_get)
    def integration_time_factor(self) -> float:
        return self._acq._get_integration_time_factor(self._idx)
    
    @integration_time_factor.setter
    @copydoc(cuvis_il.cuvis_comp_integration_time_factor_set)
    def integration_time_factor(self, val: float) -> None:
        return self._acq._set_integration_time_factor(self._idx, val)
    