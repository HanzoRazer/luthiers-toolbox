"""
Saw Lab 2.0 - Toolpath Builder

Converts planned cut paths into G-code toolpath moves.
"""
from __future__ import annotations

from typing import List, Dict, Any

from .models import SawContext, SawToolpathPlan, SawToolpathMove


class SawToolpathBuilder:
    """
    Builds G-code toolpaths from planned cut segments.
    
    Generates:
        - G0 rapid moves
        - G1 linear feed moves
        - Proper header/footer sequences
        - Feed rate commands
    """
    
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
        
        # Set spindle speed (if applicable for CNC saw)
        if ctx.max_rpm > 0:
            moves.append(SawToolpathMove(
                code=f"S{ctx.max_rpm}",
                comment=f"Spindle speed: {ctx.max_rpm} RPM"
            ))
            moves.append(SawToolpathMove(
                code="M3",
                comment="Spindle on CW"
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
            comment="Spindle stop"
        ))
        moves.append(SawToolpathMove(
            code="M30",
            comment="Program end"
        ))
        
        # Estimate time
        estimated_time = self._estimate_time(segments, ctx)
        
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
    
    def _estimate_time(
        self,
        segments: List[Dict[str, Any]],
        ctx: SawContext
    ) -> float:
        """Estimate machining time from segments."""
        time_seconds = 0.0
        rapid_feed = 10000.0  # mm/min
        
        for segment in segments:
            start = segment["start"]
            end = segment["end"]
            
            dx = end["x"] - start["x"]
            dy = end["y"] - start["y"]
            dz = end["z"] - start["z"]
            distance = (dx**2 + dy**2 + dz**2) ** 0.5
            
            if segment["type"] in ["rapid", "retract"]:
                feed = rapid_feed
            else:
                feed = segment.get("feed", ctx.feed_rate_mm_per_min)
            
            if feed > 0:
                time_seconds += (distance / feed) * 60.0
        
        # 15% overhead
        return time_seconds * 1.15
