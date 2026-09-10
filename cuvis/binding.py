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

Against a binding too old to report any of this (an older ``cuvis_il`` wheel),
:func:`missing_symbols` is empty and :func:`info` reports unknown throughout: absence of
evidence, not evidence of absence. :func:`available` and :func:`require` stay meaningful
there, because a function such an old binding never exposed is unusable whether or not
anything reports it missing.
"""

from dataclasses import dataclass, field

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
                current.built_against or "an unknown version",
            )
        )
        # Deliberately not SDKException.__init__: that reads the SDK's last-error
        # string, and here the library was never reached to set one.
        Exception.__init__(self, message)
        self.message = message


@dataclass(frozen=True)
class BindingInfo:
    """A snapshot of the binding and the cuvis library loaded alongside it.

    Obtained from :func:`info`; printing it yields a short report suitable for
    pasting into a bug report.

    :ivar built_against: version banner of the cuvis SDK the binding was compiled
        against, for example ``"CUBERT SDK v. 3.5.3 build: 0f416fb..."``. Reported in
        the same form as :attr:`library_version` so the two can be read side by side:
        the build hash is what tells apart two libraries that report the same version.
        Empty if the binding predates this feature.
    :ivar library_version: the same banner, from the library that was actually loaded.
        Empty if it could not be read.
    :ivar library_path: file the binding loaded, for example
        ``"/lib/cuvis/libcuvis.so"``. Useful when several copies are installed.
    :ivar missing_symbols: names of functions the binding imports that the loaded
        library does not export. Empty when the two agree.
    """

    built_against: str
    library_version: str
    library_path: str
    missing_symbols: tuple[str, ...] = field(default_factory=tuple)

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
            lines.append(
                "  status        : {} function(s) not provided by this SDK".format(
                    len(self.missing_symbols)
                )
            )
            lines.extend(
                "                  {}".format(name) for name in self.missing_symbols
            )
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


def missing_symbols() -> frozenset[str]:
    """Functions the binding imports that the installed cuvis library does not export.

    :return: the set of C function names, empty when the SDK matches the binding and
        also when the binding is too old to report them.
    """
    return frozenset(getattr(cuvis_il, "missing_symbols", ()))


def unavailable(*names: str) -> tuple[str, ...]:
    """Which of the named functions cannot be called, in the order given.

    A function is unusable for either of two reasons, and callers care about neither:
    the binding never exposed it, which is what an older ``cuvis_il`` wheel looks like,
    or the binding exposes it but the loaded library does not export it. Checking only
    the second would report a function the binding does not even have as available.

    :param names: C function names as they appear in ``cuvis.h``.
    :return: the subset that is unusable, empty when all of them can be called.
    """
    absent = missing_symbols()
    return tuple(
        name for name in names if name in absent or not hasattr(cuvis_il, name)
    )


def available(*names: str) -> bool:
    """Whether every named function can actually be called.

    .. code-block:: python3

        if binding.available("cuvis_measurement_get_data_image_cuda"):
            cube = mesu.get_cube_cuda()

    :param names: C function names as they appear in ``cuvis.h``.
    :return: ``True`` if the binding exposes every one of them and none is reported
        missing from the loaded library.
    """
    return not unavailable(*names)


def require(*names: str) -> None:
    """Raise unless every named function can actually be called.

    Use it at the start of an operation to fail with a clear explanation, instead of
    letting a call fail deeper in with less context.

    .. code-block:: python3

        binding.require("cuvis_cuda_mem_get_view", "cuvis_cuda_mem_free")

    :param names: C function names as they appear in ``cuvis.h``.
    :raises UnavailableSDKFunction: naming whichever of them are unusable; the message
        also states the loaded SDK version and the one the binding expects.
    """
    missing = unavailable(*names)
    if missing:
        raise UnavailableSDKFunction(*missing)


__all__ = [
    "BindingInfo",
    "UnavailableSDKFunction",
    "info",
    "missing_symbols",
    "unavailable",
    "available",
    "require",
]
