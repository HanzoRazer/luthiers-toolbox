"""
Spectrum Service — Transform raw FFT data into visualization-ready format.

This is INTERPRETATION, not measurement. We take what tap_tone_pi measured
and prepare it for display with annotations, peak labels, and overlays.
"""
from typing import List, Optional
from datetime import datetime

from .schemas import (
    ViewerPackV1,
    SpectrumDisplayData,
    PeakData,
)


class SpectrumService:
    """
    Transforms viewer_pack spectrum data into UI-ready format.

    Responsibilities:
    - Format data for chart.js / D3 rendering
    - Add peak annotations with musical note labels
    - Overlay coherence data for quality indication
    - Compare against reference spectra
    """

    # Musical note frequencies (A4 = 440 Hz)
    NOTE_FREQUENCIES = {
        "E2": 82.41, "A2": 110.0, "D3": 146.83, "G3": 196.0,
        "B3": 246.94, "E4": 329.63, "A4": 440.0, "E5": 659.25,
    }

    def prepare_display_data(
        self,
        pack: ViewerPackV1,
        frequency_range: tuple[float, float] = (20.0, 2000.0),
        include_coherence: bool = True,
    ) -> SpectrumDisplayData:
        """
        Prepare spectrum data for frontend visualization.

        Args:
            pack: The viewer pack from tap_tone_pi
            frequency_range: (min_hz, max_hz) to display
            include_coherence: Whether to include coherence overlay

        Returns:
            SpectrumDisplayData ready for chart rendering
        """
        min_hz, max_hz = frequency_range

        # Filter transfer function points to range
        tf_in_range = [
            p for p in pack.transfer_function
            if min_hz <= p.frequency_hz <= max_hz
        ]

        frequencies = [p.frequency_hz for p in tf_in_range]
        magnitudes = [p.magnitude_db for p in tf_in_range]
        coherence = [p.coherence for p in tf_in_range] if include_coherence else None

        # Build peak markers with labels
        peak_markers = self._build_peak_markers(pack.peaks, frequency_range)

        return SpectrumDisplayData(
            frequencies_hz=frequencies,
            magnitudes_db=magnitudes,
            peak_markers=peak_markers,
            coherence_overlay=coherence,
        )

    def _build_peak_markers(
        self,
        peaks: List[PeakData],
        frequency_range: tuple[float, float],
    ) -> List[dict]:
        """Build annotated peak markers for display."""
        min_hz, max_hz = frequency_range
        markers = []

        for peak in peaks:
            if not (min_hz <= peak.frequency_hz <= max_hz):
                continue

            label = self._frequency_to_label(peak.frequency_hz)

            markers.append({
                "freq": peak.frequency_hz,
                "mag": peak.amplitude_db,
                "label": label,
                "damping": peak.damping_ratio,
            })

        return markers

    def _frequency_to_label(self, freq_hz: float) -> str:
        """
        Convert frequency to musical note label if close to a note.

        This is INTERPRETATION — we're adding meaning to raw Hz values.
        """
        tolerance_cents = 50  # Half a semitone

        for note, note_freq in self.NOTE_FREQUENCIES.items():
            cents_diff = 1200 * abs(
                self._log2_safe(freq_hz / note_freq)
            )
            if cents_diff < tolerance_cents:
                return f"{note} ({freq_hz:.1f} Hz)"

        return f"{freq_hz:.1f} Hz"

    @staticmethod
    def _log2_safe(x: float) -> float:
        """Safe log2 that handles edge cases."""
        import math
        if x <= 0:
            return 0.0
        return math.log2(x)

    def identify_primary_modes(
        self,
        pack: ViewerPackV1,
        count: int = 5,
    ) -> List[dict]:
        """
        Identify the N strongest modes from the spectrum.

        This is INTERPRETATION — we're deciding what matters.
        """
        # Sort peaks by amplitude
        sorted_peaks = sorted(
            pack.peaks,
            key=lambda p: p.amplitude_db,
            reverse=True,
        )

        primary = []
        for i, peak in enumerate(sorted_peaks[:count]):
            primary.append({
                "rank": i + 1,
                "frequency_hz": peak.frequency_hz,
                "amplitude_db": peak.amplitude_db,
                "label": self._frequency_to_label(peak.frequency_hz),
                "damping_ratio": peak.damping_ratio,
                "interpretation": self._interpret_mode(peak, i),
            })

        return primary

    def _interpret_mode(self, peak: PeakData, rank: int) -> str:
        """
        Provide human-readable interpretation of a mode.

        This is the core of what we do: turn numbers into meaning.
        """
        freq = peak.frequency_hz

        # Guitar body mode interpretations
        if 80 <= freq <= 120:
            return "Likely air resonance (Helmholtz mode). Affects bass response."
        elif 150 <= freq <= 250:
            return "Primary top mode. Critical for fundamental tone."
        elif 250 <= freq <= 400:
            return "Secondary top mode. Affects midrange clarity."
        elif 400 <= freq <= 600:
            return "Cross-grain mode. Influences sustain and brightness."
        elif freq > 600:
            return "Higher partial. Contributes to 'shimmer' and overtone richness."
        else:
            return "Low-frequency mode. May indicate structural resonance."
