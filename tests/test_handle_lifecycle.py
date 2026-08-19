"""Every SDK handle owner must survive a failed construction.

These classes set ``self._handle = None`` before the call that would fill it in, so a
constructor that raises leaves a half-built object for the garbage collector. ``__del__``
then hands that ``None`` to the SWIG free function, which raises. Python does not
propagate an exception out of ``__del__``; it prints it, so the symptom is an unrelated
looking traceback appearing long after the real error the caller already handled.
"""

import gc
import sys

import pytest

import cuvis


def _construct(make):
    """Run a failing constructor and collect, recording anything ``__del__`` raises."""
    unraisable = []
    previous = sys.unraisablehook
    sys.unraisablehook = unraisable.append
    try:
        with pytest.raises(Exception):
            make()
        gc.collect()
    finally:
        sys.unraisablehook = previous
    return [type(entry.exc_value).__name__ for entry in unraisable]


# Every handle owner whose constructor can fail after _handle is set to None. AsyncMesu
# and AsyncResult are absent on purpose: they take an already valid handle and have no
# failing path, so their guard is defensive only.
FAILING_CONSTRUCTORS = {
    "Calibration": lambda: cuvis.Calibration("no_such_calibration"),
    "Measurement": lambda: cuvis.Measurement("no_such_measurement.cu3"),
    "SessionFile": lambda: cuvis.SessionFile("no_such_session.cu3s"),
    "ProcessingContext": lambda: cuvis.ProcessingContext("not a base"),
    "AcquisitionContext": lambda: cuvis.AcquisitionContext("not a base"),
    "CubeExporter": lambda: cuvis.CubeExporter("not export settings"),
    "Worker": lambda: cuvis.Worker("not worker settings"),
    "Viewer": lambda: cuvis.Viewer("not viewer settings"),
}


@pytest.mark.parametrize("name", sorted(FAILING_CONSTRUCTORS))
def test_failed_construction_is_collected_quietly(name, sdk_initialized):
    assert _construct(FAILING_CONSTRUCTORS[name]) == []
