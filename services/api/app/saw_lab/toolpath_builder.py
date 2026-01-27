"""
Saw Lab 2.0 - Toolpath Builder

Converts planned cut paths into G-code toolpath moves.
Uses trapezoidal velocity profile for accurate time estimation.
"""
from __future__ import annotations

import math
from typing import List, Dict, Any

from .models import SawContext, SawToolpathPlan, SawToolpathMove


# Machine dynamics defaults (typical CNC saw)
_DEFAULT_ACCEL_MM_PER_S2 = 500.0     # Linear acceleration (X/Y/Z)
_DEFAULT_RAPID_FEED_MM_PER_MIN = 10000.0  # Rapid traverse speed


class SawToolpathBuilder:
    """
    Builds G-code toolpaths from planned cut segments.

    Generates:
        - G0 rapid moves
        - G1 linear feed moves
        - Proper header/footer sequences
        - Feed rate commands

    Time estimation uses trapezoidal velocity profile:
        - Acceleration phase: 0 -> v_target
        - Cruise phase: constant v_target
        - Deceleration phase: v_target -> 0
    """

    def __init__(
        self,
        accel_mm_per_s2: float = _DEFAULT_ACCEL_MM_PER_S2,
        rapid_feed_mm_per_min: float = _DEFAULT_RAPID_FEED_MM_PER_MIN,
    ):
        self._accel = accel_mm_per_s2
        self._rapid_feed = rapid_feed_mm_per_min

    def build(
        self,
        segments: List[Dict[str, Any]],
        ctx: SawContext
    ) -> SawToolpathPlan:
        """
        Build complete toolpath from planned segments.

        Args:
            segments: Planned cut segments from path planner
            ctx: Saw context

        Returns:
            SawToolpathPlan with G-code moves
        """
        moves: List[SawToolpathMove] = []
        warnings: List[str] = []
        total_length = 0.0
        cut_count = 0

        # Header moves
        moves.append(SawToolpathMove(
            code="G21",
            comment="Units: mm"
        ))
        moves.append(SawToolpathMove(
            code="G90",
            comment="Absolute positioning"
        ))
        moves.append(SawToolpathMove(
            code="G17",
            comment="XY plane selection"
        ))

        # Set spindle speed (C-axis rotation)
        if ctx.max_rpm > 0:
            moves.append(SawToolpathMove(
                code=f"S{ctx.max_rpm}",
                comment=f"C-axis speed: {ctx.max_rpm} RPM"
            ))
            moves.append(SawToolpathMove(
                code="M3",
                comment="Spindle on CW (C-axis)"
            ))

        # Initial safe position
        safe_z = ctx.stock_thickness_mm + 15.0
        moves.append(SawToolpathMove(
            code="G0",
            z=safe_z,
            comment="Move to safe height"
        ))

        # Process each segment
        for segment in segments:
            segment_moves, segment_length = self._process_segment(segment, ctx)
            moves.extend(segment_moves)
            total_length += segment_length

            if segment["type"] == "cut":
                cut_count += 1

        # Footer moves
        moves.append(SawToolpathMove(
            code="G0",
            z=safe_z,
            comment="Final retract to safe height"
        ))
        moves.append(SawToolpathMove(
            code="M5",
            comment="Spindle stop (C-axis)"
        ))
        moves.append(SawToolpathMove(
            code="M30",
            comment="Program end"
        ))

        # Estimate time with trapezoidal profile
        estimated_time = self._estimate_time_trapezoidal(segments, ctx)

        # Calculate material removed (if available from segments)
        material_removed = sum(
            seg.get("material_removed_mm3", 0)
            for seg in segments
        )

        # Add warnings if needed
        if total_length < 10:
            warnings.append("Very short toolpath - verify design parameters")

        if cut_count == 0:
            warnings.append("No cutting moves generated")

        return SawToolpathPlan(
            moves=moves,
            total_length_mm=round(total_length, 2),
            estimated_time_seconds=round(estimated_time, 2),
            warnings=warnings,
            cut_count=cut_count,
            material_removed_mm3=round(material_removed, 2)
        )

    def _process_segment(
        self,
        segment: Dict[str, Any],
        ctx: SawContext
    ) -> tuple[List[SawToolpathMove], float]:
        """Process a single segment into G-code moves."""
        moves = []
        length = 0.0

        start = segment["start"]
        end = segment["end"]
        comment = segment.get("comment", "")

        # Calculate segment length
        dx = end["x"] - start["x"]
        dy = end["y"] - start["y"]
        dz = end["z"] - start["z"]
        length = (dx**2 + dy**2 + dz**2) ** 0.5

        segment_type = segment["type"]

        if segment_type == "rapid" or segment_type == "retract":
            moves.append(SawToolpathMove(
                code="G0",
                x=round(end["x"], 4),
                y=round(end["y"], 4),
                z=round(end["z"], 4),
                comment=comment
            ))
        elif segment_type == "plunge" or segment_type == "cut":
            feed = segment.get("feed", ctx.feed_rate_mm_per_min)
            moves.append(SawToolpathMove(
                code="G1",
                x=round(end["x"], 4),
                y=round(end["y"], 4),
                z=round(end["z"], 4),
                f=round(feed, 1),
                comment=comment
            ))

        return moves, length

    def _trapezoidal_move_time(self, distance_mm: float, max_feed_mm_per_min: float) -> float:
        """
        Compute move time using trapezoidal velocity profile.

        The motion has three phases:
        1. Acceleration: 0 -> v_max (or v_peak if distance is short)
        2. Cruise: constant velocity
        3. Deceleration: v_max -> 0

        For short moves where the machine cannot reach max velocity,
        it uses a triangular profile (accel then decel, no cruise).

        Args:
            distance_mm: Total move distance
            max_feed_mm_per_min: Maximum feed rate for this move

        Returns:
            Time in seconds
        """
        if distance_mm <= 0 or max_feed_mm_per_min <= 0:
            return 0.0

        v_max = max_feed_mm_per_min / 60.0  # mm/s
        a = self._accel                      # mm/s^2

        # Distance needed to accelerate from 0 to v_max
        d_accel = v_max**2 / (2.0 * a)

        # Total accel + decel distance
        d_ramp = 2.0 * d_accel

        if distance_mm >= d_ramp:
            # Trapezoidal profile: accel + cruise + decel
            t_accel = v_max / a
            t_decel = t_accel
            d_cruise = distance_mm - d_ramp
            t_cruise = d_cruise / v_max
            return t_accel + t_cruise + t_decel
        else:
            # Triangular profile: cannot reach v_max
            # Peak velocity: v_peak = sqrt(a * distance)
            v_peak = math.sqrt(a * distance_mm)
            t_accel = v_peak / a
            # Symmetric: total time = 2 * t_accel
            return 2.0 * t_accel

    def _estimate_time_trapezoidal(
        self,
        segments: List[Dict[str, Any]],
        ctx: SawContext
    ) -> float:
        """
        Estimate machining time using trapezoidal velocity profiles.

        Each segment gets its own profile based on distance and feed rate.
        Rapid moves use the rapid traverse rate.
        Cut/plunge moves use the programmed feed rate.
        """
        total_time = 0.0

        for segment in segments:
            start = segment["start"]
            end = segment["end"]

            dx = end["x"] - start["x"]
            dy = end["y"] - start["y"]
            dz = end["z"] - start["z"]
            distance = (dx**2 + dy**2 + dz**2) ** 0.5

            if segment["type"] in ["rapid", "retract"]:
                max_feed = self._rapid_feed
            else:
                max_feed = segment.get("feed", ctx.feed_rate_mm_per_min)

            total_time += self._trapezoidal_move_time(distance, max_feed)

        # Small overhead for spindle start/stop and tool change
        total_time += 3.0  # 3 seconds fixed overhead

        return total_time
