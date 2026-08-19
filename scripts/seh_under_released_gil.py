"""Does the delay-load SEH path hand back a clean exception once the GIL is released?

Built against the staged SDK, run against the installed one, which does not export the
CUDA entry points. The extension is imported as a top-level module so the package's
__init__ never runs and never replaces the missing symbols with Python stubs: the call
reaches the real SWIG wrapper, the delay-load stub raises a Win32 SEH exception,
cuvis_seh_call turns it into a C++ throw, and %exception turns that into a Python error.

With threads="1" the GIL is released around the call by an RAII guard. The build is
/EHsc, under which MSVC does not run C++ destructors while unwinding an SEH exception, so
the question is whether the GIL has been reacquired by the time SWIG_exception touches
the Python C API.
"""

import ctypes
import gc
import os
import sys

CUVIS_BIN = r"C:\Program Files\Cuvis\bin"
os.add_dll_directory(CUVIS_BIN)
for sub in ("bin", os.path.join("bin", "x64")):
    cuda = os.path.join(os.environ.get("CUDA_PATH", ""), sub)
    if os.path.isdir(cuda):
        os.add_dll_directory(cuda)

ctypes.WinDLL(
    os.path.join(CUVIS_BIN, "cuvis.dll")
)  # pin the library the stub will bind
import numpy  # noqa: F401,E402

sys.path.insert(0, r"C:\dev\cuvis_sdk\cuvis.pyil\cuvis_il")
import _cuvis_pyil as raw  # noqa: E402

print("raw extension:", raw.__file__)
print("shadowed?    :", "no")

name = "cuvis_cuda_mem_free"
print("calling raw {} ... a crash here means the GIL was not reacquired".format(name))
sys.stdout.flush()
try:
    getattr(raw, name)(0)
except Exception as exc:
    print("clean exception:", type(exc).__name__, "|", str(exc)[:110])
else:
    print("returned without raising")

sys.stdout.flush()
gc.collect()
print("interpreter still healthy:", sum(len(str(i)) for i in range(1000)))
