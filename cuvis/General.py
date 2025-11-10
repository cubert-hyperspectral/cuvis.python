import logging
import os
import platform
from importlib.metadata import version as imp_version

from ._cuvis_il import cuvis_il
from .cuvis_aux import SDKException
from pathlib import Path

import cuvis.cuvis_types as internal

from typing import Union, Optional


def init(
    settings_path: str = ".",
    global_loglevel: Union[int, str] = logging.DEBUG,
    logfile_name: Optional[str] = None,
):
    if "CUVIS_SETTINGS" in os.environ and settings_path == ".":
        # env variable is set and settings path is default kwarg
        settings_path = os.environ["CUVIS_SETTINGS"]

    if isinstance(global_loglevel, str):
        # also support string as input argument
        global_loglevel = internal.__strToLogLevel__[global_loglevel]

    if cuvis_il.status_ok != cuvis_il.cuvis_init(
        settings_path, internal.__CuvisLoglevel__[global_loglevel], logfile_name
    ):
        raise SDKException()


def shutdown():
    cuvis_il.cuvis_shutdown()


def version() -> str:
    return cuvis_il.cuvis_version_swig()


def sdk_version() -> str:
    return version()


def wrapper_version() -> str:
    pip_version = imp_version("cuvis")
    with open(Path(__file__).parent.parent / "git-hash.txt", "r") as f:
        git_hash = f.readline()
        return f"{pip_version} {git_hash}".strip()


def set_log_level(lvl: Union[int, str]):
    if isinstance(lvl, str):
        # also support string as input argument
        lvl = internal.__strToLogLevel__[lvl]

    cuvis_il.cuvis_set_log_level(internal.__CuvisLoglevel__[lvl])
    logging.basicConfig(level=lvl)
