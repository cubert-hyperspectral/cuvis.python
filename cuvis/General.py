import logging
import os
import platform
import pkg_resources

from ._cuvis_il import cuvis_il
from .cuvis_aux import SDKException
from .cuvis_types import ComponentType
from pathlib import Path

import cuvis.cuvis_types as internal

from dataclasses import dataclass


def init(settings_path: str = ".", global_loglevel: int | str = logging.DEBUG, logfile_name: str | None = None):
    if 'CUVIS_SETTINGS' in os.environ and settings_path == ".":
        # env variable is set and settings path is default kwarg
        settings_path = os.environ['CUVIS_SETTINGS']

    if isinstance(global_loglevel, str):
        # also support string as input argument
        global_loglevel = internal.__strToLogLevel__[global_loglevel]

    if cuvis_il.status_ok != cuvis_il.cuvis_init(settings_path, internal.__CuvisLoglevel__[global_loglevel], logfile_name):
        raise SDKException()


def shutdown():
    cuvis_il.cuvis_shutdown()


def version() -> str:
    return cuvis_il.cuvis_version_swig()


def sdk_version() -> str:
    return version()


def wrapper_version() -> str:
    pip_version = pkg_resources.require('cuvis')[0].version
    with open(Path(__file__).parent.parent / "git-hash.txt", 'r') as f:
        git_hash = f.readline()
        return f'{pip_version} {git_hash}'.strip()


def set_log_level(lvl:  int | str):

    if isinstance(lvl, str):
        # also support string as input argument
        lvl = internal.__strToLogLevel__[lvl]

    cuvis_il.cuvis_set_log_level(internal.__CuvisLoglevel__[lvl])
    logging.basicConfig(level=lvl)
