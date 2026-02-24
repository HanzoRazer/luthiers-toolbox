"""
Modal Visualizer Service — Render mode shapes for display.

This is INTERPRETATION. tap_tone_pi gives us shape coefficients.
We turn them into visual representations with design meaning.
"""
from typing import List, Optional, Dict, Any

from .schemas import ViewerPackV1, ModeShape


class ModalVisualizerService:
    """
    Transforms modal shape data into visualization-ready format.

    Responsibilities:
    - Generate SVG/canvas rendering data for mode shapes
    - Annotate nodal lines and antinodes
    - Compare mode shapes to reference instruments
    - Identify problematic mode patterns
    """

    # Known mode shape patterns (simplified Chladni patterns)
    MODE_PATTERNS = {
        "monopole": "Breathing mode - entire surface moves in phase",
        "dipole_x": "Cross-dipole - divided along grain",
        "dipole_y": "Long-dipole - divided across grain",
        "tripole": "Three-region mode - common in guitar tops",
        "quadrupole": "Four-region mode - indicates good stiffness distribution",
    }

    def prepare_shape_visualization(
        self,
        mode: ModeShape,
        grid_resolution: int = 50,
    ) -> Dict[str, Any]:
        """
        Prepare mode shape data for 2D/3D visualization.

        Args:
            mode: Mode shape from viewer_pack
            grid_resolution: Points per axis for rendering grid

        Returns:
            Dict with visualization data (vertices, colors, annotations)
        """
        # Generate displacement grid from coefficients
        grid = self._coefficients_to_grid(
            mode.shape_coefficients,
            grid_resolution,
        )

        # Find nodal lines (zero displacement)
        nodal_lines = self._extract_nodal_lines(grid)

        # Classify the pattern
        pattern_type = self._classify_pattern(grid)

        return {
            "mode_index": mode.mode_index,
            "frequency_hz": mode.frequency_hz,
            "damping_ratio": mode.damping_ratio,
            "grid": grid,
            "nodal_lines": nodal_lines,
            "pattern_type": pattern_type,
            "pattern_description": self.MODE_PATTERNS.get(
                pattern_type, "Complex mode pattern"
            ),
            "interpretation": self._interpret_mode_shape(
                mode, pattern_type
            ),
        }

    def _coefficients_to_grid(
        self,
        coefficients: List[float],
        resolution: int,
    ) -> List[List[float]]:
        """
        Convert shape coefficients to displacement grid.

        Simplified: assumes coefficients are for 2D basis functions.
        Real implementation would use proper modal decomposition.
        """
        import math

        grid = []
        n_coeffs = len(coefficients)

        for i in range(resolution):
            row = []
            y = i / (resolution - 1)  # 0 to 1

            for j in range(resolution):
                x = j / (resolution - 1)  # 0 to 1

                # Simplified: sum of basis functions
                # Real: would use actual mode shape basis
                displacement = 0.0
                for k, coeff in enumerate(coefficients):
                    # Sine basis (simplified)
                    m = k % 4 + 1
                    n = k // 4 + 1
                    displacement += coeff * math.sin(m * math.pi * x) * math.sin(n * math.pi * y)

                row.append(displacement)

            grid.append(row)

        return grid

    def _extract_nodal_lines(
        self,
        grid: List[List[float]],
    ) -> List[Dict[str, Any]]:
        """
        Find nodal lines (zero-crossing contours) in the displacement grid.
        """
        nodal_points = []
        resolution = len(grid)

        for i in range(resolution - 1):
            for j in range(resolution - 1):
                # Check for sign change (zero crossing)
                corners = [
                    grid[i][j],
                    grid[i][j + 1],
                    grid[i + 1][j],
                    grid[i + 1][j + 1],
                ]

                if self._has_sign_change(corners):
                    nodal_points.append({
                        "x": (j + 0.5) / resolution,
                        "y": (i + 0.5) / resolution,
                    })

        return nodal_points

    @staticmethod
    def _has_sign_change(values: List[float]) -> bool:
        """Check if values contain both positive and negative."""
        has_pos = any(v > 0 for v in values)
        has_neg = any(v < 0 for v in values)
        return has_pos and has_neg

    def _classify_pattern(self, grid: List[List[float]]) -> str:
        """
        Classify the mode shape pattern.

        This is INTERPRETATION — we're naming what we see.
        """
        resolution = len(grid)

        # Count quadrants with positive vs negative average
        mid = resolution // 2

        quadrants = [
            self._grid_region_avg(grid, 0, mid, 0, mid),      # top-left
            self._grid_region_avg(grid, 0, mid, mid, resolution),  # top-right
            self._grid_region_avg(grid, mid, resolution, 0, mid),  # bottom-left
            self._grid_region_avg(grid, mid, resolution, mid, resolution),  # bottom-right
        ]

        signs = [1 if q > 0 else -1 for q in quadrants]

        # Classify based on quadrant signs
        if all(s == signs[0] for s in signs):
            return "monopole"
        elif signs[0] == signs[1] and signs[2] == signs[3] and signs[0] != signs[2]:
            return "dipole_y"
        elif signs[0] == signs[2] and signs[1] == signs[3] and signs[0] != signs[1]:
            return "dipole_x"
        elif signs == [1, -1, -1, 1] or signs == [-1, 1, 1, -1]:
            return "quadrupole"
        else:
            return "tripole"

    @staticmethod
    def _grid_region_avg(
        grid: List[List[float]],
        i_start: int, i_end: int,
        j_start: int, j_end: int,
    ) -> float:
        """Calculate average value in a grid region."""
        total = 0.0
        count = 0

        for i in range(i_start, i_end):
            for j in range(j_start, j_end):
                total += grid[i][j]
                count += 1

        return total / count if count > 0 else 0.0

    def _interpret_mode_shape(
        self,
        mode: ModeShape,
        pattern_type: str,
    ) -> str:
        """
        Provide design-oriented interpretation of the mode shape.

        This is the value we add: meaning for the luthier.
        """
        freq = mode.frequency_hz
        damping = mode.damping_ratio

        interpretations = []

        # Frequency-based interpretation
        if freq < 100:
            interpretations.append(
                "Low frequency suggests this is the air cavity (Helmholtz) mode."
            )
        elif 100 <= freq < 200:
            interpretations.append(
                "This is likely the main top mode (T1). Critical for tone."
            )
        elif 200 <= freq < 350:
            interpretations.append(
                "Secondary top mode (T2). Affects tonal balance."
            )

        # Pattern-based interpretation
        if pattern_type == "monopole":
            interpretations.append(
                "Monopole pattern indicates good coupling to air cavity."
            )
        elif pattern_type == "dipole_x":
            interpretations.append(
                "Cross-grain dipole. May indicate asymmetric bracing needed."
            )
        elif pattern_type == "quadrupole":
            interpretations.append(
                "Quadrupole is typical of well-balanced top stiffness."
            )

        # Damping-based interpretation
        if damping and damping > 0.05:
            interpretations.append(
                f"High damping ({damping:.3f}) will limit sustain at this frequency."
            )
        elif damping and damping < 0.01:
            interpretations.append(
                f"Low damping ({damping:.3f}) indicates good sustain potential."
            )

        return " ".join(interpretations) if interpretations else "Standard mode characteristics."
