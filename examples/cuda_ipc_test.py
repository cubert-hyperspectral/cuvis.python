"""Cross-process CUDA IPC end-to-end test.

Producer: process a measurement, get the cube as a shareable IPC buffer, write the
descriptor + geometry + a host reference to a work dir, then stay alive (it is the
in-process pin; legacy IPC has no cross-process refcount).
Importer (separate process): open the descriptor, wrap the device memory zero-copy as
a torch tensor, and assert it holds the exact same data as the host reference.
Also times the open/import latency.

Run (orchestrates both processes):
  set CUVIS=C:\\Program Files\\Cuvis\\bin
  set CUVIS_SETTINGS=C:\\Program Files\\Cuvis\\user\\settings
  set PYTHONPATH=C:\\dev\\cuvis_sdk\\cuvis.pyil;C:\\dev\\cuvis_sdk\\cuvis.python
  <venv>\\Scripts\\python.exe examples\\cuda_ipc_test.py
"""

import os
import sys
import time
import argparse
import tempfile
from pathlib import Path

import numpy as np

KEY = "cube"
N = 100


def _wait_for(path, timeout=60.0):
    t0 = time.time()
    while not path.exists():
        if time.time() - t0 > timeout:
            raise TimeoutError(f"timed out waiting for {path}")
        time.sleep(0.02)


def producer(workdir: Path):
    import cuvis

    cuvis.init(settings_path=os.environ.get("CUVIS_SETTINGS", "."))
    data = os.path.join(
        os.path.dirname(__file__), "..", "tests", "test_data", "test_mesu.cu3s"
    )
    sess = cuvis.SessionFile(data)
    mesu = sess.get_measurement(0)
    pc = cuvis.ProcessingContext(sess)
    pc.processing_mode = cuvis.ProcessingMode.Raw
    pc.apply(mesu)

    backend = int(
        os.environ.get("CUVIS_IPC_BACKEND", "0")
    )  # 0=auto 1=pool 2=legacy 3=vmm
    host = np.array(mesu.cube.array, copy=True)  # (h, w, c) uint16
    cimg = mesu.get_cube_cuda_ipc(
        KEY, backend=backend
    )  # cimg is the in-process pin; keep it alive
    payload = cimg.export_payload()  # ONE self-contained blob: descriptor + geometry

    np.save(workdir / "ref.npy", host)
    (workdir / "payload.bin").write_bytes(payload)
    print(
        f"[producer] cube {host.shape} {host.dtype}, payload {len(payload)} bytes, "
        f"backend_req={backend}, pid {os.getpid()}"
    )
    (workdir / "ready").touch()

    _wait_for(workdir / "done", timeout=120.0)
    print("[producer] importer finished, releasing buffer")


def importer(workdir: Path):
    # NOTE: no cuvis SDK init here - only the import-safe cuvis_ipc consumer utilities.
    import cuvis_ipc as ipc

    payload = (workdir / "payload.bin").read_bytes()
    ref = np.load(workdir / "ref.npy")

    # Correctness: geometry comes from the payload, nothing hard-coded.
    with ipc.open(payload) as cube:
        backend = cube.backend
        got = cube.to_torch().cpu().numpy()
    ok = got.shape == ref.shape and got.dtype == ref.dtype and np.array_equal(got, ref)
    print(
        f"[importer] imported {got.shape} {got.dtype}  backend={backend}  equals_host={ok}"
    )
    if not ok:
        (workdir / "done").touch()
        return 1

    # Latency: open + wrap + one sync, N times
    import torch

    times = []
    for _ in range(N):
        t0 = time.perf_counter_ns()
        with ipc.open(payload) as cube:
            tt = cube.to_torch()
            torch.cuda.synchronize()
        t1 = time.perf_counter_ns()
        times.append((t1 - t0) / 1000.0)
        del tt
    a = np.array(times)
    print(
        f"[importer] open+wrap latency us: p50={np.percentile(a, 50):.1f} "
        f"p99={np.percentile(a, 99):.1f} mean={a.mean():.1f} min={a.min():.1f}"
    )

    (workdir / "done").touch()
    return 0


def orchestrate():
    import subprocess

    workdir = Path(tempfile.mkdtemp(prefix="cuvis_ipc_"))
    print(f"[main] work dir {workdir}")
    env = dict(os.environ)
    prod = subprocess.Popen(
        [sys.executable, __file__, "--role", "producer", "--dir", str(workdir)], env=env
    )
    try:
        _wait_for(workdir / "ready", timeout=120.0)
        rc = subprocess.call(
            [sys.executable, __file__, "--role", "importer", "--dir", str(workdir)],
            env=env,
        )
        prod.wait(timeout=30)
    finally:
        if prod.poll() is None:
            prod.terminate()
    print(f"[main] {'PASSED' if rc == 0 else 'FAILED'} (importer rc={rc})")
    return rc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", choices=["producer", "importer"])
    ap.add_argument("--dir")
    args = ap.parse_args()
    if args.role == "producer":
        producer(Path(args.dir))
        return 0
    if args.role == "importer":
        return importer(Path(args.dir))
    return orchestrate()


if __name__ == "__main__":
    sys.exit(main())
