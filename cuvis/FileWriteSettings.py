from cuvis_il import cuvis_il
from .cuvis_aux import SDKException
from .cuvis_types import PanSharpeningInterpolationType, \
    PanSharpeningAlgorithm, \
    TiffCompressionMode, TiffFormat, \
    OperationMode, ProcessingMode

import cuvis.cuvis_types as internal
import os

from dataclasses import dataclass, fields



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
        ge.export_dir = self.export_dir
        ge.channel_selection = self.channel_selection
        ge.spectra_multiplier = float(self.spectra_multiplier)
        ge.pan_scale = float(self.pan_scale)
        ge.pan_interpolation_type = internal.__CuvisPanSharpeningInterpolationType__[
            self.pan_sharpening_interpolation_type]
        ge.pan_algorithm = internal.__CuvisPanSharpeningAlgorithm__[
            self.pan_sharpening_algorithm]
        ge.add_pan = int(self.add_pan)
        ge.add_fullscale_pan = int(self.add_fullscale_pan)
        ge.permissive = int(self.permissive)
        return ge
    
    @classmethod
    def _from_internal(cls, ge):
        return cls(export_dir=ge.export_dir,
                   channel_selection=ge.channel_selection,
                   spectra_multiplier=ge.spectra_multiplier,
                   pan_sharpening_interpolation_type=internal.__PanSharpeningInterpolationType__[ge.pan_interpolation_type],
                   pan_sharpening_algorithm=internal.__PanSharpeningAlgorithm__[ge.pan_algorithm],
                   add_pan=bool(ge.add_pan),
                   add_fullscale_pan=bool(ge.add_fullscale_pan),
                   permissive=bool(ge.permissive))

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
        ts.compression_mode = internal.__CuvisTiffCompressionMode__[self.compression_mode]
        ts.format = internal.__CuvisTiffFormat__[self.format]
        return ge, ts
    
    @classmethod
    def _from_internal(cls, ge, ts):
        ge = super()._from_internal(ge)
        return cls(**ge.__dict__,
                   compression_mode=internal.__TiffCompressionMode__[ts.compression_mode],
                   format=internal.__TiffFormat__[ts.format])

@dataclass(repr=False)
class ViewExportSettings(GeneralExportSettings):
    userplugin: str = None

    def __post_init__(self):
        if self.userplugin is not None:
            if '<userplugin xmlns="http://cubert-gmbh.de/user/plugin/userplugin.xsd">' in self.userplugin:
                # Seems to be a valid plugin
                return
            if os.path.exists(self.userplugin):
                # Seems to be a valid path to a file, read in
                with open(self.userplugin) as f:
                    self.userplugin = "".join(f.readlines())
            else:
                raise SDKException('Error when validating plugin data. Please provide a valid plugin or a path to a plugin file')
            
    def __repr__(self):
        def short_str(s: str, l: int) -> str:
            return (s[:l] + '...') if len(s) > l else s

        """Returns a string containing but shortens the userplugin field."""
        s = ', '.join(f'{field.name}={getattr(self, field.name)}' if field.name != 'userplugin' else f'{field.name}={short_str(getattr(self, field.name), 15)}' 
                    for field in fields(self))
        return f'{type(self).__name__}({s})'


    def _get_internal(self):
        ge = super()._get_internal()
        vs = cuvis_il.cuvis_export_view_settings_t()
        vs.userplugin = self.userplugin
        return ge, vs
    
    @classmethod
    def _from_internal(cls, ge, vs):
        ge = super()._from_internal(ge)
        return cls(**ge.__dict__, 
                   userplugin=vs.userplugin)

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
        sa.allow_overwrite = int(self.allow_overwrite)
        sa.allow_fragmentation = int(self.allow_fragmentation)
        sa.allow_drop = int(self.allow_drop)
        sa.allow_session_file = int(self.allow_session_file)
        sa.allow_info_file = int(self.allow_info_file)
        sa.operation_mode = internal.__CuvisOperationMode__[self.operation_mode]
        sa.fps = int(self.fps)
        sa.soft_limit = int(self.soft_limit)
        sa.hard_limit = int(self.hard_limit)
        sa.max_buftime = int(self.max_buftime)
        return ge, sa
    
    @classmethod
    def _from_internal(cls, ge, sa):
        ge = super()._from_internal(ge)
        return cls(**ge.__dict__,
                   allow_overwrite = bool(sa.allow_overwrite),
                   allow_fragmentation = bool(sa.allow_fragmentation),
                   allow_drop = bool(sa.allow_drop),
                   allow_session_file = bool(sa.allow_session_file),
                   allow_info_file = bool(sa.allow_info_file),
                   operation_mode = internal.__OperationMode__[sa.operation_mode],
                   fps = sa.fps,
                   soft_limit = sa.soft_limit,
                   hard_limit = sa.hard_limit,
                   max_buftime = sa.max_buftime
                )

@dataclass
class ProcessingArgs(object):
    allow_recalib: bool = False
    processing_mode: ProcessingMode = ProcessingMode.Raw

    def _get_internal(self):
        pa = cuvis_il.cuvis_proc_args_t()
        pa.allow_recalib = int(self.allow_recalib)
        pa.processing_mode = int(internal.__CuvisProcessingMode__[self.processing_mode])
        return pa
    
    @classmethod
    def _from_internal(cls, pa):
        return cls(allow_recalib=bool(pa.allow_recalib),
                   processing_mode=internal.__ProcessingMode__[pa.processing_mode])

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
        wa.worker_count = int(self.worker_count)
        wa.poll_interval = int(self.poll_intervall)
        wa.keep_out_of_sequence = int(self.keep_out_of_sequence)
        wa.worker_queue_hard_limit = int(self.hard_limit)
        wa.worker_queue_soft_limit = int(self.soft_limit)
        wa.can_drop = int(self.can_drop)
        return wa
