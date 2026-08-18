"""Inspect the compiled binding and the cuvis library it is running against.

The Python binding (``cuvis_il``) is compiled against one version of the cuvis SDK,
but the SDK itself is installed separately on the machine. The two can therefore
disagree: an installed library older than the binding may not export every function
the binding imports. The binding tolerates that rather than failing to import, and
records what it found; this module is how that information is read back.

Nothing here needs the SDK to be initialised, so it can be called before
:func:`cuvis.init` to decide whether an operation is worth attempting at all.

.. code-block:: python3

    from cuvis import binding

    print(binding.info())               # human readable, fit for a bug report

    if not binding.info().is_complete:
        ...                             # this SDK is missing something

    binding.require("cuvis_measurement_get_data_image_cuda")   # or raise

Which error you get depends on how the unavailable function is reached:

* calling one through ``cuvis_il`` directly, or through a wrapper such as
  :meth:`cuvis.Measurement.get_cube_cuda` that calls into it, raises
  :class:`RuntimeError` from the binding layer, naming the function;
* calling :func:`require` first raises :class:`UnavailableSDKFunction`, which also
  derives from :class:`RuntimeError`, so a single ``except RuntimeError`` covers
  both, while ``except SDKException`` still catches it as an ordinary cuvis error.

Against a binding too old to report any of this (an older ``cuvis_il`` wheel), every
query answers empty: :func:`missing_symbols` is empty, :func:`available` is ``True``
and :func:`require` never raises. Absence of evidence, not evidence of absence.
"""
from dataclasses import dataclass, field
from typing import FrozenSet, Tuple

from ._cuvis_il import cuvis_il
from .cuvis_aux import SDKException


class UnavailableSDKFunction(SDKException, RuntimeError):
    """The installed cuvis library does not provide a function that was required.

    Raised by :func:`require`. It derives from both :class:`SDKException` and
    :class:`RuntimeError` on purpose: the binding layer raises a plain
    :class:`RuntimeError` when an unavailable function is called directly, so
    deriving from it lets one ``except RuntimeError`` handle either route, without
    giving up ``except SDKException`` for code that treats all cuvis errors alike.

    :ivar names: the functions that were required but are not provided, in the order
        they were requested.
    """

    def __init__(self, *names: str):
        self.names = tuple(names)
        current = info()
        message = (
            "the installed CUVIS SDK ({}) does not provide {}; this binding was built "
            "against {}".format(
                current.library_version or "unknown version",
                ", ".join(self.names) or "a required function",
                current.built_against or "an unknown version"))
        # Deliberately not SDKException.__init__: that reads the SDK's last-error
        # string, and here the library was never reached to set one.
        Exception.__init__(self, message)
        self.message = message


@dataclass(frozen=True)
class BindingInfo:
    """A snapshot of the binding and the cuvis library loaded alongside it.

    Obtained from :func:`info`; printing it yields a short report suitable for
    pasting into a bug report.

    :ivar built_against: version of the cuvis SDK the binding was compiled against,
        for example ``"3.5.3"``. Empty if the binding predates this feature.
    :ivar library_version: full version banner reported by the library that was
        actually loaded, for example ``"CUBERT SDK v. 3.4.1 build: d20de35..."``.
        Empty if it could not be read.
    :ivar library_path: file the binding loaded, for example
        ``"/lib/cuvis/libcuvis.so"``. Useful when several copies are installed.
    :ivar missing_symbols: names of functions the binding imports that the loaded
        library does not export. Empty when the two agree.
    """

    built_against: str
    library_version: str
    library_path: str
    missing_symbols: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_complete(self) -> bool:
        """Whether the loaded library provides everything the binding imports.

        ``True`` also when the binding is too old to report missing functions, since
        an empty list is all it can offer.
        """
        return not self.missing_symbols

    def __str__(self) -> str:
        """Render the snapshot as a short multi-line report.

        A binding that predates this feature is reported as unknown rather than as
        complete, since an empty list of missing functions is all it can offer and
        that is not the same as having checked.
        """
        lines = [
            "cuvis binding",
            "  built against : {}".format(self.built_against or "unknown"),
            "  loaded library: {}".format(self.library_version or "unknown"),
            "  library path  : {}".format(self.library_path or "unknown"),
        ]
        if not self.built_against:
            lines.append("  status        : unknown, this binding does not report it")
        elif self.is_complete:
            lines.append("  status        : complete")
        else:
            lines.append("  status        : {} function(s) not provided by this SDK"
                         .format(len(self.missing_symbols)))
            lines.extend("                  {}".format(name)
                         for name in self.missing_symbols)
        return "\n".join(lines)


def info() -> BindingInfo:
    """Report the binding, the library it loaded and any functions it lacks.

    Cheap: the binding works all of this out once while being imported, so this only
    reads the result.

    :return: a :class:`BindingInfo` snapshot. Fields the binding cannot supply, which
        is everything when it predates this feature, come back empty rather than
        raising.
    """
    return BindingInfo(
        built_against=getattr(cuvis_il, "built_against_version", ""),
        library_version=getattr(cuvis_il, "library_version", ""),
        library_path=getattr(cuvis_il, "library_path", ""),
        missing_symbols=tuple(getattr(cuvis_il, "missing_symbols", ())),
    )


def missing_symbols() -> FrozenSet[str]:
    """Functions the binding imports that the installed cuvis library does not export.

    :return: the set of C function names, empty when the SDK matches the binding and
        also when the binding is too old to report them.
    """
    return frozenset(getattr(cuvis_il, "missing_symbols", ()))


def available(*names: str) -> bool:
    """Whether every named function is provided by the installed cuvis library.

    .. code-block:: python3

        if binding.available("cuvis_measurement_get_data_image_cuda"):
            cube = mesu.get_cube_cuda()

    :param names: C function names as they appear in ``cuvis.h``.
    :return: ``True`` if none of them is reported missing. With a binding too old to
        report anything this is always ``True``, so treat it as "nothing known to be
        missing" rather than a guarantee.
    """
    absent = missing_symbols()
    return not any(name in absent for name in names)


def require(*names: str) -> None:
    """Raise unless every named function is provided by the installed cuvis library.

    Use it at the start of an operation to fail with a clear explanation, instead of
    letting a call fail deeper in with less context.

    .. code-block:: python3

        binding.require("cuvis_cuda_mem_get_view", "cuvis_cuda_mem_free")

    :param names: C function names as they appear in ``cuvis.h``.
    :raises UnavailableSDKFunction: naming whichever of them are missing; the message
        also states the loaded SDK version and the one the binding expects.
    """
    absent = missing_symbols()
    unavailable = tuple(name for name in names if name in absent)
    if unavailable:
        raise UnavailableSDKFunction(*unavailable)


__all__ = ["BindingInfo", "UnavailableSDKFunction", "info", "missing_symbols",
           "available", "require"]
