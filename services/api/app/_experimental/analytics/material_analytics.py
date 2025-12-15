"""
Material Analytics Engine (N9.0)

Analyzes strip consumption, material efficiency, and supplier patterns.
"""

import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict

from ..stores.rmos_stores import get_rmos_stores

logger = logging.getLogger(__name__)


class MaterialAnalytics:
    """
    Analytics engine for strip families and material usage.
    
    Provides:
    - Strip consumption tracking per material type
    - Material efficiency metrics
    - Waste calculations
    - Supplier analytics
    - Dimensional analysis
    """
    
    def __init__(self):
        """Initialize analytics engine with store access."""
        self.stores = get_rmos_stores()
    
    def get_material_type_distribution(self) -> Dict[str, Any]:
        """
        Analyze distribution of material types.
        
        Returns:
            Count and percentage per material type
        """
        families = self.stores.strip_families.get_all()
        
        if not families:
            return {
                "total_families": 0,
                "distribution": {},
                "most_common": None
            }
        
        # Count by material type
        material_counts = defaultdict(int)
        for family in families:
            material_type = family.get("material_type", "Unknown")
            material_counts[material_type] += 1
        
        total = len(families)
        distribution = {
            material: {
                "count": count,
                "percentage": (count / total * 100) if total > 0 else 0
            }
            for material, count in material_counts.items()
        }
        
        most_common = max(material_counts.items(), key=lambda x: x[1]) if material_counts else None
        
        return {
            "total_families": total,
            "distribution": distribution,
            "most_common": {
                "material": most_common[0],
                "count": most_common[1]
            } if most_common else None
        }
    
    def get_dimensional_analysis(self) -> Dict[str, Any]:
        """Analyze dimensional characteristics of strip families.
        
        Returns:
            Width, thickness, and length statistics
        """
        families = self.stores.strip_families.get_all()
        
        widths = []
        thicknesses = []
        lengths = []
        
        for family in families:
            width = family.get("strip_width_mm", 0)
            thickness = family.get("strip_thickness_mm", 0)
            
            if width > 0:
                widths.append(width)
            if thickness > 0:
                thicknesses.append(thickness)
            
            # Get strip lengths from strips array
            strips = family.get("strips", [])
            for strip in strips:
                if isinstance(strip, dict):
                    length = strip.get("length_mm", 0)
                    if length > 0:
                        lengths.append(length)
        
        return {
            "width": {  # Test expects "width" not "width_mm"
                "min_mm": min(widths) if widths else 0,
                "max_mm": max(widths) if widths else 0,
                "avg_mm": sum(widths) / len(widths) if widths else 0,
                "count": len(widths)
            },
            "width_mm": {  # Keep for backward compatibility
                "min": min(widths) if widths else 0,
                "max": max(widths) if widths else 0,
                "avg": sum(widths) / len(widths) if widths else 0,
                "count": len(widths)
            },
            "thickness": {
                "min_mm": min(thicknesses) if thicknesses else 0,
                "max_mm": max(thicknesses) if thicknesses else 0,
                "avg_mm": sum(thicknesses) / len(thicknesses) if thicknesses else 0,
                "count": len(thicknesses)
            },
            "thickness_mm": {  # Keep for backward compatibility
                "min": min(thicknesses) if thicknesses else 0,
                "max": max(thicknesses) if thicknesses else 0,
                "avg": sum(thicknesses) / len(thicknesses) if thicknesses else 0,
                "count": len(thicknesses)
            },
            "length": {
                "min_mm": min(lengths) if lengths else 0,
                "max_mm": max(lengths) if lengths else 0,
                "avg_mm": sum(lengths) / len(lengths) if lengths else 0,
                "total_mm": sum(lengths) if lengths else 0,
                "count": len(lengths)
            }
        }
    
    def get_supplier_analytics(self) -> Dict[str, Any]:
        """Analyze supplier usage and material sourcing.
        
        Returns:
            Supplier statistics and distribution
        """
        families = self.stores.strip_families.get_all()
        
        supplier_stats = defaultdict(lambda: {
            "family_count": 0,
            "material_types": set(),
            "families": []
        })
        
        for family in families:
            supplier = family.get("supplier", "Unknown")
            material_type = family.get("material_type", "Unknown")
            
            supplier_stats[supplier]["family_count"] += 1
            supplier_stats[supplier]["material_types"].add(material_type)
            supplier_stats[supplier]["families"].append({
                "id": family["id"],
                "name": family.get("name", "Unnamed"),
                "material_type": material_type
            })
        
        # Convert sets to lists for JSON serialization
        suppliers = []
        for supplier_name, stats in supplier_stats.items():
            suppliers.append({
                "supplier": supplier_name,
                "family_count": stats["family_count"],
                "material_types": list(stats["material_types"]),
                "families": stats["families"]
            })
        
        # Sort by family count
        suppliers.sort(key=lambda x: x["family_count"], reverse=True)
        
        return {
            "suppliers": suppliers,  # Test expects this field
            "total_suppliers": len(suppliers),
            "most_used": suppliers[0] if suppliers else None
        }
    
    def get_strip_consumption_by_material(self) -> Dict[str, Any]:
        """
        Calculate total strip consumption per material type.
        
        Aggregates:
        - Total strip count
        - Total length (if available)
        - Average strip dimensions
        
        Returns:
            Consumption statistics per material
        """
        families = self.stores.strip_families.get_all()
        
        material_stats = defaultdict(lambda: {
            "family_count": 0,
            "total_strips": 0,
            "total_length_mm": 0,
            "avg_width_mm": [],
            "avg_thickness_mm": []
        })
        
        for family in families:
            material_type = family.get("material_type", "Unknown")
            strips = family.get("strips", [])
            
            material_stats[material_type]["family_count"] += 1
            material_stats[material_type]["total_strips"] += len(strips)
            
            # Aggregate strip lengths
            for strip in strips:
                if isinstance(strip, dict):
                    length = strip.get("length_mm", 0)
                    material_stats[material_type]["total_length_mm"] += length
            
            # Collect dimensions for averaging
            width = family.get("strip_width_mm", 0)
            thickness = family.get("strip_thickness_mm", 0)
            
            if width > 0:
                material_stats[material_type]["avg_width_mm"].append(width)
            if thickness > 0:
                material_stats[material_type]["avg_thickness_mm"].append(thickness)
        
        # Calculate averages
        result = {}
        for material, stats in material_stats.items():
            widths = stats["avg_width_mm"]
            thicknesses = stats["avg_thickness_mm"]
            
            result[material] = {
                "family_count": stats["family_count"],
                "total_strips": stats["total_strips"],
                "total_length_mm": stats["total_length_mm"],
                "total_length_meters": stats["total_length_mm"] / 1000,
                "avg_width_mm": sum(widths) / len(widths) if widths else 0,
                "avg_thickness_mm": sum(thicknesses) / len(thicknesses) if thicknesses else 0
            }
        
        return {
            "by_material": result,
            "total_materials": len(result)
        }
    
    def get_material_efficiency(self) -> Dict[str, Any]:
        """
        Calculate material efficiency based on job results.
        
        Analyzes:
        - Waste percentage per material
        - Successful cuts vs failed
        - Material utilization rates
        
        Returns:
            Efficiency metrics per material type
        """
        families = self.stores.strip_families.get_all()
        joblogs = self.stores.joblogs.get_all()
        
        # Map family_id to material_type
        family_materials = {
            f["id"]: f.get("material_type", "Unknown")
            for f in families
        }
        
        # Aggregate by material
        material_efficiency = defaultdict(lambda: {
            "total_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "total_waste_percentage": 0,
            "waste_samples": 0
        })
        
        for job in joblogs:
            family_id = job.get("strip_family_id")
            if not family_id:
                continue
            
            material = family_materials.get(family_id, "Unknown")
            material_efficiency[material]["total_jobs"] += 1
            
            status = job.get("status")
            if status == "completed":
                material_efficiency[material]["completed_jobs"] += 1
                
                # Extract waste percentage from results
                results = job.get("results", {})
                if isinstance(results, dict):
                    waste = results.get("waste_percentage", 0)
                    if waste > 0:
                        material_efficiency[material]["total_waste_percentage"] += waste
                        material_efficiency[material]["waste_samples"] += 1
            
            elif status == "failed":
                material_efficiency[material]["failed_jobs"] += 1
        
        # Calculate final metrics
        result = {}
        for material, stats in material_efficiency.items():
            total_jobs = stats["total_jobs"]
            completed = stats["completed_jobs"]
            waste_samples = stats["waste_samples"]
            
            result[material] = {
                "total_jobs": total_jobs,
                "completed_jobs": completed,
                "failed_jobs": stats["failed_jobs"],
                "success_rate": (completed / total_jobs * 100) if total_jobs > 0 else 0,
                "avg_waste_percentage": (
                    stats["total_waste_percentage"] / waste_samples
                ) if waste_samples > 0 else 0,
                "efficiency_score": (
                    100 - (stats["total_waste_percentage"] / waste_samples)
                ) if waste_samples > 0 else 0
            }
        
        return {
            "by_material": result,
            "total_materials": len(result)
        }
    
    def get_dimensional_analysis(self) -> Dict[str, Any]:
        """
        Analyze strip dimensions across all families.
        
        Returns:
            Width and thickness ranges, common sizes
        """
        families = self.stores.strip_families.get_all()
        
        widths = []
        thicknesses = []
        
        for family in families:
            width = family.get("strip_width_mm", 0)
            thickness = family.get("strip_thickness_mm", 0)
            
            if width > 0:
                widths.append(width)
            if thickness > 0:
                thicknesses.append(thickness)
        
        # Find most common sizes (within 0.1mm tolerance)
        def find_common_sizes(values, tolerance=0.1):
            if not values:
                return []
            
            sorted_vals = sorted(values)
            groups = []
            current_group = [sorted_vals[0]]
            
            for val in sorted_vals[1:]:
                if abs(val - current_group[-1]) <= tolerance:
                    current_group.append(val)
                else:
                    groups.append(current_group)
                    current_group = [val]
            
            groups.append(current_group)
            
            # Return groups sorted by size
            return [
                {
                    "size": sum(g) / len(g),  # Average
                    "count": len(g),
                    "percentage": len(g) / len(values) * 100
                }
                for g in sorted(groups, key=len, reverse=True)
            ]
        
        return {
            "width": {  # Test expects "width" field
                "min": min(widths) if widths else 0,
                "max": max(widths) if widths else 0,
                "avg": sum(widths) / len(widths) if widths else 0,
                "common_sizes": find_common_sizes(widths)[:5]
            },
            "width_mm": {
                "min": min(widths) if widths else 0,
                "max": max(widths) if widths else 0,
                "avg": sum(widths) / len(widths) if widths else 0,
                "common_sizes": find_common_sizes(widths)[:5]  # Top 5
            },
            "thickness_mm": {
                "min": min(thicknesses) if thicknesses else 0,
                "max": max(thicknesses) if thicknesses else 0,
                "avg": sum(thicknesses) / len(thicknesses) if thicknesses else 0,
                "common_sizes": find_common_sizes(thicknesses)[:5]
            },
            "total_families": len(families)
        }
    
    def get_supplier_analytics(self) -> Dict[str, Any]:
        """
        Analyze supplier patterns from metadata.
        
        Returns:
            Supplier distribution and quality metrics
        """
        families = self.stores.strip_families.get_all()
        joblogs = self.stores.joblogs.get_all()
        
        # Map family_id to supplier
        family_suppliers = {}
        for family in families:
            metadata = family.get("metadata", {})
            if isinstance(metadata, dict):
                supplier = metadata.get("supplier", "Unknown")
                family_suppliers[family["id"]] = supplier
        
        # Count families and jobs per supplier
        supplier_stats = defaultdict(lambda: {
            "family_count": 0,
            "job_count": 0,
            "completed_jobs": 0,
            "failed_jobs": 0
        })
        
        for family in families:
            metadata = family.get("metadata", {})
            if isinstance(metadata, dict):
                supplier = metadata.get("supplier", "Unknown")
                supplier_stats[supplier]["family_count"] += 1
        
        for job in joblogs:
            family_id = job.get("strip_family_id")
            if family_id in family_suppliers:
                supplier = family_suppliers[family_id]
                supplier_stats[supplier]["job_count"] += 1
                
                status = job.get("status")
                if status == "completed":
                    supplier_stats[supplier]["completed_jobs"] += 1
                elif status == "failed":
                    supplier_stats[supplier]["failed_jobs"] += 1
        
        # Calculate quality scores
        result = []
        for supplier, stats in supplier_stats.items():
            job_count = stats["job_count"]
            completed = stats["completed_jobs"]
            
            result.append({
                "supplier": supplier,
                "family_count": stats["family_count"],
                "job_count": job_count,
                "completed_jobs": completed,
                "failed_jobs": stats["failed_jobs"],
                "success_rate": (completed / job_count * 100) if job_count > 0 else 0
            })
        
        # Sort by success rate
        result.sort(key=lambda x: x["success_rate"], reverse=True)
        
        return {
            "suppliers": result,
            "total_suppliers": len(result)
        }
    
    def get_material_inventory_status(self) -> Dict[str, Any]:
        """
        Summarize current material inventory.
        
        Returns:
            Total strips, total length, materials available
        """
        families = self.stores.strip_families.get_all()
        
        total_strips = 0
        total_length_mm = 0
        materials_available = set()
        
        for family in families:
            strips = family.get("strips", [])
            total_strips += len(strips)
            
            for strip in strips:
                if isinstance(strip, dict):
                    length = strip.get("length_mm", 0)
                    total_length_mm += length
            
            material = family.get("material_type")
            if material:
                materials_available.add(material)
        
        return {
            "total_strip_families": len(families),
            "total_strips": total_strips,
            "total_length_mm": total_length_mm,
            "total_length_meters": total_length_mm / 1000,
            "materials_available": sorted(list(materials_available)),
            "material_count": len(materials_available)
        }


def get_material_analytics() -> MaterialAnalytics:
    """
    Get singleton material analytics instance.
    
    Returns:
        MaterialAnalytics engine
    """
    return MaterialAnalytics()
