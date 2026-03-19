"""Analytics Materials Router - Material distribution, consumption, and efficiency metrics.

Provides:
- GET /materials/distribution - Material type distribution
- GET /materials/consumption - Strip consumption by material
- GET /materials/efficiency - Material efficiency metrics
- GET /materials/dimensions - Dimensional analysis (width, thickness)
- GET /materials/suppliers - Supplier quality metrics
- GET /materials/inventory - Current inventory status

Total: 6 routes for material analytics.

LANE: UTILITY
"""

import logging

from fastapi import APIRouter, HTTPException

from ..analytics.material_analytics import get_material_analytics

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analytics", "materials"])


@router.get("/materials/distribution")
def get_material_type_distribution():
    """
    Get distribution of material types.

    Returns:
        Count and percentage per material type
    """
    try:
        analytics = get_material_analytics()
        return analytics.get_material_type_distribution()
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except (KeyError, ValueError, TypeError, ZeroDivisionError, OSError) as e:
        logger.error(f"Error getting material distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/materials/consumption")
def get_material_consumption():
    """
    Get strip consumption metrics by material.

    Returns:
        Total strips, length, dimensions per material
    """
    try:
        analytics = get_material_analytics()
        return analytics.get_strip_consumption_by_material()
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except (KeyError, ValueError, TypeError, ZeroDivisionError, OSError) as e:
        logger.error(f"Error getting material consumption: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/materials/efficiency")
def get_material_efficiency():
    """
    Get material efficiency metrics.

    Returns:
        Waste percentage, success rates, efficiency scores per material
    """
    try:
        analytics = get_material_analytics()
        return analytics.get_material_efficiency()
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except (KeyError, ValueError, TypeError, ZeroDivisionError, OSError) as e:
        logger.error(f"Error getting material efficiency: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/materials/dimensions")
def get_material_dimensional_analysis():
    """
    Get dimensional analysis (width, thickness ranges).

    Returns:
        Min/max/avg/median dimensions, common sizes
    """
    try:
        analytics = get_material_analytics()
        return analytics.get_dimensional_analysis()
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except (KeyError, ValueError, TypeError, ZeroDivisionError, OSError) as e:
        logger.error(f"Error getting dimensional analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/materials/suppliers")
def get_material_supplier_analytics():
    """
    Get supplier quality metrics from metadata.

    Returns:
        Supplier performance with success rates
    """
    try:
        analytics = get_material_analytics()
        return analytics.get_supplier_analytics()
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except (KeyError, ValueError, TypeError, ZeroDivisionError, OSError) as e:
        logger.error(f"Error getting supplier analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/materials/inventory")
def get_material_inventory_status():
    """
    Get current inventory status summary.

    Returns:
        Total strips, length, material types in inventory
    """
    try:
        analytics = get_material_analytics()
        return analytics.get_material_inventory_status()
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except (KeyError, ValueError, TypeError, ZeroDivisionError, OSError) as e:
        logger.error(f"Error getting inventory status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ["router"]
