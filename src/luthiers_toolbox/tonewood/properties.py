"""
Wood properties and acoustic characteristics.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class WoodProperties:
    """Physical properties of wood."""

    density: float  # kg/m³
    hardness: float  # Janka hardness (lbf)
    stiffness: float  # Modulus of elasticity (GPa)
    workability: str  # 'excellent', 'good', 'moderate', 'difficult'

    def get_weight_per_board_foot(self) -> float:
        """
        Calculate approximate weight per board foot.
        
        Returns:
            Weight in pounds
        """
        # Board foot = 144 cubic inches = 0.00236 m³
        cubic_meters_per_bf = 0.00236
        kg_per_bf = self.density * cubic_meters_per_bf
        lbs_per_bf = kg_per_bf * 2.20462
        return lbs_per_bf

    def classify_density(self) -> str:
        """Classify density as low, medium, or high."""
        if self.density < 500:
            return "low"
        elif self.density < 700:
            return "medium"
        else:
            return "high"

    def classify_hardness(self) -> str:
        """Classify hardness as soft, medium, or hard."""
        if self.hardness < 800:
            return "soft"
        elif self.hardness < 1500:
            return "medium"
        else:
            return "hard"


@dataclass
class AcousticProperties:
    """Acoustic properties of wood."""

    frequency_response: str  # 'bright', 'warm', 'balanced', 'rich'
    resonance: str  # 'low', 'medium', 'high', 'very high'
    damping: str  # 'low', 'medium', 'high'
    tonal_character: str  # Descriptive text

    def get_resonance_score(self) -> float:
        """
        Get numeric resonance score.
        
        Returns:
            Score from 0.0 (low) to 1.0 (very high)
        """
        scores = {
            "low": 0.25,
            "medium": 0.5,
            "high": 0.75,
            "very high": 1.0,
        }
        return scores.get(self.resonance.lower(), 0.5)

    def get_damping_score(self) -> float:
        """
        Get numeric damping score.
        
        Returns:
            Score from 0.0 (low) to 1.0 (high)
        """
        scores = {
            "low": 0.25,
            "medium": 0.5,
            "high": 0.75,
        }
        return scores.get(self.damping.lower(), 0.5)

    def is_suitable_for_acoustic_top(self) -> bool:
        """
        Check if suitable for acoustic guitar top.
        
        Returns:
            True if suitable
        """
        # Good acoustic tops need high resonance and low damping
        return (
            self.get_resonance_score() >= 0.75 and self.get_damping_score() <= 0.5
        )

    def is_suitable_for_electric_body(self) -> bool:
        """
        Check if suitable for electric guitar body.
        
        Returns:
            True if suitable
        """
        # Electric bodies are less critical, but balanced properties are good
        return 0.25 <= self.get_resonance_score() <= 0.75


@dataclass
class TonalProfile:
    """Complete tonal profile for a wood combination."""

    body_wood: str
    neck_wood: str
    fretboard_wood: str
    overall_character: str
    bass_response: str
    midrange_response: str
    treble_response: str
    sustain: str

    def get_summary(self) -> str:
        """Get a text summary of the tonal profile."""
        return f"""
Tonal Profile:
  Body: {self.body_wood}
  Neck: {self.neck_wood}
  Fretboard: {self.fretboard_wood}

Character: {self.overall_character}
  Bass: {self.bass_response}
  Mids: {self.midrange_response}
  Treble: {self.treble_response}
  Sustain: {self.sustain}
        """.strip()
