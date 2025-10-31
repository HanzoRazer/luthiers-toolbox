"""
Guitar neck design tools.
"""

from typing import Dict
from .geometry import Point


class GuitarNeck:
    """
    Parametric guitar neck designer.
    
    Handles neck dimensions, profile, and headstock design.
    """

    NECK_PROFILES = ["C", "D", "V", "U", "modern_C", "vintage_V"]

    def __init__(
        self,
        scale_length: float = 25.5,  # inches
        frets: int = 22,
        nut_width: float = 1.65,  # inches
        neck_width_at_12: float = 2.25,  # inches
        thickness_at_1st: float = 0.82,  # inches
        thickness_at_12th: float = 0.95,  # inches
        profile: str = "C",
    ):
        """
        Initialize a guitar neck design.
        
        Args:
            scale_length: Scale length in inches
            frets: Number of frets
            nut_width: Width at nut
            neck_width_at_12: Width at 12th fret
            thickness_at_1st: Thickness at 1st fret
            thickness_at_12th: Thickness at 12th fret
            profile: Neck profile shape
        """
        if profile not in self.NECK_PROFILES:
            raise ValueError(f"Profile must be one of {self.NECK_PROFILES}")

        self.scale_length = scale_length
        self.frets = frets
        self.nut_width = nut_width
        self.neck_width_at_12 = neck_width_at_12
        self.thickness_at_1st = thickness_at_1st
        self.thickness_at_12th = thickness_at_12th
        self.profile = profile

    def get_fret_position(self, fret_number: int) -> float:
        """
        Calculate the distance from nut to specified fret.
        
        Args:
            fret_number: Fret number (1-based)
            
        Returns:
            Distance from nut in inches
        """
        if fret_number < 1 or fret_number > self.frets:
            raise ValueError(f"Fret number must be between 1 and {self.frets}")

        # Using equal temperament formula: 2^(n/12) for semitone spacing
        # Mathematically equivalent to dividing by 17.817 (Rule of 18)
        return self.scale_length - (self.scale_length / (2 ** (fret_number / 12)))

    def get_neck_width_at_fret(self, fret_number: int) -> float:
        """
        Calculate neck width at a specific fret.
        
        Args:
            fret_number: Fret number (0 = nut)
            
        Returns:
            Width in inches
        """
        if fret_number == 0:
            return self.nut_width

        # Linear interpolation between nut and 12th fret
        if fret_number <= 12:
            ratio = fret_number / 12
            return self.nut_width + (self.neck_width_at_12 - self.nut_width) * ratio
        else:
            # Continue linear progression beyond 12th fret
            ratio = (fret_number - 12) / 12
            return self.neck_width_at_12 + (self.neck_width_at_12 - self.nut_width) * ratio * 0.5

    def get_dimensions(self) -> Dict[str, float]:
        """Get neck dimensions."""
        return {
            "scale_length": self.scale_length,
            "frets": self.frets,
            "nut_width": self.nut_width,
            "neck_width_at_12": self.neck_width_at_12,
            "thickness_at_1st": self.thickness_at_1st,
            "thickness_at_12th": self.thickness_at_12th,
            "total_length": self.get_fret_position(self.frets) + 2.0,  # Add space beyond last fret
        }

    def __repr__(self) -> str:
        return (
            f"GuitarNeck(scale={self.scale_length}\", "
            f"frets={self.frets}, profile='{self.profile}')"
        )
