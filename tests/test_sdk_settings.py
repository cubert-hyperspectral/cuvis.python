"""
Tests for the SdkSettings utility.

Covers building settings in code, inspecting them like a dict, loading them
back from a file or directory, and serializing them to a temporary directory.
"""

import os
from pathlib import Path

import pytest

import cuvis
from cuvis.sdk_settings import SETTINGS_FILENAME, SETTINGS_NAMESPACE, SdkSettings


def _write(path, body):
    """Write a raw settings XML document and return its path."""
    path.write_text(body, encoding="utf-8")
    return path


VALID_XML = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<settings xmlns="{}" version="1.0.0">\n'
    '  <property id="force_gpu_mode" value="cuda" />\n'
    '  <property id="processing_thread_count" value="8" />\n'
    "</settings>\n".format(SETTINGS_NAMESPACE)
)


def test_kwargs_become_properties():
    """Keyword arguments are stored as string values."""
    settings = SdkSettings(force_gpu_mode="cuda", processing_thread_count=8)
    assert dict(settings) == {
        "force_gpu_mode": "cuda",
        "processing_thread_count": "8",
    }


def test_none_values_are_dropped():
    """A None value means 'not set' and never reaches the file."""
    settings = SdkSettings(il_pos_min=None, il_pos_max=4)
    assert "il_pos_min" not in settings
    assert settings["il_pos_max"] == "4"


def test_value_coercion():
    """Booleans render as true/false, everything else via str()."""
    settings = SdkSettings(a=True, b=False, c=3, d=1.5, e="text")
    assert settings["a"] == "true"
    assert settings["b"] == "false"
    assert settings["c"] == "3"
    assert settings["d"] == "1.5"
    assert settings["e"] == "text"


def test_enum_value_coercion():
    """Enums are written as their value, so SDK enums can be passed directly."""
    settings = SdkSettings(processing_mode=cuvis.ProcessingMode.Raw)
    assert settings["processing_mode"] == str(cuvis.ProcessingMode.Raw.value)


def test_mapping_interface():
    """The full MutableMapping surface is available for inspection."""
    settings = SdkSettings(force_gpu_mode="cuda")

    settings["verbose"] = True
    assert settings["verbose"] == "true"
    assert len(settings) == 2
    assert "verbose" in settings
    assert sorted(settings) == ["force_gpu_mode", "verbose"]
    assert sorted(settings.keys()) == ["force_gpu_mode", "verbose"]
    assert dict(settings.items())["force_gpu_mode"] == "cuda"
    assert settings.get("missing") is None
    assert settings.get("missing", "fallback") == "fallback"

    settings.update({"file_compression": "9"})
    assert settings["file_compression"] == "9"

    del settings["verbose"]
    assert "verbose" not in settings


def test_repr_contains_keys():
    """repr shows the class name and the current mapping."""
    text = repr(SdkSettings(force_gpu_mode="cuda"))
    assert text.startswith("SdkSettings(")
    assert "force_gpu_mode" in text
    assert "cuda" in text


def test_xml_str_structure():
    """The serialized XML carries the declaration, namespace and version."""
    xml = SdkSettings(force_gpu_mode="cuda").xml_str
    assert xml.startswith("<?xml version=")
    assert SETTINGS_NAMESPACE in xml
    assert 'version="1.0.0"' in xml
    assert 'id="force_gpu_mode"' in xml
    assert 'value="cuda"' in xml


def test_invalid_key_rejected():
    """Setting ids must be non-empty and free of whitespace."""
    with pytest.raises(ValueError):
        SdkSettings()["bad key"] = 1
    with pytest.raises(ValueError):
        SdkSettings()[""] = 1


def test_save_to_file_and_directory(tmp_path):
    """save() accepts both a file path and a directory."""
    settings = SdkSettings(force_gpu_mode="cuda")

    as_file = tmp_path / "custom.settings"
    settings.save(as_file)
    assert as_file.is_file()

    as_dir = tmp_path / "dir"
    as_dir.mkdir()
    settings.save(as_dir)
    assert (as_dir / SETTINGS_FILENAME).is_file()


def test_round_trip_via_file(tmp_path):
    """Saving and reloading a file preserves the mapping."""
    settings = SdkSettings(force_gpu_mode="cuda", processing_thread_count=8)
    target = tmp_path / SETTINGS_FILENAME
    settings.save(target)
    assert dict(SdkSettings(target)) == dict(settings)


def test_round_trip_via_directory(tmp_path):
    """Pointing the constructor at a directory finds cuvis.settings inside."""
    settings = SdkSettings(force_gpu_mode="cuda", verbose=True)
    settings.save(tmp_path)
    assert dict(SdkSettings(tmp_path)) == dict(settings)


def test_load_from_directory_matches_load_from_file(tmp_path):
    """A directory and the file inside it load to the same mapping."""
    _write(tmp_path / SETTINGS_FILENAME, VALID_XML)
    assert dict(SdkSettings(tmp_path)) == dict(SdkSettings(tmp_path / SETTINGS_FILENAME))


def test_load_accepts_str_path(tmp_path):
    """Sources may be given as plain strings."""
    _write(tmp_path / SETTINGS_FILENAME, VALID_XML)
    assert SdkSettings(str(tmp_path))["force_gpu_mode"] == "cuda"


def test_kwargs_override_loaded_values(tmp_path):
    """Keyword arguments win over values read from the source."""
    _write(tmp_path / SETTINGS_FILENAME, VALID_XML)
    settings = SdkSettings(tmp_path, processing_thread_count=2, verbose=True)
    assert settings["force_gpu_mode"] == "cuda"
    assert settings["processing_thread_count"] == "2"
    assert settings["verbose"] == "true"


def test_missing_settings_file_in_directory(tmp_path):
    """A directory without a settings file names the expected filename."""
    with pytest.raises(FileNotFoundError) as excinfo:
        SdkSettings(tmp_path)
    assert SETTINGS_FILENAME in str(excinfo.value)


INVALID_DOCUMENTS = {
    "wrong_root": "<nonsense/>",
    "missing_version": '<settings xmlns="{}"/>'.format(SETTINGS_NAMESPACE),
    "property_without_id": (
        '<settings xmlns="{0}" version="1.0.0">'
        '<property value="1"/>'
        "</settings>".format(SETTINGS_NAMESPACE)
    ),
    "duplicate_ids": (
        '<settings xmlns="{0}" version="1.0.0">'
        '<property id="a" value="1"/><property id="a" value="2"/>'
        "</settings>".format(SETTINGS_NAMESPACE)
    ),
    "unexpected_element": (
        '<settings xmlns="{0}" version="1.0.0"><other/></settings>'.format(
            SETTINGS_NAMESPACE
        )
    ),
    "malformed_xml": "<settings",
}


@pytest.mark.parametrize(
    "body", list(INVALID_DOCUMENTS.values()), ids=list(INVALID_DOCUMENTS)
)
def test_invalid_documents_rejected(tmp_path, body):
    """Structurally invalid settings documents raise ValueError."""
    path = _write(tmp_path / SETTINGS_FILENAME, body)
    with pytest.raises(ValueError):
        SdkSettings(path)


def test_context_manager_yields_directory_with_file():
    """Entering the context writes cuvis.settings into a fresh temp directory."""
    settings = SdkSettings(force_gpu_mode="cuda")
    with settings as settings_dir:
        assert isinstance(settings_dir, str)
        assert (Path(settings_dir) / SETTINGS_FILENAME).is_file()
        assert dict(SdkSettings(settings_dir)) == dict(settings)
    assert not os.path.exists(settings_dir)


def test_context_manager_reflects_latest_mutation():
    """The file is written on entry, so late mutations are included."""
    settings = SdkSettings()
    settings["processing_thread_count"] = 4
    with settings as settings_dir:
        assert SdkSettings(settings_dir)["processing_thread_count"] == "4"


def test_exported_from_package():
    """SdkSettings is part of the public cuvis namespace."""
    assert cuvis.SdkSettings is SdkSettings
