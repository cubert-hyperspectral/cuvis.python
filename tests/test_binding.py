"""
Tests for cuvis.binding.

Covers availability reporting. The installed library differs between CI and developer
machines, so the tests pin the two ends that are always true: a function the binding
does expose is available, and one nothing exposes is not.
"""

import pytest

import cuvis
from cuvis import binding

PRESENT = "cuvis_measurement_load"
ABSENT = "cuvis_a_function_that_does_not_exist"


def test_info_reports_without_an_initialised_sdk():
    """Test info() is answerable before cuvis.init, which is what gates a feature check."""
    current = binding.info()
    assert isinstance(current, cuvis.BindingInfo)
    assert isinstance(current.is_complete, bool)
    assert "cuvis binding" in str(current)


def test_a_function_the_binding_exposes_is_available():
    """Test a function present in the binding and not reported missing is available."""
    assert binding.available(PRESENT)
    assert binding.unavailable(PRESENT) == ()
    binding.require(PRESENT)


def test_a_function_no_binding_exposes_is_unavailable():
    """Test availability accounts for absent symbols, not only reported-missing ones.

    A binding too old to report missing symbols reports none, so consulting that list
    alone would call a function the binding never had and fail with an AttributeError.
    """
    assert not binding.available(ABSENT)
    assert binding.unavailable(ABSENT) == (ABSENT,)


def test_unavailable_preserves_the_requested_order():
    """Test the report names only the unusable functions, in the order asked for."""
    assert binding.unavailable(PRESENT, ABSENT, PRESENT) == (ABSENT,)


def test_require_names_every_unavailable_function():
    """Test the raised error carries the names, so the message says what to install."""
    with pytest.raises(cuvis.UnavailableSDKFunction) as excinfo:
        binding.require(PRESENT, ABSENT)
    assert excinfo.value.names == (ABSENT,)
    assert ABSENT in str(excinfo.value)


@pytest.mark.parametrize("expected", [RuntimeError, cuvis.cuvis_aux.SDKException])
def test_unavailable_function_is_catchable_by_either_base(expected):
    """Test the exception satisfies both except clauses its docstring advertises."""
    with pytest.raises(expected):
        binding.require(ABSENT)


def test_missing_symbols_is_a_frozenset():
    """Test the reported set is immutable, so a caller cannot corrupt it."""
    assert isinstance(binding.missing_symbols(), frozenset)
