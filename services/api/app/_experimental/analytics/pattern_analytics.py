"""
Pattern Analytics Engine (N9.0)

Analyzes rosette pattern complexity, geometry metrics, and usage patterns.
"""

import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict
import math

from ...stores.rmos_stores import get_rmos_stores

logger = logging.getLogger(__name__)


class PatternAnalytics:
    """
    Analytics engine for rosette patterns.
    
    Provides:
    - Complexity scoring based on ring count and geometry
    - Ring distribution analysis
    - Geometry metrics (radius ranges, segment counts)
    - Strip family usage patterns
    - Pattern popularity tracking
    """
    
    def __init__(self):
        """Initialize analytics engine with store access."""
        self.stores = get_rmos_stores()
    
    def get_complexity_distribution(self) -> Dict[str, Any]:
        """
        Analyze pattern complexity distribution.
        
        Complexity score formula:
        - Base: ring_count * 10
        - Bonus: +5 per 100 segments
        - Categories: Simple (0-30), Medium (31-60), Complex (61-100), Expert (100+)
        
        Returns:
            Distribution by complexity category with pattern counts
        """
        patterns = self.stores.patterns.get_all()
        
        distribution = {
            "simple": {"count": 0, "patterns": [], "score_range": "0-30"},
            "medium": {"count": 0, "patterns": [], "score_range": "31-60"},
            "complex": {"count": 0, "patterns": [], "score_range": "61-100"},
            "expert": {"count": 0, "patterns": [], "score_range": "100+"}
        }
        
        for pattern in patterns:
            score = self._calculate_complexity_score(pattern)
            
            # Categorize
            if score <= 30:
                category = "simple"
            elif score <= 60:
                category = "medium"
            elif score <= 100:
                category = "complex"
            else:
                category = "expert"
            
            distribution[category]["count"] += 1
            distribution[category]["patterns"].append({
                "id": pattern["id"],
                "name": pattern.get("name", "Unnamed"),
                "score": score
            })
        
        return {
            "categories": distribution,  # Test expects "categories" not "distribution"
            "distribution": distribution,  # Keep for backward compatibility
            "total_patterns": len(patterns),
            "avg_complexity": sum(
                self._calculate_complexity_score(p) for p in patterns
            ) / len(patterns) if patterns else 0
        }
    
    def get_ring_statistics(self) -> Dict[str, Any]:
        """
        Analyze ring count statistics across all patterns.
        
        Returns:
            Min, max, average, median ring counts and distribution
        """
        patterns = self.stores.patterns.get_all()
        
        if not patterns:
            return {
                "count": 0,
                "min": 0,
                "max": 0,
                "avg": 0,
                "median": 0,
                "distribution": {}
            }
        
        ring_counts = [p.get("ring_count", 0) for p in patterns]
        ring_counts.sort()
        
        # Distribution by ring count
        distribution = defaultdict(int)
        for count in ring_counts:
            distribution[count] += 1
        
        return {
            "count": len(patterns),
            "min_rings": min(ring_counts),  # Test expects min_rings
            "max_rings": max(ring_counts),  # Test expects max_rings
            "avg_rings": sum(ring_counts) / len(ring_counts),  # Test expects avg_rings
            "min": min(ring_counts),  # Keep for backward compatibility
            "max": max(ring_counts),
            "avg": sum(ring_counts) / len(ring_counts),
            "median": ring_counts[len(ring_counts) // 2],
            "distribution": dict(distribution),
            "most_common": max(distribution.items(), key=lambda x: x[1]) if distribution else (0, 0)
        }
    
    def get_geometry_metrics(self) -> Dict[str, Any]:
        """
        Analyze geometry characteristics across patterns.
        
        Extracts:
        - Radius ranges (min, max, avg)
        - Segment counts (min, max, avg)
        - Ring density (segments per ring)
        
        Returns:
            Aggregated geometry statistics
        """
        patterns = self.stores.patterns.get_all()
        
        all_radii = []
        all_segments = []
        ring_densities = []
        
        for pattern in patterns:
            geometry = pattern.get("geometry", {})
            rings = geometry.get("rings", [])
            
            for ring in rings:
                if isinstance(ring, dict):
                    radius = ring.get("radius_mm")
                    segments = ring.get("segments")
                    
                    if radius:
                        all_radii.append(radius)
                    if segments:
                        all_segments.append(segments)
                    if radius and segments:
                        # Density: segments per mm of circumference
                        circumference = 2 * math.pi * radius
                        density = segments / circumference if circumference > 0 else 0
                        ring_densities.append(density)
        
        return {
            "radius": {  # Test expects "radius" not "radius_mm"
                "min_mm": min(all_radii) if all_radii else 0,
                "max_mm": max(all_radii) if all_radii else 0,
                "avg_mm": sum(all_radii) / len(all_radii) if all_radii else 0,
                "count": len(all_radii)
            },
            "radius_mm": {  # Keep for backward compatibility
                "min": min(all_radii) if all_radii else 0,
                "max": max(all_radii) if all_radii else 0,
                "avg": sum(all_radii) / len(all_radii) if all_radii else 0,
                "count": len(all_radii)
            },
            "segments": {
                "min": min(all_segments) if all_segments else 0,
                "max": max(all_segments) if all_segments else 0,
                "avg": sum(all_segments) / len(all_segments) if all_segments else 0,
                "total_segments": sum(all_segments) if all_segments else 0,  # Test expects total_segments
                "count": len(all_segments)
            },
            "ring_density": {
                "min": min(ring_densities) if ring_densities else 0,
                "max": max(ring_densities) if ring_densities else 0,
                "avg": sum(ring_densities) / len(ring_densities) if ring_densities else 0,
                "description": "Segments per mm of circumference"
            }
        }
    
    def get_strip_family_usage(self) -> Dict[str, Any]:
        """
        Analyze which strip families are used most frequently.
        
        Returns:
            Usage statistics per strip family
        """
        patterns = self.stores.patterns.get_all()
        families = self.stores.strip_families.get_all()
        
        # Count patterns per family
        family_usage = defaultdict(lambda: {"count": 0, "patterns": []})
        
        for pattern in patterns:
            family_id = pattern.get("strip_family_id")
            if family_id:
                family_usage[family_id]["count"] += 1
                family_usage[family_id]["patterns"].append({
                    "id": pattern["id"],
                    "name": pattern.get("name", "Unnamed")
                })
        
        # Enrich with family details
        enriched_usage = []
        for family in families:
            family_id = family["id"]
            usage = family_usage.get(family_id, {"count": 0, "patterns": []})
            
            enriched_usage.append({
                "family_id": family_id,
                "family_name": family.get("name", "Unnamed"),
                "material_type": family.get("material_type", "Unknown"),
                "strip_width_mm": family.get("strip_width_mm", 0),
                "pattern_count": usage["count"],
                "patterns": usage["patterns"]
            })
        
        # Sort by usage (most used first)
        enriched_usage.sort(key=lambda x: x["pattern_count"], reverse=True)
        
        return {
            "total_families": len(families),
            "families_in_use": len([u for u in enriched_usage if u["pattern_count"] > 0]),
            "usage": enriched_usage,  # Test expects this field
            "families": {  # Add families object with usage array for backward compat
                "usage": enriched_usage
            },
            "most_popular": enriched_usage[0] if enriched_usage else None
        }
    
    def get_pattern_popularity(self, limit: int = 10) -> Dict[str, Any]:
        """
        Rank patterns by job usage frequency.
        
        Args:
            limit: Max patterns to return
            
        Returns:
            Top patterns by job count
        """
        patterns = self.stores.patterns.get_all()
        joblogs = self.stores.joblogs.get_all()
        
        # Count jobs per pattern
        pattern_job_counts = defaultdict(int)
        for job in joblogs:
            pattern_id = job.get("pattern_id")
            if pattern_id:
                pattern_job_counts[pattern_id] += 1
        
        # Enrich with pattern details
        popularity = []
        for pattern in patterns:
            pattern_id = pattern["id"]
            job_count = pattern_job_counts.get(pattern_id, 0)
            
            popularity.append({
                "id": pattern_id,
                "name": pattern.get("name", "Unnamed"),
                "ring_count": pattern.get("ring_count", 0),
                "job_count": job_count,
                "complexity_score": self._calculate_complexity_score(pattern)
            })
        
        # Sort by job count
        popularity.sort(key=lambda x: x["job_count"], reverse=True)
        
        return {
            "top_patterns": popularity[:limit],
            "total_patterns": len(patterns),
            "patterns_with_jobs": len([p for p in popularity if p["job_count"] > 0])
        }
    
    def get_pattern_details_with_analytics(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed analytics for a specific pattern.
        
        Args:
            pattern_id: Pattern UUID
            
        Returns:
            Pattern details with computed analytics
        """
        pattern = self.stores.patterns.get_by_id(pattern_id)
        if not pattern:
            return None
        
        # Get related jobs
        jobs = self.stores.joblogs.get_by_pattern(pattern_id)
        
        # Calculate metrics
        complexity_score = self._calculate_complexity_score(pattern)
        
        # Job statistics
        completed_jobs = [j for j in jobs if j.get("status") == "completed"]
        failed_jobs = [j for j in jobs if j.get("status") == "failed"]
        
        avg_duration = 0
        if completed_jobs:
            durations = [j.get("duration_seconds", 0) for j in completed_jobs]
            avg_duration = sum(durations) / len(durations)
        
        return {
            "pattern": pattern,
            "analytics": {
                "complexity_score": complexity_score,
                "job_count": len(jobs),
                "completed_jobs": len(completed_jobs),
                "failed_jobs": len(failed_jobs),
                "success_rate": len(completed_jobs) / len(jobs) * 100 if jobs else 0,
                "avg_duration_seconds": avg_duration,
                "avg_duration_minutes": avg_duration / 60
            }
        }
    
    def _calculate_complexity_score(self, pattern: Dict[str, Any]) -> float:
        """
        Calculate complexity score for a pattern.
        
        Formula:
        - Base: ring_count * 10
        - Geometry bonus: +5 per 100 total segments
        
        Args:
            pattern: Pattern dictionary
            
        Returns:
            Complexity score (0-200+)
        """
        ring_count = pattern.get("ring_count", 0)
        base_score = ring_count * 10
        
        # Geometry bonus
        geometry = pattern.get("geometry", {})
        rings = geometry.get("rings", [])
        total_segments = sum(
            ring.get("segments", 0) for ring in rings if isinstance(ring, dict)
        )
        geometry_bonus = (total_segments / 100) * 5
        
        return base_score + geometry_bonus


def get_pattern_analytics() -> PatternAnalytics:
    """
    Get singleton pattern analytics instance.
    
    Returns:
        PatternAnalytics engine
    """
    return PatternAnalytics()
