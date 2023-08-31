from . import cuvis_il
from .cuvis_aux import SDKException
from .cuvis_types import PanSharpeningInterpolationType, \
    PanSharpeningAlgorithm, \
    TiffCompressionMode, TiffFormat, \
    OperationMode, ProcessingMode

import cuvis.cuvis_types as internal

from dataclasses import dataclass

@dataclass
class GeneralExportSettings(object):
    export_dir: str = '.'
    channel_selection: str = 'all'
    spectra_multiplier: float = 1.0
    pan_scale: float = 0.0
    pan_sharpening_interpolation_type: PanSharpeningInterpolationType = PanSharpeningInterpolationType.Linear
    pan_sharpening_algorithm: PanSharpeningAlgorithm = PanSharpeningAlgorithm.CubertMacroPixel
    add_pan: bool = False
    add_fullscale_pan: bool = False
    permissive: bool = False

    def _get_internal(self):
        ge = cuvis_il.cuvis_export_general_settings_t()
        ge.__setattr__("export_dir", self.export_dir)
        ge.__setattr__("channel_selection", self.channel_selection)
        ge.__setattr__("spectra_multiplier", float(self.spectra_multiplier))
        ge.__setattr__("pan_scale", float(self.pan_scale))
        ge.__setattr__("pan_interpolation_type", internal.__CuvisPanSharpeningInterpolationType__[
            self.pan_sharpening_interpolation_type])
        ge.__setattr__("pan_algorithm", internal.__CuvisPanSharpeningAlgorithm__[
            self.pan_sharpening_algorithm])
        ge.__setattr__("add_pan", int(self.add_pan))
        ge.__setattr__("add_fullscale_pan", int(self.add_fullscale_pan))
        ge.__setattr__("permissive", int(self.permissive))
        return ge
    
    @classmethod
    def _from_internal(cls, ge):
        return cls(export_dir=ge.__getattribute__("export_dir"),
                   channel_selection=ge.__getattribute__("channel_selection"),
                   spectra_multiplier=ge.__getattribute__("spectra_multiplier"),
                   pan_sharpening_interpolation_type=internal.__PanSharpeningInterpolationType__[ge.__getattribute__("pan_interpolation_type")],
                   pan_sharpening_algorithm=internal.__PanSharpeningAlgorithm__[ge.__getattribute__("pan_algorithm")],
                   add_pan=bool(ge.__getattribute__("add_pan")),
                   add_fullscale_pan=bool(ge.__getattribute__("add_fullscale_pan")),
                   permissive=bool(ge.__getattribute__("permissive")))

@dataclass
class EnviExportSettings(GeneralExportSettings):

    def _get_internal(self):
        ge = super()._get_internal()
        es = None
        return ge, es
    
    @classmethod
    def _from_internal(cls, ge, es):
        ge = super()._from_internal(ge)
        return cls(**ge.__dict__)
        


@dataclass
class TiffExportSettings(GeneralExportSettings):
    compression_mode: str = TiffCompressionMode.Nothing
    format: str = TiffFormat.MultiChannel

    def _get_internal(self):
        ge = super()._get_internal()
        ts = cuvis_il.cuvis_export_tiff_settings_t()
        ts.__setattr__("compression_mode",
                       internal.__CuvisTiffCompressionMode__[self.compression_mode])
        ts.__setattr__("format", internal.__CuvisTiffFormat__[self.format])
        return ge, ts
    
    @classmethod
    def _from_internal(cls, ge, ts):
        ge = super()._from_internal(ge)
        return cls(**ge.__dict__,
                   compression_mode=internal.__TiffCompressionMode__[ts.__getattribute__("compression_mode")],
                   format=internal.__TiffFormat__[ts.__getattribute__("format")])

@dataclass
class ViewExportSettings(GeneralExportSettings):
    userplugin: str = None

    def _get_internal(self):
        ge = super()._get_internal()
        vs = cuvis_il.cuvis_export_view_settings_t()
        vs.__setattr__("userplugin", self.userplugin)
        return ge, vs
    
    @classmethod
    def _from_internal(cls, ge, vs):
        ge = super()._from_internal(ge)
        return cls(**ge.__dict__, 
                   userplugin=vs.__getattribute__("userplugin"))

@dataclass
class SaveArgs(GeneralExportSettings):
    allow_overwrite: bool = False
    allow_fragmentation: bool = False
    allow_drop: bool = False
    allow_session_file: bool = True
    allow_info_file: bool = True
    operation_mode: OperationMode = OperationMode.Software
    fps: float = 0.0
    soft_limit: int = 20
    hard_limit: int = 100
    max_buftime: int = 10000

    def _get_internal(self):
        ge = super()._get_internal()
        sa = cuvis_il.cuvis_save_args_t()
        sa.__setattr__("allow_overwrite", int(self.allow_overwrite))
        sa.__setattr__("allow_fragmentation", int(self.allow_fragmentation))
        sa.__setattr__("allow_drop", int(self.allow_drop))
        sa.__setattr__("allow_session_file", int(self.allow_session_file))
        sa.__setattr__("allow_info_file", int(self.allow_info_file))
        sa.__setattr__("operation_mode", internal.__CuvisOperationMode__[self.operation_mode])
        sa.__setattr__("fps", int(self.fps))
        sa.__setattr__("soft_limit", int(self.soft_limit))
        sa.__setattr__("hard_limit", int(self.hard_limit))
        sa.__setattr__("max_buftime", int(self.max_buftime))
        return ge, sa
    
    @classmethod
    def _from_internal(cls, ge, sa):
        ge = super()._from_internal(ge)
        return cls(**ge.__dict__,
                   allow_overwrite = bool(sa.__getattribute__("allow_overwrite")),
                   allow_fragmentation = bool(sa.__getattribute__("allow_fragmentation")),
                   allow_drop = bool(sa.__getattribute__("allow_drop")),
                   allow_session_file = bool(sa.__getattribute__("allow_session_file")),
                   allow_info_file = bool(sa.__getattribute__("allow_info_file")),
                   operation_mode = internal.__OperationMode__[sa.__getattribute__("operation_mode")],
                   fps = sa.__getattribute__("fps"),
                   soft_limit = sa.__getattribute__("soft_limit"),
                   hard_limit = sa.__getattribute__("hard_limit"),
                   max_buftime = sa.__getattribute__("max_buftime")
                )

@dataclass
class ProcessingArgs(object):
    allow_recalib: bool = False
    processing_mode: ProcessingMode = ProcessingMode.Raw

    def _get_internal(self):
        pa = cuvis_il.cuvis_proc_args_t()
        pa.__setattr__("allow_recalib", int(self.allow_recalib))
        pa.__setattr__("processing_mode",
                       int(internal.__CuvisProcessingMode__[self.processing_mode]))
        return pa
    
    @classmethod
    def _from_internal(cls, pa):
        return cls(allow_recalib=bool(pa.__getattribute__("allow_recalib")),
                   processing_mode=internal.__ProcessingMode__[pa.__getattribute__("processing_mode")])

@dataclass
class WorkerSettings(object):
    worker_count: int = 0
    poll_intervall: int = 10
    keep_out_of_sequence: bool = False
    hard_limit: int = 10
    soft_limit: int = 10
    can_drop: bool = True

    def _get_internal(self):
        wa = cuvis_il.cuvis_worker_settings_t()
        wa.__setattr__("worker_count", int(self.worker_count))
        wa.__setattr__("poll_interval", int(self.poll_intervall))
        wa.__setattr__("keep_out_of_sequence", int(self.keep_out_of_sequence))
        wa.__setattr__("worker_queue_hard_limit", int(self.hard_limit))
        wa.__setattr__("worker_queue_soft_limit", int(self.soft_limit))
        wa.__setattr__("can_drop", int(self.can_drop))
        return wa
