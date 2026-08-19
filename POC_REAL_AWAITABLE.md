# POC: real awaitables for the cuvis Python SDK (ALL-1671)

Not a merge candidate.
This branch exists to answer one question: can `await` on a cuvis object resume when the SDK is done, instead of when the next poll happens to come round?

It can, and the change needed is smaller than expected.
It also uncovered a crash that the obvious implementation walks straight into, which is the main reason this is written down rather than merged.

Companion branch: `poc/gil-release` in `cuvis.swig`.

## The problem

`cuvis.python` already exposes `async`/`await`, so ALL-1671 looked done.
It is not.
Every path underneath is a sleep loop:

| Site | Interval |
| --- | --- |
| `cuvis/Async.py` `AsyncMesu.__await__` | 10 ms |
| `cuvis/Async.py` `Async.__await__` | 10 ms |
| `cuvis/Worker.py` `Worker.get_next_result_async` | 100 ms |
| `cuvis/Worker.py` `Worker.register_worker_callback` | 1 ms |

None of these is an awaitable in any meaningful sense.
They are timers that check a flag, and the interval sets a floor under the latency that no amount of Python-side work can lift.

The SDK is not the limitation.
It already offers blocking waits with timeouts, and documents them:

- `cuvis_async_capture_get(handle, timeout_ms, out)` - `cuvis.h:1912`, "Give 0 to wait for ever"
- `cuvis_async_call_get(handle, timeout_ms)` - `cuvis.h:1839`
- `cuvis_worker_get_next_result(worker, mesu, view, timeout_ms)` - `cuvis.h:3066`, "-1 to wait indefinitely"

## Why the wrapper could not use them

`cuvis.swig/src/cuvis_il.i` carried no threading directive and `cuvis.pyil/CMakeLists.txt` passes SWIG only `-doxygen`.
**No wrapped function released the GIL.**
A blocking `cuvis_async_capture_get(h, 5000)` therefore froze the entire interpreter for its full timeout, which makes it unusable from an event loop.
Polling was not a design choice; it was the only thing available.

## The trap: `%module(threads="1")` crashes

SWIG has no per-function opt in for GIL release.
`%threadallow` is defined in `swigwin/Lib/python/pyuserdir.swg` as `%feature("nothreadallow","0")` - there is only a module-wide switch and a per-function opt *out*.
So the obvious change is `%module(threads="1") cuvis_il`, and it generates exactly what you want:

```cpp
CUVIS_GUARD({
  SWIG_PYTHON_THREAD_BEGIN_ALLOW;
    result = cuvis_async_capture_get(arg1,arg2,arg3);
    SWIG_PYTHON_THREAD_END_ALLOW;
  })
```

It also segfaults.

`SWIG_PYTHON_THREAD_BEGIN_ALLOW` is an RAII object (`SWIG_Python_Thread_Allow`) whose destructor reacquires the GIL.
It sits *inside* `CUVIS_GUARD`, the MSVC structured-exception guard that turns a delay-load failure into a C++ throw so a missing symbol becomes a Python exception rather than a dead process.
The extension is built `/EHsc` (`ExceptionHandling=Sync`), under which **MSVC does not run C++ destructors while unwinding an SEH exception**.

So when the delay-load stub fires, the guard never reacquires the GIL, and `SWIG_exception` in the `%exception` handler calls into the Python C API without it.

Measured, not reasoned about.
Built against the staged SDK, run against the installed one, which does not export the eight CUDA entry points, calling one on the unshadowed extension:

| Build | Result |
| --- | --- |
| `threads="1"` | `0xc06d007f`, then access violation, exit 139 |
| no threading (control) | `RuntimeError`, interpreter healthy, exit 0 |
| this branch's fix | `RuntimeError`, interpreter healthy, exit 0 |

This matters because that path is not exotic: it is the exact scenario `cuvis.binding` was built to report, an installed SDK older than the binding.

## The fix

Drop `threads="1"` and manage the GIL explicitly in the `%exception` block that is already there, so correctness does not depend on unwinding running a destructor:

```c
%exception {
  PyThreadState *_cuvis_thread = PyEval_SaveThread();
  try { CUVIS_GUARD($action) }
  catch (std::invalid_argument const& e) { CUVIS_REGAIN_GIL; SWIG_exception(SWIG_ValueError,   e.what()); }
  catch (std::exception const& e)        { CUVIS_REGAIN_GIL; SWIG_exception(SWIG_RuntimeError, e.what()); }
  catch (...)                            { CUVIS_REGAIN_GIL; SWIG_exception(SWIG_UnknownError, "unknown C++ exception from cuvis"); }
  CUVIS_REGAIN_GIL;
}
```

`CUVIS_REGAIN_GIL` is idempotent, so the same statement serves the catch blocks and the success path.
This covers 325 wrapped call sites.

There are no SWIG directors and no Python callables handed to the SDK, so nothing re-enters the interpreter from a thread that has given up the GIL.

## What changed in cuvis.python

`cuvis/Async.py` gains one helper and the two `__await__` methods collapse into it:

```python
async def _wait_off_the_loop(blocking_get):
    loop = a.get_running_loop()
    return await loop.run_in_executor(None, blocking_get, _WAIT_FOREVER)
```

`cuvis/Worker.py`:

- `get_next_result_async` runs the SDK's blocking wait in the executor instead of polling. It now raises `SDKException` on timeout rather than returning a `WorkerResult` built from handles the SDK never filled in, which is what the old version did.
- `register_worker_callback` awaits results in a loop; the 1 ms spin is gone.
- A private `_wait_for_result` reads the status directly and returns `None` on a timeout. `SDKException.__init__` calls `logging.exception` unconditionally, so a wait that expects to come back empty cannot go through the public method without writing a traceback to the log every second.

## Measurements

Simulated camera, one frame ingested per round, 12 rounds, same machine, runs taken back to back.
`scripts/bench_worker.py` in this branch reproduces it.

| | before (develop) | after (this branch) |
| --- | --- | --- |
| worker result, blocking | 33.9 ms | 23.1 ms |
| worker result, awaited | **108.6 ms** | **28.0 ms** |
| awaited / blocking | **3.20x** | **1.21x** |
| registered callback, idle | 0.8 % of a core | 0.0 % of a core |

The ratio is the number to read: absolute timings drift with machine load, but the awaited path went from three times the cost of the blocking floor to within a fifth of it.
The 108 ms figure is not a coincidence - it is the 100 ms poll interval, and it was there whether or not the result was ready.

Full suite: 123 passed against the rebuilt extension on Python 3.12.

## What the SDK would need for this to be finished

The executor approach is a real improvement but it is not free, and both costs are the SDK's to remove:

1. **One pooled thread per outstanding wait.** Fine for a handful of captures, not for hundreds.
2. **A wait cannot be cancelled.** A thread blocked in C is not interruptible, so `reset_worker_callback` cannot take effect until the current window expires. That is why `_RESULT_WAIT_MS` is 1000 rather than "wait for ever", and it is a workaround, not a design.

Both go away if the SDK hands out something an event loop can watch directly.
The proposal, for a cuvis.c ticket:

```c
/** @brief A waitable OS handle that is signalled when the async capture completes.
  *
  * On Windows a Win32 event HANDLE, suitable for IocpProactor.wait_for_handle.
  * On Linux an eventfd, suitable for loop.add_reader.
  * The handle is owned by the SDK and stays valid until the async result is freed.
  */
SDK_CAPI CUVIS_STATUS SDK_CCALL cuvis_async_capture_get_event(
    CUVIS_ASYNC_CAPTURE_RESULT i_asyncResult, CUVIS_EVENT_HANDLE* o_pEvent);
```

with the same shape for `cuvis_async_call_*` and `cuvis_worker_*`.
With that, the awaitables need no threads at all and cancellation is ordinary asyncio.

A completion callback routed through `loop.call_soon_threadsafe` would also work.
The SDK has callback plumbing already (`log_callback` at `cuvis.h:1595`, `external_event_callback` at `:1637`), but neither is tied to an async result.

A second, smaller ask: `cuvis_worker_get_next_result` reports "nothing arrived yet" through the same error channel as real failures, which is why `_wait_for_result` has to exist.
A distinct status for an expired timeout would remove it.

## Reproducing

```powershell
# 1. the SWIG side
cd C:\dev\cuvis_sdk\cuvis.pyil\cuvis.swig
git checkout poc/gil-release
powershell -ExecutionPolicy Bypass -File C:\dev\cuvis_sdk\cuvis.pyil\build_pyil.ps1

# 2. the measurements
$env:PYTHONPATH = "C:\dev\cuvis_sdk\cuvis.pyil;C:\dev\cuvis_sdk\cuvis.python-await"
& C:\dev\cuvis_sdk\.venv-pyil312\Scripts\python.exe scripts\bench_worker.py

# 3. the crash test: build against the staged SDK, run against the installed one
Remove-Item -Recurse -Force C:\dev\cuvis_sdk\cuvis.pyil\build
powershell -ExecutionPolicy Bypass -File C:\dev\cuvis_sdk\cuvis.pyil\build_pyil.ps1 `
  -CuvisRoot "C:\dev\cuvis_sdk\.cuvis-new" -CuvisLib "C:\dev\cuvis_sdk\.cuvis-new\sdk\cuvis_c\cuvis.lib"
& C:\dev\cuvis_sdk\.venv-pyil312\Scripts\python.exe scripts\seh_under_released_gil.py
```

The build must be launched from a directory holding no stray `cuvis.dll`: the configure-time probe finds one through the Windows current-directory rule, before PATH, and bakes the wrong build hash into the binding.
