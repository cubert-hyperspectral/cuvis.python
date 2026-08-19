"""Import-safe cross-process CUDA IPC consumer utilities.

Use this in a SEPARATE process that receives a cuvis IPC payload - it does NOT initialize
or link the cuvis SDK. It needs only cuda-python (`cuda.bindings`) and torch, imported lazily.

It sits outside the `cuvis` package on purpose. Importing `cuvis` requires the SDK to be
installed and the CUVIS environment variable to be set, which a consumer process by
definition does not have; `import cuvis_ipc` needs neither, and the only import here is
`struct`.

Producer (in the cuvis process):
    cimg = mesu.get_cube_cuda_ipc()      # keep this alive until the consumer is done
    payload = cimg.export_payload()      # a single transportable bytes blob (descriptor + geometry)

Consumer (this module, any process):
    import cuvis_ipc
    with cuvis_ipc.open(payload) as cube:
        t = cube.to_torch()              # correctly shaped/typed zero-copy CUDA tensor
        ...                              # use t inside the block
    # leaving the block releases this process's mapping (does not free the exporter's memory)

The exporting process must outlive this importer: legacy IPC has no cross-process refcount.
"""

import struct

# --- IPC descriptor wire format (locked; mirrors cuvis_cuda_ipc_descriptor_t) ---
# 48-byte header + 64-byte blob (pool OS handle) at offset 48, then ptr_blob_len(+pad) and a
# 64-byte ptr_blob (cudaMemPoolPtrExportData) at offset 120. Total 184.
_HEAD = struct.Struct(
    "<iiiIQQQQ"
)  # backend, device, handle_type, blob_len, size, alloc_size, offset, pid
_BLOB_OFF = 48
_BLOB_MAX = 64
_PTR_LEN_OFF = 112  # uint32 ptr_blob_len (uint32 _pad follows at 116)
_PTR_BLOB_OFF = 120
_PTR_BLOB_MAX = 64
_DESC_LEN = 184

BACKEND_NONE, BACKEND_POOL, BACKEND_LEGACY, BACKEND_VMM = 0, 1, 2, 3
H_NONE, H_WIN32, H_WIN32_KMT, H_POSIX_FD = 0, 1, 2, 3

# --- bundled payload = magic + version + geometry + descriptor ---
_MAGIC = b"CVIP"
_VERSION = 1
_PAYLOAD_HDR = struct.Struct(
    "<4sIIIII"
)  # magic, version, width, height, channels, format_code

# format code -> torch dtype name / __cuda_array_interface__ typestr (1/2/3/4 = u8/u16/u32/f32)
_TORCH_DTYPE = {1: "uint8", 2: "uint16", 3: "uint32", 4: "float32"}
_TYPESTR = {1: "|u1", 2: "<u2", 3: "<u4", 4: "<f4"}


def pack_payload(
    descriptor: bytes, width: int, height: int, channels: int, format_code: int
) -> bytes:
    """Bundle an IPC descriptor and cube geometry into one transportable blob."""
    if len(descriptor) != _DESC_LEN:
        raise ValueError(f"descriptor must be {_DESC_LEN} bytes, got {len(descriptor)}")
    return _PAYLOAD_HDR.pack(
        _MAGIC, _VERSION, int(width), int(height), int(channels), int(format_code)
    ) + bytes(descriptor)


def _unpack_payload(payload: bytes):
    magic, version, width, height, channels, fmt = _PAYLOAD_HDR.unpack_from(payload, 0)
    if magic != _MAGIC:
        raise ValueError("not a cuvis IPC payload (bad magic)")
    if version != _VERSION:
        raise ValueError(f"unsupported cuvis IPC payload version {version}")
    descriptor = bytes(payload[_PAYLOAD_HDR.size :])
    return (width, height, channels, fmt), descriptor


def _ck(ret, what):
    err = ret[0]
    if int(err) != 0:
        raise RuntimeError(f"{what} failed: {err}")
    return ret[1:] if len(ret) > 1 else None


class _CudaArray:
    def __init__(self, ptr, nbytes):
        self.__cuda_array_interface__ = {
            "shape": (nbytes,),
            "typestr": "|u1",
            "data": (int(ptr), False),
            "version": 3,
        }


class ImportedCube:
    """A mapped IPC buffer in the consumer process. Use as a context manager.

    open()/open_descriptor() return this; leaving the `with` block releases the mapping.
    to_torch() (preferred) and __cuda_array_interface__ produce zero-copy views that are
    valid only while the block is open.
    """

    def __init__(self, descriptor_bytes: bytes, shape=None, format_code=None):
        (
            self.backend,
            self.device,
            self.htype,
            blob_len,
            self.size,
            self.alloc,
            self.offset,
            self.pid,
        ) = _HEAD.unpack_from(descriptor_bytes, 0)
        if blob_len > _BLOB_MAX:
            raise ValueError(f"blob_len {blob_len} exceeds {_BLOB_MAX}")
        self._blob = bytes(descriptor_bytes[_BLOB_OFF : _BLOB_OFF + blob_len])
        (ptr_blob_len,) = struct.unpack_from("<I", descriptor_bytes, _PTR_LEN_OFF)
        if ptr_blob_len > _PTR_BLOB_MAX:
            raise ValueError(f"ptr_blob_len {ptr_blob_len} exceeds {_PTR_BLOB_MAX}")
        self._ptr_blob = bytes(
            descriptor_bytes[_PTR_BLOB_OFF : _PTR_BLOB_OFF + ptr_blob_len]
        )
        self._shape = tuple(shape) if shape is not None else None
        self._format = format_code
        self._close = None

        from cuda.bindings import runtime

        runtime.cudaSetDevice(self.device)

        if self.backend == BACKEND_POOL:
            self._ptr, self._close = self._open_pool()
        elif self.backend == BACKEND_LEGACY:
            self._ptr, self._close = self._open_legacy()
        elif self.backend == BACKEND_VMM:
            self._ptr, self._close = self._open_vmm()
        else:
            raise NotImplementedError(
                f"backend {self.backend} is not importable cross-process"
            )
        self._ptr += (
            self.offset
        )  # 0 for pool/legacy/vmm (import returns the exact base pointer)

    @property
    def shape(self):
        return self._shape

    @property
    def device_ptr(self):
        return self._ptr

    def _open_pool(self):
        # IPC-capable memory pool: import the pool from its OS shareable handle, grant this
        # device access, then import the exact pointer from the per-allocation export data.
        from cuda.bindings import runtime

        if self.htype == H_WIN32_KMT:
            htype = runtime.cudaMemAllocationHandleType.cudaMemHandleTypeWin32Kmt
        elif self.htype == H_POSIX_FD:
            htype = (
                runtime.cudaMemAllocationHandleType.cudaMemHandleTypePosixFileDescriptor
            )
        else:
            raise NotImplementedError(
                f"pool handle_type {self.htype} needs out-of-band duplication (DuplicateHandle / SCM_RIGHTS)"
            )

        handle_val = int.from_bytes(self._blob, "little")
        (pool,) = _ck(
            runtime.cudaMemPoolImportFromShareableHandle(handle_val, htype, 0),
            "cudaMemPoolImportFromShareableHandle",
        )

        acc = runtime.cudaMemAccessDesc()
        acc.location.type = runtime.cudaMemLocationType.cudaMemLocationTypeDevice
        acc.location.id = self.device
        acc.flags = runtime.cudaMemAccessFlags.cudaMemAccessFlagsProtReadWrite
        _ck(runtime.cudaMemPoolSetAccess(pool, [acc], 1), "cudaMemPoolSetAccess")

        export_data = runtime.cudaMemPoolPtrExportData()
        export_data.reserved = self._ptr_blob.ljust(_PTR_BLOB_MAX, b"\x00")
        (ptr,) = _ck(
            runtime.cudaMemPoolImportPointer(pool, export_data),
            "cudaMemPoolImportPointer",
        )

        def close():
            runtime.cudaFree(ptr)  # release this process's imported pointer
            runtime.cudaMemPoolDestroy(pool)  # release the imported pool handle

        return int(ptr), close

    def _open_legacy(self):
        # Legacy cudaIpc: the descriptor blob is a self-contained 64-byte cudaIpcMemHandle_t.
        from cuda.bindings import runtime

        h = runtime.cudaIpcMemHandle_t()
        h.reserved = self._blob.ljust(_BLOB_MAX, b"\x00")
        (ptr,) = _ck(
            runtime.cudaIpcOpenMemHandle(h, runtime.cudaIpcMemLazyEnablePeerAccess),
            "cudaIpcOpenMemHandle",
        )

        def close():
            runtime.cudaIpcCloseMemHandle(
                ptr
            )  # release this process's mapping (not the exporter's)

        return int(ptr), close

    def _open_vmm(self):
        # VMM: import the generic handle from its OS shareable handle, reserve + map + grant access.
        from cuda.bindings import driver

        driver.cuInit(0)
        if self.htype == H_WIN32_KMT:
            htype = driver.CUmemAllocationHandleType.CU_MEM_HANDLE_TYPE_WIN32_KMT
        elif self.htype == H_POSIX_FD:
            htype = driver.CUmemAllocationHandleType.CU_MEM_HANDLE_TYPE_POSIX_FILE_DESCRIPTOR
        elif self.htype == H_WIN32:
            htype = driver.CUmemAllocationHandleType.CU_MEM_HANDLE_TYPE_WIN32
        else:
            raise NotImplementedError(f"vmm handle_type {self.htype} not supported")

        handle_val = int.from_bytes(self._blob, "little")
        (gen,) = _ck(
            driver.cuMemImportFromShareableHandle(handle_val, htype),
            "cuMemImportFromShareableHandle",
        )
        size = self.alloc
        (ptr,) = _ck(driver.cuMemAddressReserve(size, 0, 0, 0), "cuMemAddressReserve")
        _ck(driver.cuMemMap(ptr, size, 0, gen, 0), "cuMemMap")

        acc = driver.CUmemAccessDesc()
        acc.location.type = driver.CUmemLocationType.CU_MEM_LOCATION_TYPE_DEVICE
        acc.location.id = self.device
        acc.flags = driver.CUmemAccess_flags.CU_MEM_ACCESS_FLAGS_PROT_READWRITE
        _ck(driver.cuMemSetAccess(ptr, size, [acc], 1), "cuMemSetAccess")

        def close():
            driver.cuMemUnmap(ptr, size)
            driver.cuMemAddressFree(ptr, size)
            driver.cuMemRelease(gen)

        return int(ptr), close

    def _torch_dtype(self, torch):
        return (
            None if self._format is None else getattr(torch, _TORCH_DTYPE[self._format])
        )

    def to_torch(self, dtype=None, shape=None):
        """Zero-copy CUDA torch tensor over the mapped buffer, valid inside the with-block.

        With open(payload), dtype and shape are taken from the payload geometry; overrides
        may be passed explicitly (needed after open_descriptor without geometry)."""
        import torch

        n = self.size - self.offset
        t = torch.as_tensor(_CudaArray(self._ptr, n), device=f"cuda:{self.device}")
        dt = dtype if dtype is not None else self._torch_dtype(torch)
        if dt is not None and dt != torch.uint8:
            t = t.view(dt)
        sh = shape if shape is not None else self._shape
        if sh is not None:
            t = t.reshape(*sh)
        return t

    tensor = to_torch  # back-compat alias

    @property
    def __cuda_array_interface__(self):
        if self._shape is None or self._format is None:
            raise RuntimeError(
                "__cuda_array_interface__ needs geometry; open via open(payload) or use to_torch(dtype, shape)"
            )
        return {
            "shape": self._shape,
            "typestr": _TYPESTR[self._format],
            "data": (int(self._ptr), False),
            "version": 3,
        }

    def close(self):
        if self._close is not None:
            self._close()
            self._close = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def open(payload: bytes) -> ImportedCube:
    """Open a payload from CudaImageData.export_payload(): maps the buffer and carries geometry."""
    (width, height, channels, fmt), descriptor = _unpack_payload(payload)
    return ImportedCube(descriptor, shape=(height, width, channels), format_code=fmt)


def open_descriptor(descriptor_bytes: bytes, shape=None) -> ImportedCube:
    """Advanced: open a raw 184-byte descriptor when you transport geometry yourself.

    Pass shape here (or dtype/shape to .to_torch()); prefer open(payload) for the easy path."""
    return ImportedCube(descriptor_bytes, shape=shape)


__all__ = [
    "ImportedCube",
    "open",
    "open_descriptor",
    "pack_payload",
    "BACKEND_NONE",
    "BACKEND_POOL",
    "BACKEND_LEGACY",
    "BACKEND_VMM",
]
