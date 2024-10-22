from .cuvis_aux import SessionData, Capabilities, MeasurementFlags, SensorInfo, GPSData, CalibrationInfo
from .cuvis_types import OperationMode, HardwareState, ProcessingMode, PanSharpeningInterpolationType, \
    PanSharpeningAlgorithm, TiffCompressionMode, TiffFormat, ComponentType, ReferenceType, SessionItemType
from .Worker import Worker, WorkerResult
from .Viewer import Viewer
from .SessionFile import SessionFile
from .ProcessingContext import ProcessingContext
from .Measurement import Measurement
from .General import init, shutdown, version, set_log_level
from .FileWriteSettings import GeneralExportSettings, SaveArgs, \
    ProcessingArgs, \
    EnviExportSettings, TiffExportSettings, ViewExportSettings, \
    WorkerSettings, ViewerSettings
from .Export import CubeExporter, EnviExporter, TiffExporter, ViewExporter
from .Calibration import Calibration
from .AcquisitionContext import AcquisitionContext
import os
import platform
import sys

lib_dir = os.getenv("CUVIS")
if lib_dir is None:
    print('CUVIS environmental variable is not set!')
    sys.exit(1)
if platform.system() == "Windows":
    os.add_dll_directory(lib_dir)
    add_il = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
    os.environ['PATH'] += os.pathsep + add_il
    sys.path.append(str(add_il))
elif platform.system() == 'Linux':
    os.environ['PATH'] = lib_dir + os.pathsep + os.environ['PATH']
else:
    raise NotImplementedError('Invalid operating system detected!')
    # sys.exit(1)


del os, platform, sys
