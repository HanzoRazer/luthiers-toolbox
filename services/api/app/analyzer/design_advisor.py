"""
Design Advisor Service — Turn measurements into actionable recommendations.

This is the core INTERPRETATION layer. tap_tone_pi tells us WHAT IS.
We tell the luthier WHAT TO DO.
"""
from typing import List, Optional
from datetime import datetime, timezone

from .schemas import (
    ViewerPackV1,
    InterpretationResult,
    DesignRecommendation,
    RecommendationSeverity,
)
from .spectrum_service import SpectrumService


class DesignAdvisorService:
    """
    Analyzes viewer_pack data and generates design recommendations.

    This is where measurement becomes manufacturing guidance.

    Responsibilities:
    - Wolf tone risk assessment and mitigation
    - Bracing pattern suggestions
    - Thickness recommendations
    - Comparison to reference instruments
    """

    # Reference instruments for comparison
    REFERENCE_LIBRARY = {
        "martin_d28_1937": {
            "name": "Martin D-28 (1937)",
            "primary_modes": [95, 180, 280, 380],
            "wsi_typical": 0.08,
            "character": "warm, balanced",
        },
        "torres_1856": {
            "name": "Torres FE-17 (1856)",
            "primary_modes": [88, 165, 250, 340],
            "wsi_typical": 0.06,
            "character": "warm, singing",
        },
        "hauser_1937": {
            "name": "Hauser I (1937)",
            "primary_modes": [92, 175, 265, 360],
            "wsi_typical": 0.07,
            "character": "clear, projecting",
        },
    }

    def __init__(self):
        self.spectrum_service = SpectrumService()

    def analyze(
        self,
        pack: ViewerPackV1,
        reference_id: Optional[str] = None,
    ) -> InterpretationResult:
        """
        Perform full analysis of viewer_pack and generate recommendations.

        Args:
            pack: Measurement data from tap_tone_pi
            reference_id: Optional reference instrument to compare against

        Returns:
            InterpretationResult with recommendations
        """
        recommendations: List[DesignRecommendation] = []

        # Analyze wolf tone risk
        wolf_assessment, wolf_recs = self._assess_wolf_risk(pack)
        recommendations.extend(wolf_recs)

        # Analyze modal distribution
        modal_recs = self._analyze_modal_distribution(pack)
        recommendations.extend(modal_recs)

        # Analyze damping characteristics
        damping_recs = self._analyze_damping(pack)
        recommendations.extend(damping_recs)

        # Compare to reference if requested
        reference_comparison = None
        if reference_id and reference_id in self.REFERENCE_LIBRARY:
            reference_comparison, ref_recs = self._compare_to_reference(
                pack, reference_id
            )
            recommendations.extend(ref_recs)

        # Identify primary modes
        primary_modes = self.spectrum_service.identify_primary_modes(pack)

        # Determine overall tonal character
        tonal_character = self._assess_tonal_character(pack, primary_modes)

        return InterpretationResult(
            specimen_id=pack.specimen_id,
            interpreted_at=datetime.now(timezone.utc).isoformat(),
            primary_modes=primary_modes,
            wolf_assessment=wolf_assessment,
            tonal_character=tonal_character,
            recommendations=recommendations,
            reference_comparison=reference_comparison,
        )

    def _assess_wolf_risk(
        self,
        pack: ViewerPackV1,
    ) -> tuple[str, List[DesignRecommendation]]:
        """
        Assess wolf tone risk and provide mitigation recommendations.

        Wolf tones occur when a played note's frequency matches a body
        resonance with high Q (low damping), causing energy to oscillate
        between string and body rather than radiating as sound.
        """
        recommendations = []

        if not pack.wolf_metrics:
            return "No wolf metrics available", []

        wsi = pack.wolf_metrics.wsi
        wolf_freq = pack.wolf_metrics.wsi_frequency_hz

        # Interpret WSI
        if wsi < 0.05:
            assessment = f"Excellent. WSI {wsi:.3f} indicates minimal wolf risk."

        elif wsi < 0.10:
            assessment = f"Good. WSI {wsi:.3f} is within acceptable range."
            recommendations.append(DesignRecommendation(
                severity=RecommendationSeverity.INFO,
                category="wolf_tone",
                message=f"Minor wolf susceptibility at {wolf_freq:.1f} Hz",
                details="Monitor during stringing. Usually not problematic.",
            ))

        elif wsi < 0.15:
            assessment = f"Moderate concern. WSI {wsi:.3f} may cause audible wolf."
            recommendations.append(DesignRecommendation(
                severity=RecommendationSeverity.SUGGESTION,
                category="wolf_tone",
                message=f"Consider wolf mitigation at {wolf_freq:.1f} Hz",
                details=(
                    "Options: (1) Asymmetric bracing to shift mode frequency, "
                    "(2) Add damping material near antinode, "
                    "(3) Adjust soundhole position/size."
                ),
            ))

        else:
            assessment = f"High risk. WSI {wsi:.3f} will likely cause problematic wolf."
            recommendations.append(DesignRecommendation(
                severity=RecommendationSeverity.WARNING,
                category="wolf_tone",
                message=f"Strong wolf predicted at {wolf_freq:.1f} Hz",
                details=(
                    f"This corresponds to approximately {self._freq_to_note(wolf_freq)}. "
                    "Recommend: (1) Redesign bracing pattern, "
                    "(2) Consider Torres-style asymmetric layout, "
                    "(3) May need soundboard replacement if already glued."
                ),
                reference_instrument="Torres FE-17 (asymmetric bracing)",
            ))

        return assessment, recommendations

    def _analyze_modal_distribution(
        self,
        pack: ViewerPackV1,
    ) -> List[DesignRecommendation]:
        """
        Analyze spacing of primary modes and recommend adjustments.
        """
        recommendations = []

        if len(pack.peaks) < 3:
            return recommendations

        # Sort peaks by frequency
        sorted_peaks = sorted(pack.peaks, key=lambda p: p.frequency_hz)[:5]

        # Check spacing between first few modes
        if len(sorted_peaks) >= 2:
            spacing_1_2 = sorted_peaks[1].frequency_hz - sorted_peaks[0].frequency_hz

            if spacing_1_2 < 50:
                recommendations.append(DesignRecommendation(
                    severity=RecommendationSeverity.SUGGESTION,
                    category="modal_distribution",
                    message="First two modes are closely spaced",
                    details=(
                        f"Modes at {sorted_peaks[0].frequency_hz:.1f} Hz and "
                        f"{sorted_peaks[1].frequency_hz:.1f} Hz are only {spacing_1_2:.1f} Hz apart. "
                        "This can cause 'muddy' bass. Consider stiffening the top slightly."
                    ),
                ))
            elif spacing_1_2 > 120:
                recommendations.append(DesignRecommendation(
                    severity=RecommendationSeverity.INFO,
                    category="modal_distribution",
                    message="Wide spacing between first modes",
                    details=(
                        f"Gap of {spacing_1_2:.1f} Hz may result in 'hollow' tone. "
                        "If undesired, consider reducing top stiffness."
                    ),
                ))

        return recommendations

    def _analyze_damping(
        self,
        pack: ViewerPackV1,
    ) -> List[DesignRecommendation]:
        """
        Analyze damping ratios and recommend finish/bracing adjustments.
        """
        recommendations = []

        # Check damping of primary modes
        for peak in pack.peaks[:3]:  # First three modes
            if peak.damping_ratio is None:
                continue

            if peak.damping_ratio > 0.06:
                recommendations.append(DesignRecommendation(
                    severity=RecommendationSeverity.SUGGESTION,
                    category="damping",
                    message=f"High damping at {peak.frequency_hz:.1f} Hz",
                    details=(
                        f"Damping ratio {peak.damping_ratio:.4f} will limit sustain. "
                        "Check for: (1) Thick finish, (2) Loose braces, "
                        "(3) Over-constrained edges."
                    ),
                ))

        return recommendations

    def _compare_to_reference(
        self,
        pack: ViewerPackV1,
        reference_id: str,
    ) -> tuple[dict, List[DesignRecommendation]]:
        """
        Compare measured modes to a reference instrument.
        """
        ref = self.REFERENCE_LIBRARY[reference_id]
        recommendations = []

        # Get measured primary mode frequencies
        measured_modes = sorted(
            [p.frequency_hz for p in pack.peaks[:4]]
        )

        # Compare to reference
        comparison = {
            "reference_name": ref["name"],
            "reference_character": ref["character"],
            "mode_comparison": [],
        }

        for i, ref_freq in enumerate(ref["primary_modes"]):
            if i < len(measured_modes):
                measured = measured_modes[i]
                diff = measured - ref_freq
                diff_percent = (diff / ref_freq) * 100

                comparison["mode_comparison"].append({
                    "mode_index": i + 1,
                    "reference_hz": ref_freq,
                    "measured_hz": measured,
                    "difference_hz": diff,
                    "difference_percent": diff_percent,
                })

                if abs(diff_percent) > 15:
                    recommendations.append(DesignRecommendation(
                        severity=RecommendationSeverity.INFO,
                        category="reference_comparison",
                        message=f"Mode {i+1} differs from {ref['name']}",
                        details=(
                            f"Measured: {measured:.1f} Hz, Reference: {ref_freq:.1f} Hz "
                            f"({diff_percent:+.1f}%). "
                            "This is not necessarily bad—just different character."
                        ),
                        reference_instrument=ref["name"],
                    ))

        # Compare WSI
        if pack.wolf_metrics:
            wsi_diff = pack.wolf_metrics.wsi - ref["wsi_typical"]
            comparison["wsi_comparison"] = {
                "reference_wsi": ref["wsi_typical"],
                "measured_wsi": pack.wolf_metrics.wsi,
                "difference": wsi_diff,
            }

        return comparison, recommendations

    def _assess_tonal_character(
        self,
        pack: ViewerPackV1,
        primary_modes: List[dict],
    ) -> str:
        """
        Describe the overall tonal character based on modal analysis.

        This is subjective interpretation — the art of lutherie.
        """
        if not primary_modes:
            return "Insufficient data for character assessment"

        # Get first mode frequency
        first_mode = primary_modes[0]["frequency_hz"] if primary_modes else 0

        # Simple heuristics (real implementation would be more sophisticated)
        characteristics = []

        if first_mode < 90:
            characteristics.append("deep bass")
        elif first_mode < 100:
            characteristics.append("warm")
        else:
            characteristics.append("bright")

        # Check for wolf susceptibility
        if pack.wolf_metrics and pack.wolf_metrics.wsi > 0.12:
            characteristics.append("some wolf risk")

        # Check damping
        avg_damping = sum(
            p.damping_ratio or 0 for p in pack.peaks[:3]
        ) / max(len(pack.peaks[:3]), 1)

        if avg_damping < 0.02:
            characteristics.append("sustaining")
        elif avg_damping > 0.05:
            characteristics.append("controlled decay")

        return ", ".join(characteristics).capitalize()

    @staticmethod
    def _freq_to_note(freq_hz: float) -> str:
        """Convert frequency to nearest note name."""
        import math

        if freq_hz <= 0:
            return "N/A"

        # A4 = 440 Hz
        semitones_from_a4 = 12 * math.log2(freq_hz / 440.0)
        note_index = round(semitones_from_a4) % 12
        octave = 4 + (round(semitones_from_a4) + 9) // 12

        notes = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]
        return f"{notes[note_index]}{octave}"
