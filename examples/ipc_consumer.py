"""Standalone cross-process IPC consumer.

Runs in a process that never initialized the cuvis SDK: it imports ONLY cuvis_ipc (plus
cuda-python + torch) and needs no CUVIS env var and no cuvis.dll. Point it at a payload file
written by a producer (cimg.export_payload()); it opens the shared buffer and reads it.

  python ipc_consumer.py <payload.bin>
"""

import sys
import cuvis_ipc as ipc  # import-safe: no SDK init, no CUVIS env, no cuvis.dll


def main():
    if len(sys.argv) != 2:
        print("usage: python ipc_consumer.py <payload.bin>")
        return 2
    payload = open(sys.argv[1], "rb").read()
    with ipc.open(payload) as cube:
        t = cube.to_torch()  # correct shape + dtype from the payload; zero-copy
        print(
            f"opened shape={tuple(t.shape)} dtype={t.dtype} device={t.device} sum={int(t.sum())}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
