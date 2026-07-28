"""Opt-in CUDA support for cuvis.

CUDA is off by default. Reach it explicitly:

    from cuvis import cuda

    caps = cuda.capabilities()          # inspect what this binary + environment support
    if caps.same_process:
        cuda.enable()                   # BEFORE loading/processing measurements
        ...
        t = mesu.get_cube().to_torch()  # zero-copy device tensor (DLPack, lifecycle-managed)

`enable()` also disables the host auto-refresh (`Measurement._refresh_images = False`) so a
GPU-processed cube stays on the device instead of being copied to host and freed.

Note: the shipped cuvis binding links the CUDA runtime, so `import cuvis` already requires a
CUDA runtime to be present. This module gates the CUDA *feature surface* and the optional
`torch` / `cuda-python` consumer dependencies, not the binding's own runtime dependency.
"""
import importlib.util
from typing import NamedTuple

from cuvis_il import cuvis_il

from .cube_utils import CudaImageData  # re-exported; the device-image type

# Backend codes (match cuvis.h CUVIS_CUDA_IPC_BACKEND_*).
_BACKEND_NONE = 0
_BACKEND_POOL = 1
_BACKEND_LEGACY = 2
_BACKEND_VMM = 3

_enabled = False


class CudaCapabilities(NamedTuple):
    """What the loaded cuvis binary and the current Python environment support.

    same_process: the CUDA boundary responds (same-process device sharing works).
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


def _backend_available(code: int) -> bool:
    try:
        p = cuvis_il.new_p_int()
        if cuvis_il.cuvis_cuda_ipc_backend_available(code, p) != cuvis_il.status_ok:
            return False
        return bool(cuvis_il.p_int_value(p))
    except Exception:
        # Symbol absent or a CUDA-less binary: treat as unavailable.
        return False


def capabilities() -> CudaCapabilities:
    """Probe CUDA capabilities at runtime. Safe to call before enable()."""
    return CudaCapabilities(
        same_process=_backend_available(_BACKEND_NONE),
        ipc_pool=_backend_available(_BACKEND_POOL),
        ipc_legacy=_backend_available(_BACKEND_LEGACY),
        ipc_vmm=_backend_available(_BACKEND_VMM),
        torch=importlib.util.find_spec("torch") is not None,
        cuda_python=importlib.util.find_spec("cuda.bindings") is not None,
    )


def enable() -> None:
    """Turn on CUDA mode. Call this BEFORE loading or processing measurements.

    Routes `Measurement.get_cube()` through the device path and disables the host
    auto-refresh so the GPU cube is kept on the device. Raises RuntimeError if this
    cuvis build has no CUDA support.
    """
    global _enabled
    if not capabilities().same_process:
        raise RuntimeError("this cuvis build has no CUDA support")
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


__all__ = ["CudaCapabilities", "capabilities", "enable", "disable", "is_enabled", "CudaImageData"]
