# Changelog

All notable changes to the `cuvis` Python wrapper are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Entry wording follows the conventions in [CONTRIBUTING.md](CONTRIBUTING.md#changelog-conventions) - every API entry names the fully qualified symbol first, then states the change with one of the fixed predicates.

Versions are `MAJOR.MINOR.PATCH.TWEAK`.
`MAJOR.MINOR.PATCH` is the cuvis SDK release the wrapper targets; `TWEAK` counts wrapper-only revisions against that same SDK.
See [CONTRIBUTING.md](CONTRIBUTING.md#version-scheme) for the full scheme.

Entries for versions released before this file existed were reconstructed from the published PyPI artifacts and from an AST-level diff of the public `cuvis` API surface between the corresponding commits.
Pre-releases (`b*`, `rc*`) are not listed.

## [Unreleased]

### Added

- `CI` - `.github/workflows/ci.yml` runs the test suite and a lint job enforcing `ruff check` and `ruff format --check` on every pull request and on every push to `develop` and `main`.
- `CI` - `.github/workflows/release.yml` is driven by `v*.*.*.*` tags: it validates the tag against `pyproject.toml` and against this file, builds, publishes to TestPyPI, and publishes to PyPI plus a GitHub Release after manual approval.
- `CI` - `scripts/check_changelog.py` validates this file's structure (header format, allowed section names, descending versions) and the tag/version/changelog agreement at release time.
- `CONTRIBUTING.md` - documents the branch model, the version scheme, the changelog conventions and the release checklist.
- `pyproject.toml` - `dev` extra pinning `ruff==0.16.3`, plus `[tool.ruff]` configuration selecting the `E4`, `E7`, `E9` and `F` rule sets.

### Changed

- Whole tree reformatted with `ruff format`; no behaviour change.
- `README.md` - documents the version scheme, and lists Python 3.14 among the supported interpreters as `pyproject.toml` already did.
- `prebuild.py` - writes `cuvis/git-hash.txt` instead of `git-hash.txt` at the repository root, so the file lands inside the package that declares it as package data.
- `cuvis.FileWriteSettings.GeneralExportSettings.__repr__`, `cuvis.FileWriteSettings.ViewerSettings.__repr__` - the docstring that sat below the nested helper, where it was a dead expression rather than a docstring, moved to the top of the method.

### Removed

- `CI` - `.github/workflows/tests.yml` and `.github/workflows/publish_version.yml` removed; their jobs moved into `ci.yml` and `release.yml`.
- `git-hash.txt` at the repository root - removed; the file is generated into `cuvis/` by `prebuild.py` and is no longer tracked.
- Unused imports and locals dropped from `cuvis.AcquisitionContext`, `cuvis.Export`, `cuvis.General`, `cuvis.Measurement`, `cuvis.Viewer`, `cuvis.Worker`, `cuvis.cuvis_aux`, `cuvis.doc` and the test modules; no public name was removed.

### Fixed

- `cuvis.General.wrapper_version` - raised `FileNotFoundError` on every pip-installed release since 3.3.1, because it read `git-hash.txt` from the directory above the package while no distribution ever shipped that file.
  The hash is now read from `cuvis/git-hash.txt`, which the wheel and the sdist do ship, and a missing file degrades to reporting the version alone instead of raising.
- `tests/test_general.py` - `test_wrapper_version` asserted the literal `3.5.3`, so it had to be edited on every SDK bump and passed only because an editable install exposed the untracked root `git-hash.txt`.
  It now compares against the installed distribution version.

## [3.5.3.2] - 2026-08-19

Targets cuvis SDK 3.5.3.
Wrapper-only revision.

### Added

- `cuvis.cube_utils.ImageData.spectrum` - new property returning the single spectrum of a point-spectrometer measurement as a 1-D `np.ndarray`.
- `cuvis.cube_utils.ImageData.is_spectrum` - new property, `True` when the buffer is a `1 x 1 x N` point spectrum rather than a cube.
- `cuvis.cube_utils.ImageData.shape` - new property returning the buffer shape as a tuple, or `None` when no buffer is attached.
- `cuvis.cube_utils.ImageData.dtype` - new property returning the numpy dtype of the underlying buffer.
- `cuvis.cube_utils.ImageData.__array__` - new method, so `np.asarray(image_data)` and any numpy call accepting an array-like now work directly.
- `cuvis.cube_utils.ImageData.__array_ufunc__` - new method, so numpy ufuncs applied to an `ImageData` return plain `np.ndarray` results.
- `cuvis.cube_utils.ImageData.__repr__` - new method reporting shape, dtype and spectrum-ness.

### Changed

- `cuvis.cube_utils.ImageData.from_array` - parameters `width`, `height` and `channels` gained the default `None`; they are inferred from the array shape when omitted.
- `cuvis.cube_utils.ImageData.__getitem__` - return type changed from `Union[np.ndarray, tuple[np.ndarray, np.ndarray], object]` to `Union[np.ndarray, tuple, ImageData, np.generic]`; band slices now come back wrapped as `ImageData` and scalar reads as numpy scalars.

### Fixed

- `cuvis.cube_utils.ImageData` - reading a qmini point spectrum failed because the `1 x 1 x N` buffer shape was not handled in the indexing path.
- `cuvis.cube_utils.ImageData` - comparing against a scalar (`cube > 500`) raised `TypeError`; comparisons now dispatch through the numpy protocol and return a boolean array.

## [3.5.3.1] - 2026-06-02

Targets cuvis SDK 3.5.3.
Wrapper-only revision.

### Added

- `cuvis.FileWriteSettings.SaveArgs.allow_overwrite` - new field, default `False`, mapping to the SDK's `allow_overwrite` save flag.

### Changed

- `cuvis.FileWriteSettings.PanSharpeningSettings.spectra_multiplier` - type changed from `int` to `float`, matching the SDK field.
- `cuvis.cuvis_aux.SensorInfo.temperature` - type changed from `int` to `float`, matching the SDK field.

### Removed

- `cuvis.FileWriteSettings.SaveArgs.allow_fragmentation` - removed; the field never mapped to an SDK flag of that name.
  Use `allow_overwrite`, or `SaveArgs.merge_mode` for fragmentation behaviour.

### Fixed

- `cuvis.FileWriteSettings.SaveArgs` - `pan_scale` was coerced with `float()` on the way into the SDK struct although the SDK expects the value unconverted; the redundant cast was removed.

## [3.5.3.0] - 2026-06-01

Targets cuvis SDK 3.5.3.
SDK synchronisation release; the wrapper's public API is unchanged from 3.5.1.0.

### Changed

- `README.md` - the link to the cuvis C SDK was made more prominent.

## [3.5.1.0] - 2026-02-25

Targets cuvis SDK 3.5.1.
SDK synchronisation release; the wrapper's public API is unchanged from 3.5.0.2.

### Added

- `CI` - `.github/workflows/publish_version.yml`, a manually dispatched PyPI/TestPyPI publish workflow restricted to repository admins.

## [3.5.0.2] - 2026-01-12

Targets cuvis SDK 3.5.0.
Wrapper-only revision.

### Added

- `tests/` - first unit-test suite for the wrapper, covering acquisition, cube utilities, export, general, measurement, processing context, session file and worker.

### Changed

- `cuvis.FileWriteSettings.WorkerSettings.input_queue_size` - default changed from `0` to `10`; `0` disabled the input queue entirely, which is never what a caller constructing `WorkerSettings()` wants.

### Fixed

- `cuvis.FileWriteSettings.ViewerSettings.__post_init__` - constructing `ViewerSettings()` without arguments took the deprecation path for the pan-sharpening keywords, because a value equal to the class default was indistinguishable from an explicitly passed one.
  Defaults are now compared against the class attribute and skipped.

## [3.5.0.1] - 2025-12-27

Targets cuvis SDK 3.5.0.
Wrapper-only revision.

### Fixed

- `cuvis.FileWriteSettings.GeneralExportSettings`, `cuvis.FileWriteSettings.ViewerSettings` - `channel_selection`, `spectra_multiplier`, `pan_scale`, `pan_sharpening_interpolation_type`, `pan_sharpening_algorithm`, `pre_pan_sharpen_cube` and `add_pan` could no longer be passed to the constructor after 3.5.0 turned them into properties.
  They are accepted again as deprecated `InitVar` keywords that forward to `pan_sharpening`.

## [3.5.0] - 2025-12-23

Targets cuvis SDK 3.5.0.

### Added

- `cuvis.FileWriteSettings.PanSharpeningSettings` - new dataclass grouping every pan-sharpening option (`channel_selection`, `spectra_multiplier`, `pan_scale`, `pan_sharpening_interpolation_type`, `pan_sharpening_algorithm`, `pre_pan_sharpen_cube`, `add_pan`).
- `cuvis.FileWriteSettings.GeneralExportSettings.pan_sharpening`, `cuvis.FileWriteSettings.ViewerSettings.pan_sharpening` - new field holding a default-constructed `PanSharpeningSettings`.
- `cuvis.cuvis_types.SessionMergeMode` - new enum with members `Default = 0`, `Fragmentation = 1`, `Merge = 2`.
- `cuvis.FileWriteSettings.SaveArgs.merge_mode` - new field, default `SessionMergeMode.Default`.
- `cuvis.cuvis_types.PanSharpeningAlgorithm.PCAFusion` - new enum member with value `4`.
- `cuvis.AcquisitionContext.AcquisitionContext.dead_pixel_correction` - new property setter.
- `cuvis.AcquisitionContext.AcquisitionContext.dead_pixel_correction_available` - new read-only property.

### Changed

- `cuvis.FileWriteSettings.GeneralExportSettings.channel_selection`, `.spectra_multiplier`, `.pan_scale`, `.pan_sharpening_interpolation_type`, `.pan_sharpening_algorithm`, `.pre_pan_sharpen_cube`, `.add_pan` - fields became properties with setters that delegate to `pan_sharpening`.
- `cuvis.FileWriteSettings.ViewerSettings.channel_selection`, `.spectra_multiplier`, `.pan_scale`, `.pan_sharpening_interpolation_type`, `.pan_sharpening_algorithm`, `.pre_pan_sharpen_cube`, `.add_pan` - fields became properties with setters that delegate to `pan_sharpening`.
- `cuvis.ProcessingContext.ProcessingContext.__init__` - new parameter `load_references: bool = True`, so reference loading can be skipped explicitly.
- `cuvis.General.version` - version reporting switched from `pkg_resources` to `importlib.metadata.version`.
- `pyproject.toml` - `cuvis-il` requirement raised from `>3.3.1` to `>=3.5.0,<3.6.0`.

### Removed

- `cuvis.cuvis_types.PanSharpeningAlgorithm.AlphaBlendOverlay` - removed; the SDK dropped the algorithm.
  Value `4` is now `PCAFusion`.
- `cuvis.FileWriteSettings.ViewerSettings.blend_opacity` - removed together with `AlphaBlendOverlay`.
- `cuvis.FileWriteSettings.SaveArgs.allow_overwrite` - removed in favour of `SaveArgs.merge_mode`.
  Reinstated in 3.5.3.1.

### Fixed

- `cuvis` - dead-pixel-correction and pan-sharpening wrapper code wrote wrong values into the SDK structs.

## [3.4.1.1] - 2026-03-12

Targets cuvis SDK 3.4.1.
Wrapper-only revision, released from `release/v3.4` after the 3.5 line had already opened.
The wrapper's public API is unchanged from 3.4.1.

### Changed

- `cuvis.General.version` - version reporting switched from `pkg_resources` to `importlib.metadata.version`, so the wrapper no longer depends on the removed `pkg_resources` API.
  Backport of the same change made on `main` for 3.5.0.

## [3.4.1] - 2025-10-01

Targets cuvis SDK 3.4.1.

### Changed

- `cuvis.Viewer.Viewer.apply` - return type changed from `dict[str, ImageData]` to `Union[dict[str, ImageData], ImageData]`; a single-view configuration returns the image directly.
- `pyproject.toml` - `cuvis-il` requirement raised from `>3.3.1` to `>=3.4.0,<3.5.0`.

## [3.4.0.post1] - 2025-07-03

Targets cuvis SDK 3.4.0.
Packaging-only re-release.

### Changed

- `pyproject.toml` - `cuvis-il` requirement capped at `<3.5.0`, so a 3.4 wrapper install cannot pull a 3.5 interface layer.

## [3.4.0] - 2025-07-02

Targets cuvis SDK 3.4.0.

### Added

- `cuvis.cuvis_aux.ComponentInfo` - new dataclass with fields `display_name`, `pixel_format`, `sensor_info`, `type` and `user_field`.
  Replaces `cuvis.General.ComponentInfo`.
- `cuvis.cuvis_aux.CalibrationInfo.cube_width`, `.cube_height`, `.cube_channels`, `.cube_wavelengths` - new fields exposing the calibrated cube geometry.
- `cuvis.cuvis_aux.SensorInfo.integration_time` - new field of type `float`.
- `cuvis.FileWriteSettings.ViewExportSettings.pan_failback`, `cuvis.FileWriteSettings.ViewerSettings.pan_failback` - new field, default `True`.
- `cuvis.General.init` - new parameter `logfile_name: Optional[str] = None`, making the log file name configurable.
- The settings directory can be supplied through an environment variable instead of only through `cuvis.General.init(settings_path=...)`.

### Changed

- `cuvis.General.init` - parameter `global_loglevel` type changed from `int` to `Union[int, str]`, so level names are accepted.
- `cuvis.General.set_log_level` - parameter `lvl` type changed from unannotated to `Union[int, str]`.

### Removed

- `cuvis.General.init` - parameter `log_path` removed; use `logfile_name`.
- `cuvis.General.ComponentInfo` - removed; moved to `cuvis.cuvis_aux.ComponentInfo`.
- `cuvis.AcquisitionContext.AcquisitionContext.binning` - property setter removed; the SDK no longer exposes a binning toggle.
- `cuvis.AcquisitionContext.AcquisitionContext.set_binning_async` - removed together with the `binning` setter.
- `cuvis.cuvis_aux.SensorInfo.binning` - removed together with the `binning` setter.

### Fixed

- `cuvis` - type annotations that were invalid on Python 3.9 corrected, restoring the declared `requires-python = ">=3.9"` floor.
- `cuvis.Viewer.Viewer` - incorrect return annotation corrected.

## [3.3.3] - 2025-05-19

Targets cuvis SDK 3.3.3.

### Changed

- `cuvis.Measurement.Measurement.name`, `.comment` - fields became properties with setters, replacing `set_name` and `set_comment`.
- `cuvis.Measurement.Measurement.assembly`, `.averages`, `.capture_time`, `.distance`, `.factory_calibration`, `.frame_id`, `.integration_time`, `.measurement_flags`, `.path`, `.processing_mode`, `.product_name`, `.serial_number`, `.session_info` - fields became read-only properties, so the values are read from the SDK on access instead of being snapshotted at construction.

### Removed

- `cuvis.Measurement.Measurement.set_name` - removed; assign to the `name` property.
- `cuvis.Measurement.Measurement.set_comment` - removed; assign to the `comment` property.

## [3.3.2] - 2025-03-17

Targets cuvis SDK 3.3.2.
The wrapper's public API is unchanged from 3.3.1.

### Changed

- Build metadata moved from `setup.py` to `pyproject.toml`; the package is built with the setuptools PEP 517 backend.

## [3.3.1] - 2025-03-05

Targets cuvis SDK 3.3.1.

### Added

- `cuvis.cube_utils.ImageData` - new class, moved out of `cuvis.Measurement`.
- `cuvis.cube_utils.ImageData.from_array` - new classmethod building an `ImageData` from an `np.ndarray` plus `width`, `height`, `channels` and optional `wavelength`.
- `cuvis.cube_utils.ImageData.to_numpy` - new method returning the buffer as an `np.ndarray`.
- `cuvis.Measurement.Measurement.cube` - new property returning the cube as `ImageData`.
- `cuvis.SessionFile.SessionFile.thumbnail` - new property returning the thumbnail as `ImageData`, replacing `get_thumbnail`.
- `cuvis.Calibration.Calibration.info` - new property returning a `CalibrationInfo`, replacing `get_info`.
- `cuvis.AcquisitionContext.AcquisitionContext.ready` - new read-only property.
- `cuvis.AcquisitionContext.AcquisitionContext.register_ready_callback` - new method taking `Callable[None, Awaitable[None]]`.
- `cuvis.AcquisitionContext.AcquisitionContext.reset_ready_callback` - new method clearing the registered callback.
- `cuvis.FileWriteSettings.ViewerSettings` - new dataclass for `Viewer` configuration, with `complete`, `blend_opacity`, `pan_scale`, `pan_sharpening_algorithm`, `pan_sharpening_interpolation_type`, `pre_pan_sharpen_cube` and a `userplugin` setter.
- `cuvis.General.sdk_version` - new function returning the loaded SDK version.
- `cuvis.General.wrapper_version` - new function returning the wrapper's own version, distinct from the SDK version.

### Changed

- `cuvis.Viewer.Viewer.__init__` - parameter `settings` type changed from `Union[int, ViewExportSettings]` to `Union[int, ViewerSettings]`.
- `cuvis.AcquisitionContext.AcquisitionContext.capture` - new parameter `to_interal = False`, and the return type changed from `AsyncMesu` to `Optional[AsyncMesu]`.
- `cuvis.Measurement.Measurement.__init__` - parameter `base` type changed from `Union[int, str]` to `Union[int, str, Path]`.
- `cuvis.SessionFile.SessionFile.get_measurement` - parameter `frameNo` gained the default `0`.
- `cuvis.Async.AsyncMesu.get`, `cuvis.Viewer.Viewer.apply`, `cuvis.cuvis_aux.Bitset.strings` - return annotations switched from `typing.Tuple`/`Dict`/`List` to the builtin generics.

### Removed

- `cuvis.Measurement.ImageData` - removed; moved to `cuvis.cube_utils.ImageData`.
- `cuvis.SessionFile.SessionFile.get_thumbnail` - removed; use the `thumbnail` property.
- `cuvis.Calibration.Calibration.get_info` - removed; use the `info` property, which returns `CalibrationInfo` instead of the raw `cuvis_calibration_info_t`.

## [3.3.0.post1] - 2024-09-30

Targets cuvis SDK 3.3.0.
Packaging-only re-release; no source change is recorded in the repository for this version.

## [3.3.0] - 2024-09-30

Targets cuvis SDK 3.3.0.

### Added

- `cuvis.General.init`, `cuvis.General.shutdown`, `cuvis.General.set_log_level`, `cuvis.General.version` - new module-level functions replacing the `General` class.
- `cuvis.cuvis_aux.WorkerState` - new dataclass with fields `framesInQueue`, `hasAcquisitionContext`, `isProcessing`, `measurementsBeingProcessed`, `measurementsInQueue`, `resultsInQueue` and `sessionFilesInQueue`.
- `cuvis.Worker.Worker.state` - new property returning a `WorkerState`.
- `cuvis.Worker.Worker.start_processing`, `.stop_processing`, `.drop_all_queued` - new methods giving explicit control over the processing loop.
- `cuvis.Worker.Worker.is_processing`, `.is_processing_mandatory`, `.threads_busy` - new read-only properties.
- `cuvis.Worker.Worker.can_drop_results`, `.can_skip_measurements`, `.can_skip_supplementary` - new read-only properties replacing the `drop_behaviour` setter.
- `cuvis.Worker.Worker.input_queue_limit`, `.mandatory_queue_limit`, `.output_queue_limit`, `.supplementary_queue_limit` - new read-only properties replacing the `queue_limits` setter.
- `cuvis.Worker.Worker.ingest_session_file` - new method taking `session: SessionFile` and `frame_selection: str = "all"`, replacing `set_session_file`.
- `cuvis.FileWriteSettings.WorkerSettings.input_queue_size`, `.mandatory_queue_size`, `.output_queue_size`, `.supplementary_queue_size` - new fields replacing `soft_limit` and `hard_limit`.
- `cuvis.FileWriteSettings.WorkerSettings.can_drop_results`, `.can_skip_measurements`, `.can_skip_supplementary_steps` - new fields replacing `can_drop` and `keep_out_of_sequence`.
- `cuvis.cuvis_aux.CalibrationInfo` - new dataclass with fields `annotation_name`, `calibration_date`, `file_path`, `model_name`, `serial_no` and `unique_id`.
- `cuvis.cuvis_aux.SensorInfo.width`, `.height`, `.pixel_format`, `.raw_frame_id`, `.binning` - new fields.
- `cuvis.Measurement.Measurement.averages`, `.distance`, `.frame_id` - new fields.
- `cuvis.Measurement.Measurement.thumbnail` - new property, replacing `get_thumbnail`.
- `cuvis.SessionFile.SessionFile.get_thumbnail` - new method.
- `cuvis.AcquisitionContext.AcquisitionContext.binning` - new property setter, replacing `preview_mode`.
- `cuvis.AcquisitionContext.AcquisitionContext.set_binning_async` - new method returning `Async`.
- `cuvis.AcquisitionContext.Component.pixel_format` - new property setter.
- `cuvis.AcquisitionContext.Component.available_pixel_formats` - new read-only property returning `list[str]`.
- `cuvis.Calibration.Calibration.get_info` - new method returning `cuvis_calibration_info_t`.
- `cuvis.Export.Exporter.flush` - new method.
- `cuvis.FileWriteSettings.SaveArgs.full_export` - new field, default `False`.
- `cuvis.FileWriteSettings.GeneralExportSettings.pre_pan_sharpen_cube` - new field, default `False`.
- `cuvis.doc.copydoc` - new decorator copying a docstring from another callable.

### Changed

- `cuvis.AcquisitionContext.Component.gain`, `.integration_time_factor` - type changed from `int` to `float`, and both gained setters.
- `cuvis.AcquisitionContext.Component.temperature` - return type changed from `int` to `float`.
- `cuvis.Worker.Worker.query_session_progress` - changed from a method to a read-only property returning `float`.
- `cuvis.FileWriteSettings.GeneralExportSettings.spectra_multiplier` - type changed from `float` to `int`, and the default from `1.0` to `1`.

### Removed

- `cuvis.General.General` - removed; replaced by module-level `init`, `shutdown`, `set_log_level` and `version`.
- `cuvis.AcquisitionContext.AcquisitionContext.preview_mode` - property setter removed; use `binning`.
- `cuvis.AcquisitionContext.AcquisitionContext.set_preview_mode_async` - removed; use `set_binning_async`.
- `cuvis.Worker.Worker.set_session_file` - removed; use `ingest_session_file`.
- `cuvis.Worker.Worker.drop_behaviour` - property setter removed; configure through `WorkerSettings` and read the `can_*` properties.
- `cuvis.Worker.Worker.queue_limits` - property setter removed; configure through `WorkerSettings` and read the `*_queue_limit` properties.
- `cuvis.Measurement.Measurement.get_thumbnail` - removed; use the `thumbnail` property.
- `cuvis.Measurement.Measurement.get_data_info` - removed.
- `cuvis.FileWriteSettings.WorkerSettings.soft_limit`, `.hard_limit`, `.poll_intervall`, `.worker_count`, `.can_drop`, `.keep_out_of_sequence` - removed; replaced by the `*_queue_size` and `can_*` fields.

## [3.2.1] - 2023-12-01

Targets cuvis SDK 3.2.1.
First release covered by this changelog; the wrapper's history before this point is not reconstructed here.
