"""
Guitar body design tools.
"""

from typing import Dict, List, Optional
from .geometry import Point, Line, Arc


class GuitarBody:
    """
    Parametric guitar body designer.
    
    Supports common body shapes (Stratocaster, Telecaster, Les Paul, etc.)
    with customizable dimensions and contours.
    """

    BODY_SHAPES = ["stratocaster", "telecaster", "les_paul", "sg", "custom"]

    def __init__(
        self,
        shape: str = "stratocaster",
        scale_length: float = 25.5,  # inches
        body_length: float = 18.0,  # inches
        body_width: float = 13.0,  # inches
        thickness: float = 1.75,  # inches
    ):
        """
        Initialize a guitar body design.
        
        Args:
            shape: Body shape template
            scale_length: Scale length in inches
            body_length: Overall body length
            body_width: Maximum body width
            thickness: Body thickness
        """
        if shape not in self.BODY_SHAPES:
            raise ValueError(f"Shape must be one of {self.BODY_SHAPES}")

        self.shape = shape
        self.scale_length = scale_length
        self.body_length = body_length
        self.body_width = body_width
        self.thickness = thickness
        self.outline_points: List[Point] = []
        self._generate_outline()

    def _generate_outline(self) -> None:
        """Generate the body outline based on shape parameters."""
        if self.shape == "stratocaster":
            self._generate_strat_outline()
        elif self.shape == "telecaster":
            self._generate_tele_outline()
        elif self.shape == "les_paul":
            self._generate_lp_outline()
        else:
            self._generate_basic_outline()

    def _generate_strat_outline(self) -> None:
        """Generate Stratocaster-style body outline."""
        # Simplified Strat outline with key points
        self.outline_points = [
            Point(0, 0),
            Point(self.body_length * 0.3, self.body_width * 0.5),
            Point(self.body_length * 0.5, self.body_width * 0.6),
            Point(self.body_length * 0.7, self.body_width * 0.5),
            Point(self.body_length, self.body_width * 0.3),
            Point(self.body_length, -self.body_width * 0.3),
            Point(self.body_length * 0.7, -self.body_width * 0.5),
            Point(self.body_length * 0.3, -self.body_width * 0.4),
        ]

    def _generate_tele_outline(self) -> None:
        """Generate Telecaster-style body outline."""
        # Simplified Tele outline - more angular
        self.outline_points = [
            Point(0, 0),
            Point(self.body_length * 0.3, self.body_width * 0.45),
            Point(self.body_length * 0.6, self.body_width * 0.5),
            Point(self.body_length, self.body_width * 0.35),
            Point(self.body_length, -self.body_width * 0.35),
            Point(self.body_length * 0.6, -self.body_width * 0.5),
            Point(self.body_length * 0.3, -self.body_width * 0.35),
        ]

    def _generate_lp_outline(self) -> None:
        """Generate Les Paul-style body outline."""
        # Simplified LP outline - more symmetric
        self.outline_points = [
            Point(0, 0),
            Point(self.body_length * 0.25, self.body_width * 0.5),
            Point(self.body_length * 0.75, self.body_width * 0.5),
            Point(self.body_length, self.body_width * 0.3),
            Point(self.body_length, -self.body_width * 0.3),
            Point(self.body_length * 0.75, -self.body_width * 0.5),
            Point(self.body_length * 0.25, -self.body_width * 0.5),
        ]

    def _generate_basic_outline(self) -> None:
        """Generate a basic rectangular outline."""
        self.outline_points = [
            Point(0, self.body_width / 2),
            Point(self.body_length, self.body_width / 2),
            Point(self.body_length, -self.body_width / 2),
            Point(0, -self.body_width / 2),
        ]

    def get_dimensions(self) -> Dict[str, float]:
        """Get body dimensions."""
        return {
            "length": self.body_length,
            "width": self.body_width,
            "thickness": self.thickness,
            "scale_length": self.scale_length,
        }

    def get_outline(self) -> List[Point]:
        """Get the body outline points."""
        return self.outline_points

    def export_dxf(self, filename: str) -> None:
        """
        Export body design to DXF format.
        
        Args:
            filename: Output DXF file path
        """
        try:
            import ezdxf
        except ImportError:
            raise ImportError("ezdxf package required for DXF export")

        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        # Draw body outline
        for i in range(len(self.outline_points)):
            start = self.outline_points[i]
            end = self.outline_points[(i + 1) % len(self.outline_points)]
            msp.add_line((start.x, start.y), (end.x, end.y))

        doc.saveas(filename)

    def __repr__(self) -> str:
        return (
            f"GuitarBody(shape='{self.shape}', "
            f"length={self.body_length}\", width={self.body_width}\")"
        )
