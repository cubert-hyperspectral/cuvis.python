from ._cuvis_il import cuvis_il
from .cuvis_aux import SDKException
from .cuvis_types import (
    PanSharpeningInterpolationType,
    PanSharpeningAlgorithm,
    TiffCompressionMode,
    TiffFormat,
    OperationMode,
    ProcessingMode,
    SessionMergeMode,
)

import cuvis.cuvis_types as internal
import os
import warnings

from dataclasses import dataclass, fields, field, InitVar
from typing import Optional


@dataclass
class PanSharpeningSettings(object):
    channel_selection: str = "all"
    spectra_multiplier: int = 1
    pan_scale: float = 0.0
    pan_sharpening_interpolation_type: PanSharpeningInterpolationType = (
        PanSharpeningInterpolationType.Linear
    )
    pan_sharpening_algorithm: PanSharpeningAlgorithm = (
        PanSharpeningAlgorithm.CubertMacroPixel
    )
    pre_pan_sharpen_cube: bool = False
    add_pan: bool = False

    def _get_internal(self) -> cuvis_il.cuvis_pansharpening_settings_t:
        ps = cuvis_il.cuvis_pansharpening_settings_t()
        ps.channel_selection = self.channel_selection
        ps.spectra_multiplier = self.spectra_multiplier
        ps.pan_scale = float(self.pan_scale)
        ps.pan_interpolation_type = internal.__CuvisPanSharpeningInterpolationType__[
            self.pan_sharpening_interpolation_type
        ]
        ps.pan_algorithm = internal.__CuvisPanSharpeningAlgorithm__[
            self.pan_sharpening_algorithm
        ]
        ps.pre_pan_sharpen_cube = int(self.pre_pan_sharpen_cube)
        ps.add_pan = int(self.add_pan)
        return ps

    @classmethod
    def _from_internal(cls, ps: cuvis_il.cuvis_pansharpening_settings_t):
        if ps is None:
            return cls()
        return cls(
            channel_selection=ps.channel_selection,
            spectra_multiplier=ps.spectra_multiplier,
            pan_scale=ps.pan_scale,
            pan_sharpening_interpolation_type=internal.__PanSharpeningInterpolationType__[
                ps.pan_interpolation_type
            ],
            pan_sharpening_algorithm=internal.__PanSharpeningAlgorithm__[
                ps.pan_algorithm
            ],
            pre_pan_sharpen_cube=bool(ps.pre_pan_sharpen_cube),
            add_pan=bool(ps.add_pan),
        )


@dataclass
class GeneralExportSettings(object):
    export_dir: str = "."
    pan_sharpening: PanSharpeningSettings = field(default_factory=PanSharpeningSettings)
    add_fullscale_pan: bool = False
    permissive: bool = False
    channel_selection: InitVar[Optional[str]] = None
    spectra_multiplier: InitVar[Optional[int]] = None
    pan_scale: InitVar[Optional[float]] = None
    pan_sharpening_interpolation_type: InitVar[
        Optional[PanSharpeningInterpolationType]
    ] = None
    pan_sharpening_algorithm: InitVar[Optional[PanSharpeningAlgorithm]] = None
    pre_pan_sharpen_cube: InitVar[Optional[bool]] = None
    add_pan: InitVar[Optional[bool]] = None

    def __post_init__(
        self,
        channel_selection: Optional[str],
        spectra_multiplier: Optional[int],
        pan_scale: Optional[float],
        pan_sharpening_interpolation_type: Optional[PanSharpeningInterpolationType],
        pan_sharpening_algorithm: Optional[PanSharpeningAlgorithm],
        pre_pan_sharpen_cube: Optional[bool],
        add_pan: Optional[bool],
    ) -> None:
        updates = (
            ("channel_selection", channel_selection),
            ("spectra_multiplier", spectra_multiplier),
            ("pan_scale", pan_scale),
            ("pan_sharpening_interpolation_type", pan_sharpening_interpolation_type),
            ("pan_sharpening_algorithm", pan_sharpening_algorithm),
            ("pre_pan_sharpen_cube", pre_pan_sharpen_cube),
            ("add_pan", add_pan),
        )
        owner = type(self)
        used_deprecated = False
        for name, value in updates:
            if value is None or value is getattr(owner, name):
                continue
            setattr(self, name, value)
            used_deprecated = True
        if used_deprecated:
            warnings.warn(
                "Passing flat pan-sharpening attributes directly is deprecated; "
                "use pan_sharpening=PanSharpeningSettings(...) instead.",
                DeprecationWarning,
                stacklevel=2,
            )

    # ---- Backwards compatible “flat” attributes ----
    @property
    def channel_selection(self) -> str:
        return self.pan_sharpening.channel_selection

    @channel_selection.setter
    def channel_selection(self, value: str) -> None:
        self.pan_sharpening.channel_selection = value

    @property
    def spectra_multiplier(self) -> int:
        return self.pan_sharpening.spectra_multiplier

    @spectra_multiplier.setter
    def spectra_multiplier(self, value: int) -> None:
        self.pan_sharpening.spectra_multiplier = value

    @property
    def pan_scale(self) -> float:
        return self.pan_sharpening.pan_scale

    @pan_scale.setter
    def pan_scale(self, value: float) -> None:
        self.pan_sharpening.pan_scale = value

    @property
    def pan_sharpening_interpolation_type(self) -> PanSharpeningInterpolationType:
        return self.pan_sharpening.pan_sharpening_interpolation_type

    @pan_sharpening_interpolation_type.setter
    def pan_sharpening_interpolation_type(
        self, value: PanSharpeningInterpolationType
    ) -> None:
        self.pan_sharpening.pan_sharpening_interpolation_type = value

    @property
    def pan_sharpening_algorithm(self) -> PanSharpeningAlgorithm:
        return self.pan_sharpening.pan_sharpening_algorithm

    @pan_sharpening_algorithm.setter
    def pan_sharpening_algorithm(self, value: PanSharpeningAlgorithm) -> None:
        self.pan_sharpening.pan_sharpening_algorithm = value

    @property
    def pre_pan_sharpen_cube(self) -> bool:
        return self.pan_sharpening.pre_pan_sharpen_cube

    @pre_pan_sharpen_cube.setter
    def pre_pan_sharpen_cube(self, value: bool) -> None:
        self.pan_sharpening.pre_pan_sharpen_cube = value

    @property
    def add_pan(self) -> bool:
        return self.pan_sharpening.add_pan

    @add_pan.setter
    def add_pan(self, value: bool) -> None:
        self.pan_sharpening.add_pan = value

    # ---- End of Backwards compatible “flat” attributes ----

    def _get_internal(self) -> cuvis_il.cuvis_export_general_settings_t:
        ge = cuvis_il.cuvis_export_general_settings_t()
        ge.export_dir = self.export_dir
        ge.add_fullscale_pan = int(self.add_fullscale_pan)
        ge.permissive = int(self.permissive)
        # nested pansharpening struct
        ge.pansharpening_settings = self.pan_sharpening._get_internal()
        return ge

    @classmethod
    def _from_internal(cls, ge: cuvis_il.cuvis_export_general_settings_t):
        ps = getattr(ge, "pansharpening_settings", None)
        pan_sharpening = PanSharpeningSettings._from_internal(ps)
        return cls(
            export_dir=ge.export_dir,
            pan_sharpening=pan_sharpening,
            add_fullscale_pan=bool(ge.add_fullscale_pan),
            permissive=bool(ge.permissive),
        )


@dataclass
class EnviExportSettings(GeneralExportSettings):
    def _get_internal(self):
        ge = super()._get_internal()
        es = None
        return ge, es

    @classmethod
    def _from_internal(cls, ge: cuvis_il.cuvis_export_general_settings_t, es):
        ge = super()._from_internal(ge)
        return cls(**ge.__dict__)


@dataclass
class TiffExportSettings(GeneralExportSettings):
    compression_mode: str = TiffCompressionMode.Nothing
    format: str = TiffFormat.MultiChannel

    def _get_internal(self):
        ge = super()._get_internal()
        ts = cuvis_il.cuvis_export_tiff_settings_t()
        ts.compression_mode = internal.__CuvisTiffCompressionMode__[
            self.compression_mode
        ]
        ts.format = internal.__CuvisTiffFormat__[self.format]
        return ge, ts

    @classmethod
    def _from_internal(
        cls,
        ge: cuvis_il.cuvis_export_general_settings_t,
        ts: cuvis_il.cuvis_export_tiff_settings_t,
    ):
        ge = super()._from_internal(ge)
        return cls(
            **ge.__dict__,
            compression_mode=internal.__TiffCompressionMode__[ts.compression_mode],
            format=internal.__TiffFormat__[ts.format],
        )


@dataclass(repr=False)
class ViewExportSettings(GeneralExportSettings):
    userplugin: InitVar[str] = None
    pan_failback: bool = True

    def __post_init__(
        self,
        channel_selection: Optional[str],
        spectra_multiplier: Optional[int],
        pan_scale: Optional[float],
        pan_sharpening_interpolation_type: Optional[PanSharpeningInterpolationType],
        pan_sharpening_algorithm: Optional[PanSharpeningAlgorithm],
        pre_pan_sharpen_cube: Optional[bool],
        add_pan: Optional[bool],
        userplugin: str,
    ):
        super().__post_init__(
            channel_selection,
            spectra_multiplier,
            pan_scale,
            pan_sharpening_interpolation_type,
            pan_sharpening_algorithm,
            pre_pan_sharpen_cube,
            add_pan,
        )
        self._set_userplugin(userplugin)

    def _set_userplugin(self, up: str):
        if up is not None:
            if (
                '<userplugin xmlns="http://cubert-gmbh.de/user/plugin/userplugin.xsd">'
                in up
            ):
                # Seems to be a valid plugin
                self._userplugin = up
                return
            if os.path.exists(up):
                # Seems to be a valid path to a file, read in
                with open(up) as f:
                    self._userplugin = "".join(f.readlines())
            else:
                raise SDKException(
                    "Error when validating plugin data. Please provide a valid plugin or a path to a plugin file"
                )

    @property
    def userplugin(self) -> str:
        return self._userplugin

    @userplugin.setter
    def userplugin(self, v: str) -> None:
        self._set_userplugin(userplugin=v)

    def __repr__(self):
        def short_str(s: str, l: int) -> str:
            return (s[:l] + "...") if len(s) > l else s

        """Returns a string containing but shortens the userplugin field."""
        s = ", ".join(
            list(f"{field.name}={getattr(self, field.name)}" for field in fields(self))
            + [f"userplugin={short_str(self._userplugin, 15)}"]
        )
        return f"{type(self).__name__}({s})"

    def _get_internal(self):
        ge = super()._get_internal()
        vs = cuvis_il.cuvis_export_view_settings_t()
        vs.userplugin = self.userplugin
        vs.pan_failback = int(self.pan_failback)
        return ge, vs

    @classmethod
    def _from_internal(
        cls,
        ge: cuvis_il.cuvis_export_general_settings_t,
        vs: cuvis_il.cuvis_export_view_settings_t,
    ):
        ge = super()._from_internal(ge)
        return cls(
            **ge.__dict__, userplugin=vs.userplugin, pan_failback=vs.pan_failback
        )


@dataclass
class SaveArgs(GeneralExportSettings):
    merge_mode: SessionMergeMode = SessionMergeMode.Default
    allow_fragmentation: bool = False
    allow_drop: bool = False
    allow_session_file: bool = True
    allow_info_file: bool = True
    operation_mode: OperationMode = OperationMode.Software
    fps: float = 0.0
    soft_limit: int = 20
    hard_limit: int = 100
    max_buftime: int = 10000
    full_export: bool = False

    def _get_internal(self):
        ge = super()._get_internal()
        sa = cuvis_il.cuvis_save_args_t()
        sa.merge_mode = internal.__CuvisSessionMergeMode__[self.merge_mode]
        sa.allow_drop = int(self.allow_drop)
        sa.allow_session_file = int(self.allow_session_file)
        sa.allow_info_file = int(self.allow_info_file)
        sa.operation_mode = internal.__CuvisOperationMode__[self.operation_mode]
        sa.fps = int(self.fps)
        sa.soft_limit = int(self.soft_limit)
        sa.hard_limit = int(self.hard_limit)
        sa.max_buftime = int(self.max_buftime)
        sa.full_export = int(self.full_export)
        return ge, sa

    @classmethod
    def _from_internal(
        cls,
        ge: cuvis_il.cuvis_export_general_settings_t,
        sa: cuvis_il.cuvis_save_args_t,
    ):
        ge = super()._from_internal(ge)
        return cls(
            **ge.__dict__,
            allow_overwrite=bool(sa.allow_overwrite),
            merge_mode=internal.__SessionMergeMode__[sa.merge_mode],
            allow_fragmentation=bool(sa.allow_fragmentation),
            allow_drop=bool(sa.allow_drop),
            allow_session_file=bool(sa.allow_session_file),
            allow_info_file=bool(sa.allow_info_file),
            operation_mode=internal.__OperationMode__[sa.operation_mode],
            fps=sa.fps,
            soft_limit=sa.soft_limit,
            hard_limit=sa.hard_limit,
            max_buftime=sa.max_buftime,
            full_export=sa.full_export,
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
    def _from_internal(cls, pa: cuvis_il.cuvis_proc_args_t):
        return cls(
            allow_recalib=bool(pa.allow_recalib),
            processing_mode=internal.__ProcessingMode__[pa.processing_mode],
        )


@dataclass
class WorkerSettings(object):
    input_queue_size: int = 10
    mandatory_queue_size: int = 4
    supplementary_queue_size: int = 4
    output_queue_size: int = 10
    can_skip_measurements: bool = False
    can_skip_supplementary_steps: bool = True
    can_drop_results: bool = True

    def _get_internal(self):
        wa = cuvis_il.cuvis_worker_settings_t()
        wa.input_queue_size = int(self.input_queue_size)
        wa.mandatory_queue_size = int(self.mandatory_queue_size)
        wa.supplementary_queue_size = int(self.supplementary_queue_size)
        wa.output_queue_size = int(self.output_queue_size)
        wa.can_skip_measurements = int(self.can_skip_measurements)
        wa.can_skip_supplementary_steps = int(self.can_skip_supplementary_steps)
        wa.can_drop_results = int(self.can_drop_results)
        return wa


@dataclass(repr=False)
class ViewerSettings:
    pan_failback: bool = True
    complete: bool = False
    pan_sharpening: PanSharpeningSettings = field(default_factory=PanSharpeningSettings)
    channel_selection: InitVar[Optional[str]] = None
    spectra_multiplier: InitVar[Optional[int]] = None
    pan_scale: InitVar[Optional[float]] = None
    pan_sharpening_interpolation_type: InitVar[
        Optional[PanSharpeningInterpolationType]
    ] = None
    pan_sharpening_algorithm: InitVar[Optional[PanSharpeningAlgorithm]] = None
    pre_pan_sharpen_cube: InitVar[Optional[bool]] = None
    add_pan: InitVar[Optional[bool]] = None
    userplugin: InitVar[str] = None

    def __post_init__(
        self,
        channel_selection: Optional[str],
        spectra_multiplier: Optional[int],
        pan_scale: Optional[float],
        pan_sharpening_interpolation_type: Optional[PanSharpeningInterpolationType],
        pan_sharpening_algorithm: Optional[PanSharpeningAlgorithm],
        pre_pan_sharpen_cube: Optional[bool],
        add_pan: Optional[bool],
        userplugin: str,
    ):
        updates = (
            ("channel_selection", channel_selection),
            ("spectra_multiplier", spectra_multiplier),
            ("pan_scale", pan_scale),
            ("pan_sharpening_interpolation_type", pan_sharpening_interpolation_type),
            ("pan_sharpening_algorithm", pan_sharpening_algorithm),
            ("pre_pan_sharpen_cube", pre_pan_sharpen_cube),
            ("add_pan", add_pan),
        )
        owner = type(self)
        used_deprecated = False
        for name, value in updates:
            if value is None or value is getattr(owner, name):
                continue
            setattr(self, name, value)
            used_deprecated = True
        if used_deprecated:
            warnings.warn(
                "Passing flat pan-sharpening attributes directly is deprecated; "
                "use pan_sharpening=PanSharpeningSettings(...) instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        self._set_userplugin(userplugin)

    def _set_userplugin(self, up: str):
        if up is not None:
            if (
                '<userplugin xmlns="http://cubert-gmbh.de/user/plugin/userplugin.xsd">'
                in up
            ):
                # Seems to be a valid plugin
                self._userplugin = up
                return
            if os.path.exists(up):
                # Seems to be a valid path to a file, read in
                with open(up) as f:
                    self._userplugin = "".join(f.readlines())
            else:
                raise SDKException(
                    "Error when validating plugin data. Please provide a valid plugin or a path to a plugin file"
                )

    @property
    def userplugin(self) -> str:
        return self._userplugin

    @userplugin.setter
    def userplugin(self, v: str) -> None:
        self._set_userplugin(v)

    # ---- Backwards compatible “flat” attributes ----
    @property
    def channel_selection(self) -> str:
        return self.pan_sharpening.channel_selection

    @channel_selection.setter
    def channel_selection(self, value: str) -> None:
        self.pan_sharpening.channel_selection = value

    @property
    def spectra_multiplier(self) -> int:
        return self.pan_sharpening.spectra_multiplier

    @spectra_multiplier.setter
    def spectra_multiplier(self, value: int) -> None:
        self.pan_sharpening.spectra_multiplier = value

    @property
    def pan_scale(self) -> float:
        return self.pan_sharpening.pan_scale

    @pan_scale.setter
    def pan_scale(self, value: float) -> None:
        self.pan_sharpening.pan_scale = value

    @property
    def pan_sharpening_interpolation_type(self) -> PanSharpeningInterpolationType:
        return self.pan_sharpening.pan_sharpening_interpolation_type

    @pan_sharpening_interpolation_type.setter
    def pan_sharpening_interpolation_type(
        self, value: PanSharpeningInterpolationType
    ) -> None:
        self.pan_sharpening.pan_sharpening_interpolation_type = value

    @property
    def pan_sharpening_algorithm(self) -> PanSharpeningAlgorithm:
        return self.pan_sharpening.pan_sharpening_algorithm

    @pan_sharpening_algorithm.setter
    def pan_sharpening_algorithm(self, value: PanSharpeningAlgorithm) -> None:
        self.pan_sharpening.pan_sharpening_algorithm = value

    @property
    def pre_pan_sharpen_cube(self) -> bool:
        return self.pan_sharpening.pre_pan_sharpen_cube

    @pre_pan_sharpen_cube.setter
    def pre_pan_sharpen_cube(self, value: bool) -> None:
        self.pan_sharpening.pre_pan_sharpen_cube = value

    @property
    def add_pan(self) -> bool:
        return self.pan_sharpening.add_pan

    @add_pan.setter
    def add_pan(self, value: bool) -> None:
        self.pan_sharpening.add_pan = value

    def __repr__(self):
        def short_str(s: str, l: int) -> str:
            return (s[:l] + "...") if len(s) > l else s

        """Returns a string containing but shortens the userplugin field."""
        s = ", ".join(
            list(f"{field.name}={getattr(self, field.name)}" for field in fields(self))
            + [f"userplugin={short_str(self._userplugin, 15)}"]
        )
        return f"{type(self).__name__}({s})"

    def _get_internal(self):
        vs = cuvis_il.cuvis_viewer_settings_t()
        vs.userplugin = self.userplugin
        vs.pan_failback = int(self.pan_failback)
        vs.complete = int(self.complete)
        # nested pansharpening struct
        vs.pansharpening_settings = self.pan_sharpening._get_internal()
        return vs

    @classmethod
    def _from_internal(cls, vs: cuvis_il.cuvis_viewer_settings_t):
        return cls(
            userplugin=vs.userplugin,
            pan_scale=float(vs.pan_scale),
            pan_failback=bool(vs.pan_failback),
            complete=bool(vs.complete),
            pan_sharpening=PanSharpeningSettings._from_internal(vs.pan_sharpening),
        )
