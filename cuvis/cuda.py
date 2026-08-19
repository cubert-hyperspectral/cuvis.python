"""Opt-in CUDA support for cuvis.

CUDA is off by default. Reach it explicitly:

    from cuvis import cuda

    caps = cuda.capabilities()          # what this SDK, this device and this env support
    if caps.same_process:
        cuda.enable()                   # BEFORE loading/processing measurements
        ...
        t = mesu.get_cube().to_torch()  # zero-copy device tensor (DLPack, lifecycle-managed)

`enable()` also disables the host auto-refresh (`Measurement._refresh_images = False`) so a
GPU-processed cube stays on the device instead of being copied to host and freed.

Three unrelated things can each deny CUDA, and they are answered separately rather than
collapsed into one boolean: the installed cuvis library may not provide the functions, which
`cuvis.binding` reports without calling anything; the device or driver may not support a
backend, which only the SDK can answer; and the optional consumer packages may be absent.
Keeping them apart is what lets `enable()` say which of the three went wrong.
"""

import importlib.util
from typing import NamedTuple

from . import binding
from ._cuvis_il import cuvis_il

# Backend codes, matching CUVIS_CUDA_IPC_BACKEND_* in cuvis.h. BACKEND_NONE doubles as the
# same-process probe and as "auto" where an export picks a backend itself.
BACKEND_NONE = 0
BACKEND_POOL = 1
BACKEND_LEGACY = 2
BACKEND_VMM = 3

# Functions the same-process device path calls, as named in cuvis.h. BACKEND_PROBE answers
# for a backend and so gates every capability query, including same_process.
BACKEND_PROBE = "cuvis_cuda_ipc_backend_available"
DEVICE_FUNCTIONS = (
    "cuvis_measurement_get_data_image_cuda",
    "cuvis_cuda_mem_get_view",
    "cuvis_cuda_mem_copy_handle",
    "cuvis_cuda_mem_free",
)

# Needed on top of those to export a device buffer to another process.
IPC_FUNCTIONS = (
    "cuvis_cuda_ipc_handle_create",
    "cuvis_cuda_ipc_get_descriptor",
    "cuvis_cuda_ipc_handle_free",
)

_enabled = False


class CudaCapabilities(NamedTuple):
    """What the installed cuvis library, the current device and this environment support.

    same_process: the CUDA boundary responds, so same-process device sharing works.
    ipc_pool: exportable memory pool backend (zero-copy cross-process, needs an exportable pool).
    ipc_legacy: legacy cudaIpc backend (copy-on-export; available on most WDDM/Linux GPUs).
    ipc_vmm: driver-API VMM backend (copy-on-export, with an exportable handle type).
    torch / cuda_python: optional consumer packages importable (checked, not imported).
    """

    same_process: bool
    ipc_pool: bool
    ipc_legacy: bool
    ipc_vmm: bool
    torch: bool
    cuda_python: bool

    @property
    def any_ipc(self) -> bool:
        return self.ipc_pool or self.ipc_legacy or self.ipc_vmm


def _installed(package: str) -> bool:
    """Whether an optional consumer package is installed, without importing it.

    find_spec imports parent packages to reach a submodule, and cuvis puts its own
    directory on sys.path, so probing `cuda.bindings` can resolve `cuda` to this very
    module whenever cuda-python is absent. A probe that cannot resolve is an answer:
    the package is not installed.
    """
    try:
        return importlib.util.find_spec(package) is not None
    except (ImportError, ValueError):
        return False


def _backend_supported(code: int) -> bool:
    """Ask the SDK whether this device and driver support one backend.

    Reached only once the function is known to exist, so a false answer here is the SDK's
    verdict on the hardware rather than a missing symbol wearing the same disguise.
    """
    out = cuvis_il.new_p_int()
    if cuvis_il.status_ok != cuvis_il.cuvis_cuda_ipc_backend_available(code, out):
        return False
    return bool(cuvis_il.p_int_value(out))


def capabilities() -> CudaCapabilities:
    """Probe what is supported, here and now. Safe to call before init() or enable()."""
    device = binding.available(BACKEND_PROBE, *DEVICE_FUNCTIONS)
    ipc = device and binding.available(*IPC_FUNCTIONS)
    return CudaCapabilities(
        same_process=device and _backend_supported(BACKEND_NONE),
        ipc_pool=ipc and _backend_supported(BACKEND_POOL),
        ipc_legacy=ipc and _backend_supported(BACKEND_LEGACY),
        ipc_vmm=ipc and _backend_supported(BACKEND_VMM),
        torch=_installed("torch"),
        cuda_python=_installed("cuda.bindings"),
    )


def require_device() -> None:
    """Raise unless the installed cuvis library provides the same-process device path.

    Guards the entry points so a library without CUDA fails by naming the functions it
    lacks, rather than as an AttributeError from deep inside the binding.

    :raises cuvis.UnavailableSDKFunction: naming the functions that are unavailable.
    """
    binding.require(*DEVICE_FUNCTIONS)


def require_ipc() -> None:
    """Raise unless the installed cuvis library provides the cross-process export path.

    :raises cuvis.UnavailableSDKFunction: naming the functions that are unavailable.
    """
    binding.require(*DEVICE_FUNCTIONS, *IPC_FUNCTIONS)


def enable() -> None:
    """Turn on CUDA mode. Call this BEFORE loading or processing measurements.

    Routes `Measurement.get_cube()` through the device path and disables the host
    auto-refresh so the GPU cube is kept on the device.

    :raises cuvis.UnavailableSDKFunction: the installed cuvis library does not provide the
        CUDA functions; the message names them and both library versions.
    :raises RuntimeError: the library provides them, but this device or driver reports no
        CUDA support.
    """
    global _enabled
    binding.require(BACKEND_PROBE, *DEVICE_FUNCTIONS)
    if not _backend_supported(BACKEND_NONE):
        raise RuntimeError(
            "the installed CUVIS SDK provides the CUDA functions, but this device "
            "reports no CUDA support\n{}".format(binding.info())
        )
    from .Measurement import Measurement

    Measurement._refresh_images = False
    _enabled = True


def disable() -> None:
    """Turn off CUDA mode and restore the host auto-refresh."""
    global _enabled
    from .Measurement import Measurement

    Measurement._refresh_images = True
    _enabled = False


def is_enabled() -> bool:
    return _enabled


__all__ = [
    "CudaCapabilities",
    "capabilities",
    "require_device",
    "require_ipc",
    "enable",
    "disable",
    "is_enabled",
    "BACKEND_NONE",
    "BACKEND_POOL",
    "BACKEND_LEGACY",
    "BACKEND_VMM",
]
