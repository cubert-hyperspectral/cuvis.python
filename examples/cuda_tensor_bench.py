"""Benchmark: get a measurement's cube into a torch CUDA tensor, three ways, timed.

Each way ends with a tensor on cuda. Before timing, every path is checked to hold
the EXACT same data as the host cube (np.array_equal), so the zero-copy paths are
proven to read the same pixels, not just the same shape.

  A - host round-trip (status quo): cuvis_measurement_get_data_image (device->host
      copy in SDK) -> cuvis_read_imbuf (numpy) -> torch.from_numpy().to(cuda). 2 copies.
  B - DLPack zero-copy:  get_cube_cuda().to_torch().               pointer wrap, 0 copies.
  C - __cuda_array_interface__ zero-copy: torch.as_tensor(cimg).   pointer wrap, 0 copies.

Run:
  set CUVIS=C:\\Program Files\\Cuvis\\bin
  set CUVIS_SETTINGS=C:\\Program Files\\Cuvis\\user\\settings
  set PYTHONPATH=C:\\dev\\cuvis_sdk\\cuvis.pyil;C:\\dev\\cuvis_sdk\\cuvis.python
  <venv>\\Scripts\\python.exe examples\\cuda_tensor_bench.py
"""

import os
import time

import numpy as np
import torch

import cuvis
from cuvis.cuvis_aux import SDKException
from cuvis_il import cuvis_il

KEY = "cube"
WARMUP = 5
N = 100

_FMT_TO_READER = {
    1: cuvis_il.cuvis_read_imbuf_uint8,
    2: cuvis_il.cuvis_read_imbuf_uint16,
    3: cuvis_il.cuvis_read_imbuf_uint32,
    4: cuvis_il.cuvis_read_imbuf_float32,
}


def host_array(mesu):
    """Fresh host fetch of the cube (device->host copy in the SDK), as a numpy copy."""
    buf = cuvis_il.cuvis_imbuffer_t()
    if cuvis_il.status_ok != cuvis_il.cuvis_measurement_get_data_image(
        mesu._handle, KEY, buf
    ):
        raise SDKException()
    arr = _FMT_TO_READER[buf.format](buf)  # numpy view over the SDK buffer
    return np.array(arr, copy=True)  # detach from the SDK buffer


def path_a(mesu):
    """Host round-trip -> cuda tensor. Two data movements."""
    buf = cuvis_il.cuvis_imbuffer_t()
    if cuvis_il.status_ok != cuvis_il.cuvis_measurement_get_data_image(
        mesu._handle, KEY, buf
    ):
        raise SDKException()
    arr = _FMT_TO_READER[buf.format](buf)
    t = torch.from_numpy(arr).to("cuda")
    del buf
    return t


def path_b(mesu):
    """DLPack zero-copy."""
    return mesu.get_cube_cuda(KEY).to_torch()


def path_c(mesu):
    """__cuda_array_interface__ zero-copy. Keep cimg alive for the tensor's use."""
    cimg = mesu.get_cube_cuda(KEY)
    t = torch.as_tensor(cimg, device=f"cuda:{cimg._view()[2]}")
    return t, cimg  # return cimg so caller keeps it alive


def bench(fn, n=N, warmup=WARMUP):
    for _ in range(warmup):
        r = fn()
        del r
    torch.cuda.synchronize()
    times = []
    for _ in range(n):
        t0 = time.perf_counter_ns()
        r = fn()
        torch.cuda.synchronize()
        t1 = time.perf_counter_ns()
        times.append((t1 - t0) / 1000.0)  # us
        del r
    a = np.array(times)
    return dict(
        p50=np.percentile(a, 50), p99=np.percentile(a, 99), mean=a.mean(), min=a.min()
    )


def main():
    cuvis.init(settings_path=os.environ.get("CUVIS_SETTINGS", "."))
    data = os.path.join(
        os.path.dirname(__file__), "..", "tests", "test_data", "test_mesu.cu3s"
    )
    sess = cuvis.SessionFile(data)
    mesu = sess.get_measurement(0)
    pc = cuvis.ProcessingContext(sess)
    pc.processing_mode = cuvis.ProcessingMode.Raw
    pc.apply(mesu)

    ref = host_array(mesu)
    print(
        f"host reference cube: shape={ref.shape} dtype={ref.dtype} bytes={ref.nbytes}"
    )

    # Preflight: device-backed cube available?
    try:
        _ = mesu.get_cube_cuda(KEY)
    except SDKException as e:
        print(f"PREFLIGHT FAILED: get_cube_cuda raised: {e}")
        print("Cube is not device-backed; running only path A (host round-trip).")
        stats = bench(lambda: path_a(mesu))
        _print_table({"A host round-trip": stats}, ref)
        return

    # ---- Correctness: each path holds the EXACT same data as the host cube ----
    print("\n[correctness] each path vs host cube (exact equality)")
    ta = path_a(mesu)
    tb = path_b(mesu)
    tc, _c_keep = path_c(mesu)

    checks = {
        "A host round-trip": ta,
        "B DLPack zero-copy": tb,
        "C CAI zero-copy": tc,
    }
    all_ok = True
    for name, t in checks.items():
        got = t.cpu().numpy()
        shape_ok = got.shape == ref.shape
        dtype_ok = got.dtype == ref.dtype
        data_ok = shape_ok and dtype_ok and np.array_equal(got, ref)
        # cross-check the zero-copy tensors are bit-identical to A on-device too
        eq_a = (
            bool(torch.equal(t.to("cuda"), ta.to("cuda")))
            if t.dtype == ta.dtype
            else False
        )
        status = "ok  " if data_ok and eq_a else "FAIL"
        all_ok = all_ok and data_ok and eq_a
        print(
            f"  {status}  {name}: shape={got.shape} dtype={got.dtype} "
            f"equals_host={data_ok} equals_A={eq_a}"
        )
    if not all_ok:
        print(
            "\nDATA MISMATCH - not all paths carry identical data. Aborting before timing."
        )
        raise SystemExit(1)
    print("  all paths carry identical data.")
    del ta, tb, tc, _c_keep

    # ---- Timing ----
    torch.zeros(1, device="cuda")  # force context
    results = {
        "A host round-trip": bench(lambda: path_a(mesu)),
        "B DLPack zero-copy": bench(lambda: path_b(mesu)),
        "C CAI zero-copy": bench(lambda: path_c(mesu)),
    }
    _print_table(results, ref)


def _print_table(results, ref):
    print(f"\ncube {ref.shape} {ref.dtype} ({ref.nbytes} bytes), N={N} iters")
    print(f"{'way':<22}{'p50 us':>12}{'p99 us':>12}{'mean us':>12}{'min us':>12}")
    print("-" * 70)
    for name, s in results.items():
        print(
            f"{name:<22}{s['p50']:>12.1f}{s['p99']:>12.1f}{s['mean']:>12.1f}{s['min']:>12.1f}"
        )
    print(
        "\nA moves ~8 MB twice (device->host->device); B/C wrap the device pointer (no copy)."
    )


if __name__ == "__main__":
    main()
