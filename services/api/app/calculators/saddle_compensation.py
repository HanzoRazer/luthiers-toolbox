"""
Bridge Saddle Compensation Calculator.

Two modes:
  - MODE 1 (Design): Estimate per-string compensation from physical parameters
  - MODE 2 (Setup): Compute saddle adjustments from measured cents error

Semi-empirical model based on string gauge, action, scale length, tension, and wound status.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field


# =============================================================================
# Constants
# =============================================================================

# Reference scale length for normalization (Gibson standard)
REFERENCE_SCALE_MM = 647.7  # 25.5" in mm

# Semi-empirical compensation model coefficients
BASE_COMPENSATION_MM = 0.45
GAUGE_COEFFICIENT = 0.55
ACTION_COEFFICIENT = 0.18
ACTION_EXPONENT = 1.7
SCALE_COEFFICIENT = 0.25
TENSION_COEFFICIENT = 7.5
WOUND_BONUS_MM = 0.55

# CSV column definitions for bench tool mode
INPUT_CSV_COLUMNS = [
    "name", "x_mm", "current_comp_mm",
    "cents_error", "weight"
]

OUTPUT_CSV_COLUMNS = [
    "name", "x_mm", "current_comp_mm",
    "cents_error", "weight", "delta_mm",
    "target_comp_mm", "fitted_comp_mm", "residual_mm"
]


# =============================================================================
# MODE 1 — Design Calculator Models
# =============================================================================


class StringSpec(BaseModel):
    """Specification for a single string."""

    name: str = Field(..., description="String identifier (e.g., 'E6', 'B2')")
    gauge_in: float = Field(..., gt=0, description="String gauge in inches")
    tension_lb: float = Field(..., gt=0, description="String tension in pounds")
    is_wound: bool = Field(..., description="Whether the string is wound")
    x_mm: float = Field(..., description="X position from bass edge in mm")


class DesignCalculatorInput(BaseModel):
    """Input for design mode compensation calculation."""

    scale_length_mm: float = Field(
        ..., gt=0, description="Scale length in millimeters"
    )
    action_12th_treble_mm: float = Field(
        ..., ge=0, description="Action at 12th fret, treble side (mm)"
    )
    action_12th_bass_mm: float = Field(
        ..., ge=0, description="Action at 12th fret, bass side (mm)"
    )
    strings: List[StringSpec] = Field(
        ..., min_length=1, description="List of string specifications"
    )


class StringCompensationResult(BaseModel):
    """Compensation result for a single string."""

    name: str
    x_mm: float
    compensation_mm: float = Field(..., description="Estimated compensation in mm")
    fitted_compensation_mm: float = Field(
        ..., description="Compensation from straight saddle fit"
    )
    residual_mm: float = Field(
        ..., description="Difference between estimated and fitted (crown deviation)"
    )


class StraightSaddleFit(BaseModel):
    """Result of fitting a straight saddle line."""

    slope: float = Field(..., description="Slope of fitted line (mm/mm)")
    intercept_mm: float = Field(..., description="Intercept at x=0 in mm")
    slant_angle_deg: float = Field(
        ..., description="Saddle slant angle relative to perpendicular"
    )
    r_squared: float = Field(..., ge=0, le=1, description="Coefficient of determination")


class DesignCalculatorResult(BaseModel):
    """Complete result from design mode calculation."""

    scale_length_mm: float
    string_results: List[StringCompensationResult]
    saddle_fit: StraightSaddleFit
    max_residual_mm: float = Field(
        ..., description="Maximum crown deviation from straight saddle"
    )
    avg_compensation_mm: float = Field(..., description="Average compensation across strings")
    recommendation: str = Field(..., description="Human-readable recommendation")


# =============================================================================
# MODE 2 — Setup Calculator Models
# =============================================================================


class StringMeasurementInput(BaseModel):
    """Measured intonation data for a single string."""

    name: str = Field(..., description="String identifier")
    x_mm: float = Field(..., description="X position from bass edge in mm")
    current_comp_mm: float = Field(
        ..., description="Current saddle compensation position (mm)"
    )
    cents_error: float = Field(
        ..., description="Measured cents error (positive = sharp, negative = flat)"
    )
    weight: float = Field(
        default=1.0, ge=0, description="Weight for fitting (0-1, default 1.0)"
    )


class SetupCalculatorInput(BaseModel):
    """Input for setup mode calculation."""

    scale_length_mm: float = Field(..., gt=0, description="Scale length in mm")
    strings: List[StringMeasurementInput] = Field(
        ..., min_length=1, description="Measured string data"
    )


class StringSetupResult(BaseModel):
    """Setup adjustment result for a single string."""

    name: str
    x_mm: float
    current_comp_mm: float
    cents_error: float
    delta_L_mm: float = Field(
        ..., description="Saddle adjustment needed (positive = move back)"
    )
    new_comp_mm: float = Field(..., description="New compensation position")


class SetupCalculatorResult(BaseModel):
    """Complete result from setup mode calculation."""

    scale_length_mm: float
    string_results: List[StringSetupResult]
    avg_adjustment_mm: float = Field(..., description="Average adjustment magnitude")
    max_adjustment_mm: float = Field(..., description="Maximum adjustment magnitude")
    recommendation: str


# =============================================================================
# MODE 1 — Design Calculator Functions
# =============================================================================


def _interpolate_action(
    x_mm: float,
    action_bass_mm: float,
    action_treble_mm: float,
    string_spread_mm: float,
) -> float:
    """Interpolate action at string position assuming linear taper."""
    if string_spread_mm <= 0:
        return (action_bass_mm + action_treble_mm) / 2
    t = x_mm / string_spread_mm
    return action_bass_mm + t * (action_treble_mm - action_bass_mm)


def estimate_string_compensation_mm(
    gauge_in: float,
    tension_lb: float,
    is_wound: bool,
    action_mm: float,
    scale_length_mm: float,
) -> float:
    """
    Estimate compensation for a single string using semi-empirical model.

    c_i = base(0.45) + gauge_term(0.55 * gauge_mm)
        + action_term(0.18 * action^1.7)
        + scale_term(0.25 * scale/647.7)
        + tension_term(7.5 / tension_lb)
        + wound_term(0.55 if wound else 0)

    Args:
        gauge_in: String gauge in inches
        tension_lb: String tension in pounds
        is_wound: Whether string is wound
        action_mm: Action at 12th fret for this string position
        scale_length_mm: Scale length in mm

    Returns:
        Estimated compensation in mm
    """
    gauge_mm = gauge_in * 25.4

    base_term = BASE_COMPENSATION_MM
    gauge_term = GAUGE_COEFFICIENT * gauge_mm
    action_term = ACTION_COEFFICIENT * (action_mm ** ACTION_EXPONENT)
    scale_term = SCALE_COEFFICIENT * (scale_length_mm / REFERENCE_SCALE_MM)
    tension_term = TENSION_COEFFICIENT / tension_lb
    wound_term = WOUND_BONUS_MM if is_wound else 0.0

    compensation = (
        base_term + gauge_term + action_term + scale_term + tension_term + wound_term
    )

    return compensation


def fit_straight_saddle(
    x_positions: List[float],
    compensations: List[float],
) -> StraightSaddleFit:
    """
    Fit a straight line to compensation data using least squares.

    The saddle slant angle is computed from the slope:
        slant_angle_deg = degrees(arctan(slope))

    Args:
        x_positions: X positions of strings (mm from bass edge)
        compensations: Compensation values for each string (mm)

    Returns:
        StraightSaddleFit with slope, intercept, angle, and R-squared
    """
    n = len(x_positions)
    if n < 2:
        # Single string: no slope
        return StraightSaddleFit(
            slope=0.0,
            intercept_mm=compensations[0] if compensations else 0.0,
            slant_angle_deg=0.0,
            r_squared=1.0,
        )

    # Compute means
    x_mean = sum(x_positions) / n
    y_mean = sum(compensations) / n

    # Compute slope and intercept
    numerator = sum(
        (x - x_mean) * (y - y_mean) for x, y in zip(x_positions, compensations)
    )
    denominator = sum((x - x_mean) ** 2 for x in x_positions)

    if denominator < 1e-10:
        # All x values are the same
        slope = 0.0
        intercept = y_mean
    else:
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

    # Compute R-squared
    ss_tot = sum((y - y_mean) ** 2 for y in compensations)
    ss_res = sum(
        (y - (slope * x + intercept)) ** 2
        for x, y in zip(x_positions, compensations)
    )

    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-10 else 1.0
    r_squared = max(0.0, min(1.0, r_squared))

    # Compute slant angle
    slant_angle_deg = math.degrees(math.atan(slope))

    return StraightSaddleFit(
        slope=slope,
        intercept_mm=intercept,
        slant_angle_deg=slant_angle_deg,
        r_squared=r_squared,
    )


def build_design_report(inp: DesignCalculatorInput) -> DesignCalculatorResult:
    """
    Build complete design mode report.

    Calculates per-string compensation, fits straight saddle, computes residuals.

    Args:
        inp: Design calculator input with scale length, action, and string specs

    Returns:
        DesignCalculatorResult with all calculations and recommendation
    """
    # Determine string spread for action interpolation
    x_positions = [s.x_mm for s in inp.strings]
    string_spread_mm = max(x_positions) - min(x_positions) if x_positions else 0

    # Calculate per-string compensation
    compensations: List[float] = []
    for string in inp.strings:
        action_at_string = _interpolate_action(
            string.x_mm,
            inp.action_12th_bass_mm,
            inp.action_12th_treble_mm,
            string_spread_mm,
        )
        comp = estimate_string_compensation_mm(
            gauge_in=string.gauge_in,
            tension_lb=string.tension_lb,
            is_wound=string.is_wound,
            action_mm=action_at_string,
            scale_length_mm=inp.scale_length_mm,
        )
        compensations.append(comp)

    # Fit straight saddle
    saddle_fit = fit_straight_saddle(x_positions, compensations)

    # Compute fitted values and residuals
    string_results: List[StringCompensationResult] = []
    residuals: List[float] = []

    for string, comp in zip(inp.strings, compensations):
        fitted = saddle_fit.slope * string.x_mm + saddle_fit.intercept_mm
        residual = comp - fitted
        residuals.append(residual)

        string_results.append(
            StringCompensationResult(
                name=string.name,
                x_mm=string.x_mm,
                compensation_mm=round(comp, 3),
                fitted_compensation_mm=round(fitted, 3),
                residual_mm=round(residual, 3),
            )
        )

    max_residual = max(abs(r) for r in residuals) if residuals else 0.0
    avg_compensation = sum(compensations) / len(compensations) if compensations else 0.0

    # Generate recommendation
    angle = abs(saddle_fit.slant_angle_deg)
    if angle < 1.5:
        rec = "Saddle can be nearly perpendicular; minimal slant needed."
    elif angle < 3.0:
        rec = f"Moderate saddle slant of {angle:.1f}° recommended. Typical for most guitars."
    elif angle < 5.0:
        rec = f"Significant saddle slant of {angle:.1f}°. Consider compensated saddle design."
    else:
        rec = f"Large saddle slant of {angle:.1f}°. Highly recommend individual crown compensation."

    if max_residual > 0.5:
        rec += f" Crown deviation up to {max_residual:.2f}mm — consider crowned saddle."

    return DesignCalculatorResult(
        scale_length_mm=inp.scale_length_mm,
        string_results=string_results,
        saddle_fit=saddle_fit,
        max_residual_mm=round(max_residual, 3),
        avg_compensation_mm=round(avg_compensation, 3),
        recommendation=rec,
    )


# =============================================================================
# MODE 2 — Setup Calculator Functions
# =============================================================================


def compute_saddle_adjustment(
    scale_length_mm: float,
    cents_error: float,
) -> float:
    """
    Compute saddle adjustment from measured cents error.

    Formula: delta_L = scale_length * (2^(cents/1200) - 1)

    Positive cents_error (sharp) → positive delta_L (move saddle back)
    Negative cents_error (flat) → negative delta_L (move saddle forward)

    Args:
        scale_length_mm: Scale length in mm
        cents_error: Measured error in cents (positive = sharp)

    Returns:
        Saddle adjustment in mm (positive = increase compensation)
    """
    # cents_error positive means fretted note is sharp
    # To fix sharp: increase string length → move saddle back
    delta_L = scale_length_mm * (2 ** (cents_error / 1200) - 1)
    return delta_L


def build_setup_result(inp: SetupCalculatorInput) -> SetupCalculatorResult:
    """
    Build complete setup mode report.

    Computes per-string saddle adjustments from measured cents errors.

    Args:
        inp: Setup calculator input with scale length and string measurements

    Returns:
        SetupCalculatorResult with adjustments and recommendations
    """
    string_results: List[StringSetupResult] = []
    adjustments: List[float] = []

    for string in inp.strings:
        delta_L = compute_saddle_adjustment(inp.scale_length_mm, string.cents_error)
        new_comp = string.current_comp_mm + delta_L
        adjustments.append(abs(delta_L))

        string_results.append(
            StringSetupResult(
                name=string.name,
                x_mm=string.x_mm,
                current_comp_mm=string.current_comp_mm,
                cents_error=string.cents_error,
                delta_L_mm=round(delta_L, 3),
                new_comp_mm=round(new_comp, 3),
            )
        )

    avg_adjustment = sum(adjustments) / len(adjustments) if adjustments else 0.0
    max_adjustment = max(adjustments) if adjustments else 0.0

    # Generate recommendation
    if max_adjustment < 0.2:
        rec = "Intonation is excellent. Minor adjustments only."
    elif max_adjustment < 0.5:
        rec = "Moderate adjustments needed. Standard setup procedure."
    elif max_adjustment < 1.0:
        rec = "Significant adjustments required. Check nut slots and fret condition."
    else:
        rec = (
            f"Large adjustments up to {max_adjustment:.2f}mm needed. "
            "Verify scale length, nut position, and consider refret if persistent."
        )

    return SetupCalculatorResult(
        scale_length_mm=inp.scale_length_mm,
        string_results=string_results,
        avg_adjustment_mm=round(avg_adjustment, 3),
        max_adjustment_mm=round(max_adjustment, 3),
        recommendation=rec,
    )

# =============================================================================
# CSV I/O for Bench Tool Mode
# =============================================================================


def read_string_inputs_from_csv(
    path: Union[str, Path]
) -> List[StringMeasurementInput]:
    """
    Read string measurement inputs from a CSV file.

    Expected columns: name, x_mm, current_comp_mm, cents_error, weight
    Weight is optional (defaults to 1.0).

    Args:
        path: Path to input CSV file

    Returns:
        List of StringMeasurementInput objects
    """
    path = Path(path)
    strings: List[StringMeasurementInput] = []

    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            strings.append(
                StringMeasurementInput(
                    name=row["name"].strip(),
                    x_mm=float(row["x_mm"]),
                    current_comp_mm=float(row["current_comp_mm"]),
                    cents_error=float(row["cents_error"]),
                    weight=float(row.get("weight", 1.0) or 1.0),
                )
            )

    return strings


def write_results_to_csv(
    result: SetupCalculatorResult,
    path: Union[str, Path],
    inputs: Optional[List[StringMeasurementInput]] = None,
) -> None:
    """
    Write setup calculator results to a CSV file.

    Output columns: name, x_mm, current_comp_mm, cents_error, weight,
                    delta_mm, target_comp_mm, fitted_comp_mm, residual_mm

    Args:
        result: SetupCalculatorResult from build_setup_result()
        path: Path to output CSV file
        inputs: Original inputs (for weight column); if None, weight defaults to 1.0
    """
    path = Path(path)

    # Build weight lookup from inputs if provided
    weight_map = {}
    if inputs:
        for inp in inputs:
            weight_map[inp.name] = inp.weight

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(OUTPUT_CSV_COLUMNS)

        for sr in result.string_results:
            weight = weight_map.get(sr.name, 1.0)
            # target_comp_mm = new_comp_mm (the calculated target)
            # fitted_comp_mm and residual_mm are N/A for setup mode (use 0)
            writer.writerow([
                sr.name,
                sr.x_mm,
                sr.current_comp_mm,
                sr.cents_error,
                weight,
                sr.delta_L_mm,
                sr.new_comp_mm,  # target_comp_mm
                0.0,  # fitted_comp_mm (N/A for setup mode)
                0.0,  # residual_mm (N/A for setup mode)
            ])


def write_example_input_csv(path: Union[str, Path]) -> None:
    """
    Write an example input CSV template.

    Creates a template with 6 strings (standard guitar) and example values.

    Args:
        path: Path to output CSV template file
    """
    path = Path(path)

    example_strings = [
        ("E6", 0.0, 2.8, 3.0, 1.0),
        ("A5", 10.4, 2.5, -2.0, 1.0),
        ("D4", 20.8, 2.3, 1.5, 1.0),
        ("G3", 31.2, 2.0, 0.0, 1.0),
        ("B2", 41.6, 1.8, 2.0, 1.0),
        ("E1", 52.0, 1.6, -1.0, 1.0),
    ]

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(INPUT_CSV_COLUMNS)
        for row in example_strings:
            writer.writerow(row)


# =============================================================================
# CLI Entry Point
# =============================================================================


def main() -> int:
    """
    CLI entry point for saddle compensation calculator.

    Usage:
        python -m app.calculators.saddle_compensation \
            --scale-length-mm 628.65 \
            --input-csv bench_input.csv \
            --output-csv bench_output.csv

        python -m app.calculators.saddle_compensation \
            --write-example-csv template.csv
    """
    parser = argparse.ArgumentParser(
        description="Bridge saddle compensation calculator (bench tool mode)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Generate example input template:
    python -m app.calculators.saddle_compensation --write-example-csv template.csv

  Calculate adjustments from measurements:
    python -m app.calculators.saddle_compensation --scale-length-mm 628.65 \
        --input-csv measurements.csv --output-csv results.csv
""",
    )

    parser.add_argument(
        "--scale-length-mm",
        type=float,
        help="Scale length in millimeters (e.g., 628.65 for Gibson 24.75\")",
    )
    parser.add_argument(
        "--input-csv",
        type=str,
        help="Path to input CSV with string measurements",
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        help="Path to output CSV for results",
    )
    parser.add_argument(
        "--write-example-csv",
        type=str,
        metavar="PATH",
        help="Write example input template to PATH and exit",
    )

    args = parser.parse_args()

    # Handle example template generation
    if args.write_example_csv:
        write_example_input_csv(args.write_example_csv)
        print(f"Example template written to: {args.write_example_csv}")
        return 0

    # Validate required args for calculation
    if not args.scale_length_mm:
        parser.error("--scale-length-mm is required for calculation")
    if not args.input_csv:
        parser.error("--input-csv is required for calculation")
    if not args.output_csv:
        parser.error("--output-csv is required for calculation")

    # Read inputs
    try:
        strings = read_string_inputs_from_csv(args.input_csv)
    except FileNotFoundError:
        print(f"Error: Input file not found: {args.input_csv}", file=sys.stderr)
        return 1
    except (KeyError, ValueError) as e:
        print(f"Error: Invalid CSV format: {e}", file=sys.stderr)
        return 1

    if not strings:
        print("Error: No strings found in input CSV", file=sys.stderr)
        return 1

    # Run calculation
    inp = SetupCalculatorInput(
        scale_length_mm=args.scale_length_mm,
        strings=strings,
    )
    result = build_setup_result(inp)

    # Write results
    write_results_to_csv(result, args.output_csv, strings)

    # Print summary
    print(f"Processed {len(strings)} strings")
    print(f"Average adjustment: {result.avg_adjustment_mm:.3f} mm")
    print(f"Maximum adjustment: {result.max_adjustment_mm:.3f} mm")
    print(f"Recommendation: {result.recommendation}")
    print(f"Results written to: {args.output_csv}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
