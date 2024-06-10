import numpy as np
from enum import Enum

from ._cuvis_il import cuvis_il

def __generateTranslationDict(enum_cls):
    transDict =  {value : cuvis_il.__dict__[value.name] for value in enum_cls }
    return transDict, __inverseTranslationDict(transDict)

def __inverseTranslationDict(translationDict):
        return {v : k for k, v in translationDict.items()}
    


__CuvisMeasurementFlag__ = {
    "POOR_REFERENCE" : cuvis_il.CUVIS_MESU_FLAG_POOR_REFERENCE,
    "OVERILLUMINATED" : cuvis_il.CUVIS_MESU_FLAG_OVERILLUMINATED,
    "POOR_WHITE_BALANCING" : cuvis_il.CUVIS_MESU_FLAG_POOR_WHITE_BALANCING,
    "DARK_INTTIME" : cuvis_il.CUVIS_MESU_FLAG_POOR_WHITE_BALANCING,
    "DARK_TEMP" : cuvis_il.CUVIS_MESU_FLAG_DARK_TEMP,
    "WHITE_INTTIME" : cuvis_il.CUVIS_MESU_FLAG_WHITE_INTTIME,
    "WHITE_TEMP" : cuvis_il.CUVIS_MESU_FLAG_WHITE_TEMP,
    "WHITEDARK_INTTIME" : cuvis_il.CUVIS_MESU_FLAG_WHITEDARK_INTTIME,
    "WHITEDARK_TEMP" : cuvis_il.CUVIS_MESU_FLAG_WHITEDARK_TEMP,
}

__MeasurementFlag__ = __inverseTranslationDict(__CuvisMeasurementFlag__)

class ProcessingMode(Enum):
    Preview = 1
    Raw = 2
    DarkSubtract = 3
    Reflectance = 4
    SpectralRadiance = 5
    
__CuvisProcessingMode__ = {
    ProcessingMode.Preview : cuvis_il.Preview,
    ProcessingMode.Raw : cuvis_il.Cube_Raw,
    ProcessingMode.DarkSubtract : cuvis_il.Cube_DarkSubtract,
    ProcessingMode.Reflectance : cuvis_il.Cube_Reflectance,
    ProcessingMode.SpectralRadiance : cuvis_il.Cube_SpectralRadiance
}

__ProcessingMode__ = __inverseTranslationDict(__CuvisProcessingMode__)

class DataType(Enum):
    data_type_unsupported = 1
    data_type_image = 2
    data_type_gps = 3
    data_type_string = 4
    data_type_sensor_info = 5

__CuvisDataType__, __DataType__ = __generateTranslationDict(DataType)

class ReferenceType(Enum):
    Dark = 1
    White = 2
    WhiteDark = 3
    SpRad = 4
    Distance = 5

__CuvisReferenceType__= {
    ReferenceType.Dark : cuvis_il.Reference_Dark,
    ReferenceType.White : cuvis_il.Reference_White,
    ReferenceType.WhiteDark : cuvis_il.Reference_WhiteDark,
    ReferenceType.SpRad : cuvis_il.Reference_SpRad,
    ReferenceType.Distance : cuvis_il.Reference_Distance
}

__ReferenceType__ = __inverseTranslationDict(__CuvisReferenceType__)

class SessionItemType(Enum):
    all_frames = 1
    no_gaps = 2
    references = 3


__CuvisSessionItemType__ = {
    SessionItemType.all_frames : cuvis_il.session_item_type_frames,
    SessionItemType.no_gaps : cuvis_il.session_item_type_frames_no_gaps,
    SessionItemType.references : cuvis_il.session_item_type_references
}

DataFormat = dict({
    (1, np.uint8),
    (2, np.uint16),
    (3, np.uint32),
    (4, np.float32)
})

class PanSharpeningInterpolationType(Enum):
    NearestNeighbour = 1
    Linear = 2
    Cubic = 3
    Lanczos = 4

__CuvisPanSharpeningInterpolationType__ = {
    PanSharpeningInterpolationType.NearestNeighbour :
     cuvis_il.pan_sharpening_interpolation_type_NearestNeighbor,
    PanSharpeningInterpolationType.Linear : cuvis_il.pan_sharpening_interpolation_type_Linear,
    PanSharpeningInterpolationType.Cubic : cuvis_il.pan_sharpening_interpolation_type_Cubic,
    PanSharpeningInterpolationType.Lanczos : cuvis_il.pan_sharpening_interpolation_type_Lanczos,
}

__PanSharpeningInterpolationType__ = __inverseTranslationDict(__CuvisPanSharpeningInterpolationType__)

class PanSharpeningAlgorithm(Enum):
    Noop = 1
    CubertMacroPixel = 2
    CubertPanRatio = 3
    AlphaBlendOverlay = 4

__CuvisPanSharpeningAlgorithm__ = {
    PanSharpeningAlgorithm.Noop : cuvis_il.pan_sharpening_algorithm_Noop,
    PanSharpeningAlgorithm.CubertMacroPixel : cuvis_il.pan_sharpening_algorithm_CubertMacroPixel,
    PanSharpeningAlgorithm.CubertPanRatio : cuvis_il.pan_sharpening_algorithm_CubertPanRatio,
    PanSharpeningAlgorithm.AlphaBlendOverlay : cuvis_il.pan_sharpening_algorithm_AlphablendPanOverlay
}

__PanSharpeningAlgorithm__ = __inverseTranslationDict(__CuvisPanSharpeningAlgorithm__)

class TiffCompressionMode(Enum):
    Nothing = 1
    LZW = 2


__CuvisTiffCompressionMode__ = {
    TiffCompressionMode.Nothing : cuvis_il.tiff_compression_mode_None,
    TiffCompressionMode.LZW : cuvis_il.tiff_compression_mode_LZW,
}

__TiffCompressionMode__ = __inverseTranslationDict(__CuvisTiffCompressionMode__)

class TiffFormat(Enum):
    Single = 1
    MultiChannel = 2
    MultiPage = 3

__CuvisTiffFormat__ = {
    TiffFormat.Single : cuvis_il.tiff_format_Single,
    TiffFormat.MultiChannel : cuvis_il.tiff_format_MultiChannel,
    TiffFormat.MultiPage : cuvis_il.tiff_format_MultiPage,
}

__TiffFormat__ = __inverseTranslationDict(__CuvisTiffFormat__)

class HardwareState(Enum):
    Online = 1
    PartiallyOnline = 2
    Offline = 3

__CuvisHardwareState__ = {
    HardwareState.Online : cuvis_il.hardware_state_online,
    HardwareState.PartiallyOnline : cuvis_il.hardware_state_partially_online,
    HardwareState.Offline : cuvis_il.hardware_state_offline,
}

__HardwareState__ = __inverseTranslationDict(__CuvisHardwareState__)

class OperationMode(Enum):
    External = 1
    Internal = 2
    Software = 3
    UNDEFINED = 4

__CuvisOperationMode__ = {
    OperationMode.External : cuvis_il.OperationMode_External,
    OperationMode.Internal : cuvis_il.OperationMode_Internal,
    OperationMode.Software : cuvis_il.OperationMode_Software,
    OperationMode.UNDEFINED : cuvis_il.OperationMode_Undefined,
}

__OperationMode__ = __inverseTranslationDict(__CuvisOperationMode__)

class ComponentType(Enum):
    ImageSensor = 1
    MiscSensor = 2

__CuvisComponentType__ = {
    ComponentType.ImageSensor : cuvis_il.component_type_image_sensor,
    ComponentType.MiscSensor : cuvis_il.component_type_misc_sensor,
}

__ComponentType__ = __inverseTranslationDict(__CuvisComponentType__)

class AsyncResult(Enum):
    done = 0
    timeout = 1
    overwritten = 2
    deferred = 3


CUVIS_imbuffer_format = dict({
    ("imbuffer_format_uint8", cuvis_il.imbuffer_format_uint8),
    ("imbuffer_format_uint16", cuvis_il.imbuffer_format_uint16),
    ("imbuffer_format_uint32", cuvis_il.imbuffer_format_uint32),
    ("imbuffer_format_float", cuvis_il.imbuffer_format_float),
})

__CuvisCapabilities__ = {
    "AcquisitionCapture" : cuvis_il.CUVIS_MODE_CAPABILITY_ACQUISITION_CAPTURE,
    "AcquisitionTimelapse" :
     cuvis_il.CUVIS_MODE_CAPABILITY_ACQUISITION_TIMELAPSE,
    "AcquisitionContinuous" :
     cuvis_il.CUVIS_MODE_CAPABILITY_ACQUISITION_CONTINUOUS,
    
        "AcquisitionSnapshot"
         :
        cuvis_il.CUVIS_MODE_CAPABILITY_ACQUISITION_SNAPSHOT,
    "AcquisitionSetIntegrationtime" :
     cuvis_il.CUVIS_MODE_CAPABILITY_ACQUISITION_SETINTEGRATIONTIME,
    "AcquisitionSetGain" : cuvis_il.CUVIS_MODE_CAPABILITY_ACQUISITION_SETGAIN,
    "AcquisitionAveraging" :
     cuvis_il.CUVIS_MODE_CAPABILITY_ACQUISITION_AVERAGING,
    "ProcessingSensorRaw" :
     cuvis_il.CUVIS_MODE_CAPABILITY_PROCESSING_SENSOR_RAW,
    "ProcessingCubeRaw" : cuvis_il.CUVIS_MODE_CAPABILITY_PROCESSING_CUBE_RAW,
    "ProcessingCubeRef" : cuvis_il.CUVIS_MODE_CAPABILITY_PROCESSING_CUBE_REF,
    "ProcessingCubeDarkSubtract" :
     cuvis_il.CUVIS_MODE_CAPABILITY_PROCESSING_CUBE_DARKSUBTRACT,
    "ProcessingCubeFlatFielding" :
     cuvis_il.CUVIS_MODE_CAPABILITY_PROCESSING_CUBE_FLATFIELDING,
    "ProcessingCubeSpectralRadiance" :
     cuvis_il.CUVIS_MODE_CAPABILITY_PROCESSING_CUBE_SPECTRALRADIANCE,
    "ProcessingSaveFile" : cuvis_il.CUVIS_MODE_CAPABILITY_PROCESSING_SAVE_FILE,
    "ProcessingClearRaw" : cuvis_il.CUVIS_MODE_CAPABILITY_PROCESSING_CLEAR_RAW,
    "ProcessingCalcLive" : cuvis_il.CUVIS_MODE_CAPABILITY_PROCESSING_CALC_LIVE,
    "ProcessingAutoExposure" :
     cuvis_il.CUVIS_MODE_CAPABILITY_PROCESSING_AUTOEXPOSURE,
    "ProcessingOrientation" :
     cuvis_il.CUVIS_MODE_CAPABILITY_PROCESSING_ORIENTATION,
    "ProcessingSetWhite" : cuvis_il.CUVIS_MODE_CAPABILITY_PROCESSING_SET_WHITE,
    "ProcessingSetDark" : cuvis_il.CUVIS_MODE_CAPABILITY_PROCESSING_SET_DARK,
    "ProcessingSetSprad" :
     cuvis_il.CUVIS_MODE_CAPABILITY_PROCESSING_SET_SPRADCALIB,
    "ProcessingSetDistanceCalib" :
     cuvis_il.CUVIS_MODE_CAPABILITY_PROCESSING_SET_DISTANCECALIB,
    "ProcessingSetDistanceValue" :
     cuvis_il.CUVIS_MODE_CAPABILITY_PROCESSING_SET_DISTANCE_VALUE,
    "ProcessingUseDarkSpradcalib" :
     cuvis_il.CUVIS_MODE_CAPABILITY_PROCESSING_USE_DARK_SPRADCALIB,
    "ProcessingUseWhiteSpradCalib" :
     cuvis_il.CUVIS_MODE_CAPABILITY_PROCESSING_USE_WHITE_SPRADCALIB,
    "ProcessingRequireWhiteDarkReflectance" :
     cuvis_il.CUVIS_MODE_CAPABILITY_PROCESSING_REQUIRE_WHITEDARK_REFLECTANCE,
    "UNDEFINED" : 2 ** 26
}

__Capabilities__ = __inverseTranslationDict(__CuvisCapabilities__)