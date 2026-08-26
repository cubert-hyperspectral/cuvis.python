"""Adversarial / misuse tests for the cuvis CUDA-mem C API.

Exercises the boundary the way a careless caller would: multiple IPC exports of one
buffer, double free, use-after-free, wrong-vault handle mixups, invalid handles, and
whether repeated exports over-allocate device memory. Findings feed the docs.

Run:
  set CUVIS=C:\\Program Files\\Cuvis\\bin
  set CUVIS_SETTINGS=C:\\Program Files\\Cuvis\\user\\settings
  set PYTHONPATH=C:\\dev\\cuvis_sdk\\cuvis.pyil;C:\\dev\\cuvis_sdk\\cuvis.python
  <venv>\\Scripts\\python.exe examples\\cuda_misuse_test.py
"""

import os
import cuvis
from cuvis_il import cuvis_il as il

OK = il.status_ok
PASS = []


def check(cond, msg):
    print(("  ok  " if cond else "  FAIL") + "  " + msg)
    PASS.append(bool(cond))


def _free_mib():
    """CUDA free memory in MiB, or None if cuda-python is unavailable."""
    try:
        from cuda.bindings import runtime as rt

        rt.cudaSetDevice(0)
        rt.cudaDeviceSynchronize()
        err, free_b, _total = rt.cudaMemGetInfo()
        return free_b / (1024 * 1024)
    except Exception as e:
        print(f"  (cudaMemGetInfo unavailable: {e})")
        return None


def acquire_mem(mesu, key="cube"):
    buf = il.cuvis_cuda_imbuffer_t()
    st = il.cuvis_measurement_get_data_image_cuda(mesu._handle, key, buf)
    assert st == OK, "acquire failed"
    return buf.handle


def make_ipc(mem):
    p = il.new_p_int()
    st = il.cuvis_cuda_ipc_handle_create(mem, 0, p)  # backend 0 = auto
    return st, (il.p_int_value(p) if st == OK else None)


def descriptor_bytes(ipc):
    d = il.cuvis_cuda_ipc_descriptor_t()
    st = il.cuvis_cuda_ipc_get_descriptor(ipc, d)
    return st, (il.cuvis_cuda_descriptor_bytes(d) if st == OK else None)


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

    # --- M1: multiple IPC exports of one buffer ---
    print("[M1] export the same buffer as many IPC handles")
    mem = acquire_mem(mesu)
    N = 64
    before = _free_mib()
    ipcs = []
    for _ in range(N):
        st, h = make_ipc(mem)
        if st != OK:
            break
        ipcs.append(h)
    check(
        len(ipcs) == N, f"{N} IPC exports of one buffer all succeeded (got {len(ipcs)})"
    )
    check(len(set(ipcs)) == len(ipcs), "each export returned a distinct handle")
    after = _free_mib()
    if before is not None and after is not None:
        delta = before - after
        print(
            f"       device free before={before:.1f} MiB after={after:.1f} MiB delta={delta:.1f} MiB"
        )
        check(
            delta < 8.0,
            f"{N} exports did not allocate N buffers (delta {delta:.1f} MiB << {N}*8 MiB)",
        )

    # all descriptors valid and identical (same underlying buffer)
    sts = [descriptor_bytes(h) for h in ipcs]
    check(all(st == OK for st, _ in sts), "every IPC handle yields a descriptor")
    blobs = {b for _, b in sts if b is not None}
    check(len(blobs) == 1, "all descriptors are byte-identical (one physical buffer)")

    # --- M2: buffer stays alive until the LAST reference is freed ---
    print("[M2] refcount: free all but one, buffer still usable")
    for h in ipcs[:-1]:
        check(
            il.cuvis_cuda_ipc_handle_free(h) == OK, None
        ) if False else il.cuvis_cuda_ipc_handle_free(h)
    last = ipcs[-1]
    st, _ = descriptor_bytes(last)
    check(st == OK, "last IPC handle still valid after the other 63 were freed")
    # free the mem handle too; the buffer is still pinned by the last IPC handle
    check(
        il.cuvis_cuda_mem_free(mem) == OK,
        "mem handle freed while one IPC handle remains",
    )
    st, _ = descriptor_bytes(last)
    check(
        st == OK,
        "descriptor still valid after mem handle freed (buffer alive via IPC handle)",
    )
    check(
        il.cuvis_cuda_ipc_handle_free(last) == OK,
        "last IPC handle freed -> last reference gone",
    )

    # --- M3: double free is rejected, not a crash ---
    print("[M3] double free")
    check(
        il.cuvis_cuda_ipc_handle_free(last) != OK,
        "double free of an IPC handle is rejected",
    )
    check(il.cuvis_cuda_mem_free(mem) != OK, "double free of a mem handle is rejected")

    # --- M4: use-after-free is rejected ---
    print("[M4] use after free")
    v = il.cuvis_cuda_mem_view_t()
    check(
        il.cuvis_cuda_mem_get_view(mem, v) != OK,
        "get_view on a freed mem handle is rejected",
    )
    st, _ = descriptor_bytes(last)
    check(st != OK, "get_descriptor on a freed IPC handle is rejected")

    # --- M5: invalid / never-existed handles ---
    print("[M5] invalid handles")
    check(
        il.cuvis_cuda_mem_free(999999) != OK,
        "free of a never-existed mem handle is rejected",
    )
    st, _ = make_ipc(999999)
    check(st != OK, "handle_create on an invalid mem handle is rejected")
    check(
        il.cuvis_cuda_ipc_handle_free(999999) != OK,
        "free of a never-existed IPC handle is rejected",
    )

    # --- M6: wrong-vault handle mixups (the two vaults have independent id spaces) ---
    print("[M6] cross-vault handle mixups")
    mem2 = acquire_mem(mesu)
    st, ipc2 = make_ipc(mem2)
    print(
        f"       mem2={mem2} ipc2={ipc2}  (independent id spaces - may collide numerically)"
    )
    # Passing an IPC handle to a mem function looks it up in the WRONG vault.
    v2 = il.cuvis_cuda_mem_view_t()
    st_view = il.cuvis_cuda_mem_get_view(ipc2, v2)
    print(f"       cuvis_cuda_mem_get_view(ipc handle) -> status {st_view}")
    # Passing a mem handle to an IPC function likewise.
    d2 = il.cuvis_cuda_ipc_descriptor_t()
    st_desc = il.cuvis_cuda_ipc_get_descriptor(mem2, d2)
    print(f"       cuvis_cuda_ipc_get_descriptor(mem handle) -> status {st_desc}")
    print(
        "       (see the hazard note in the docs: handle types are not interchangeable,"
    )
    print("        and because the vaults number independently a wrong-type handle can")
    print("        alias an unrelated same-id handle in the other vault.)")
    il.cuvis_cuda_ipc_handle_free(ipc2)
    il.cuvis_cuda_mem_free(mem2)

    print()
    n_fail = PASS.count(False)
    print(f"MISUSE TESTS: {PASS.count(True)} ok, {n_fail} FAIL")
    raise SystemExit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
