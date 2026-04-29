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
    cents: Optional[float]
    ratio: Optional[Tuple[int, int]]
    frequency_ratio: float


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
    """Convert cents to frequency ratio."""
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


def serialize_scala_to_text(scale: ScalaScale) -> str:
    """Serialize a ScalaScale back to .scl file format.

    Outputs a valid Scala file that can be parsed by parse_scala_content.
    """
    lines = [
        f"! {scale.description}",
        "!",
        scale.description,
        str(scale.pitch_count),
        "!",
    ]

    for pitch in scale.pitches:
        if pitch.cents is not None:
            # Preserve cents form
            lines.append(f" {pitch.cents:.6f}")
        elif pitch.ratio is not None:
            # Preserve ratio form
            num, den = pitch.ratio
            if den == 1:
                lines.append(f" {num}")
            else:
                lines.append(f" {num}/{den}")
        else:
            # Fall back to cents
            import math
            cents = 1200.0 * math.log2(pitch.frequency_ratio)
            lines.append(f" {cents:.6f}")

    return "\n".join(lines) + "\n"
