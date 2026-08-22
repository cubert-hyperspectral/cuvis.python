# ImageData: API notes and proposed additions

Written 2026-08-19, against `hotfix/fix_broken_qmini_imagedata_wrapping` at version 3.5.3.2.

This is a design note, not a plan.
It records what the class looks like after the QMini hotfix, which additions are worth making next, and which tempting ones should be refused.
Nothing here is scheduled.

The reason to write it down now is that 3.5.3.2 introduces the whole numeric surface of `ImageData` at once.
Every member it ships becomes permanent.
The additions below are the ones that fit that surface without contradicting it, and a few of them are cheaper to do before the release than after.

## What shipped in 3.5.3.2

Attributes: `array`, `width`, `height`, `channels`, `wavelength`.
Properties: `shape`, `dtype`, `is_spectrum`, `spectrum`.
Protocols: `__getitem__`, `__array__`, `__array_ufunc__`, `__repr__`, the seven arithmetic operators with their reflected forms, `__neg__`, `__abs__`.
Constructors: `__init__` from a `cuvis_imbuffer_t`, `from_array` from a NumPy array.

Two invariants hold the design together.
`array` is always three dimensional, `(height, width, channels)`, so a point spectrometer arrives as `(1, 1, channels)` rather than as a bare vector.
`wavelength` is either `None` or exactly `channels` long, and is never guessed: a slice whose effect on the band axis cannot be determined drops the wavelengths rather than inventing them.

## Proposed additions

### 1. Band lookup by wavelength

The gap a user notices first.
Hyperspectral work is expressed in nanometres, but every accessor on the class takes band indices, so callers hand-compute indices from the `wavelength` list before they can slice.

The minimal addition is one function that converts, leaving the existing slicing to do the rest:

```python
def band_at(self, nm: int) -> int:
    """The index of the band whose centre is closest to `nm`."""
```

which composes with what already exists:

```python
red = cube[:, :, cube.band_at(650)]
window = cube[:, :, cube.band_at(600) : cube.band_at(700) + 1]
```

Nearest match is the only honest semantic.
The SDK reports wavelengths as `uint32_t` nanometres (`cuvis.h:939`), the grid is whatever the camera's calibration produced, and an exact-match lookup would fail for most inputs a user types.
`band_at` should raise when `wavelength is None`, because there is no defensible answer for a preview or an info layer.

A richer alternative is an indexer object, `cube.nm[600:700]`, so that nanometres read like slicing.
It is more pleasant at the call site and considerably more machinery: a second indexing protocol to document, test and keep in step with `__getitem__`.
Not worth it for what is fundamentally a coordinate conversion.
`band_at` first; revisit only if call sites turn out to be dominated by ranges.

### 2. Mean spectrum over a region

After slicing, the most common hyperspectral operation is averaging a spatial region into one spectrum.
Today that loses the wavelengths, because the shape changes and the ufunc machinery correctly declines to carry metadata across a reduction:

```python
np.mean(cube, axis=(0, 1))  # plain ndarray, shape (channels,), wavelengths gone
```

so the caller reassembles by hand.
A method that returns a single pixel `ImageData` closes the loop and keeps the band axis labelled:

```python
def mean_spectrum(self) -> "ImageData":
    """The spatial mean, as a (1, 1, channels) ImageData carrying this instance's wavelengths."""
```

Then `cube[100:200, 50:150].mean_spectrum()` is the whole region-of-interest workflow, and the result is `is_spectrum` and plots exactly like a QMini reading.
This is the one addition that turns the existing pieces into a workflow rather than adding another spelling of something already possible.

### 3. Comparison operators

`np.asarray(cube) > 500` works and is documented.
`cube > 500` raises `TypeError`, and `np.greater(cube, 500)` returns a plain boolean array since the guard added in 3.5.3.2.
The asymmetry is the kind that costs a user ten minutes.

Adding `__lt__`, `__le__`, `__gt__`, `__ge__` through the existing `_binary_op` factory, returning the plain array rather than rewrapping, removes it for about four lines.

`__eq__` and `__ne__` must stay out.
Defining them would make `img == img` elementwise, which silently breaks every truth test on the result, and it would take `__hash__` with it unless explicitly restored.
`ImageData` is hashable today and identity comparison is the useful default for a handle-like object.
Asymmetric operator sets are unusual enough to deserve a comment at the definition site saying why.

### 4. `spectrum` as a method taking pixel coordinates

Discussed during the hotfix and deliberately left out of it.

`spectrum` is currently a property restricted to single pixel images.
The general operation is "the band vector at a pixel", which `__getitem__` already performs, except that it returns `(values, wavelengths)` rather than a bare array.
So there are two ways to reach a band vector with two different return types, and the property covers only the `0, 0` case:

```python
point.spectrum  # ndarray
cube[10, 10]  # (ndarray, wavelengths)
```

A method subsumes both with one return type and no arbitrary restriction:

```python
def spectrum(self, y: int = 0, x: int = 0) -> np.ndarray:
```

`point.spectrum()` keeps reading well, `cube.spectrum(10, 10)` gains what the property could not express, and `is_spectrum` reverts to what it should have been all along: an informational shape check, not the precondition of another member.

The catch is timing.
Turning a property into a method is a breaking change, so this is free before 3.5.3.2 ships and a deprecation cycle afterwards.
It is listed here rather than applied because it widens a hotfix, but it is the item on this list whose cost grows the fastest.

### 5. Store the buffer format, or stop requiring it

Not an addition so much as a wart to resolve, recorded here because it touches the constructor signature.

`__init__` accepts `dformat`, raises `TypeError` when it is missing, and never reads it.
The format is taken from `img_buf.format` directly, two lines further down.
The three call sites do not even agree on the type they pass: `Measurement.py:108` passes a `DataFormat` enum member, `SessionFile.py:60` and `Viewer.py:46` pass the raw integer.

Either the value is worth keeping, in which case store it as a public `format` and use it instead of re-reading the buffer, or it is not, in which case drop the parameter.
The current state is the worst of the three: a required argument, inconsistently supplied, with no effect.
Dropping it is technically a signature change, but `ImageData(img_buf, dformat)` is not something callers outside the wrapper construct.

## Considered and refused

**`wavelength` as an ndarray.**
It is a list of Python ints today, so callers wrap it in `np.asarray` when they want arithmetic.
Changing the type would break `wavelength == [450, 458]` comparisons, including several in `tests/test_cube_utils.py`, and turn every truth test on the result into an ambiguity error.
Adding a second `wavelength_nm` property alongside it trades that break for a permanent duplicate.
The `np.asarray` at the call site is the smaller cost.

**Iteration and `__len__`.**
There is no defensible answer to what iterating an image yields.
Rows, pixels and bands are all plausible, and a wrong guess is worse than a `TypeError`.

**`is_cube`, `is_image`, or other siblings of `is_spectrum`.**
`not img.is_spectrum` already says it.
`is_spectrum` earns its place because the alternative forces callers to know the `(1, 1, channels)` convention; a negation does not clear that bar.

**More conversion spellings.**
`array`, `to_numpy()` and `np.asarray(img)` are already three ways to reach the same buffer.
The direction of travel should be fewer, not more: `to_numpy()` is the redundant one, and if anything happens here it should be a deprecation.

## Ordering

If these are picked up, the order that yields the most per change:

1. `spectrum(y, x)`, if and only if it happens before 3.5.3.2 ships. Afterwards it drops to last, behind a deprecation cycle.
2. `band_at`. Largest gap, smallest implementation, no interaction with anything else.
3. `mean_spectrum`. Depends on nothing, completes the region-of-interest workflow.
4. Comparison operators. Small and self-contained.
5. The `dformat` cleanup. Internal, do it alongside whichever of the above touches the constructor.
