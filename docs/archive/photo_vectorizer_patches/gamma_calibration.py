"""
gamma_calibration.py — Derive γ transfer coefficients from measurement data.

This module provides tools to calibrate the γ (gamma) transfer coefficient
from measured Chladni (free-plate) and assembled-box frequencies.

Theory:
    γ = f_box / f_free

    Where:
        f_free = free plate modal frequency (Chladni pattern)
        f_box  = same mode frequency when plate is assembled into body

    For guitar tops, γ is typically 0.70 - 0.95 depending on:
        - Boundary conditions (linings, kerfing)
        - Air loading (cavity volume, soundhole)
        - Bracing pattern and mass

Calibration Approach:
    1. Measure multiple modes on free plate (tap test + FFT)
    2. Assemble plate into body
    3. Measure same modes on assembled instrument
    4. Compute γ for each mode
    5. Statistical analysis: mean, std, confidence intervals
    6. Mode-weighted average for design use

Usage:
    >>> from tap_tone_pi.design import GammaCalibration, ModeMeasurement
    >>>
    >>> # Single specimen calibration
    >>> cal = GammaCalibration()
    >>> cal.add_mode(mode_id="1,1", f_free=185.0, f_box=158.0)
    >>> cal.add_mode(mode_id="2,1", f_free=312.0, f_box=275.0)
    >>> cal.add_mode(mode_id="1,2", f_free=425.0, f_box=385.0)
    >>>
    >>> result = cal.compute()
    >>> print(f"γ = {result.gamma_mean:.3f} ± {result.gamma_std:.3f}")

    >>> # Multi-specimen calibration
    >>> cal = GammaCalibration()
    >>> cal.add_specimen("guitar_001", [
    ...     ModeMeasurement("1,1", 185.0, 158.0),
    ...     ModeMeasurement("2,1", 312.0, 275.0),
    ... ])
    >>> cal.add_specimen("guitar_002", [
    ...     ModeMeasurement("1,1", 178.0, 152.0),
    ...     ModeMeasurement("2,1", 298.0, 262.0),
    ... ])
    >>> result = cal.compute()
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class ModeMeasurement:
    """Single mode frequency measurement pair.

    Attributes:
        mode_id: Mode identifier, e.g., "1,1" or "fundamental"
        f_free_Hz: Free plate frequency (Hz)
        f_box_Hz: Assembled box frequency (Hz)
        uncertainty_free_Hz: Measurement uncertainty for f_free (optional)
        uncertainty_box_Hz: Measurement uncertainty for f_box (optional)
    """

    mode_id: str
    f_free_Hz: float
    f_box_Hz: float
    uncertainty_free_Hz: float = 0.0
    uncertainty_box_Hz: float = 0.0

    def __post_init__(self):
        if self.f_free_Hz <= 0:
            raise ValueError(f"f_free_Hz must be positive, got {self.f_free_Hz}")
        if self.f_box_Hz <= 0:
            raise ValueError(f"f_box_Hz must be positive, got {self.f_box_Hz}")

    @property
    def gamma(self) -> float:
        """Compute γ = f_box / f_free."""
        return self.f_box_Hz / self.f_free_Hz

    @property
    def gamma_uncertainty(self) -> float:
        """Propagate uncertainty to γ using standard error propagation.

        For γ = f_box / f_free:
            σ_γ/γ = sqrt((σ_box/f_box)² + (σ_free/f_free)²)
        """
        if self.uncertainty_free_Hz == 0 and self.uncertainty_box_Hz == 0:
            return 0.0

        rel_unc_free = self.uncertainty_free_Hz / self.f_free_Hz
        rel_unc_box = self.uncertainty_box_Hz / self.f_box_Hz
        rel_unc_gamma = math.sqrt(rel_unc_free**2 + rel_unc_box**2)

        return self.gamma * rel_unc_gamma


@dataclass
class SpecimenData:
    """Measurement data for a single specimen (guitar).

    Attributes:
        specimen_id: Unique identifier for this specimen
        modes: List of mode measurements
        metadata: Optional metadata (wood species, thickness, etc.)
    """

    specimen_id: str
    modes: List[ModeMeasurement] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_mode(
        self,
        mode_id: str,
        f_free_Hz: float,
        f_box_Hz: float,
        uncertainty_free_Hz: float = 0.0,
        uncertainty_box_Hz: float = 0.0,
    ) -> None:
        """Add a mode measurement."""
        self.modes.append(
            ModeMeasurement(
                mode_id=mode_id,
                f_free_Hz=f_free_Hz,
                f_box_Hz=f_box_Hz,
                uncertainty_free_Hz=uncertainty_free_Hz,
                uncertainty_box_Hz=uncertainty_box_Hz,
            )
        )

    def get_gamma_values(self) -> List[float]:
        """Get γ values for all modes."""
        return [m.gamma for m in self.modes]

    def get_mode_ids(self) -> List[str]:
        """Get mode IDs."""
        return [m.mode_id for m in self.modes]


@dataclass
class GammaCalibrationResult:
    """Result of γ calibration analysis.

    Attributes:
        gamma_mean: Mean γ across all measurements
        gamma_std: Standard deviation of γ
        gamma_sem: Standard error of the mean
        gamma_ci_95: 95% confidence interval (low, high)
        n_measurements: Total number of mode measurements
        n_specimens: Number of specimens
        mode_gammas: Dict mapping mode_id to (mean_γ, std_γ)
        specimen_gammas: Dict mapping specimen_id to mean_γ
        all_gammas: List of all individual γ values
        weighted_gamma: Inverse-variance weighted mean (if uncertainties provided)
    """

    gamma_mean: float
    gamma_std: float
    gamma_sem: float
    gamma_ci_95: Tuple[float, float]
    n_measurements: int
    n_specimens: int
    mode_gammas: Dict[str, Tuple[float, float]]  # mode_id -> (mean, std)
    specimen_gammas: Dict[str, float]  # specimen_id -> mean_gamma
    all_gammas: List[float]
    weighted_gamma: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "gamma_mean": self.gamma_mean,
            "gamma_std": self.gamma_std,
            "gamma_sem": self.gamma_sem,
            "gamma_ci_95": list(self.gamma_ci_95),
            "n_measurements": self.n_measurements,
            "n_specimens": self.n_specimens,
            "mode_gammas": {k: list(v) for k, v in self.mode_gammas.items()},
            "specimen_gammas": self.specimen_gammas,
            "weighted_gamma": self.weighted_gamma,
        }


# =============================================================================
# Calibration Engine
# =============================================================================


class GammaCalibration:
    """Engine for calibrating γ from measurement data.

    Supports:
        - Single specimen with multiple modes
        - Multiple specimens for statistical robustness
        - Mode-specific γ analysis
        - Uncertainty propagation
        - Weighted averaging

    Example:
        >>> cal = GammaCalibration()
        >>> cal.add_mode("1,1", 185.0, 158.0)
        >>> cal.add_mode("2,1", 312.0, 275.0)
        >>> result = cal.compute()
        >>> print(result.gamma_mean)
    """

    def __init__(self):
        self.specimens: Dict[str, SpecimenData] = {}
        self._default_specimen = "default"

    def add_mode(
        self,
        mode_id: str,
        f_free_Hz: float,
        f_box_Hz: float,
        uncertainty_free_Hz: float = 0.0,
        uncertainty_box_Hz: float = 0.0,
    ) -> None:
        """Add a mode measurement to the default specimen.

        Convenience method for single-specimen calibration.
        """
        if self._default_specimen not in self.specimens:
            self.specimens[self._default_specimen] = SpecimenData(
                specimen_id=self._default_specimen
            )

        self.specimens[self._default_specimen].add_mode(
            mode_id=mode_id,
            f_free_Hz=f_free_Hz,
            f_box_Hz=f_box_Hz,
            uncertainty_free_Hz=uncertainty_free_Hz,
            uncertainty_box_Hz=uncertainty_box_Hz,
        )

    def add_specimen(
        self,
        specimen_id: str,
        modes: List[ModeMeasurement],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a complete specimen with its mode measurements."""
        self.specimens[specimen_id] = SpecimenData(
            specimen_id=specimen_id,
            modes=modes,
            metadata=metadata or {},
        )

    def add_measurement(
        self,
        specimen_id: str,
        mode_id: str,
        f_free_Hz: float,
        f_box_Hz: float,
        uncertainty_free_Hz: float = 0.0,
        uncertainty_box_Hz: float = 0.0,
    ) -> None:
        """Add a single measurement to a specific specimen."""
        if specimen_id not in self.specimens:
            self.specimens[specimen_id] = SpecimenData(specimen_id=specimen_id)

        self.specimens[specimen_id].add_mode(
            mode_id=mode_id,
            f_free_Hz=f_free_Hz,
            f_box_Hz=f_box_Hz,
            uncertainty_free_Hz=uncertainty_free_Hz,
            uncertainty_box_Hz=uncertainty_box_Hz,
        )

    def compute(self) -> GammaCalibrationResult:
        """Compute calibration statistics.

        Returns:
            GammaCalibrationResult with statistics

        Raises:
            ValueError: If no measurements have been added
        """
        if not self.specimens:
            raise ValueError("No measurements added. Use add_mode() or add_specimen().")

        # Collect all γ values
        all_gammas: List[float] = []
        all_measurements: List[ModeMeasurement] = []

        for specimen in self.specimens.values():
            for mode in specimen.modes:
                all_gammas.append(mode.gamma)
                all_measurements.append(mode)

        if not all_gammas:
            raise ValueError("No mode measurements found.")

        n = len(all_gammas)

        # Basic statistics
        gamma_mean = statistics.mean(all_gammas)
        gamma_std = statistics.stdev(all_gammas) if n > 1 else 0.0
        gamma_sem = gamma_std / math.sqrt(n) if n > 1 else 0.0

        # 95% CI using t-distribution approximation
        # For n > 30, t ≈ 1.96; for smaller n, use approximate values
        if n >= 30:
            t_crit = 1.96
        elif n >= 10:
            t_crit = 2.23
        elif n >= 5:
            t_crit = 2.78
        else:
            t_crit = 3.18  # Conservative for small samples

        ci_half = t_crit * gamma_sem
        gamma_ci_95 = (gamma_mean - ci_half, gamma_mean + ci_half)

        # Per-mode statistics
        mode_data: Dict[str, List[float]] = {}
        for specimen in self.specimens.values():
            for mode in specimen.modes:
                if mode.mode_id not in mode_data:
                    mode_data[mode.mode_id] = []
                mode_data[mode.mode_id].append(mode.gamma)

        mode_gammas: Dict[str, Tuple[float, float]] = {}
        for mode_id, gammas in mode_data.items():
            m = statistics.mean(gammas)
            s = statistics.stdev(gammas) if len(gammas) > 1 else 0.0
            mode_gammas[mode_id] = (m, s)

        # Per-specimen mean
        specimen_gammas: Dict[str, float] = {}
        for specimen_id, specimen in self.specimens.items():
            if specimen.modes:
                specimen_gammas[specimen_id] = statistics.mean(
                    specimen.get_gamma_values()
                )

        # Weighted average (inverse-variance weighting) if uncertainties available
        weighted_gamma = None
        weights = []
        weighted_values = []

        for meas in all_measurements:
            if meas.gamma_uncertainty > 0:
                w = 1.0 / (meas.gamma_uncertainty**2)
                weights.append(w)
                weighted_values.append(meas.gamma * w)

        if weights:
            weighted_gamma = sum(weighted_values) / sum(weights)

        return GammaCalibrationResult(
            gamma_mean=gamma_mean,
            gamma_std=gamma_std,
            gamma_sem=gamma_sem,
            gamma_ci_95=gamma_ci_95,
            n_measurements=n,
            n_specimens=len(self.specimens),
            mode_gammas=mode_gammas,
            specimen_gammas=specimen_gammas,
            all_gammas=all_gammas,
            weighted_gamma=weighted_gamma,
        )

    def clear(self) -> None:
        """Clear all measurements."""
        self.specimens.clear()


# =============================================================================
# Reporting
# =============================================================================


def format_gamma_calibration_report(result: GammaCalibrationResult) -> str:
    """Format calibration result as human-readable report."""
    lines = []
    lines.append("=" * 65)
    lines.append("γ (Gamma) Calibration Report")
    lines.append("=" * 65)

    lines.append("\nData Summary:")
    lines.append(f"  Specimens:    {result.n_specimens}")
    lines.append(f"  Measurements: {result.n_measurements}")

    lines.append("\nOverall Statistics:")
    lines.append(f"  γ mean = {result.gamma_mean:.4f}")
    lines.append(f"  γ std  = {result.gamma_std:.4f}")
    lines.append(f"  γ SEM  = {result.gamma_sem:.4f}")
    lines.append(
        f"  95% CI = ({result.gamma_ci_95[0]:.4f}, {result.gamma_ci_95[1]:.4f})"
    )

    if result.weighted_gamma is not None:
        lines.append(f"  γ weighted = {result.weighted_gamma:.4f} (inverse-variance)")

    if result.mode_gammas:
        lines.append("\nPer-Mode Analysis:")
        for mode_id, (mean, std) in sorted(result.mode_gammas.items()):
            if std > 0:
                lines.append(f"  Mode {mode_id}: γ = {mean:.4f} ± {std:.4f}")
            else:
                lines.append(f"  Mode {mode_id}: γ = {mean:.4f}")

    if len(result.specimen_gammas) > 1:
        lines.append("\nPer-Specimen Analysis:")
        for spec_id, gamma in sorted(result.specimen_gammas.items()):
            lines.append(f"  {spec_id}: γ = {gamma:.4f}")

    lines.append("\nRecommendation:")
    lines.append(f"  Use γ = {result.gamma_mean:.3f} for design calculations")
    if result.gamma_std > 0.05:
        lines.append("  (High variability - consider more specimens)")

    lines.append("")
    return "\n".join(lines)


# =============================================================================
# Convenience Functions
# =============================================================================


def calibrate_gamma_from_pairs(
    frequency_pairs: List[Tuple[float, float]],
    mode_ids: Optional[List[str]] = None,
) -> GammaCalibrationResult:
    """Quick calibration from list of (f_free, f_box) pairs.

    Args:
        frequency_pairs: List of (f_free_Hz, f_box_Hz) tuples
        mode_ids: Optional list of mode identifiers

    Returns:
        GammaCalibrationResult

    Example:
        >>> result = calibrate_gamma_from_pairs([
        ...     (185.0, 158.0),  # Mode 1
        ...     (312.0, 275.0),  # Mode 2
        ...     (425.0, 385.0),  # Mode 3
        ... ])
        >>> print(result.gamma_mean)
    """
    cal = GammaCalibration()

    for i, (f_free, f_box) in enumerate(frequency_pairs):
        mode_id = mode_ids[i] if mode_ids else f"mode_{i + 1}"
        cal.add_mode(mode_id, f_free, f_box)

    return cal.compute()


def calibrate_gamma_multi_specimen(
    specimen_data: Dict[str, List[Tuple[float, float]]],
) -> GammaCalibrationResult:
    """Calibrate γ from multiple specimens.

    Args:
        specimen_data: Dict mapping specimen_id to list of (f_free, f_box) pairs

    Returns:
        GammaCalibrationResult

    Example:
        >>> result = calibrate_gamma_multi_specimen({
        ...     "guitar_001": [(185, 158), (312, 275)],
        ...     "guitar_002": [(178, 152), (298, 262)],
        ... })
    """
    cal = GammaCalibration()

    for specimen_id, pairs in specimen_data.items():
        modes = [
            ModeMeasurement(f"mode_{i + 1}", f_free, f_box)
            for i, (f_free, f_box) in enumerate(pairs)
        ]
        cal.add_specimen(specimen_id, modes)

    return cal.compute()
