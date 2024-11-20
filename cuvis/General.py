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


def init(settings_path: str = ".", log_path: str = "", global_loglevel: int = logging.DEBUG):
    FORMAT = '%(asctime)s -- %(levelname)s: %(message)s'
    if os.path.exists(log_path):
        pass
    elif platform.system() == "Linux":
        log_path = os.path.join(os.path.expanduser('~'), ".cuvis")
        os.makedirs(log_path, exist_ok=True)
    elif platform.system() == "Windows":
        log_path = "C:\\ProgramData\\cuvis"
        os.makedirs(log_path, exist_ok=True)

    if os.path.exists(log_path):
        logging.basicConfig(filename=os.path.join(log_path, "cuvisSDK_python.log"),
                            format=FORMAT,
                            encoding='utf-8',
                            level=global_loglevel,
                            filemode='w')
    else:
        raise SDKException(
            "path {} does not exist...".format(os.path.abspath(log_path)))
    logging.info("Logger ready.")

    if cuvis_il.status_ok != cuvis_il.cuvis_init(settings_path, internal.__CuvisLoglevel__[global_loglevel]):
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


def set_log_level(lvl):
    lvl_dict = {"info": {"cuvis": cuvis_il.loglevel_info,
                         "logging": logging.INFO},
                "debug": {"cuvis": cuvis_il.loglevel_debug,
                          "logging": logging.DEBUG},
                "error": {"cuvis": cuvis_il.loglevel_error,
                          "logging": logging.ERROR},
                "fatal": {"cuvis": cuvis_il.loglevel_fatal,
                          "logging": logging.CRITICAL},
                "warning": {"cuvis": cuvis_il.loglevel_warning,
                            "logging": logging.WARNING},
                }

    cuvis_il.cuvis_set_log_level(lvl_dict[lvl]["cuvis"])
    logging.basicConfig(level=lvl_dict[lvl]["logging"])


@dataclass
class ComponentInfo(object):
    type: ComponentType = None
    display_name: str = None
    sensor_info: str = None
    user_field: str = None
    pixel_format: str = None

    def _get_internal(self):
        ci = cuvis_il.cuvis_component_info_t()
        ci.type = internal.__CuvisComponentType__[self.type]
        ci.displayname = self.display_name
        ci.sensorinfo = self.sensor_info
        ci.userfield = self.user_field
        ci.pixelformat = self.pixel_format
        return ci

    @classmethod
    def _from_internal(cls, ci):
        return cls(type=internal.__ComponentType__[ci.type],
                   display_name=ci.displayname,
                   sensor_info=ci.sensorinfo,
                   user_field=ci.userfield,
                   pixel_format=ci.pixelformat)
