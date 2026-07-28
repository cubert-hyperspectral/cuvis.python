"""cuvis Python SDK.

The SDK surface (Measurement, ProcessingContext, init, ...) loads lazily on first access,
so `import cuvis` has no side effects and does not load the native binding. This lets the
import-safe `cuvis.ipc` cross-process consumer utilities be used in a process that never
initialized the SDK (no CUVIS env var, no cuvis.dll). The binding and its CUVIS/DLL setup
load only when an SDK symbol is actually used, via cuvis_il's own __init__.
"""

import importlib

# Public name -> submodule that defines it. Loaded lazily via __getattr__ so that merely
# importing `cuvis` (or `cuvis.ipc`) never pulls in the CUDA-linked binding.
_LAZY = {
    # cuvis_aux
    "SessionData": "cuvis_aux",
    "Capabilities": "cuvis_aux",
    "MeasurementFlags": "cuvis_aux",
    "SensorInfo": "cuvis_aux",
    "GPSData": "cuvis_aux",
    "CalibrationInfo": "cuvis_aux",
    # cuvis_types
    "OperationMode": "cuvis_types",
    "HardwareState": "cuvis_types",
    "ProcessingMode": "cuvis_types",
    "PanSharpeningInterpolationType": "cuvis_types",
    "PanSharpeningAlgorithm": "cuvis_types",
    "TiffCompressionMode": "cuvis_types",
    "TiffFormat": "cuvis_types",
    "ComponentType": "cuvis_types",
    "ReferenceType": "cuvis_types",
    "SessionItemType": "cuvis_types",
    "SessionMergeMode": "cuvis_types",
    # core
    "Worker": "Worker",
    "WorkerResult": "Worker",
    "Viewer": "Viewer",
    "SessionFile": "SessionFile",
    "ProcessingContext": "ProcessingContext",
    "Measurement": "Measurement",
    "init": "General",
    "shutdown": "General",
    "version": "General",
    "set_log_level": "General",
    # FileWriteSettings
    "GeneralExportSettings": "FileWriteSettings",
    "SaveArgs": "FileWriteSettings",
    "ProcessingArgs": "FileWriteSettings",
    "EnviExportSettings": "FileWriteSettings",
    "TiffExportSettings": "FileWriteSettings",
    "ViewExportSettings": "FileWriteSettings",
    "WorkerSettings": "FileWriteSettings",
    "ViewerSettings": "FileWriteSettings",
    # Export
    "CubeExporter": "Export",
    "EnviExporter": "Export",
    "TiffExporter": "Export",
    "ViewExporter": "Export",
    # binding
    "BindingInfo": "binding",
    "UnavailableSDKFunction": "binding",
    # misc
    "Calibration": "Calibration",
    "AcquisitionContext": "AcquisitionContext",
    "SdkSettings": "sdk_settings",
    "ImageData": "cube_utils",
    "CudaImageData": "cube_utils",
}

# Submodules reachable as attributes. `ipc` is import-safe without the SDK; `binding` and
# `cuda` answer what the installed SDK provides and so must be reachable before init().
_SUBMODULES = ("ipc", "cuda", "binding")

__all__ = list(_LAZY) + list(_SUBMODULES)


def __getattr__(name):
    """PEP 562 lazy attribute loader - imports the owning submodule on first access."""
    if name in _LAZY:
        return getattr(importlib.import_module("." + _LAZY[name], __name__), name)
    if name in _SUBMODULES:
        return importlib.import_module("." + name, __name__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(list(globals()) + __all__)
