"""Tests for the CudaImageData device-buffer path.

The device tests need two things: a CUDA device the SDK accepts, and an SDK actually
processing on it. Since 3.6.0 the latter is not the default -- a process whose `cuvis.init`
did not ask for it processes on the host, and then no cube is backed by device memory -- so
point CUVIS_SETTINGS at a directory whose `cuvis.settings` carries
`force_gpu_mode="cuda"` before running these::

    python -c "import cuvis; cuvis.SdkSettings(force_gpu_mode='cuda').save('/tmp/cuvis-gpu')"
    CUVIS_SETTINGS=/tmp/cuvis-gpu python -m pytest tests/test_cuda_image_data.py

They skip otherwise, which CI always is: it runs in the cuvis_pyil container on a GPU-less
runner. That is precisely how a release went out calling two cuvis_il functions that do not
exist, so the tests that matter most here are the ones needing no device at all.
"""

import ast
import struct
from pathlib import Path

import pytest

import cuvis
from cuvis import cuda
from cuvis._cuvis_il import cuvis_il
from cuvis.cube_utils import _descriptor_bytes

_HAS_DEVICE = cuda.capabilities().same_process
requires_device = pytest.mark.skipif(
    not _HAS_DEVICE, reason="needs a CUDA device the SDK accepts"
)


def _binding_names(module_path):
    """Every `cuvis_il.<name>` this module reaches for, found without importing it."""
    tree = ast.parse(Path(module_path).read_text(encoding="utf-8"))
    return {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "cuvis_il"
    }


def test_every_binding_symbol_the_cuda_path_uses_exists():
    """Test cube_utils calls no cuvis_il function the installed binding lacks.

    Nothing on a GPU-less runner ever executes the device path, so a missing symbol there
    surfaces only as an AttributeError in a user's process. This catches it at any commit.
    """
    used = _binding_names(cuvis.cube_utils.__file__)
    missing = sorted(name for name in used if not hasattr(cuvis_il, name))
    assert not missing, f"cube_utils references absent cuvis_il symbols: {missing}"


def test_free_passes_the_handle_the_way_the_c_api_takes_it():
    """Test cuvis_cuda_mem_free is called with CUVIS_CUDA_MEM*, not the handle by value.

    The C API declares `cuvis_cuda_mem_free(CUVIS_CUDA_MEM* i_mem)`, like
    `cuvis_cuda_ipc_handle_free`. Passing the int raises TypeError out of the binding, and the
    buffer is then never returned to the SDK's pool.
    """
    with pytest.raises(TypeError):
        cuvis_il.cuvis_cuda_mem_free(0)  # the shape that silently leaked

    box = cuvis_il.new_p_int()
    cuvis_il.p_int_assign(box, 0)
    cuvis_il.cuvis_cuda_mem_free(box)  # freeing a null handle is a no-op, not an error


# --- the IPC descriptor, which needs no device to serialise -------------------------------
def test_descriptor_serialises_to_the_locked_wire_layout():
    """Test _descriptor_bytes emits the 184-byte layout cuvis_ipc parses, blobs included."""
    desc = cuvis_il.cuvis_cuda_ipc_descriptor_t()
    desc.backend = 2
    desc.device_ordinal = 1
    desc.handle_type = 3
    desc.blob_len = 4
    desc.size = 65880000
    desc.alloc_size = 67108864
    desc.offset = 128
    desc.exporter_pid = 4321
    desc.ptr_blob_len = 2
    for index, value in enumerate((0xDE, 0xAD, 0xBE, 0xEF)):
        cuvis_il.p_unsigned_char_setitem(desc.blob, index, value)
    for index, value in enumerate((0x01, 0x02)):
        cuvis_il.p_unsigned_char_setitem(desc.ptr_blob, index, value)

    raw = _descriptor_bytes(desc)

    assert len(raw) == 184
    head = struct.unpack_from("<iiiIQQQQ", raw, 0)
    assert head == (2, 1, 3, 4, 65880000, 67108864, 128, 4321)
    assert raw[48:52] == bytes((0xDE, 0xAD, 0xBE, 0xEF))
    assert struct.unpack_from("<I", raw, 112) == (2,)
    assert raw[120:122] == bytes((0x01, 0x02))


def test_descriptor_rejects_an_over_long_blob():
    """Test a blob_len past the fixed field width fails loudly rather than truncating."""
    desc = cuvis_il.cuvis_cuda_ipc_descriptor_t()
    desc.blob_len = 65
    with pytest.raises(ValueError, match="exceeds 64"):
        _descriptor_bytes(desc)


def test_the_wire_layout_matches_the_consumer_half():
    """Test cuvis_ipc and cube_utils agree on the offsets; they are two copies of one layout."""
    cuvis_ipc = pytest.importorskip("cuvis_ipc")
    from cuvis import cube_utils

    assert cube_utils._IPC_HEAD.format == cuvis_ipc._HEAD.format
    assert cube_utils._IPC_BLOB_OFF == cuvis_ipc._BLOB_OFF
    assert cube_utils._IPC_PTR_LEN_OFF == cuvis_ipc._PTR_LEN_OFF
    assert cube_utils._IPC_PTR_BLOB_OFF == cuvis_ipc._PTR_BLOB_OFF
    assert cube_utils._IPC_BLOB_MAX == cuvis_ipc._BLOB_MAX
    assert cube_utils._IPC_DESC_LEN == cuvis_ipc._DESC_LEN


# --- the real device path ------------------------------------------------------------------
def _device_cube(pc, session):
    """A cube left in device memory, or a skip naming why the SDK did not produce one."""
    try:
        return pc.apply(session.get_measurement(0)).get_cube_cuda()
    except cuvis.cuvis_aux.SDKException as exc:
        pytest.skip(
            "SDK is not processing on the device ({}); set CUVIS_SETTINGS to a directory "
            "whose cuvis.settings has force_gpu_mode=cuda".format(exc)
        )


@pytest.fixture
def raw_context(test_session_file):
    """A Raw ProcessingContext shared with the session, as the reader path uses it."""
    pc = cuvis.ProcessingContext(test_session_file)
    test_session_file._pc = pc
    pc.processing_mode = cuvis.ProcessingMode.Raw
    return pc


@pytest.fixture
def device_cube(test_session_file, raw_context):
    """A processed cube left in device memory, plus the same cube fetched to the host."""
    import numpy as np

    host = np.ascontiguousarray(
        raw_context.apply(test_session_file.get_measurement(0)).cube.array
    )
    cuda.enable()  # one way for this process, so it happens after the host reference
    try:
        yield _device_cube(raw_context, test_session_file), host
    finally:
        cuda.disable()


@requires_device
def test_view_describes_the_device_buffer(device_cube):
    """Test _view() returns a usable pointer and the cube's exact byte count."""
    cimg, host = device_cube
    ptr, size, ordinal = cimg._view()
    assert ptr > 0
    assert size == host.nbytes
    assert ordinal >= 0


@requires_device
def test_to_torch_is_the_same_cube_on_the_device(device_cube):
    """Test the zero-copy tensor holds exactly what the host path would have produced."""
    torch = pytest.importorskip("torch")
    cimg, host = device_cube
    tensor = cimg.to_torch()
    assert tensor.is_cuda
    assert tuple(tensor.shape) == host.shape
    assert torch.equal(tensor.cpu(), torch.from_numpy(host))


@requires_device
def test_cuda_array_interface_reports_the_buffer(device_cube):
    """Test the fallback interop path answers instead of raising from the binding."""
    cimg, host = device_cube
    with pytest.warns(UserWarning, match="lifecycle"):
        interface = cimg.__cuda_array_interface__
    assert interface["shape"] == host.shape
    assert interface["data"][0] > 0


@requires_device
def test_device_buffers_are_returned_to_the_sdk(test_session_file, raw_context):
    """Test repeated read-and-drop cycles do not accumulate device memory.

    A free that raises leaves every cube's buffer outstanding, which is invisible until a
    long run exhausts the card. The SDK pools the buffers, so this asserts a plateau rather
    than a return to the starting value.
    """
    torch = pytest.importorskip("torch")
    cuda.enable()
    try:
        _device_cube(raw_context, test_session_file).to_torch()
        torch.cuda.synchronize()
        settled = torch.cuda.mem_get_info()[0]
        for _ in range(20):
            held = _device_cube(raw_context, test_session_file).to_torch()
            del held
        torch.cuda.synchronize()
        free_now = torch.cuda.mem_get_info()[0]
    finally:
        cuda.disable()
    lost_mib = (settled - free_now) / 2**20
    assert lost_mib < 256, (
        f"{lost_mib:.0f} MiB of device memory not returned over 20 cycles"
    )
