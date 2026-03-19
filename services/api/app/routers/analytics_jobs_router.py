"""Analytics Jobs Router - Job success, duration, throughput, and failure metrics.

Provides:
- GET /analytics/jobs/success-trends - Success rate trends over time
- GET /analytics/jobs/duration - Duration analysis by job type
- GET /analytics/jobs/status - Job status distribution
- GET /analytics/jobs/throughput - Throughput metrics (jobs per day/week/month)
- GET /analytics/jobs/failures - Failure analysis
- GET /analytics/jobs/types - Job type distribution
- GET /analytics/jobs/recent - Recent jobs summary

Total: 7 routes for job analytics.

LANE: UTILITY
"""

import logging

from fastapi import APIRouter, HTTPException, Query

from ..analytics.job_analytics import get_job_analytics

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analytics", "jobs"])


@router.get("/analytics/jobs/success-trends")
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
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except (KeyError, ValueError, TypeError, ZeroDivisionError, OSError) as e:
        logger.error(f"Error getting success trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/jobs/duration")
def get_job_duration_analysis():
    """
    Get duration analysis by job type.

    Returns:
        Min, max, avg, median duration per job type
    """
    try:
        analytics = get_job_analytics()
        return analytics.get_duration_analysis_by_job_type()
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except (KeyError, ValueError, TypeError, ZeroDivisionError, OSError) as e:
        logger.error(f"Error getting duration analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/jobs/status")
def get_job_status_distribution():
    """
    Get distribution of job statuses.

    Returns:
        Count and percentage per status
    """
    try:
        analytics = get_job_analytics()
        return analytics.get_status_distribution()
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except (KeyError, ValueError, TypeError, ZeroDivisionError, OSError) as e:
        logger.error(f"Error getting status distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/jobs/throughput")
def get_job_throughput_metrics():
    """
    Get throughput metrics (jobs per day/week/month).

    Returns:
        Average jobs per time period, peak days
    """
    try:
        analytics = get_job_analytics()
        return analytics.get_throughput_metrics()
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except (KeyError, ValueError, TypeError, ZeroDivisionError, OSError) as e:
        logger.error(f"Error getting throughput metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/jobs/failures")
def get_job_failure_analysis():
    """
    Get failure analysis for failed jobs.

    Returns:
        Failure rates by job type, pattern, material
    """
    try:
        analytics = get_job_analytics()
        return analytics.get_failure_analysis()
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except (KeyError, ValueError, TypeError, ZeroDivisionError, OSError) as e:
        logger.error(f"Error getting failure analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/jobs/types")
def get_job_type_distribution():
    """
    Get distribution of job types.

    Returns:
        Count and percentage per job type
    """
    try:
        analytics = get_job_analytics()
        return analytics.get_job_type_distribution()
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except (KeyError, ValueError, TypeError, ZeroDivisionError, OSError) as e:
        logger.error(f"Error getting job type distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/jobs/recent")
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
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except (KeyError, ValueError, TypeError, ZeroDivisionError, OSError) as e:
        logger.error(f"Error getting recent jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ["router"]
