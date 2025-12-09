"""
RMOS 2.0 Toolpath Service
Facade for toolpath planning with geometry engine integration.
"""
from typing import List, Dict, Any
from ..rmos.api_contracts import RmosContext, RmosToolpathPlan
from .geometry_engine import get_geometry_engine

try:
    from ..art_studio.schemas import RosetteParamSpec
except ImportError:
    from ..rmos.api_contracts import RosetteParamSpec


class ToolpathService:
    """
    Unified toolpath planning facade.
    Integrates geometry engine with feed rate, plunge strategy, and G-code generation.
    """
    
    def generate_toolpaths(
        self,
        design: RosetteParamSpec,
        ctx: RmosContext
    ) -> RmosToolpathPlan:
        """
        Generate complete toolpath plan for rosette design.
        
        Args:
            design: Rosette design parameters
            ctx: Manufacturing environment context
        
        Returns:
            RmosToolpathPlan with toolpath segments, length, time estimate
        """
        warnings: List[str] = []
        
        try:
            # Get geometry engine based on context
            engine = get_geometry_engine(ctx)
            
            # Generate rosette path geometry
            path_segments = engine.generate_rosette_paths(design, ctx)
            
            # Convert to toolpath operations
            toolpaths = []
            total_length_mm = 0.0
            
            # Add initial positioning (safe Z, rapid to start)
            toolpaths.append({
                "operation": "rapid",
                "code": "G0",
                "z": 5.0,
                "comment": "Retract to safe height"
            })
            
            # Process each ring
            for segment in path_segments:
                if segment["type"] == "ring":
                    ring_idx = segment["ring_index"]
                    points = segment["points"]
                    
                    if len(points) > 0:
                        # Rapid to start of ring
                        start_pt = points[0]
                        toolpaths.append({
                            "operation": "rapid",
                            "code": "G0",
                            "x": start_pt["x"],
                            "y": start_pt["y"],
                            "comment": f"Move to ring {ring_idx} start"
                        })
                        
                        # Plunge to cut depth
                        cut_depth = -1.5  # Default 1.5mm depth
                        toolpaths.append({
                            "operation": "plunge",
                            "code": "G1",
                            "z": cut_depth,
                            "f": 300,
                            "comment": f"Plunge for ring {ring_idx}"
                        })
                        
                        # Cut around ring
                        for pt in points:
                            toolpaths.append({
                                "operation": "cut",
                                "code": "G1",
                                "x": pt["x"],
                                "y": pt["y"],
                                "f": 1200,
                                "comment": f"Ring {ring_idx} cutting"
                            })
                            
                            # Accumulate path length
                            if len(toolpaths) > 1:
                                prev = toolpaths[-2]
                                if "x" in prev and "y" in prev:
                                    dx = pt["x"] - prev.get("x", 0)
                                    dy = pt["y"] - prev.get("y", 0)
                                    total_length_mm += (dx**2 + dy**2) ** 0.5
                        
                        # Retract after ring
                        toolpaths.append({
                            "operation": "retract",
                            "code": "G0",
                            "z": 5.0,
                            "comment": f"Retract after ring {ring_idx}"
                        })
            
            # Final positioning
            toolpaths.append({
                "operation": "end",
                "code": "M30",
                "comment": "End of program"
            })
            
            # Estimate machining time
            estimated_time = self._estimate_time(toolpaths)
            
            # Validate toolpath
            if len(toolpaths) < 5:
                warnings.append("Toolpath generation produced minimal moves; verify design parameters")
            
            if total_length_mm < 10:
                warnings.append("Total path length unusually short; check ring count and diameters")
            
            return RmosToolpathPlan(
                toolpaths=toolpaths,
                total_length_mm=round(total_length_mm, 2),
                estimated_time_seconds=round(estimated_time, 2),
                warnings=warnings
            )
            
        except Exception as e:
            warnings.append(f"Toolpath generation error: {str(e)}")
            return RmosToolpathPlan(
                toolpaths=[],
                total_length_mm=0.0,
                estimated_time_seconds=0.0,
                warnings=warnings
            )
    
    def _estimate_time(self, toolpaths: List[Dict[str, Any]]) -> float:
        """
        Estimate machining time in seconds based on toolpath operations.
        
        Args:
            toolpaths: List of toolpath operation dicts
        
        Returns:
            Estimated time in seconds
        """
        time_seconds = 0.0
        rapid_feed = 5000.0  # mm/min
        cut_feed = 1200.0    # mm/min
        plunge_feed = 300.0  # mm/min
        
        prev = None
        for move in toolpaths:
            if prev is not None:
                # Calculate distance
                dx = move.get("x", 0) - prev.get("x", 0)
                dy = move.get("y", 0) - prev.get("y", 0)
                dz = move.get("z", 0) - prev.get("z", 0)
                distance = (dx**2 + dy**2 + dz**2) ** 0.5
                
                # Select feed rate based on operation
                if move.get("operation") == "rapid":
                    feed = rapid_feed
                elif move.get("operation") == "plunge":
                    feed = plunge_feed
                elif move.get("operation") == "cut":
                    feed = cut_feed
                else:
                    feed = cut_feed  # Default
                
                # Time = distance / feed (convert feed from mm/min to mm/s)
                if feed > 0:
                    time_seconds += (distance / (feed / 60.0))
            
            prev = move
        
        # Add 10% overhead for acceleration/deceleration
        time_seconds *= 1.1
        
        return time_seconds
