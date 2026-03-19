"""Analytics Patterns Router - Pattern complexity, geometry, and popularity metrics.

Provides:
- GET /patterns/complexity - Complexity score distribution
- GET /patterns/rings - Ring count statistics
- GET /patterns/geometry - Geometry metrics (radius, segments, density)
- GET /patterns/families - Strip family usage
- GET /patterns/popularity - Most popular patterns by job usage
- GET /patterns/{pattern_id}/details - Detailed analytics for a pattern

Total: 6 routes for pattern analytics.

LANE: UTILITY
"""

import logging

from fastapi import APIRouter, HTTPException, Query

from ..analytics.pattern_analytics import get_pattern_analytics

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analytics", "patterns"])


@router.get("/patterns/complexity")
def get_pattern_complexity_distribution():
    """
    Get distribution of patterns by complexity score.

    Categorizes patterns as Simple, Medium, Complex, or Expert.

    Returns:
        JSON with counts and percentages per category
    """
    try:
        analytics = get_pattern_analytics()
        return analytics.get_complexity_distribution()
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except (KeyError, ValueError, TypeError, ZeroDivisionError, OSError) as e:
        logger.error(f"Error getting complexity distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns/rings")
def get_pattern_ring_statistics():
    """
    Get ring count statistics across all patterns.

    Returns:
        Min, max, avg, median ring counts with distribution
    """
    try:
        analytics = get_pattern_analytics()
        return analytics.get_ring_statistics()
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except (KeyError, ValueError, TypeError, ZeroDivisionError, OSError) as e:
        logger.error(f"Error getting ring statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns/geometry")
def get_pattern_geometry_metrics():
    """
    Get geometry metrics (radius, segments, density).

    Returns:
        Radius ranges, segment counts, ring density analysis
    """
    try:
        analytics = get_pattern_analytics()
        return analytics.get_geometry_metrics()
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except (KeyError, ValueError, TypeError, ZeroDivisionError, OSError) as e:
        logger.error(f"Error getting geometry metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns/families")
def get_pattern_strip_family_usage():
    """
    Get strip family usage across patterns.

    Returns:
        Which material families are used most frequently
    """
    try:
        analytics = get_pattern_analytics()
        return analytics.get_strip_family_usage()
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except (KeyError, ValueError, TypeError, ZeroDivisionError, OSError) as e:
        logger.error(f"Error getting strip family usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns/popularity")
def get_pattern_popularity(limit: int = Query(10, ge=1, le=100)):
    """
    Get most popular patterns by job usage.

    Args:
        limit: Max patterns to return (default 10)

    Returns:
        Top patterns ranked by job count
    """
    try:
        analytics = get_pattern_analytics()
        return analytics.get_pattern_popularity(limit=limit)
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except (KeyError, ValueError, TypeError, ZeroDivisionError, OSError) as e:
        logger.error(f"Error getting pattern popularity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns/{pattern_id}/details")
def get_pattern_details_with_analytics(pattern_id: str):
    """
    Get detailed analytics for a specific pattern.

    Args:
        pattern_id: Pattern UUID

    Returns:
        Pattern with complexity, usage count, success rate, avg duration
    """
    try:
        analytics = get_pattern_analytics()
        result = analytics.get_pattern_details_with_analytics(pattern_id)

        if not result:
            raise HTTPException(
                status_code=404, detail=f"Pattern {pattern_id} not found"
            )

        return result
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except (KeyError, ValueError, TypeError, ZeroDivisionError, OSError) as e:
        logger.error(f"Error getting pattern details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ["router"]
