# app/cam/carving/graduation_map.py

"""
Graduation Map Loading and Interpolation (BEN-GAP-08)

Handles thickness graduation maps for archtop carving.
Supports both grid-based thickness data and parametric archtop profiles.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple, Union

from .config import GraduationMapConfig, SurfaceType, AsymmetricCarveProfile


@dataclass
class GraduationPoint:
    """Single point in graduation map."""
    x_mm: float
    y_mm: float
    thickness_mm: float

    def to_dict(self) -> dict:
        return {
            "x_mm": round(self.x_mm, 3),
            "y_mm": round(self.y_mm, 3),
            "thickness_mm": round(self.thickness_mm, 3),
        }


@dataclass
class GraduationMap:
    """
    Graduation thickness map for 3D carving.

    Stores thickness values across a 2D grid. Surface Z height is computed as:
        Z = reference_plane_z - (stock_thickness - thickness_at_point)

    For archtop carving, thicker areas become higher (dome apex).
    """
    config: GraduationMapConfig
    thickness_grid: List[List[float]] = field(default_factory=list)
    outline_points: List[Tuple[float, float]] = field(default_factory=list)

    # Cached interpolation grid
    _x_coords: List[float] = field(default_factory=list, repr=False)
    _y_coords: List[float] = field(default_factory=list, repr=False)

    def __post_init__(self):
        """Initialize coordinate grids."""
        if not self._x_coords:
            self._build_coordinate_grids()

    def _build_coordinate_grids(self):
        """Build X and Y coordinate arrays for interpolation."""
        x_min, x_max = self.config.bounds_x_mm
        y_min, y_max = self.config.bounds_y_mm

        self._x_coords = [
            x_min + i * (x_max - x_min) / (self.config.grid_size_x - 1)
            for i in range(self.config.grid_size_x)
        ]
        self._y_coords = [
            y_min + i * (y_max - y_min) / (self.config.grid_size_y - 1)
            for i in range(self.config.grid_size_y)
        ]

    def get_thickness_at(self, x_mm: float, y_mm: float) -> float:
        """
        Get interpolated thickness at arbitrary point.

        Uses bilinear interpolation between grid points.
        Returns edge_thickness for points outside grid or outline.
        """
        if not self.thickness_grid:
            # No grid loaded, use parametric model
            return self._parametric_thickness(x_mm, y_mm)

        x_min, x_max = self.config.bounds_x_mm
        y_min, y_max = self.config.bounds_y_mm

        # Clamp to bounds
        if x_mm < x_min or x_mm > x_max or y_mm < y_min or y_mm > y_max:
            return self.config.edge_thickness_mm

        # Find grid cell
        dx = (x_max - x_min) / (self.config.grid_size_x - 1)
        dy = (y_max - y_min) / (self.config.grid_size_y - 1)

        i = int((x_mm - x_min) / dx)
        j = int((y_mm - y_min) / dy)

        # Clamp indices
        i = max(0, min(i, self.config.grid_size_x - 2))
        j = max(0, min(j, self.config.grid_size_y - 2))

        # Bilinear interpolation weights
        tx = (x_mm - self._x_coords[i]) / dx
        ty = (y_mm - self._y_coords[j]) / dy

        # Get corner values
        t00 = self.thickness_grid[j][i]
        t10 = self.thickness_grid[j][i + 1]
        t01 = self.thickness_grid[j + 1][i]
        t11 = self.thickness_grid[j + 1][i + 1]

        # Bilinear interpolation
        thickness = (
            t00 * (1 - tx) * (1 - ty) +
            t10 * tx * (1 - ty) +
            t01 * (1 - tx) * ty +
            t11 * tx * ty
        )

        return thickness

    def _parametric_thickness(self, x_mm: float, y_mm: float) -> float:
        """
        Calculate thickness using parametric archtop model.

        Models an ellipsoidal dome with optional edge recurve.
        Used when no grid data is loaded.
        """
        x_min, x_max = self.config.bounds_x_mm
        y_min, y_max = self.config.bounds_y_mm

        # Normalize to -1..1 range
        nx = 2 * (x_mm - x_min) / (x_max - x_min) - 1
        ny = 2 * (y_mm - y_min) / (y_max - y_min) - 1

        # Distance from center (0..1)
        r = math.sqrt(nx * nx + ny * ny)

        if r > 1.0:
            return self.config.edge_thickness_mm

        apex = self.config.apex_thickness_mm
        edge = self.config.edge_thickness_mm
        recurve = self.config.recurve_depth_mm

        if self.config.surface_type == SurfaceType.ARCHTOP:
            # Ellipsoidal dome with optional recurve
            # Main dome: thickness decreases from apex to edge
            dome_factor = math.sqrt(1 - r * r)  # Ellipsoid profile
            base_thickness = edge + (apex - edge) * dome_factor

            # Recurve near edge (Benedetto style)
            if recurve > 0 and r > 0.85:
                # Smooth transition to recurve
                recurve_factor = (r - 0.85) / 0.15
                recurve_amount = recurve * recurve_factor * recurve_factor
                base_thickness -= recurve_amount

            return max(edge * 0.8, base_thickness)  # Don't go too thin

        elif self.config.surface_type == SurfaceType.ARCHTOP_ASYMMETRIC:
            # Asymmetric carved top (LP-GAP-05)
            return self._asymmetric_thickness(x_mm, y_mm)

        elif self.config.surface_type == SurfaceType.CONCAVE:
            # Inverted dome (dish shape)
            dome_factor = math.sqrt(1 - r * r)
            return apex - (apex - edge) * dome_factor

        else:
            # Freeform: linear interpolation
            return apex - (apex - edge) * r

    def _asymmetric_thickness(self, x_mm: float, y_mm: float) -> float:
        """
        Calculate thickness using asymmetric carved top model (LP-GAP-05).

        Models an ellipsoidal dome with:
        - Peak offset from center (typically toward neck)
        - Compound radius (different X and Y radii)
        - Variable slopes across different zones
        - Binding ledge at perimeter

        Based on authentic 1959 Les Paul carved top measurements.
        """
        profile = self.config.asymmetric_profile
        if profile is None:
            # Fall back to symmetric model
            return self._parametric_thickness_symmetric(x_mm, y_mm)

        x_min, x_max = self.config.bounds_x_mm
        y_min, y_max = self.config.bounds_y_mm
        half_width = (x_max - x_min) / 2
        half_length = (y_max - y_min) / 2

        apex = self.config.apex_thickness_mm
        edge = self.config.edge_thickness_mm

        # Calculate position relative to offset peak
        center_x = (x_max + x_min) / 2
        center_y = (y_max + y_min) / 2
        peak_x = center_x + profile.peak_offset_x_mm
        peak_y = center_y + profile.peak_offset_y_mm

        dx = x_mm - peak_x
        dy = y_mm - peak_y

        # Normalize using compound radius (elliptical dome)
        # Use major_radius for X (width), minor_radius for Y (length)
        nx = dx / profile.major_radius_mm if profile.major_radius_mm > 0 else 0
        ny = dy / profile.minor_radius_mm if profile.minor_radius_mm > 0 else 0

        # Elliptical distance from peak (0 at peak, increases outward)
        r_ellipse = math.sqrt(nx * nx + ny * ny)

        # Normalized distance for zone calculations (0-1 from center to edge)
        nx_body = (x_mm - center_x) / half_width
        ny_body = (y_mm - center_y) / half_length
        r_body = math.sqrt(nx_body * nx_body + ny_body * ny_body)

        # Check for binding ledge (flat zone at very edge)
        edge_zone = 1.0 - (profile.binding_ledge_mm / min(half_width, half_length))
        if r_body > edge_zone:
            return edge

        # Outside bounds
        if r_body > 1.0:
            return edge

        # Determine slope zone and calculate dome factor
        # Zone 1: Crown (gentle slope near peak)
        # Zone 2: Cutaway transitions (steep slope)
        # Zone 3: Lower bout (medium slope)
        # Zone 4: Average (default slope)

        if r_body < profile.crown_zone_radius:
            # Crown zone: gentle slope
            slope_rad = math.radians(profile.slope_crown_deg)
        elif abs(nx_body) > profile.cutaway_zone_x_min and ny_body < profile.cutaway_zone_y_max:
            # Cutaway zone: steep slope
            slope_rad = math.radians(profile.slope_cutaway_deg)
        elif ny_body > 0.3:  # Lower bout
            slope_rad = math.radians(profile.slope_lower_bout_deg)
        else:
            # Average slope
            slope_rad = math.radians(profile.slope_average_deg)

        # Calculate height based on elliptical dome with variable slope
        # Use cosine-based dome profile scaled by total rise
        if r_ellipse >= 1.0:
            dome_height = 0.0
        else:
            # Smooth cosine dome: height = total_rise * cos(r * pi/2)
            # Modified to account for variable slope zones
            dome_height = profile.total_rise_mm * math.cos(r_ellipse * math.pi / 2)

            # Apply slope adjustment in transition zones
            if r_body > profile.crown_zone_radius:
                # Blend between crown slope and zone slope
                zone_factor = (r_body - profile.crown_zone_radius) / (1.0 - profile.crown_zone_radius)
                # Steeper slope means height drops faster
                slope_factor = 1.0 + zone_factor * (math.tan(slope_rad) - 0.05)
                dome_height *= max(0.0, 1.0 - zone_factor * (slope_factor - 1.0) * 0.5)

        # Convert dome height to thickness
        # thickness = edge + (apex - edge) * (dome_height / total_rise)
        if profile.total_rise_mm > 0:
            thickness = edge + (apex - edge) * (dome_height / profile.total_rise_mm)
        else:
            thickness = edge

        return max(edge * 0.8, thickness)  # Don't go too thin

    def _parametric_thickness_symmetric(self, x_mm: float, y_mm: float) -> float:
        """Symmetric fallback for when asymmetric_profile is None."""
        x_min, x_max = self.config.bounds_x_mm
        y_min, y_max = self.config.bounds_y_mm

        nx = 2 * (x_mm - x_min) / (x_max - x_min) - 1
        ny = 2 * (y_mm - y_min) / (y_max - y_min) - 1
        r = math.sqrt(nx * nx + ny * ny)

        if r > 1.0:
            return self.config.edge_thickness_mm

        apex = self.config.apex_thickness_mm
        edge = self.config.edge_thickness_mm
        dome_factor = math.sqrt(1 - r * r)
        return edge + (apex - edge) * dome_factor

    def get_surface_z_at(
        self,
        x_mm: float,
        y_mm: float,
        stock_thickness_mm: float,
    ) -> float:
        """
        Get surface Z height at point.

        For archtop: Z = stock_top - (stock_thickness - local_thickness)
        Stock top is at Z=0, carving goes negative.
        """
        thickness = self.get_thickness_at(x_mm, y_mm)
        # Surface Z relative to stock top (Z=0)
        # Thicker areas are higher (less removed)
        z = -(stock_thickness_mm - thickness)
        return z

    def get_contour_at_z(
        self,
        z_level_mm: float,
        stock_thickness_mm: float,
        resolution: int = 100,
    ) -> List[Tuple[float, float]]:
        """
        Get points forming a contour at specified Z level.

        Uses marching squares on the thickness grid to find contour.
        """
        # Convert Z level to thickness threshold
        # z = -(stock - thickness) => thickness = stock + z
        thickness_threshold = stock_thickness_mm + z_level_mm

        points = []
        x_min, x_max = self.config.bounds_x_mm
        y_min, y_max = self.config.bounds_y_mm

        # Scan at resolution
        for i in range(resolution):
            angle = 2 * math.pi * i / resolution
            # Radial search from center
            for r_step in range(50):
                r = r_step * 0.02  # 0 to 1 in 50 steps
                x = (x_max + x_min) / 2 + r * (x_max - x_min) / 2 * math.cos(angle)
                y = (y_max + y_min) / 2 + r * (y_max - y_min) / 2 * math.sin(angle)

                thickness = self.get_thickness_at(x, y)
                if thickness <= thickness_threshold:
                    # Found contour crossing
                    points.append((x, y))
                    break

        return points

    def generate_z_levels(
        self,
        stock_thickness_mm: float,
        stepdown_mm: float,
        finish_allowance_mm: float = 0.0,
    ) -> List[float]:
        """
        Generate Z levels for parallel-plane roughing.

        Returns list of Z heights from stock top to final surface.
        """
        # Surface range
        z_top = 0.0  # Stock top
        z_deepest = -(stock_thickness_mm - self.config.edge_thickness_mm)
        z_deepest += finish_allowance_mm  # Leave material for finishing

        levels = []
        z = z_top - stepdown_mm  # First cut below top

        while z > z_deepest:
            levels.append(z)
            z -= stepdown_mm

        # Always include final level
        if not levels or levels[-1] > z_deepest:
            levels.append(z_deepest)

        return levels

    def is_inside_outline(self, x_mm: float, y_mm: float) -> bool:
        """Check if point is inside the carving outline."""
        if not self.outline_points:
            # No outline defined, use bounds
            x_min, x_max = self.config.bounds_x_mm
            y_min, y_max = self.config.bounds_y_mm
            return x_min <= x_mm <= x_max and y_min <= y_mm <= y_max

        # Ray casting algorithm for point-in-polygon
        n = len(self.outline_points)
        inside = False

        j = n - 1
        for i in range(n):
            xi, yi = self.outline_points[i]
            xj, yj = self.outline_points[j]

            if ((yi > y_mm) != (yj > y_mm)) and \
               (x_mm < (xj - xi) * (y_mm - yi) / (yj - yi) + xi):
                inside = not inside
            j = i

        return inside

    def to_dict(self) -> dict:
        return {
            "config": self.config.to_dict(),
            "grid_size": (len(self.thickness_grid[0]) if self.thickness_grid else 0,
                         len(self.thickness_grid)),
            "outline_points": len(self.outline_points),
            "apex_thickness_mm": self.config.apex_thickness_mm,
            "edge_thickness_mm": self.config.edge_thickness_mm,
        }

    @classmethod
    def from_json(cls, json_path: Union[str, Path]) -> "GraduationMap":
        """Load graduation map from JSON file."""
        path = Path(json_path)
        with open(path, "r") as f:
            data = json.load(f)

        config = GraduationMapConfig(
            grid_size_x=data.get("grid_size_x", 64),
            grid_size_y=data.get("grid_size_y", 64),
            bounds_x_mm=tuple(data.get("bounds_x_mm", [-250, 250])),
            bounds_y_mm=tuple(data.get("bounds_y_mm", [-200, 200])),
            apex_thickness_mm=data.get("apex_thickness_mm", 7.0),
            edge_thickness_mm=data.get("edge_thickness_mm", 3.5),
            recurve_depth_mm=data.get("recurve_depth_mm", 0.0),
            surface_type=SurfaceType(data.get("surface_type", "archtop")),
        )

        grad_map = cls(config=config)

        # Load thickness grid if present
        if "thickness_grid" in data:
            grad_map.thickness_grid = data["thickness_grid"]

        # Load outline if present
        if "outline" in data:
            grad_map.outline_points = [tuple(p) for p in data["outline"]]

        return grad_map

    @classmethod
    def create_parametric(
        cls,
        config: Optional[GraduationMapConfig] = None,
    ) -> "GraduationMap":
        """Create graduation map using parametric model (no grid data)."""
        if config is None:
            config = GraduationMapConfig()

        grad_map = cls(config=config)
        # No thickness_grid = uses parametric model
        return grad_map

    def generate_grid_from_parametric(self) -> None:
        """Generate thickness grid from parametric model."""
        self.thickness_grid = []

        for j in range(self.config.grid_size_y):
            row = []
            for i in range(self.config.grid_size_x):
                x = self._x_coords[i] if self._x_coords else 0
                y = self._y_coords[j] if self._y_coords else 0
                thickness = self._parametric_thickness(x, y)
                row.append(round(thickness, 4))
            self.thickness_grid.append(row)

    def save_json(self, json_path: Union[str, Path]) -> None:
        """Save graduation map to JSON file."""
        path = Path(json_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "schema_version": "1.0",
            "surface_type": self.config.surface_type.value,
            "grid_size_x": self.config.grid_size_x,
            "grid_size_y": self.config.grid_size_y,
            "bounds_x_mm": list(self.config.bounds_x_mm),
            "bounds_y_mm": list(self.config.bounds_y_mm),
            "apex_thickness_mm": self.config.apex_thickness_mm,
            "edge_thickness_mm": self.config.edge_thickness_mm,
            "recurve_depth_mm": self.config.recurve_depth_mm,
            "thickness_grid": self.thickness_grid,
            "outline": self.outline_points,
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)
