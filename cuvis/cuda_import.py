"""Deprecated: use cuvis.ipc instead.

Kept as a thin shim for back-compat. `open_ipc(descriptor)` maps a raw descriptor (you supply
geometry via .tensor(dtype, shape)); the preferred path is a bundled payload via
cuvis.ipc.open(payload). See cuvis/ipc.py.
"""
from .ipc import ImportedCube as ImportedIpcTensor  # noqa: F401  (back-compat name)
from .ipc import open_descriptor, BACKEND_NONE, BACKEND_POOL, BACKEND_LEGACY, BACKEND_VMM  # noqa: F401


def open_ipc(descriptor_bytes) -> ImportedIpcTensor:
    """Deprecated alias of cuvis.ipc.open_descriptor()."""
    return open_descriptor(descriptor_bytes)


__all__ = ["ImportedIpcTensor", "open_ipc", "BACKEND_NONE", "BACKEND_POOL",
           "BACKEND_LEGACY", "BACKEND_VMM"]
