# tests/test_golden_fret_positions.py
"""
Golden Fixture Tests: Fret Position Calculations

Locks the deterministic fret position calculations to golden snapshots.
These are critical for manufacturing accuracy - any drift would produce
incorrect fret slots on physical instruments.

Standard scale lengths:
- 25.5" (647.7mm) - Fender Stratocaster/Telecaster
- 24.75" (628.65mm) - Gibson Les Paul/SG
- 25" (635mm) - PRS
- 34" (863.6mm) - Fender bass

Run: pytest tests/test_golden_fret_positions.py -v
"""

import json
from pathlib import Path
import pytest


GOLDEN = Path(__file__).parent / "golden"


def _round_positions(positions: list, decimals: int = 4) -> list:
    """Round positions to avoid floating-point noise in comparisons."""
    return [round(p, decimals) for p in positions]


# =============================================================================
# GOLDEN FIXTURE DATA (pre-calculated reference values)
# =============================================================================

# Fender scale (25.5" = 647.7mm), 22 frets
GOLDEN_FENDER_22_FRET_POSITIONS = [
    36.3526, 70.6649, 103.0514, 133.6202, 162.4733, 189.7069,
    215.4121, 239.6746, 262.5753, 284.1907, 304.5929, 323.85,
    342.0263, 359.1825, 375.3757, 390.6601, 405.0866, 418.7035,
    431.5561, 443.6873, 455.1376, 465.9453,
]

# Gibson scale (24.75" = 628.65mm), 22 frets
GOLDEN_GIBSON_22_FRET_POSITIONS = [
    35.2834, 68.5865, 100.0205, 129.6902, 157.6946, 184.1273,
    209.0765, 232.6253, 254.8525, 275.8321, 295.6343, 314.325,
    331.9667, 348.6183, 364.3352, 379.1701, 393.1723, 406.3887,
    418.8632, 430.6377, 441.7512, 452.2411,
]

# PRS scale (25" = 635mm), 24 frets
GOLDEN_PRS_24_FRET_POSITIONS = [
    35.6398, 69.2793, 101.0308, 131.0002, 159.2875, 185.9872,
    211.1883, 234.9751, 257.4267, 278.6183, 298.6205, 317.5,
    335.3199, 352.1397, 368.0154, 383.0001, 397.1438, 410.4936,
    423.0942, 434.9875, 446.2134, 456.8091, 466.8102, 476.25,
]

# Bass scale (34" = 863.6mm), 21 frets
GOLDEN_BASS_21_FRET_POSITIONS = [
    48.4701, 94.2199, 137.4019, 178.1602, 216.631, 252.9426,
    287.2162, 319.5661, 350.1004, 378.9209, 406.1238, 431.8,
    456.0351, 478.9099, 500.5009, 520.8801, 540.1155, 558.2713,
    575.4081, 591.583, 606.8502,
]


# =============================================================================
# GOLDEN SNAPSHOT TESTS
# =============================================================================


@pytest.mark.unit
def test_golden_fender_22_fret_positions():
    """
    Golden test: Fender 25.5" scale, 22 frets.

    Locks the standard Stratocaster/Telecaster fret positions.
    Critical for all Fender-style instruments.
    """
    from app.instrument_geometry.neck.fret_math import compute_fret_positions_mm

    positions = compute_fret_positions_mm(scale_length_mm=647.7, fret_count=22)
    rounded = _round_positions(positions)

    assert rounded == GOLDEN_FENDER_22_FRET_POSITIONS, (
        "Fender 22-fret positions drifted from golden fixture. "
        "This would cause manufacturing errors on Stratocaster/Telecaster builds."
    )


@pytest.mark.unit
def test_golden_gibson_22_fret_positions():
    """
    Golden test: Gibson 24.75" scale, 22 frets.

    Locks the standard Les Paul/SG fret positions.
    Critical for all Gibson-style instruments.
    """
    from app.instrument_geometry.neck.fret_math import compute_fret_positions_mm

    positions = compute_fret_positions_mm(scale_length_mm=628.65, fret_count=22)
    rounded = _round_positions(positions)

    assert rounded == GOLDEN_GIBSON_22_FRET_POSITIONS, (
        "Gibson 22-fret positions drifted from golden fixture. "
        "This would cause manufacturing errors on Les Paul/SG builds."
    )


@pytest.mark.unit
def test_golden_prs_24_fret_positions():
    """
    Golden test: PRS 25" scale, 24 frets.

    Locks the standard PRS fret positions.
    Critical for all PRS-style instruments and extended-range builds.
    """
    from app.instrument_geometry.neck.fret_math import compute_fret_positions_mm

    positions = compute_fret_positions_mm(scale_length_mm=635.0, fret_count=24)
    rounded = _round_positions(positions)

    assert rounded == GOLDEN_PRS_24_FRET_POSITIONS, (
        "PRS 24-fret positions drifted from golden fixture. "
        "This would cause manufacturing errors on PRS-style builds."
    )


@pytest.mark.unit
def test_golden_bass_21_fret_positions():
    """
    Golden test: Fender bass 34" scale, 21 frets.

    Locks the standard Precision/Jazz bass fret positions.
    Critical for all 34" bass builds.
    """
    from app.instrument_geometry.neck.fret_math import compute_fret_positions_mm

    positions = compute_fret_positions_mm(scale_length_mm=863.6, fret_count=21)
    rounded = _round_positions(positions)

    assert rounded == GOLDEN_BASS_21_FRET_POSITIONS, (
        "Bass 21-fret positions drifted from golden fixture. "
        "This would cause manufacturing errors on Precision/Jazz bass builds."
    )


# =============================================================================
# INVARIANT TESTS (mathematical properties that must always hold)
# =============================================================================


@pytest.mark.unit
def test_fret_positions_always_increasing():
    """Fret positions must be strictly monotonically increasing."""
    from app.instrument_geometry.neck.fret_math import compute_fret_positions_mm

    for scale_mm in [508.0, 628.65, 635.0, 647.7, 863.6]:  # 20" to 34"
        positions = compute_fret_positions_mm(scale_mm, fret_count=24)

        for i in range(1, len(positions)):
            assert positions[i] > positions[i-1], (
                f"Scale {scale_mm}mm: Fret {i+1} ({positions[i]}) must be > "
                f"fret {i} ({positions[i-1]})"
            )


@pytest.mark.unit
def test_fret_12_is_half_scale_length():
    """12th fret must be exactly half the scale length (octave)."""
    from app.instrument_geometry.neck.fret_math import compute_fret_positions_mm

    for scale_mm in [508.0, 628.65, 635.0, 647.7, 863.6]:
        positions = compute_fret_positions_mm(scale_mm, fret_count=22)
        fret_12 = positions[11]  # 0-indexed

        expected = scale_mm / 2.0
        assert abs(fret_12 - expected) < 0.001, (
            f"Scale {scale_mm}mm: 12th fret at {fret_12}mm, expected {expected}mm (half scale)"
        )


@pytest.mark.unit
def test_fret_24_is_three_quarters_scale_length():
    """24th fret must be 3/4 of the scale length (two octaves)."""
    from app.instrument_geometry.neck.fret_math import compute_fret_positions_mm

    for scale_mm in [508.0, 628.65, 635.0, 647.7, 863.6]:
        positions = compute_fret_positions_mm(scale_mm, fret_count=24)
        fret_24 = positions[23]  # 0-indexed

        expected = scale_mm * 0.75
        assert abs(fret_24 - expected) < 0.001, (
            f"Scale {scale_mm}mm: 24th fret at {fret_24}mm, expected {expected}mm (3/4 scale)"
        )


@pytest.mark.unit
def test_all_positions_within_scale_length():
    """All fret positions must be less than scale length."""
    from app.instrument_geometry.neck.fret_math import compute_fret_positions_mm

    for scale_mm in [508.0, 628.65, 635.0, 647.7, 863.6]:
        for fret_count in [19, 21, 22, 24]:
            positions = compute_fret_positions_mm(scale_mm, fret_count)

            for i, pos in enumerate(positions):
                assert pos < scale_mm, (
                    f"Scale {scale_mm}mm, fret {i+1}: position {pos}mm >= scale length"
                )


@pytest.mark.unit
def test_fret_spacing_decreases_toward_bridge():
    """Fret spacing must decrease as you move toward the bridge."""
    from app.instrument_geometry.neck.fret_math import compute_fret_positions_mm

    positions = compute_fret_positions_mm(647.7, fret_count=22)

    # Calculate spacing between consecutive frets
    spacings = [positions[0]]  # First fret distance from nut
    for i in range(1, len(positions)):
        spacings.append(positions[i] - positions[i-1])

    # Each spacing should be smaller than the previous
    for i in range(1, len(spacings)):
        assert spacings[i] < spacings[i-1], (
            f"Spacing before fret {i+1} ({spacings[i]}mm) should be less than "
            f"spacing before fret {i} ({spacings[i-1]}mm)"
        )


@pytest.mark.unit
def test_determinism_across_multiple_calls():
    """Same inputs must always produce identical outputs."""
    from app.instrument_geometry.neck.fret_math import compute_fret_positions_mm

    results = []
    for _ in range(10):
        positions = compute_fret_positions_mm(647.7, fret_count=22)
        results.append(tuple(positions))

    # All results must be identical
    assert len(set(results)) == 1, "Fret calculations must be deterministic"
