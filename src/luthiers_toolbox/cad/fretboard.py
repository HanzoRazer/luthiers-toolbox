"""
Fretboard design and fret slot calculation tools.
"""

from typing import List, Dict, Tuple
from .geometry import Point


class Fretboard:
    """
    Parametric fretboard designer.
    
    Calculates fret positions, slot widths, and inlay positions.
    """

    def __init__(
        self,
        scale_length: float = 25.5,  # inches
        frets: int = 22,
        nut_width: float = 1.65,  # inches
        end_width: float = 2.25,  # inches
        thickness: float = 0.25,  # inches
        radius: float = 9.5,  # inches (fretboard radius)
        fret_wire_width: float = 0.02,  # inches
    ):
        """
        Initialize a fretboard design.
        
        Args:
            scale_length: Scale length in inches
            frets: Number of frets
            nut_width: Width at nut
            end_width: Width at last fret
            thickness: Fretboard thickness
            radius: Fretboard radius
            fret_wire_width: Width of fret slots
        """
        self.scale_length = scale_length
        self.frets = frets
        self.nut_width = nut_width
        self.end_width = end_width
        self.thickness = thickness
        self.radius = radius
        self.fret_wire_width = fret_wire_width

    def calculate_fret_positions(self) -> List[float]:
        """
        Calculate all fret positions from the nut.
        
        Returns:
            List of distances from nut in inches
        """
        positions = []
        for i in range(1, self.frets + 1):
            # Using the precise constant 17.817 for equal temperament
            position = self.scale_length - (self.scale_length / (2 ** (i / 12)))
            positions.append(position)
        return positions

    def calculate_fret_spacing(self) -> List[float]:
        """
        Calculate spacing between consecutive frets.
        
        Returns:
            List of distances between frets in inches
        """
        positions = self.calculate_fret_positions()
        spacings = []
        prev_pos = 0
        for pos in positions:
            spacings.append(pos - prev_pos)
            prev_pos = pos
        return spacings

    def get_width_at_fret(self, fret_number: int) -> float:
        """
        Calculate fretboard width at a specific fret.
        
        Args:
            fret_number: Fret number (0 = nut)
            
        Returns:
            Width in inches
        """
        if fret_number == 0:
            return self.nut_width

        # Linear taper from nut to last fret
        ratio = fret_number / self.frets
        return self.nut_width + (self.end_width - self.nut_width) * ratio

    def get_inlay_positions(self, pattern: str = "standard") -> List[int]:
        """
        Get fret numbers for position markers/inlays.
        
        Args:
            pattern: Inlay pattern ('standard', 'block', 'custom')
            
        Returns:
            List of fret numbers with inlays
        """
        if pattern == "standard":
            # Standard dot inlays
            return [3, 5, 7, 9, 12, 15, 17, 19, 21]
        elif pattern == "block":
            # Block inlays (common on higher-end guitars)
            return [3, 5, 7, 9, 12, 15, 17, 19, 21]
        else:
            # Custom pattern - can be extended
            return [3, 5, 7, 9, 12, 15, 17, 19, 21]

    def get_slot_dimensions(self, fret_number: int) -> Dict[str, float]:
        """
        Get dimensions for a specific fret slot.
        
        Args:
            fret_number: Fret number (1-based)
            
        Returns:
            Dict with slot position, width, and depth
        """
        positions = self.calculate_fret_positions()
        if fret_number < 1 or fret_number > len(positions):
            raise ValueError(f"Fret number must be between 1 and {self.frets}")

        return {
            "position": positions[fret_number - 1],
            "width": self.get_width_at_fret(fret_number),
            "slot_width": self.fret_wire_width,
            "slot_depth": self.thickness * 0.6,  # Typically 60% of thickness
        }

    def get_dimensions(self) -> Dict[str, float]:
        """Get fretboard dimensions."""
        positions = self.calculate_fret_positions()
        return {
            "scale_length": self.scale_length,
            "frets": self.frets,
            "nut_width": self.nut_width,
            "end_width": self.end_width,
            "thickness": self.thickness,
            "radius": self.radius,
            "total_length": positions[-1] + 1.0 if positions else self.scale_length,
        }

    def export_fret_template(self) -> List[Tuple[float, float]]:
        """
        Export fret positions and widths for CNC machining.
        
        Returns:
            List of (position, width) tuples
        """
        positions = self.calculate_fret_positions()
        return [(pos, self.get_width_at_fret(i + 1)) for i, pos in enumerate(positions)]

    def __repr__(self) -> str:
        return (
            f"Fretboard(scale={self.scale_length}\", "
            f"frets={self.frets}, radius={self.radius}\")"
        )
