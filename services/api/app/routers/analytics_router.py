"""
Analytics API Router (N9.0)

REST endpoints for pattern, material, and job analytics.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from .._experimental.analytics.pattern_analytics import get_pattern_analytics
from .._experimental.analytics.material_analytics import get_material_analytics
from .._experimental.analytics.job_analytics import get_job_analytics

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# PATTERN ANALYTICS ENDPOINTS
# ============================================================================

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
    except Exception as e:
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
    except Exception as e:
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
    except Exception as e:
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
    except Exception as e:
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
    except Exception as e:
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
            raise HTTPException(status_code=404, detail=f"Pattern {pattern_id} not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pattern details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MATERIAL ANALYTICS ENDPOINTS
# ============================================================================

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
    except Exception as e:
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
    except Exception as e:
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
    except Exception as e:
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
    except Exception as e:
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
    except Exception as e:
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
    except Exception as e:
        logger.error(f"Error getting inventory status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# JOB ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/jobs/success-trends")
def get_job_success_trends(days: int = Query(30, ge=1, le=365)):
    """
    Get success rate trends over time.
    
    Args:
        days: Number of days to analyze (default 30)
        
    Returns:
        Daily success rates and overall trend
    """
    try:
        analytics = get_job_analytics()
        return analytics.get_success_rate_trends(days=days)
    except Exception as e:
        logger.error(f"Error getting success trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/duration")
def get_job_duration_analysis():
    """
    Get duration analysis by job type.
    
    Returns:
        Min, max, avg, median duration per job type
    """
    try:
        analytics = get_job_analytics()
        return analytics.get_duration_analysis_by_job_type()
    except Exception as e:
        logger.error(f"Error getting duration analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/status")
def get_job_status_distribution():
    """
    Get distribution of job statuses.
    
    Returns:
        Count and percentage per status
    """
    try:
        analytics = get_job_analytics()
        return analytics.get_status_distribution()
    except Exception as e:
        logger.error(f"Error getting status distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/throughput")
def get_job_throughput_metrics():
    """
    Get throughput metrics (jobs per day/week/month).
    
    Returns:
        Average jobs per time period, peak days
    """
    try:
        analytics = get_job_analytics()
        return analytics.get_throughput_metrics()
    except Exception as e:
        logger.error(f"Error getting throughput metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/failures")
def get_job_failure_analysis():
    """
    Get failure analysis for failed jobs.
    
    Returns:
        Failure rates by job type, pattern, material
    """
    try:
        analytics = get_job_analytics()
        return analytics.get_failure_analysis()
    except Exception as e:
        logger.error(f"Error getting failure analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/types")
def get_job_type_distribution():
    """
    Get distribution of job types.
    
    Returns:
        Count and percentage per job type
    """
    try:
        analytics = get_job_analytics()
        return analytics.get_job_type_distribution()
    except Exception as e:
        logger.error(f"Error getting job type distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/recent")
def get_recent_jobs(limit: int = Query(10, ge=1, le=100)):
    """
    Get summary of recent jobs.
    
    Args:
        limit: Max jobs to return (default 10)
        
    Returns:
        Recent jobs with key metrics
    """
    try:
        analytics = get_job_analytics()
        return analytics.get_recent_job_summary(limit=limit)
    except Exception as e:
        logger.error(f"Error getting recent jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
