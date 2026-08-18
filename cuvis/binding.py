"""What the compiled binding expects, and what the installed cuvis library provides.

The binding is compiled against one version of the cuvis SDK and can end up running
against another, because the library is installed separately. When the installed one is
older it may not export everything the binding imports. The binding survives that and
reports it; this module is the place to ask about it:

    from cuvis import binding

    print(binding.info())                  # a report fit for a bug report
    if not binding.info().is_complete:
        ...                                # some SDK functions are unavailable
    binding.require("cuvis_measurement_get_data_image_cuda")   # raises if unavailable

Calling an unavailable function raises `UnavailableSDKFunction`, so it can be caught as
an ordinary cuvis error rather than a bare RuntimeError from the binding layer.
"""
from dataclasses import dataclass, field
from typing import FrozenSet, Tuple

from ._cuvis_il import cuvis_il
from .cuvis_aux import SDKException


class UnavailableSDKFunction(SDKException):
    """The installed cuvis library does not export a function the binding needs."""

    def __init__(self, *names: str):
        self.names = tuple(names)
        current = info()
        message = (
            "the installed CUVIS SDK ({}) does not provide {}; this binding was built "
            "against {}".format(
                current.library_version or "unknown version",
                ", ".join(self.names) or "a required function",
                current.built_against or "an unknown version"))
        # Deliberately not SDKException.__init__: there is no SDK-side last error to read,
        # the library never got as far as being called.
        Exception.__init__(self, message)
        self.message = message


@dataclass(frozen=True)
class BindingInfo:
    """A snapshot of the binding and the cuvis library it loaded."""

    built_against: str
    library_version: str
    library_path: str
    missing_symbols: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_complete(self) -> bool:
        """True when the loaded library exports everything the binding imports."""
        return not self.missing_symbols

    def __str__(self) -> str:
        lines = [
            "cuvis binding",
            "  built against : {}".format(self.built_against or "unknown"),
            "  loaded library: {}".format(self.library_version or "unknown"),
            "  library path  : {}".format(self.library_path or "unknown"),
        ]
        if self.is_complete:
            lines.append("  status        : complete")
        else:
            lines.append("  status        : {} function(s) not provided by this SDK"
                         .format(len(self.missing_symbols)))
            lines.extend("                  {}".format(name)
                         for name in self.missing_symbols)
        return "\n".join(lines)


def info() -> BindingInfo:
    """Everything known about the binding and the library it is running against."""
    return BindingInfo(
        built_against=getattr(cuvis_il, "built_against_version", ""),
        library_version=getattr(cuvis_il, "library_version", ""),
        library_path=getattr(cuvis_il, "library_path", ""),
        missing_symbols=tuple(getattr(cuvis_il, "missing_symbols", ())),
    )


def missing_symbols() -> FrozenSet[str]:
    """Functions the binding imports that the installed cuvis library does not export.

    Empty with a matching SDK, and also empty on a binding too old to report it.
    """
    return frozenset(getattr(cuvis_il, "missing_symbols", ()))


def available(*names: str) -> bool:
    """True when every named function is provided by the installed cuvis library."""
    absent = missing_symbols()
    return not any(name in absent for name in names)


def require(*names: str) -> None:
    """Raise UnavailableSDKFunction naming whichever of `names` is not provided."""
    absent = missing_symbols()
    unavailable = tuple(name for name in names if name in absent)
    if unavailable:
        raise UnavailableSDKFunction(*unavailable)


__all__ = ["BindingInfo", "UnavailableSDKFunction", "info", "missing_symbols",
           "available", "require"]
