# Sprint FRET-A Phase 1.5 — Math Kernel Delegation Refactor
### Path 1: Staged Refactor of Self-Contained Schema Math to Kernel Calls

**Status:** READY TO EXECUTE on `sprint/fret-ecosphere-a` (post-Phase 1)
**Date:** 2026-04-29
**Codename:** Sprint FRET-A Phase 1.5
**Branch:** `sprint/fret-ecosphere-a` (continuing, no new branch)
**Parent:** Sprint FRET-A v2 (this is restoration of the v2 phase 1 + 2 work that was collapsed into the schema)
**Estimated time:** 2.5–3 hours
**Blocks:** FRET-A Phase 2 (router) — refactor first so the API exposes structurally honest temperament support

---

## 1. Why This Sprint Exists

Phase 1 of FRET-A (commit `9d37f1ea`) delivered the FretboardEcosphere schema with self-contained fret position math, including stub support for 19-TET, 24-TET, and 31-TET temperaments. The math underneath those alt-temperament cases is hardcoded 12-TET. The schema also duplicates ~30 lines of fret position logic that already exists in `alternative_temperaments.compute_fret_positions_from_ratios_mm`.

Two concerns this sprint addresses:

1. **Honest temperament support.** The schema exposes `temperament: Literal["12-TET", "19-TET", "24-TET", "31-TET"]` but the underlying math is 12-TET-only. Before Phase 2 wires this into a public API, the math has to be real.
2. **Single source of truth.** Two copies of fret position math means a future bug fix in `fret_math.py` doesn't propagate to the schema. Delegation closes that drift.

This sprint stages the work in three commits: extend the kernel, add the Scala parser, refactor the schema to delegate.

---

## 2. Inventory of What Exists vs What's Needed

| Capability | Current state | After this sprint |
|---|---|---|
| `compute_fret_positions_mm(scale, count)` | 12-TET only, line 67 of `fret_math.py` | Unchanged (backward compat) |
| `compute_multiscale_fret_positions_mm` | Line 128, takes `perpendicular_fret: int` | + `perpendicular_distance: Optional[float]`, + `scale_lengths_mm: Optional[List[float]]` |
| `compute_fret_positions_from_ratios_mm` | Exists at `alternative_temperaments.py:443` | Unchanged — already correct |
| `TemperamentSystem` enum | 12-TET, just major/minor, Pythagorean, meantone-¼, custom | + 19-TET, 24-TET, 31-TET added |
| N-TET position generator | Doesn't exist | New: `compute_n_tet_ratios(n: int, fret_count: int)` in `alternative_temperaments.py` |
| Scala (.scl) parser | Doesn't exist | New: `services/api/app/calculators/scala_loader.py` |
| Schema fret math | 30 lines self-contained in `fretboard_ecosphere.py` | Delegates to `compute_fret_positions_from_ratios_mm` |
| Schema temperament list | Hardcoded literal, math is fake | Resolves `TemperamentSystem` to ratios via kernel |

---

## 3. Three Commits, In Order

```
Commit 1: feat(fret_math): extend with N-TET temperaments + FretFind parameters
Commit 2: feat(calculators): add scala_loader for .scl file parsing
Commit 3: refactor(ecosphere): delegate schema fret math to existing kernels
```

Each commit is independently testable. If commit 3 introduces a regression, commits 1 and 2 still stand on their own merits and don't need to be reverted.

---

## 4. Commit 1 — Extend the kernel

### Files touched

```
services/api/app/calculators/alternative_temperaments.py    (add N-TET support)
services/api/app/instrument_geometry/neck/fret_math.py      (add PD + per-string scale)
services/api/app/tests/calculators/test_alternative_temperaments.py    (new tests)
services/api/app/tests/test_fan_fret_perpendicular.py       (new tests)
```

### 4.1 N-TET support in `alternative_temperaments.py`

Extend the `TemperamentSystem` enum:

```python
class TemperamentSystem(str, Enum):
    EQUAL_12TET = "12-TET"
    EQUAL_19TET = "19-TET"          # NEW
    EQUAL_24TET = "24-TET"          # NEW
    EQUAL_31TET = "31-TET"          # NEW
    JUST_MAJOR = "just_major"
    JUST_MINOR = "just_minor"
    PYTHAGOREAN = "pythagorean"
    MEANTONE_QUARTER = "meantone_1/4"
    CUSTOM = "custom"
```

Add a new generator function (place after `compute_equal_temperament_position` at line ~106):

```python
def compute_n_tet_ratios(n: int, fret_count: int) -> List[float]:
    """Generate frequency ratios for N-tone equal temperament.

    For N-TET, each fret raises pitch by 2^(1/N). Standard guitar uses 12-TET
    (12 semitones per octave). Microtonal instruments use 19-TET, 24-TET
    (quarter-tones), 31-TET (close approximation to meantone), etc.

    Args:
        n: Number of equal divisions per octave (must be ≥ 2)
        fret_count: Number of fret positions to generate

    Returns:
        List of frequency ratios [r_1, r_2, ..., r_fret_count] where
        r_i is the pitch ratio at fret i relative to the open string (1/1).

    Raises:
        ValueError: if n < 2 or fret_count < 1

    Example:
        >>> compute_n_tet_ratios(12, 12)
        [1.0595..., 1.1225..., ..., 2.0]  # standard guitar octave
        >>> compute_n_tet_ratios(24, 24)
        [1.0293..., 1.0595..., ..., 2.0]  # quarter-tone fretting
    """
    if n < 2:
        raise ValueError(f"n must be >= 2 (got {n}); 1-TET has no fret positions")
    if fret_count < 1:
        raise ValueError(f"fret_count must be >= 1 (got {fret_count})")

    return [2.0 ** (i / n) for i in range(1, fret_count + 1)]
```

Add a small helper that maps a `TemperamentSystem` value to its ratio list:

```python
def resolve_temperament_ratios(
    system: TemperamentSystem,
    fret_count: int,
    custom_ratios: Optional[List[float]] = None,
) -> List[float]:
    """Resolve a TemperamentSystem to a flat list of fret ratios.

    Returns the ratios that compute_fret_positions_from_ratios_mm consumes.
    Unifies the per-system functions (just_intonation, pythagorean, meantone)
    behind a single dispatch.

    For N-TET systems, calls compute_n_tet_ratios.
    For named systems (just_*, pythagorean, meantone_1/4), calls the existing
    compute_*_positions function and extracts the ratios.
    For CUSTOM, returns custom_ratios verbatim (validated for monotonicity
    by the downstream caller).
    """
    if system == TemperamentSystem.CUSTOM:
        if not custom_ratios:
            raise ValueError("CUSTOM temperament requires custom_ratios")
        return list(custom_ratios)

    if system == TemperamentSystem.EQUAL_12TET:
        return compute_n_tet_ratios(12, fret_count)
    if system == TemperamentSystem.EQUAL_19TET:
        return compute_n_tet_ratios(19, fret_count)
    if system == TemperamentSystem.EQUAL_24TET:
        return compute_n_tet_ratios(24, fret_count)
    if system == TemperamentSystem.EQUAL_31TET:
        return compute_n_tet_ratios(31, fret_count)

    # Named non-equal temperaments
    if system == TemperamentSystem.JUST_MAJOR:
        positions = compute_just_intonation_positions(
            scale_length_mm=1.0,  # we want ratios, scale_length is normalized out
            fret_count=fret_count,
            mode="major",
        )
        return [p.ratio for p in positions]
    if system == TemperamentSystem.JUST_MINOR:
        positions = compute_just_intonation_positions(
            scale_length_mm=1.0, fret_count=fret_count, mode="minor",
        )
        return [p.ratio for p in positions]
    if system == TemperamentSystem.PYTHAGOREAN:
        positions = compute_pythagorean_positions(
            scale_length_mm=1.0, fret_count=fret_count,
        )
        return [p.ratio for p in positions]
    if system == TemperamentSystem.MEANTONE_QUARTER:
        positions = compute_meantone_positions(
            scale_length_mm=1.0, fret_count=fret_count,
        )
        return [p.ratio for p in positions]

    raise ValueError(f"Unknown temperament system: {system}")
```

> **Pre-flight check before writing this:** confirm that `compute_just_intonation_positions`, `compute_pythagorean_positions`, and `compute_meantone_positions` return objects with a `.ratio` attribute. If they return positions only without preserved ratios, the `[p.ratio for p in positions]` lines need to compute `ratio = scale_length / (scale_length - position)` instead. Verify by reading the dataclass definition of `FretPosition` near line 34. If ratios aren't stored, the helper still works but the comprehension changes.

If `FretPosition` doesn't carry ratios, add a `from_position_mm` classmethod or recompute them inline. Don't modify the dataclass shape (that's out of scope and would break other callers).

### 4.2 FretFind parameters in `compute_multiscale_fret_positions_mm`

Extend the function at `fret_math.py:128`. The signature change is additive only:

```python
def compute_multiscale_fret_positions_mm(
    bass_scale_mm: float,
    treble_scale_mm: float,
    fret_count: int,
    string_count: int,
    perpendicular_fret: int = 0,
    fretboard_width_mm: float = 50.0,
    # NEW — additive, backward compatible:
    perpendicular_distance: Optional[float] = None,
    scale_lengths_mm: Optional[List[float]] = None,
) -> List[List[FanFretPoint]]:
```

Resolution rules (document in docstring, implement at the top of the function body):

```python
"""
Resolution order:

    1. If scale_lengths_mm is provided AND len(scale_lengths_mm) == string_count:
       use per-string scale array. bass_scale_mm and treble_scale_mm are
       ignored (with a logged INFO message via warnings.warn if they
       conflict with the array endpoints, defined as:
           array[0] != bass_scale_mm or array[-1] != treble_scale_mm
       within 0.01mm tolerance).
    2. Else if scale_lengths_mm is None or len mismatches string_count:
       use bass_scale_mm + treble_scale_mm with linear interpolation
       (existing behavior, byte-identical output).

    3. If perpendicular_distance is not None and 0.0 <= perpendicular_distance <= 1.0:
       resolve to a perpendicular fret position via the FretFind PD convention.
       PD is the ratio along the string at which the fret should be
       perpendicular (PD=0 → nut, PD=0.5 → octave/12th fret, PD=1.0 → bridge).
    4. Elif perpendicular_fret > 0:
       use the existing integer-fret behavior (resolve to PD via the
       12-TET formula PD = 1 - 2^(-fret/12)).
    5. Else: no forced perpendicular (frets fan freely).

    If both perpendicular_distance and perpendicular_fret are provided,
    raise ValueError — caller must pick one.
"""
```

Add the helper for round-trip conversion:

```python
def perpendicular_distance_for_fret(fret_number: int, semitones_per_octave: int = 12) -> float:
    """FretFind PD ratio for a given fret in equal temperament.

    PD = 1 - 2^(-fret_number / semitones_per_octave)

    For 12-TET:
        Fret 1  → 0.05613
        Fret 7  → 0.33258
        Fret 12 → 0.50000  (octave, FretFind default)
        Fret 24 → 0.75000
    """
    if fret_number < 0:
        raise ValueError(f"fret_number must be >= 0 (got {fret_number})")
    if semitones_per_octave < 1:
        raise ValueError(f"semitones_per_octave must be >= 1 (got {semitones_per_octave})")
    return 1.0 - 2.0 ** (-fret_number / semitones_per_octave)
```

### 4.3 Tests for Commit 1

**File:** `services/api/app/tests/calculators/test_alternative_temperaments.py` (extend existing or create if absent)

```python
class TestNTET:
    def test_12tet_matches_existing_compute_fret_positions_mm(self):
        # compute_n_tet_ratios(12, 22) → ratios → compute_fret_positions_from_ratios_mm
        # must equal compute_fret_positions_mm(scale, 22) within 1e-9 mm
        ...

    def test_19tet_first_fret_ratio(self):
        ratios = compute_n_tet_ratios(19, 19)
        assert abs(ratios[0] - 2 ** (1/19)) < 1e-12
        assert abs(ratios[-1] - 2.0) < 1e-12

    def test_24tet_quarter_tones(self):
        ratios = compute_n_tet_ratios(24, 24)
        # Fret 2 of 24-TET ≈ Fret 1 of 12-TET (within 1e-12)
        twelve = compute_n_tet_ratios(12, 12)
        assert abs(ratios[1] - twelve[0]) < 1e-12

    def test_31tet_octave_at_fret_31(self):
        ratios = compute_n_tet_ratios(31, 31)
        assert abs(ratios[-1] - 2.0) < 1e-12

    def test_n_tet_validation(self):
        with pytest.raises(ValueError, match=">= 2"):
            compute_n_tet_ratios(1, 12)
        with pytest.raises(ValueError, match=">= 1"):
            compute_n_tet_ratios(12, 0)


class TestResolveTemperament:
    def test_resolves_12tet(self):
        ratios = resolve_temperament_ratios(TemperamentSystem.EQUAL_12TET, 22)
        assert len(ratios) == 22
        assert abs(ratios[11] - 2.0) < 1e-9

    def test_resolves_19tet(self):
        ratios = resolve_temperament_ratios(TemperamentSystem.EQUAL_19TET, 19)
        assert len(ratios) == 19
        assert abs(ratios[-1] - 2.0) < 1e-12

    def test_resolves_just_major(self):
        ratios = resolve_temperament_ratios(TemperamentSystem.JUST_MAJOR, 12)
        assert len(ratios) == 12

    def test_custom_requires_ratios(self):
        with pytest.raises(ValueError, match="CUSTOM"):
            resolve_temperament_ratios(TemperamentSystem.CUSTOM, 12)

    def test_custom_passes_through(self):
        ratios = resolve_temperament_ratios(
            TemperamentSystem.CUSTOM, 3, custom_ratios=[1.1, 1.5, 2.0]
        )
        assert ratios == [1.1, 1.5, 2.0]
```

**File:** `services/api/app/tests/test_fan_fret_perpendicular.py` (new tests, add to existing file)

```python
class TestFretFindParity:
    def test_perpendicular_distance_half_matches_fret_12(self):
        """PD=0.5 should produce same perpendicular fret as perpendicular_fret=12."""
        result_pd = compute_multiscale_fret_positions_mm(
            bass_scale_mm=686.0, treble_scale_mm=648.0,
            fret_count=22, string_count=6,
            perpendicular_distance=0.5,
        )
        result_int = compute_multiscale_fret_positions_mm(
            bass_scale_mm=686.0, treble_scale_mm=648.0,
            fret_count=22, string_count=6,
            perpendicular_fret=12,
        )
        # Compare 12th fret angle on both — should be 0.0 (perpendicular) within tolerance
        for s in range(6):
            assert abs(result_pd[11][s].angle_rad) < 1e-9
            assert abs(result_int[11][s].angle_rad) < 1e-9

    def test_perpendicular_distance_third_matches_fret_7(self):
        pd = perpendicular_distance_for_fret(7)
        # Should be 0.33258...
        assert abs(pd - 0.33258) < 1e-4

    def test_per_string_scale_array_matches_linear_interp(self):
        """A linear-progression scale_lengths_mm array should equal bass/treble interp."""
        # 6 strings, linear from 686 to 648
        linear = [686.0 - (686.0 - 648.0) * i / 5 for i in range(6)]

        result_array = compute_multiscale_fret_positions_mm(
            bass_scale_mm=686.0, treble_scale_mm=648.0,  # ignored but present
            fret_count=22, string_count=6,
            scale_lengths_mm=linear,
        )
        result_interp = compute_multiscale_fret_positions_mm(
            bass_scale_mm=686.0, treble_scale_mm=648.0,
            fret_count=22, string_count=6,
        )
        for f in range(22):
            for s in range(6):
                assert abs(result_array[f][s].x_mm - result_interp[f][s].x_mm) < 1e-6
                assert abs(result_array[f][s].y_mm - result_interp[f][s].y_mm) < 1e-6

    def test_per_string_scale_nonlinear_diverges_from_interp(self):
        """A non-linear scale array should produce different geometry than linear interp."""
        nonlinear = [686.0, 685.0, 680.0, 670.0, 655.0, 648.0]  # bunched at bass
        result_nonlinear = compute_multiscale_fret_positions_mm(
            bass_scale_mm=686.0, treble_scale_mm=648.0,
            fret_count=22, string_count=6,
            scale_lengths_mm=nonlinear,
        )
        result_interp = compute_multiscale_fret_positions_mm(
            bass_scale_mm=686.0, treble_scale_mm=648.0,
            fret_count=22, string_count=6,
        )
        # At least one fret position should differ by more than 1mm
        max_diff = max(
            abs(result_nonlinear[f][s].x_mm - result_interp[f][s].x_mm)
            for f in range(22) for s in range(6)
        )
        assert max_diff > 1.0

    def test_v1_signature_byte_identical(self):
        """Call with no new params — output must match pre-Phase-1.5 baseline."""
        # Snapshot test against existing GOLDEN values from
        # tests/test_golden_fret_positions.py
        result = compute_multiscale_fret_positions_mm(
            bass_scale_mm=647.7, treble_scale_mm=647.7,  # equivalent to single-scale
            fret_count=22, string_count=6,
        )
        # Single-scale collapses to compute_fret_positions_mm
        from app.instrument_geometry.neck.fret_math import compute_fret_positions_mm
        baseline = compute_fret_positions_mm(647.7, 22)
        for f in range(22):
            # Take any string (geometry is identical when bass==treble)
            assert abs(result[f][0].x_mm - baseline[f]) < 1e-9

    def test_pd_and_int_fret_both_set_raises(self):
        with pytest.raises(ValueError, match="pick one"):
            compute_multiscale_fret_positions_mm(
                bass_scale_mm=686.0, treble_scale_mm=648.0,
                fret_count=22, string_count=6,
                perpendicular_fret=12,
                perpendicular_distance=0.5,
            )
```

### 4.4 Acceptance for Commit 1

```
□ compute_n_tet_ratios exists and passes 5 tests
□ resolve_temperament_ratios exists and passes 5 tests
□ TemperamentSystem enum has 19-TET, 24-TET, 31-TET added
□ compute_multiscale_fret_positions_mm has new params, 6 tests pass
□ All existing tests in test_alternative_temperaments.py pass unmodified
□ All existing tests in test_fan_fret_perpendicular.py pass unmodified
□ All existing tests in test_golden_fret_positions.py pass unmodified
□ /tmp/baseline_pre_fret_a.txt regression check: same test count, same passes
```

### 4.5 Commit message for Commit 1

```
feat(fret_math): add N-TET temperaments and FretFind parameters

Extends alternative_temperaments.py with N-TET support (19-TET, 24-TET,
31-TET) and a unified resolve_temperament_ratios dispatcher.

Adds optional FretFind parameters to fret_math.compute_multiscale_fret_positions_mm:
  - perpendicular_distance: float ∈ [0, 1] (FretFind PD convention)
  - scale_lengths_mm: List[float] (per-string scale array, FretFind individual mode)

Both additions are backward compatible. Default behavior with no new
parameters produces byte-identical output (verified by snapshot test
against test_golden_fret_positions.py).

Tests added: 16 (5 N-TET + 5 dispatcher + 6 FretFind parity)
Tests modified: 0
Tests removed: 0

References: FretFind2D (acspike.github.io/FretFind2D),
            FRET-A v2 dev order Phase 1 (this commit completes the
            originally-planned scope that got collapsed into the
            schema in commit 9d37f1ea).
```

---

## 5. Commit 2 — Scala (.scl) parser

### Files touched

```
services/api/app/calculators/scala_loader.py                (new)
services/api/app/tests/calculators/test_scala_loader.py     (new)
data/scala_samples/12tet.scl                                (new)
data/scala_samples/just_major.scl                           (new)
data/scala_samples/meantone_quarter.scl                     (new)
```

### 5.1 The parser module

**File:** `services/api/app/calculators/scala_loader.py`

```python
"""
Scala (.scl) file parser.

Reference: http://www.huygens-fokker.org/scala/scl_format.html

Format rules:
    - Lines starting with '!' are comments
    - First non-comment line: description string (free text, may be empty)
    - Second non-comment line: integer pitch count (number of pitches per period)
    - Subsequent non-comment lines: pitches as either:
        * cents (decimal point present, e.g. "100.0")
        * ratio (slash present, e.g. "9/8")
        * integer (treated as ratio with denominator 1, e.g. "2" = 2/1)
    - 1/1 (the unison) is implicit and not stored
    - Last pitch is the period (typically 2/1 for octave-based scales)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple, Union


@dataclass(frozen=True)
class ScalaPitch:
    """A single pitch entry from a Scala file.

    Stored in its source form (cents or ratio) plus a derived float ratio
    for downstream math.
    """
    source_text: str
    cents: Optional[float]                 # set if source was cents
    ratio: Optional[Tuple[int, int]]       # set if source was ratio
    frequency_ratio: float                  # always populated (derived)


@dataclass(frozen=True)
class ScalaScale:
    """A parsed Scala scale.

    Attributes:
        description: Free-text scale description from the file
        pitch_count: Number of pitches per period (excluding 1/1)
        pitches: List of ScalaPitch in ascending order, last is the period
    """
    description: str
    pitch_count: int
    pitches: List[ScalaPitch] = field(default_factory=list)


def _cents_to_ratio(cents: float) -> float:
    return 2.0 ** (cents / 1200.0)


def _parse_pitch_line(line: str) -> ScalaPitch:
    """Parse a single non-comment pitch line."""
    stripped = line.strip()

    if "/" in stripped:
        # Ratio form: "9/8" or "3/2" etc.
        num_str, _, den_str = stripped.partition("/")
        try:
            numerator = int(num_str.strip())
            denominator = int(den_str.strip())
        except ValueError as e:
            raise ValueError(f"Invalid ratio: {stripped!r}") from e
        if denominator <= 0 or numerator <= 0:
            raise ValueError(f"Ratio components must be positive: {stripped!r}")
        ratio_val = numerator / denominator
        return ScalaPitch(
            source_text=stripped,
            cents=None,
            ratio=(numerator, denominator),
            frequency_ratio=ratio_val,
        )

    if "." in stripped:
        # Cents form: "100.0", "498.045", etc.
        try:
            cents = float(stripped)
        except ValueError as e:
            raise ValueError(f"Invalid cents value: {stripped!r}") from e
        return ScalaPitch(
            source_text=stripped,
            cents=cents,
            ratio=None,
            frequency_ratio=_cents_to_ratio(cents),
        )

    # Integer form: "2" treated as "2/1"
    try:
        n = int(stripped)
    except ValueError as e:
        raise ValueError(f"Invalid pitch line: {stripped!r}") from e
    if n <= 0:
        raise ValueError(f"Integer pitch must be positive: {stripped!r}")
    return ScalaPitch(
        source_text=stripped,
        cents=None,
        ratio=(n, 1),
        frequency_ratio=float(n),
    )


def parse_scala_content(content: str) -> ScalaScale:
    """Parse Scala file content. Returns a ScalaScale."""
    lines = content.splitlines()
    non_comment = [
        line for line in lines
        if line.strip() and not line.lstrip().startswith("!")
    ]

    if len(non_comment) < 2:
        raise ValueError(
            "Scala file must have at least description and pitch count lines"
        )

    description = non_comment[0].strip()
    try:
        pitch_count = int(non_comment[1].strip())
    except ValueError as e:
        raise ValueError(
            f"Pitch count line must be an integer, got: {non_comment[1]!r}"
        ) from e

    pitch_lines = non_comment[2:]
    if len(pitch_lines) != pitch_count:
        raise ValueError(
            f"Pitch count ({pitch_count}) does not match number of "
            f"pitch lines ({len(pitch_lines)})"
        )

    pitches = [_parse_pitch_line(line) for line in pitch_lines]

    # Validate monotonicity
    for i in range(1, len(pitches)):
        if pitches[i].frequency_ratio <= pitches[i - 1].frequency_ratio:
            raise ValueError(
                f"Pitches must strictly increase: "
                f"pitch[{i-1}]={pitches[i-1].frequency_ratio:.6f}, "
                f"pitch[{i}]={pitches[i].frequency_ratio:.6f}"
            )

    return ScalaScale(
        description=description,
        pitch_count=pitch_count,
        pitches=pitches,
    )


def parse_scala_file(path: Union[str, Path]) -> ScalaScale:
    """Parse a .scl file from disk."""
    p = Path(path)
    return parse_scala_content(p.read_text(encoding="utf-8"))


def scala_to_fret_ratios(
    scale: ScalaScale,
    fret_count: int,
) -> List[float]:
    """Convert a Scala scale to a flat list of per-fret ratios.

    For an N-pitch scale, ratios repeat per period. Fret k gets the
    (k mod N)-th pitch of period (k // N + 1) — i.e., the scale loops
    upward by its period.

    Returns a list suitable for compute_fret_positions_from_ratios_mm.
    """
    if fret_count < 1:
        raise ValueError(f"fret_count must be >= 1 (got {fret_count})")
    if not scale.pitches:
        raise ValueError("Scala scale has no pitches")

    period_ratio = scale.pitches[-1].frequency_ratio
    pitches = [p.frequency_ratio for p in scale.pitches]
    n = len(pitches)

    ratios: List[float] = []
    for fret in range(1, fret_count + 1):
        period_index = (fret - 1) // n
        within_period = (fret - 1) % n
        ratio = pitches[within_period] * (period_ratio ** period_index)
        ratios.append(ratio)
    return ratios
```

### 5.2 Sample .scl files

**File:** `data/scala_samples/12tet.scl`

```
! 12tet.scl
!
12 tone equal temperament
 12
!
 100.000000
 200.000000
 300.000000
 400.000000
 500.000000
 600.000000
 700.000000
 800.000000
 900.000000
 1000.000000
 1100.000000
 2/1
```

**File:** `data/scala_samples/just_major.scl`

```
! just_major.scl
!
Just intonation, major mode (Ptolemy intense diatonic)
 7
!
 9/8
 5/4
 4/3
 3/2
 5/3
 15/8
 2/1
```

**File:** `data/scala_samples/meantone_quarter.scl`

```
! meantone_quarter.scl
!
Quarter-comma meantone, 12 tones
 12
!
 76.049000
 193.157000
 310.265000
 386.314000
 503.422000
 579.471000
 696.578000
 772.627000
 889.735000
 1006.843000
 1082.892000
 2/1
```

### 5.3 Tests for Commit 2

**File:** `services/api/app/tests/calculators/test_scala_loader.py`

```python
import pytest
from pathlib import Path
from app.calculators.scala_loader import (
    parse_scala_content,
    parse_scala_file,
    scala_to_fret_ratios,
    ScalaScale,
    ScalaPitch,
)
from app.calculators.alternative_temperaments import compute_n_tet_ratios

SAMPLES = Path(__file__).resolve().parents[3] / "data" / "scala_samples"


class TestParseScalaContent:
    def test_parses_12tet(self):
        scale = parse_scala_file(SAMPLES / "12tet.scl")
        assert scale.pitch_count == 12
        assert len(scale.pitches) == 12
        # Last is 2/1
        assert scale.pitches[-1].frequency_ratio == pytest.approx(2.0)

    def test_parses_just_major(self):
        scale = parse_scala_file(SAMPLES / "just_major.scl")
        assert scale.pitch_count == 7
        # 5/4 is the third pitch
        assert scale.pitches[1].ratio == (5, 4)

    def test_parses_meantone(self):
        scale = parse_scala_file(SAMPLES / "meantone_quarter.scl")
        assert scale.pitch_count == 12
        # First pitch is ~76 cents (much smaller than 12-TET 100)
        assert scale.pitches[0].cents == pytest.approx(76.049)

    def test_rejects_pitch_count_mismatch(self):
        bad = "desc\n5\n100.0\n200.0\n"  # claims 5 pitches, has 2
        with pytest.raises(ValueError, match="does not match"):
            parse_scala_content(bad)

    def test_rejects_non_monotonic(self):
        bad = "desc\n3\n200.0\n100.0\n300.0\n"
        with pytest.raises(ValueError, match="strictly increase"):
            parse_scala_content(bad)

    def test_handles_comment_lines(self):
        content = "! a comment\ndesc\n! another comment\n2\n100.0\n2/1\n"
        scale = parse_scala_content(content)
        assert scale.description == "desc"
        assert scale.pitch_count == 2

    def test_integer_pitch_treated_as_ratio_over_1(self):
        content = "desc\n1\n3\n"
        scale = parse_scala_content(content)
        assert scale.pitches[0].ratio == (3, 1)
        assert scale.pitches[0].frequency_ratio == 3.0


class TestScalaToFretRatios:
    def test_12tet_round_trip(self):
        """Parsing 12tet.scl and using it to generate ratios should match
        compute_n_tet_ratios(12) within floating-point precision."""
        scale = parse_scala_file(SAMPLES / "12tet.scl")
        scl_ratios = scala_to_fret_ratios(scale, fret_count=12)
        ntet_ratios = compute_n_tet_ratios(12, 12)
        for s, n in zip(scl_ratios, ntet_ratios):
            assert abs(s - n) < 1e-9

    def test_loops_across_period(self):
        """For 22-fret guitar, 12-TET .scl should loop into the second octave."""
        scale = parse_scala_file(SAMPLES / "12tet.scl")
        ratios = scala_to_fret_ratios(scale, fret_count=22)
        assert len(ratios) == 22
        # Fret 12 = 2/1, Fret 13 should be 2 * (12-TET first ratio)
        first = ratios[0]
        assert abs(ratios[12] - 2.0 * first) < 1e-9

    def test_just_major_first_pitch(self):
        scale = parse_scala_file(SAMPLES / "just_major.scl")
        ratios = scala_to_fret_ratios(scale, fret_count=7)
        assert abs(ratios[0] - 9/8) < 1e-9
        assert abs(ratios[-1] - 2.0) < 1e-9
```

### 5.4 Acceptance for Commit 2

```
□ scala_loader.py module exists with parse_scala_content, parse_scala_file,
   scala_to_fret_ratios, ScalaScale, ScalaPitch
□ 3 sample .scl files committed under data/scala_samples/
□ 9 new tests pass
□ 12-TET round-trip identity confirmed (Scala-parsed → ratios = compute_n_tet_ratios(12))
□ All other existing tests still pass
```

### 5.5 Commit message for Commit 2

```
feat(calculators): add Scala (.scl) file parser

New module services/api/app/calculators/scala_loader.py implementing
the Huygens-Fokker .scl format spec.

Public API:
  parse_scala_content(content: str) -> ScalaScale
  parse_scala_file(path) -> ScalaScale
  scala_to_fret_ratios(scale, fret_count) -> List[float]

Three sample files under data/scala_samples/:
  12tet.scl              (round-trip identity with compute_n_tet_ratios(12))
  just_major.scl         (Ptolemy intense diatonic)
  meantone_quarter.scl   (quarter-comma meantone)

Output is compatible with compute_fret_positions_from_ratios_mm,
which means any .scl file can drive fret position generation through
the existing kernel.

Tests added: 9
Tests modified: 0

References: http://www.huygens-fokker.org/scala/scl_format.html
            FRET-A v2 dev order Phase 2 (this commit completes that scope).
```

---

## 6. Commit 3 — Refactor schema to delegate

### Files touched

```
services/api/app/instrument_geometry/neck/fretboard_ecosphere.py    (refactor)
services/api/tests/test_fretboard_ecosphere.py                       (extend tests)
```

### 6.1 What gets refactored

The Phase 1 commit (`9d37f1ea`) introduced `_fret_position_temperament()` (or whatever the internal method ended up being called) inside the schema. That method should:

- Stop computing fret positions internally
- Resolve the schema's `temperament` field to a `TemperamentSystem` enum value
- Call `resolve_temperament_ratios(system, fret_count, custom_ratios)` to get ratios
- Call `compute_fret_positions_from_ratios_mm(scale_length, ratios)` to get positions
- Return those positions

Skeleton of the refactored method (adjust to actual schema names — the implementing session needs to read the current `fretboard_ecosphere.py` first to match conventions):

```python
from app.calculators.alternative_temperaments import (
    TemperamentSystem,
    resolve_temperament_ratios,
    compute_fret_positions_from_ratios_mm,
)

class FretboardEcosphere(BaseModel):
    # ... existing fields ...

    def _fret_positions_for_string(self, scale_length_mm: float) -> List[float]:
        """Compute fret positions along a single string of given scale length.

        Delegates to alternative_temperaments kernel — temperament resolution
        and ratio-to-position conversion both live there.
        """
        system = self._resolve_temperament_system()
        custom = self._custom_ratios_if_any()
        ratios = resolve_temperament_ratios(
            system,
            fret_count=self.fret_count,
            custom_ratios=custom,
        )
        return compute_fret_positions_from_ratios_mm(scale_length_mm, ratios)

    def _resolve_temperament_system(self) -> TemperamentSystem:
        """Map the schema's temperament field to TemperamentSystem enum."""
        mapping = {
            "12-TET": TemperamentSystem.EQUAL_12TET,
            "19-TET": TemperamentSystem.EQUAL_19TET,
            "24-TET": TemperamentSystem.EQUAL_24TET,
            "31-TET": TemperamentSystem.EQUAL_31TET,
        }
        if self.temperament in mapping:
            return mapping[self.temperament]
        # Extend as needed for non-equal-temperament cases
        raise ValueError(f"Unsupported temperament: {self.temperament}")

    def _custom_ratios_if_any(self) -> Optional[List[float]]:
        """Return custom_ratios if the schema's temperament is custom."""
        # Phase 1 schema may not have a custom_ratios field yet —
        # if it doesn't, return None and address in Phase 2 if needed
        return getattr(self, "custom_ratios", None)
```

If the Phase 1 schema also has a `to_scala_intervals()` method, refactor it to use `scala_loader` for serialization rather than computing intervals internally:

```python
from app.calculators.scala_loader import ScalaScale, ScalaPitch

def to_scala_intervals(self) -> ScalaScale:
    """Export the schema's temperament as a Scala scale.

    Useful for round-tripping: schema → .scl → schema gives identical math.
    """
    system = self._resolve_temperament_system()
    ratios = resolve_temperament_ratios(
        system, fret_count=self.fret_count, custom_ratios=self._custom_ratios_if_any()
    )
    pitches = [
        ScalaPitch(
            source_text=f"{r:.10f}",
            cents=None,
            ratio=None,
            frequency_ratio=r,
        )
        for r in ratios
    ]
    return ScalaScale(
        description=f"Generated from FretboardEcosphere temperament={self.temperament}",
        pitch_count=len(pitches),
        pitches=pitches,
    )
```

### 6.2 Tests for Commit 3

The 24 tests from commit `9d37f1ea` should all still pass. Add three regression tests that prove the delegation works:

```python
class TestKernelDelegation:
    def test_12tet_schema_matches_kernel_directly(self):
        """Schema-computed positions must equal kernel-computed positions
        within 1e-9 mm (i.e., delegation is honest, not just close)."""
        from app.calculators.alternative_temperaments import (
            resolve_temperament_ratios,
            compute_fret_positions_from_ratios_mm,
            TemperamentSystem,
        )

        eco = FretboardEcosphere(
            scale_length_mm=647.7, fret_count=22, temperament="12-TET",
            # ... whatever required fields the Phase 1 schema needs
        )
        schema_positions = eco._fret_positions_for_string(647.7)

        ratios = resolve_temperament_ratios(TemperamentSystem.EQUAL_12TET, 22)
        kernel_positions = compute_fret_positions_from_ratios_mm(647.7, ratios)

        for s, k in zip(schema_positions, kernel_positions):
            assert abs(s - k) < 1e-9

    def test_19tet_real_math_not_12tet_stub(self):
        """19-TET output must differ from 12-TET (proves the alt-temperament
        is actually 19-TET now, not the old 12-TET stub)."""
        eco_12 = FretboardEcosphere(
            scale_length_mm=647.7, fret_count=12, temperament="12-TET",
        )
        eco_19 = FretboardEcosphere(
            scale_length_mm=647.7, fret_count=12, temperament="19-TET",
        )
        # Position of fret 12: in 12-TET it's the octave; in 19-TET it isn't
        pos_12 = eco_12._fret_positions_for_string(647.7)[11]  # fret 12, 0-indexed
        pos_19 = eco_19._fret_positions_for_string(647.7)[11]
        # Fret 12 in 12-TET = scale_length / 2 = 323.85 mm
        assert abs(pos_12 - 323.85) < 0.01
        # Fret 12 in 19-TET ≠ octave — should differ by at least 5mm
        assert abs(pos_12 - pos_19) > 5.0

    def test_scala_round_trip(self):
        """Schema → to_scala_intervals → ScalaScale → scala_to_fret_ratios →
        positions should match schema's own positions."""
        from app.calculators.scala_loader import scala_to_fret_ratios
        from app.calculators.alternative_temperaments import compute_fret_positions_from_ratios_mm

        eco = FretboardEcosphere(
            scale_length_mm=647.7, fret_count=22, temperament="12-TET",
        )
        scale = eco.to_scala_intervals()
        scl_ratios = scala_to_fret_ratios(scale, fret_count=22)
        scl_positions = compute_fret_positions_from_ratios_mm(647.7, scl_ratios)
        eco_positions = eco._fret_positions_for_string(647.7)

        for s, e in zip(scl_positions, eco_positions):
            assert abs(s - e) < 1e-9
```

### 6.3 Acceptance for Commit 3

```
□ Schema's _fret_position_* method delegates to alternative_temperaments kernel
□ Schema's to_scala_intervals method delegates to scala_loader
□ All 24 existing schema tests pass unmodified
□ 3 new delegation tests pass
□ 19-TET schema output is structurally different from 12-TET schema output
   (proves N-TET is real, not stubbed)
□ Schema → Scala → Ratios → Positions round-trip is byte-identical
□ Diff against pre-commit shows reduction in schema LOC (math removed,
   delegation added — net negative ~25 lines)
□ No regressions in existing math kernel tests (16 added in commit 1,
   9 added in commit 2, all still pass)
```

### 6.4 Commit message for Commit 3

```
refactor(ecosphere): delegate schema fret math to existing kernels

The FretboardEcosphere schema (commit 9d37f1ea) implemented fret position
math internally, including stub support for 19-TET, 24-TET, and 31-TET
that was actually 12-TET under the hood.

This commit refactors the schema to:
  - Delegate fret position math to alternative_temperaments.compute_fret_positions_from_ratios_mm
  - Resolve temperament systems via alternative_temperaments.resolve_temperament_ratios
    (added in earlier commit, supports real N-TET math)
  - Delegate Scala interval export to scala_loader.ScalaScale serialization

Net effect:
  - 19-TET, 24-TET, 31-TET temperaments now use real math (verified
    by test_19tet_real_math_not_12tet_stub)
  - Schema → Scala → schema round-trip is byte-identical (verified
    by test_scala_round_trip)
  - Single source of truth for fret position math — bug fixes in
    fret_math.py / alternative_temperaments.py now propagate to the
    schema automatically

Tests:
  - 24 existing schema tests: unchanged, all pass
  - 3 new delegation tests: pass
  - Math kernel tests (added in earlier commits): unchanged

References:
  Sprint FRET-A Phase 1.5 dev order
  Commit 9d37f1ea (Phase 1: schema with self-contained math)
```

---

## 7. Pre-flight Checklist

```
□ On branch sprint/fret-ecosphere-a (post commit 9d37f1ea)
□ Read fretboard_ecosphere.py — confirm exact method names and field names
   before writing the refactor patches in commit 3
□ Verify FretPosition dataclass has a .ratio attribute (per §4.1 note);
   if not, adjust resolve_temperament_ratios accordingly
□ Confirm test directory structure:
   - services/api/app/tests/calculators/ exists
   - services/api/tests/ vs services/api/app/tests/ — match Phase 1's choice
□ /tmp/baseline_pre_fret_a.txt exists from earlier baseline capture
   (used to confirm no test loss after each commit)
```

---

## 8. Verification Between Commits

After each commit, run:

```bash
cd services/api
pytest -v --tb=short > /tmp/post_commit_$(git rev-parse --short HEAD).txt 2>&1
echo "Exit code: $?" >> /tmp/post_commit_$(git rev-parse --short HEAD).txt
diff <(grep -E "^(PASSED|FAILED|ERROR)" /tmp/baseline_pre_fret_a.txt | sort) \
     <(grep -E "^(PASSED|FAILED|ERROR)" /tmp/post_commit_*.txt | sort) \
     | head -50
```

If the diff shows any test moving from PASSED to FAILED, **stop and investigate before next commit**. The whole point of staging in three commits is preserving bisection ability.

---

## 9. What This Sprint Does NOT Do

```
- Does NOT touch the Phase 1 schema's existing 24 tests (all preserved)
- Does NOT add new schema fields beyond what Phase 1 has
- Does NOT touch the API router (Phase 2)
- Does NOT touch DXF projection (Phase 7)
- Does NOT modify mvp_router.py, fret_slots_export.py, or any
  CAM pipeline code
- Does NOT address the SPRINTS.md GRBL spindle backlog item
- Does NOT remove the FRET-A v2 phase numbering — this slots in as
  Phase 1.5 between the existing Phase 1 (committed) and the
  upcoming Phase 2 (router)
```

---

## 10. After This Sprint Lands

The next session resumes Phase 2 of FRET-A v2 (FastAPI router). With the kernels honest and the schema delegating, the router can expose the temperament list as a real public API without the structural lie.

Two follow-ups to track:

```
□ FRET-A v2 dev order's Phase 1 acceptance criteria are now retroactively met
   (math kernel additions, .scl parser) — note this in SPRINTS.md when
   commit 3 lands so future readers know phase ordering shifted
   
□ The 3 .scl sample files at data/scala_samples/ are reusable by any future
   feature that wants temperament import — flag in SPRINTS.md as a
   reusable asset, not an FRET-A-specific thing
```

---

## 11. Sprint Sizing

```
Commit 1 (kernel extension)      : 1.0 hr
Commit 2 (Scala parser)          : 1.0 hr
Commit 3 (schema refactor)       : 0.75 hr
Verification + diff checks       : 0.25 hr
                            Total: 3.0 hr (fits one focused session)
```

---

**End of Sprint FRET-A Phase 1.5 Dev Order**
