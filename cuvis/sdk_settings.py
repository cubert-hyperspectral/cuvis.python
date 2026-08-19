import io
import tempfile
from collections.abc import Iterator, MutableMapping
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union
from xml.etree import ElementTree as ET

SETTINGS_NAMESPACE = "http://cubert-gmbh.de/core/settings.xsd"
SETTINGS_VERSION = "1.0.0"
SETTINGS_FILENAME = "cuvis.settings"

_SETTINGS_TAG = "{{{}}}settings".format(SETTINGS_NAMESPACE)
_PROPERTY_TAG = "{{{}}}property".format(SETTINGS_NAMESPACE)


def _resolve_source(source: Union[str, Path]) -> Path:
    source = Path(source)
    if not source.is_dir():
        return source
    settings_path = source / SETTINGS_FILENAME
    if not settings_path.is_file():
        raise FileNotFoundError(
            "No '{}' found in directory '{}'.".format(SETTINGS_FILENAME, source)
        )
    return settings_path


def _load(path: Path) -> dict[str, str]:
    try:
        root = ET.parse(str(path)).getroot()
    except ET.ParseError as e:
        raise ValueError("Settings file '{}' is not valid XML: {}".format(path, e))

    if root.tag != _SETTINGS_TAG:
        raise ValueError(
            "Settings file '{}' has root element '{}', expected '{}'.".format(
                path, root.tag, _SETTINGS_TAG
            )
        )
    if root.get("version") is None:
        raise ValueError(
            "Settings file '{}' is missing the required 'version' attribute.".format(
                path
            )
        )

    data = {}
    for prop in root:
        if prop.tag != _PROPERTY_TAG:
            raise ValueError(
                "Settings file '{}' contains unexpected element '{}', "
                "expected '{}'.".format(path, prop.tag, _PROPERTY_TAG)
            )
        key = prop.get("id")
        if key is None:
            raise ValueError(
                "Settings file '{}' contains a property without an 'id' "
                "attribute.".format(path)
            )
        if key in data:
            raise ValueError(
                "Settings file '{}' contains duplicate property id '{}'.".format(
                    path, key
                )
            )
        data[key] = prop.get("value", "")
    return data


class SdkSettings(MutableMapping):
    """Dict-like builder for the SDK's ``cuvis.settings`` file.

    Behaves like a ``dict`` of setting id to value, can be loaded from an
    existing settings file or from a directory containing one, and serializes
    itself into a temporary directory when used as a context manager.

    Example::

        settings = SdkSettings(force_gpu_mode="cuda", processing_thread_count=8)
        settings["verbose"] = True
        print(dict(settings))

        with settings as settings_dir:
            cuvis.init(settings_dir)
    """

    def __init__(self, source: Optional[Union[str, Path]] = None, /, **kwargs):
        self._tmpdir = None
        ET.register_namespace("", SETTINGS_NAMESPACE)

        loaded = _load(_resolve_source(source)) if source is not None else {}
        overrides = {
            self._check_key(k): self._coerce_value(v)
            for k, v in kwargs.items()
            if v is not None
        }
        self._data = dict(loaded, **overrides)
        self._rebuild_tree()

    @staticmethod
    def _check_key(key: str) -> str:
        if not isinstance(key, str) or not key or key.split() != [key]:
            raise ValueError(
                "Invalid setting id {!r}: must be a non-empty string without "
                "whitespace.".format(key)
            )
        return key

    @staticmethod
    def _coerce_value(value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, Enum):
            return str(value.value)
        return str(value)

    def __getitem__(self, key: str) -> str:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[self._check_key(key)] = self._coerce_value(value)
        self._rebuild_tree()

    def __delitem__(self, key: str) -> None:
        del self._data[key]
        self._rebuild_tree()

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return "{}({!r})".format(type(self).__name__, self._data)

    def _rebuild_tree(self) -> None:
        root = ET.Element(_SETTINGS_TAG)
        root.set("version", SETTINGS_VERSION)
        for key, value in self._data.items():
            prop = ET.SubElement(root, _PROPERTY_TAG)
            prop.set("id", key)
            prop.set("value", value)
        self._tree = ET.ElementTree(root)
        ET.indent(self._tree)

    @property
    def xml_str(self) -> str:
        buf = io.BytesIO()
        self._tree.write(buf, xml_declaration=True, encoding="utf-8")
        return buf.getvalue().decode("utf-8")

    def save(self, path: Union[str, Path]) -> None:
        path = Path(path)
        if path.is_dir():
            path = path / SETTINGS_FILENAME
        self._tree.write(str(path), xml_declaration=True, encoding="utf-8")

    def __enter__(self) -> str:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.save(self._tmpdir.name)
        return self._tmpdir.name

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self._tmpdir.cleanup()
        self._tmpdir = None
        return False
