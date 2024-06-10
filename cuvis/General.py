import logging
import os
import platform

from ._cuvis_il import cuvis_il
from .cuvis_aux import SDKException
from .cuvis_types import ComponentType

import cuvis.cuvis_types as internal

from dataclasses import dataclass

class General(object):
    def __init__(self, path=""):
        log_path = "."
        FORMAT = '%(asctime)s -- %(levelname)s: %(message)s'
        if os.path.exists(path):
            log_path = path + os.sep
        elif platform.system() == "Linux":
            log_path = os.path.expanduser('~') + os.sep + ".cuvis" + os.sep
            if not os.path.exists(log_path):
                os.mkdir(log_path)
        elif platform.system() == "Windows":
            log_path = os.getenv('APPDATA') + os.sep + ".cuvis" + os.sep
            if not os.path.exists(log_path):
                os.mkdir(log_path)
                
        if os.path.exists(log_path):
            logging.basicConfig(filename=log_path + "cuvisSDK_python.log",
                                format=FORMAT,
                                encoding='utf-8',
                                level=logging.DEBUG,
                                filemode='w')
        else:
            raise SDKException(
                "path {} does not exist...".format(os.path.abspath(log_path)))
        logging.info("Logger ready.")

        if cuvis_il.status_ok != cuvis_il.cuvis_init(log_path):
            raise SDKException()
        pass

    @property
    def version(self) -> str:
        return cuvis_il.cuvis_version_swig()

    def set_log_level(self, lvl):
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
