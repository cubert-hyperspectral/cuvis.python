"""Adaptive smoke test for the CUDA IPC Python wrapping.

Run:
  set CUVIS=C:\\Program Files\\Cuvis\\bin
  set PYTHONPATH=C:\\dev\\cuvis_sdk\\cuvis.pyil;C:\\dev\\cuvis_sdk\\cuvis.python
  <venv>\\Scripts\\python.exe examples\\cuda_smoke.py

Tiers 1-3 need only the built binding. Tier 4 additionally needs a measurement whose
image data is CUDA-device-backed, and (for the tensor compare) torch.
"""

import struct
import sys

FAIL = []


def check(cond, msg):
    print(("  ok  " if cond else "  FAIL") + "  " + msg)
    if not cond:
        FAIL.append(msg)


# ---- Tier 1: the installed cuvis library provides the CUDA surface ----
# Asked through cuvis.binding rather than by probing cuvis_il attributes: a function can
# be absent because the binding never wrapped it, or because the loaded cuvis.dll does
# not export it, and binding.unavailable answers both at once. binding.info() names the
# two libraries, which is what tells a version mismatch from a missing feature.
print("[tier 1] SDK provides the CUDA functions")
from cuvis import binding, cuda
from cuvis_il import cuvis_il

print(binding.info())
absent = binding.unavailable(cuda.BACKEND_PROBE, *cuda.DEVICE_FUNCTIONS, *cuda.IPC_FUNCTIONS)
check(not absent, "every CUDA function is provided" + (f" (missing: {', '.join(absent)})" if absent else ""))

# SWIG helpers and structs are not cuvis.h functions, so the library cannot be asked
# about them; they either were compiled into the binding or were not.
for name in ("cuvis_cuda_view_ptr", "cuvis_cuda_descriptor_bytes",
             "cuvis_cuda_imbuffer_t", "cuvis_cuda_mem_view_t",
             "cuvis_cuda_ipc_descriptor_t"):
    check(hasattr(cuvis_il, name), f"cuvis_il.{name} compiled in")

if absent:
    print()
    print("Nothing further can run against this SDK. Stopping.")
    raise SystemExit(1)

# Removed in the Phase 16 API simplification - assert they are gone.
removed = [
    "cuvis_measurement_get_data_image_cuda_ipc",
    "cuvis_cuda_mem_ref",
    "cuvis_cuda_mem_export",
    "cuvis_cuda_mem_get_descriptor",
    "cuvis_cuda_ipc_export_free",
    "cuvis_cuda_mem_get_device_ptr",
    "cuvis_cuda_mem_get_device_ordinal",
    "cuvis_cuda_ipc_get_last_error_msg",
]
for name in removed:
    check(not hasattr(cuvis_il, name), f"cuvis_il.{name} removed")

# ---- Tier 2: what this device and driver actually support ----
print("[tier 2] device backends")
caps = cuda.capabilities()
check(caps.same_process, "same-process device sharing available")
for label, code in (("NONE", cuda.BACKEND_NONE), ("POOL", cuda.BACKEND_POOL),
                    ("LEGACY", cuda.BACKEND_LEGACY), ("VMM", cuda.BACKEND_VMM)):
    p = cuvis_il.new_p_int()
    st = cuvis_il.cuvis_cuda_ipc_backend_available(code, p)
    check(st == cuvis_il.status_ok, f"backend_available({label}) status ok")
    print(f"       backend {label}: available={cuvis_il.p_int_value(p)}")
print(f"       any cross-process backend: {caps.any_ipc}")
print(f"       torch={caps.torch} cuda-python={caps.cuda_python}")

# ---- Tier 3: the two %inline helpers ----
print("[tier 3] %inline helpers")
desc = cuvis_il.cuvis_cuda_ipc_descriptor_t()
raw = cuvis_il.cuvis_cuda_descriptor_bytes(desc)
check(isinstance(raw, (bytes, bytearray)), "descriptor_bytes returns bytes")
check(len(raw) == 184, f"descriptor is 184 bytes (got {len(raw)})")
head = struct.unpack_from("<iiiIQQQQ", raw, 0)
print(f"       parsed header fields: {head}")
view = cuvis_il.cuvis_cuda_mem_view_t()
ptr = cuvis_il.cuvis_cuda_view_ptr(view)
check(isinstance(ptr, int), f"view_ptr returns int (default {ptr})")

# ---- Tier 4: end-to-end against a real measurement (adaptive) ----
print("[tier 4] measurement -> get_cube_cuda (needs a device-backed cube)")
import os
import cuvis
from cuvis.cuvis_aux import SDKException

cuvis.init(settings_path=os.environ.get("CUVIS_SETTINGS", "."))
data = os.path.join(
    os.path.dirname(__file__), "..", "tests", "test_data", "test_mesu.cu3s"
)
if not os.path.exists(data):
    print(f"       skip: test data not found at {data}")
else:
    sess = cuvis.SessionFile(data)
    mesu = sess.get_measurement(0)
    pc = cuvis.ProcessingContext(sess)
    pc.processing_mode = cuvis.ProcessingMode.Raw
    pc.apply(mesu)
    host = mesu.cube  # ImageData (host numpy copy)
    print(f"       host cube: shape={host.array.shape} dtype={host.array.dtype}")
    try:
        cimg = mesu.get_cube_cuda("cube")
        print(
            f"       CudaImageData: {cimg.width}x{cimg.height}x{cimg.channels} dtype={cimg.dtype}"
        )
        check(
            (cimg.height, cimg.width, cimg.channels) == host.array.shape,
            "cuda geometry matches host cube shape",
        )
        cai = cimg.__cuda_array_interface__
        print(
            f"       __cuda_array_interface__: shape={cai['shape']} typestr={cai['typestr']}"
        )
        try:
            import numpy as np
            import torch  # noqa

            t = cimg.to_torch()
            check(tuple(t.shape) == host.array.shape, "torch tensor shape matches host")
            check(
                np.array_equal(t.cpu().numpy(), host.array),
                "torch tensor data equals host cube",
            )
        except ImportError:
            print("       (torch not installed - skipping zero-copy tensor compare)")
    except SDKException as e:
        print(f"       get_cube_cuda raised SDKException: {e}")
        print(
            "       -> plumbing reached the C function; the cube is not CUDA-device-backed,"
        )
        print("          so the device happy-path needs a GPU-resident measurement.")

print()
if FAIL:
    print(f"SMOKE FAILED: {len(FAIL)} check(s) failed")
    sys.exit(1)
print("SMOKE PASSED (tiers that could run)")
