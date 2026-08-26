"""Minimal DLPack producer over a raw CUDA device pointer.

Builds a DLManagedTensor PyCapsule via ctypes so torch.from_dlpack can consume a
foreign device buffer zero-copy. The capsule deleter calls a supplied on_delete
callback when torch releases the tensor, which is how buffer lifetime is tied to
the tensor (the callback drops the SDK reference that pins the buffer).

Ported from utils_data_cuda/examples/torch_local.py; the only change is that the
deleter calls an injected callback instead of a hard-coded ctypes SDK.
"""

import ctypes

_kDLCUDA = 2
_kDLInt = 0
_kDLUInt = 1
_kDLFloat = 2


class _DLDevice(ctypes.Structure):
    _fields_ = [("device_type", ctypes.c_int), ("device_id", ctypes.c_int)]


class _DLDataType(ctypes.Structure):
    _fields_ = [
        ("code", ctypes.c_uint8),
        ("bits", ctypes.c_uint8),
        ("lanes", ctypes.c_uint16),
    ]


class _DLTensor(ctypes.Structure):
    _fields_ = [
        ("data", ctypes.c_void_p),
        ("device", _DLDevice),
        ("ndim", ctypes.c_int),
        ("dtype", _DLDataType),
        ("shape", ctypes.POINTER(ctypes.c_int64)),
        ("strides", ctypes.POINTER(ctypes.c_int64)),
        ("byte_offset", ctypes.c_uint64),
    ]


class _DLManagedTensor(ctypes.Structure):
    pass


_DELETER = ctypes.CFUNCTYPE(None, ctypes.POINTER(_DLManagedTensor))
_DLManagedTensor._fields_ = [
    ("dl_tensor", _DLTensor),
    ("manager_ctx", ctypes.c_void_p),
    ("deleter", _DELETER),
]

_pycapsule_new = ctypes.pythonapi.PyCapsule_New
_pycapsule_new.restype = ctypes.py_object
_pycapsule_new.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p]

# Keep ctypes structs / deleters / callbacks alive until torch invokes the deleter.
_LIVE = {}


class CudaDlpack:
    """DLPack producer over (ptr, nbytes) on a CUDA device. on_delete() runs when
    torch releases the tensor. Exposes a flat uint8 buffer; reshape/retype in torch."""

    def __init__(self, ptr, nbytes, device, on_delete):
        self._ptr = int(ptr)
        self._n = int(nbytes)
        self._dev = int(device)
        self._on_delete = on_delete

    def __dlpack_device__(self):
        return (_kDLCUDA, self._dev)

    def __dlpack__(self, stream=None, max_version=None, dl_device=None, copy=None):
        shape = (ctypes.c_int64 * 1)(self._n)
        mt = _DLManagedTensor()
        mt.dl_tensor.data = ctypes.c_void_p(self._ptr)
        mt.dl_tensor.device = _DLDevice(_kDLCUDA, self._dev)
        mt.dl_tensor.ndim = 1
        mt.dl_tensor.dtype = _DLDataType(_kDLUInt, 8, 1)
        mt.dl_tensor.shape = shape
        mt.dl_tensor.strides = None
        mt.dl_tensor.byte_offset = 0

        on_delete = self._on_delete
        key = id(mt)

        def _del(_p):
            try:
                on_delete()
            finally:
                _LIVE.pop(key, None)

        deleter = _DELETER(_del)
        mt.deleter = deleter
        _LIVE[key] = (mt, shape, deleter)
        return _pycapsule_new(ctypes.byref(mt), b"dltensor", None)


def make_cuda_dlpack(ptr, nbytes, device, on_delete):
    """Return an object that torch.from_dlpack consumes into a zero-copy CUDA tensor."""
    return CudaDlpack(ptr, nbytes, device, on_delete)
