"""
Tests for cuvis.cuda capability reporting.

The assertions hold whether or not the installed cuvis library provides the CUDA
functions, since CI and developer machines differ on that. What is pinned is that
capabilities() answers rather than raises, and that an unavailable function is
reported by name instead of surfacing as an AttributeError from the binding.
"""

import pytest

import cuvis
from cuvis import binding, cuda

_HAS_DEVICE = binding.available(cuda.BACKEND_PROBE, *cuda.DEVICE_FUNCTIONS)


def test_capabilities_answers_without_raising():
    """Test capabilities() reports booleans instead of raising on a CUDA-less SDK."""
    caps = cuda.capabilities()
    assert isinstance(caps, cuda.CudaCapabilities)
    assert all(isinstance(value, bool) for value in caps)
    assert isinstance(caps.any_ipc, bool)


def test_capabilities_is_safe_before_init():
    """Test capabilities() needs no initialised SDK, so a caller can gate on it first."""
    assert cuda.capabilities() == cuda.capabilities()


def test_cuda_mode_is_off_by_default():
    """Test CUDA stays opt-in, leaving the host refresh path in place."""
    assert cuda.is_enabled() is False
    assert cuvis.Measurement._refresh_images is True


def test_disable_restores_the_host_refresh():
    """Test disable() is safe to call unconditionally and restores the host path."""
    cuda.disable()
    assert cuda.is_enabled() is False
    assert cuvis.Measurement._refresh_images is True


@pytest.mark.skipif(_HAS_DEVICE, reason="this SDK provides the CUDA functions")
def test_capabilities_are_false_without_the_sdk_functions():
    """Test a library lacking the CUDA functions reports no CUDA support."""
    caps = cuda.capabilities()
    assert caps.same_process is False
    assert caps.any_ipc is False


@pytest.mark.skipif(_HAS_DEVICE, reason="this SDK provides the CUDA functions")
@pytest.mark.parametrize("guard", [cuda.require_device, cuda.require_ipc, cuda.enable])
def test_missing_functions_are_reported_by_name(guard):
    """Test the CUDA entry points name what the SDK lacks (see cuvis.binding)."""
    with pytest.raises(cuvis.UnavailableSDKFunction) as excinfo:
        guard()
    assert excinfo.value.names
    assert all(name in str(excinfo.value) for name in excinfo.value.names)
    assert cuda.is_enabled() is False


@pytest.mark.skipif(_HAS_DEVICE, reason="this SDK provides the CUDA functions")
def test_get_cube_cuda_reports_the_missing_functions(test_measurement):
    """Test the device path fails with the diagnostic, not an AttributeError."""
    with pytest.raises(cuvis.UnavailableSDKFunction):
        test_measurement.get_cube_cuda()


def test_unavailable_function_is_catchable_either_way():
    """Test UnavailableSDKFunction satisfies both except clauses it advertises."""
    for expected in (RuntimeError, cuvis.cuvis_aux.SDKException):
        with pytest.raises(expected):
            binding.require("cuvis_a_function_that_does_not_exist")
