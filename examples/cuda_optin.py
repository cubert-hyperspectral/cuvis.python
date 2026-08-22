"""Opt-in CUDA usage: check capabilities, enable, read the cube zero-copy as a tensor.

Run:
  set CUVIS=C:\\Program Files\\Cuvis\\bin
  set CUVIS_SETTINGS=C:\\Program Files\\Cuvis\\user\\settings
  set PYTHONPATH=C:\\dev\\cuvis_sdk\\cuvis.pyil;C:\\dev\\cuvis_sdk\\cuvis.python
  <venv>\\Scripts\\python.exe examples\\cuda_optin.py
"""

import os
import cuvis
from cuvis import (
    cuda,
)  # explicit opt-in module; importing cuvis alone does not enable CUDA

# 1. Inspect what this binary + environment support, then decide.
caps = cuda.capabilities()
print("CUDA capabilities:", caps)
print("  same-process device sharing:", caps.same_process)
print("  cross-process IPC (pool):", caps.ipc_pool)
print("  torch installed:", caps.torch, " cuda-python installed:", caps.cuda_python)

if not caps.same_process:
    print("This build has no CUDA support; nothing to do.")
    raise SystemExit(0)

# 2. Opt in BEFORE loading/processing (also disables the host auto-refresh so the
#    GPU cube stays on the device).
cuda.enable()
print("cuda mode enabled:", cuda.is_enabled())

cuvis.init(settings_path=os.environ.get("CUVIS_SETTINGS", "."))
data = os.path.join(
    os.path.dirname(__file__), "..", "tests", "test_data", "test_mesu.cu3s"
)
sess = cuvis.SessionFile(data)
mesu = sess.get_measurement(0)
pc = cuvis.ProcessingContext(sess)
pc.processing_mode = cuvis.ProcessingMode.Raw
pc.apply(mesu)

# 3. get_cube() now routes through CUDA and returns a CudaImageData (raises if the
#    device path is unavailable - no silent host copy).
cimg = mesu.get_cube()
print("get_cube() returned:", type(cimg).__name__)

# 4. Preferred same-process wrap: DLPack (torch owns the lifetime).
if caps.torch:
    t = cimg.to_torch()
    print("to_torch (DLPack):", tuple(t.shape), t.dtype, t.device)
else:
    print("install cuvis[torch] to wrap as a tensor via to_torch()")
