"""
Mass-Frequency Tracker — System identification via sequential mass removal.

Ross Echols method:
"Two points make a line. A line is a function."

Workflow:
  - Sequential sessions on same instrument
  - Weight recorded at each session (manual input)
  - Modal frequencies extracted per session

Calculations:
  - dF/dM per mode per brace location
  - Linear predictor: delta_M needed to reach target
  - Polynomial fit at 3+ points for nonlinear range

Outputs:
  - Slope chart per mode (dF/dM vs session)
  - Target predictor: "Remove Xg to reach YHz"
  - Sensitivity map: which location moves which mode
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np

from .schemas import (
    MassFrequencyHistory,
    MassFrequencyPrediction,
    ModeSlope,
    SessionRecord,
    TargetPrediction,
)
from .session_store import SessionStore


@dataclass
class FitResult:
    """Result of linear or polynomial fit."""
    slope: float  # dF/dM (Hz per gram)
    intercept: float
    r_squared: float
    coefficients: List[float]  # For polynomial: [c0, c1, c2, ...]
    method: str  # "linear" or "polynomial"


class MassFrequencyTracker:
    """
    Track mass-frequency relationships across sessions.

    Core physics:
        f = (1/2pi) * sqrt(K/M)

    For small changes:
        df/dM = -f / (2M)

    Empirically, dF/dM varies by mode and brace location.
    We fit measured data to extract these sensitivities.
    """

    def __init__(self, store: Optional[SessionStore] = None):
        self.store = store or SessionStore()

    def record_session(
        self,
        specimen_id: str,
        mass_g: float,
        mode_frequencies_hz: List[float],
        timestamp: Optional[str] = None,
        brace_location: Optional[str] = None,
        k_eff_mean: Optional[float] = None,
    ) -> SessionRecord:
        """Record a new measurement session."""
        return self.store.record_session(
            specimen_id=specimen_id,
            mass_g=mass_g,
            mode_frequencies_hz=mode_frequencies_hz,
            timestamp=timestamp,
            brace_location=brace_location,
            k_eff_mean=k_eff_mean,
        )

    def get_history(self, specimen_id: str) -> MassFrequencyHistory:
        """
        Get full history and computed slopes for a specimen.

        Returns:
            MassFrequencyHistory with sessions, slopes, and summary stats
        """
        sessions = self.store.get_sessions(specimen_id)

        if len(sessions) < 2:
            return MassFrequencyHistory(
                specimen_id=specimen_id,
                sessions=sessions,
                mode_slopes=[],
                total_mass_removed_g=0.0,
                session_count=len(sessions),
            )

        # Compute slopes for each mode
        mode_slopes = self._compute_mode_slopes(sessions)

        # Total mass change
        first_mass = sessions[0].mass_g
        last_mass = sessions[-1].mass_g
        total_removed = first_mass - last_mass

        return MassFrequencyHistory(
            specimen_id=specimen_id,
            sessions=sessions,
            mode_slopes=mode_slopes,
            total_mass_removed_g=total_removed,
            session_count=len(sessions),
        )

    def predict_target(
        self,
        specimen_id: str,
        target_frequencies_hz: Dict[int, float],
    ) -> MassFrequencyPrediction:
        """
        Predict mass removal needed to reach target frequencies.

        Args:
            specimen_id: The specimen to predict for
            target_frequencies_hz: Dict of {mode_index: target_hz}

        Returns:
            MassFrequencyPrediction with delta_mass for each target
        """
        sessions = self.store.get_sessions(specimen_id)

        if len(sessions) < 2:
            return MassFrequencyPrediction(
                specimen_id=specimen_id,
                predictions=[],
                sensitivity_map={},
                recommendation="Need at least 2 sessions for prediction.",
            )

        predictions = []
        mode_slopes = self._compute_mode_slopes(sessions)

        # Current frequencies (from latest session)
        current_freqs = sessions[-1].mode_frequencies_hz

        for mode_idx, target_hz in target_frequencies_hz.items():
            if mode_idx >= len(current_freqs):
                continue

            current_hz = current_freqs[mode_idx]

            # Find slope for this mode
            slope_data = next(
                (s for s in mode_slopes if s.mode_index == mode_idx),
                None
            )

            if slope_data is None or abs(slope_data.slope_hz_per_g) < 1e-6:
                continue

            # Linear prediction: delta_f = slope * delta_m
            # delta_m = delta_f / slope
            delta_f = target_hz - current_hz
            delta_m = delta_f / slope_data.slope_hz_per_g

            # Confidence based on R^2 and data points
            if slope_data.r_squared > 0.95 and slope_data.data_points >= 3:
                confidence = "high"
            elif slope_data.r_squared > 0.80 and slope_data.data_points >= 2:
                confidence = "medium"
            else:
                confidence = "low"

            predictions.append(TargetPrediction(
                mode_index=mode_idx,
                current_hz=current_hz,
                target_hz=target_hz,
                delta_mass_g=delta_m,
                confidence=confidence,
                method="polynomial" if slope_data.data_points >= 3 else "linear",
            ))

        # Build sensitivity map by brace location
        sensitivity_map = self._build_sensitivity_map(specimen_id)

        # Generate recommendation
        recommendation = self._generate_recommendation(predictions, mode_slopes)

        return MassFrequencyPrediction(
            specimen_id=specimen_id,
            predictions=predictions,
            sensitivity_map=sensitivity_map,
            recommendation=recommendation,
        )

    def _compute_mode_slopes(
        self,
        sessions: List[SessionRecord],
    ) -> List[ModeSlope]:
        """
        Compute dF/dM for each mode across sessions.

        Uses linear fit for 2 points, polynomial for 3+.
        """
        if len(sessions) < 2:
            return []

        # Extract mass and frequency arrays
        masses = np.array([s.mass_g for s in sessions])
        n_modes = min(len(s.mode_frequencies_hz) for s in sessions)

        slopes = []
        for mode_idx in range(n_modes):
            freqs = np.array([s.mode_frequencies_hz[mode_idx] for s in sessions])

            fit = self._fit_mass_frequency(masses, freqs)

            slopes.append(ModeSlope(
                mode_index=mode_idx,
                frequency_hz=float(freqs[-1]),  # Current frequency
                slope_hz_per_g=fit.slope,
                r_squared=fit.r_squared,
                data_points=len(sessions),
            ))

        return slopes

    def _fit_mass_frequency(
        self,
        masses: np.ndarray,
        frequencies: np.ndarray,
    ) -> FitResult:
        """
        Fit mass-frequency relationship.

        2 points: linear fit
        3+ points: quadratic fit, return linear slope at current point
        """
        n = len(masses)

        if n < 2:
            return FitResult(
                slope=0.0,
                intercept=frequencies[0] if len(frequencies) > 0 else 0.0,
                r_squared=0.0,
                coefficients=[0.0],
                method="insufficient_data",
            )

        if n == 2:
            # Simple linear fit
            dm = masses[1] - masses[0]
            df = frequencies[1] - frequencies[0]

            if abs(dm) < 1e-9:
                slope = 0.0
            else:
                slope = df / dm

            return FitResult(
                slope=slope,
                intercept=frequencies[0] - slope * masses[0],
                r_squared=1.0,  # Perfect fit with 2 points
                coefficients=[slope],
                method="linear",
            )

        # 3+ points: polynomial fit (degree 2)
        # f(m) = c0 + c1*m + c2*m^2
        # dF/dM at current mass = c1 + 2*c2*m_current
        coeffs = np.polyfit(masses, frequencies, 2)
        poly = np.poly1d(coeffs)

        # R-squared
        f_pred = poly(masses)
        ss_res = np.sum((frequencies - f_pred) ** 2)
        ss_tot = np.sum((frequencies - np.mean(frequencies)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        # Slope at current mass (derivative of polynomial)
        m_current = masses[-1]
        # d/dm(c0 + c1*m + c2*m^2) = c1 + 2*c2*m
        # Note: np.polyfit returns [c2, c1, c0]
        c2, c1, c0 = coeffs
        slope = c1 + 2 * c2 * m_current

        return FitResult(
            slope=slope,
            intercept=c0,
            r_squared=r_squared,
            coefficients=list(coeffs),
            method="polynomial",
        )

    def _build_sensitivity_map(
        self,
        specimen_id: str,
    ) -> Dict[str, List[ModeSlope]]:
        """
        Build map of brace_location -> mode slopes.

        Shows which brace affects which modes.
        """
        sessions = self.store.get_sessions(specimen_id)

        # Group sessions by brace location
        by_location: Dict[str, List[SessionRecord]] = {}
        for session in sessions:
            loc = session.brace_location or "unspecified"
            if loc not in by_location:
                by_location[loc] = []
            by_location[loc].append(session)

        # Compute slopes per location
        sensitivity_map = {}
        for location, loc_sessions in by_location.items():
            if len(loc_sessions) >= 2:
                slopes = self._compute_mode_slopes(loc_sessions)
                sensitivity_map[location] = slopes

        return sensitivity_map

    def _generate_recommendation(
        self,
        predictions: List[TargetPrediction],
        mode_slopes: List[ModeSlope],
    ) -> str:
        """Generate human-readable recommendation."""
        if not predictions:
            return "No predictions available. Record more sessions."

        # Check for conflicting requirements
        remove_amounts = [p.delta_mass_g for p in predictions if p.delta_mass_g < 0]
        add_amounts = [p.delta_mass_g for p in predictions if p.delta_mass_g > 0]

        if remove_amounts and add_amounts:
            return (
                "Conflicting targets: some modes need mass removal, "
                "others need addition. Prioritize the most important mode."
            )

        if remove_amounts:
            avg_remove = abs(np.mean(remove_amounts))
            high_conf = [p for p in predictions if p.confidence == "high"]
            if high_conf:
                best = min(high_conf, key=lambda p: abs(p.delta_mass_g))
                return (
                    f"Remove approximately {abs(best.delta_mass_g):.1f}g to reach "
                    f"mode {best.mode_index + 1} target of {best.target_hz:.1f} Hz. "
                    f"Prediction confidence: {best.confidence}."
                )
            return f"Average removal needed: {avg_remove:.1f}g. Confidence: low."

        return "Targets require adding mass — unusual for carving workflow."


# =============================================================================
# K_eff VALIDATION LINK
# =============================================================================


def validate_k_eff_correlation(
    sessions: List[SessionRecord],
) -> Optional[Dict]:
    """
    Check correlation between K_eff and modal frequencies.

    This validates that the stiffness map correlates with
    measured acoustic behavior.

    Returns:
        Dict with correlation coefficient per mode, or None if insufficient data
    """
    # Filter sessions with K_eff data
    with_k_eff = [s for s in sessions if s.k_eff_mean is not None]

    if len(with_k_eff) < 3:
        return None

    k_effs = np.array([s.k_eff_mean for s in with_k_eff])
    n_modes = min(len(s.mode_frequencies_hz) for s in with_k_eff)

    correlations = {}
    for mode_idx in range(n_modes):
        freqs = np.array([s.mode_frequencies_hz[mode_idx] for s in with_k_eff])

        # Pearson correlation
        if np.std(k_effs) > 0 and np.std(freqs) > 0:
            corr = np.corrcoef(k_effs, freqs)[0, 1]
            correlations[f"mode_{mode_idx + 1}"] = float(corr)

    return {
        "correlations": correlations,
        "n_sessions": len(with_k_eff),
        "interpretation": _interpret_k_eff_correlation(correlations),
    }


def _interpret_k_eff_correlation(correlations: Dict[str, float]) -> str:
    """Interpret K_eff correlation results."""
    if not correlations:
        return "Insufficient data for correlation analysis."

    avg_corr = np.mean(list(correlations.values()))

    if avg_corr > 0.8:
        return (
            "Strong positive correlation between K_eff and frequency. "
            "Stiffness map is a good predictor of modal behavior."
        )
    elif avg_corr > 0.5:
        return (
            "Moderate correlation. Stiffness map captures some acoustic "
            "behavior but other factors (mass distribution, boundary "
            "conditions) are significant."
        )
    elif avg_corr > 0:
        return "Weak positive correlation. Stiffness map is a rough guide only."
    else:
        return (
            "Negative or no correlation. Check measurement consistency "
            "or consider that mass removal dominates over stiffness."
        )
