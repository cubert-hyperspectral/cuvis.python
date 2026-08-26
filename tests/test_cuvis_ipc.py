"""
Tests for the cuvis_ipc cross-process consumer module.

Covers the payload codec and the property the module exists for: it is importable in
a process that has no cuvis SDK. Mapping a buffer needs a CUDA device and a live
exporting process, so that is not covered here.
"""

import os
import subprocess
import sys

import pytest

import cuvis_ipc

DESCRIPTOR = bytes(range(184))
GEOMETRY = (290, 275, 51, 2)  # width, height, channels, format code


def test_payload_round_trip():
    """Test a packed payload decodes back to the same descriptor and geometry."""
    payload = cuvis_ipc.pack_payload(DESCRIPTOR, *GEOMETRY)
    geometry, descriptor = cuvis_ipc._unpack_payload(payload)
    assert geometry == GEOMETRY
    assert descriptor == DESCRIPTOR


def test_pack_payload_rejects_a_wrong_sized_descriptor():
    """Test the descriptor length is checked, since the wire format is fixed."""
    with pytest.raises(ValueError, match="184 bytes"):
        cuvis_ipc.pack_payload(DESCRIPTOR[:-1], *GEOMETRY)


def test_unpack_rejects_foreign_bytes():
    """Test the magic guards against anything that is not a cuvis payload."""
    with pytest.raises(ValueError, match="magic"):
        cuvis_ipc._unpack_payload(b"XXXX" + bytes(200))


def test_unpack_rejects_a_future_version():
    """Test a payload from a newer wire format is refused rather than misread."""
    payload = bytearray(cuvis_ipc.pack_payload(DESCRIPTOR, *GEOMETRY))
    payload[4:8] = (cuvis_ipc._VERSION + 1).to_bytes(4, "little")
    with pytest.raises(ValueError, match="version"):
        cuvis_ipc._unpack_payload(bytes(payload))


def test_importable_without_the_sdk():
    """Test the consumer module imports with no CUVIS environment variable set.

    This is the whole reason it sits outside the cuvis package: importing cuvis
    requires the SDK, and a consumer process opening a payload does not have one.
    """
    env = {k: v for k, v in os.environ.items() if k != "CUVIS"}
    result = subprocess.run(
        [sys.executable, "-c", "import cuvis_ipc, sys; print('cuvis' in sys.modules)"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "False"
