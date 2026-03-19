"""Analytics Advanced Router - Correlation, anomaly detection, and prediction endpoints.

Provides:
- GET /advanced/correlation - Pearson correlation between metrics
- GET /advanced/anomalies/durations - Duration anomaly detection (z-score)
- GET /advanced/anomalies/success - Success rate anomaly detection
- POST /advanced/predict - Failure risk prediction

Total: 4 routes for advanced analytics.

LANE: UTILITY
"""

import logging
from typing import Optional

from fastapi import APIRouter, Body, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analytics", "advanced"])


@router.get("/advanced/correlation")
def correlation(x: Optional[str] = None, y: Optional[str] = None):
    """Get Pearson correlation between two metrics."""
    from ..analytics.advanced_analytics import get_advanced_analytics

    if not x or not y:
        raise HTTPException(
            status_code=400,
            detail="Query parameters 'x' and 'y' are required (e.g. job.duration_seconds, pattern.complexity_score)",
        )
    try:
        analytics = get_advanced_analytics()
        return analytics.pearson_correlation(x, y)
    except HTTPException:
        raise
    except (ValueError, KeyError, ZeroDivisionError, TypeError) as e:
        logger.exception("correlation error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/advanced/anomalies/durations")
def duration_anomalies(z: Optional[float] = 3.0):
    """Detect duration anomalies using z-score threshold."""
    from ..analytics.advanced_analytics import get_advanced_analytics

    try:
        analytics = get_advanced_analytics()
        return analytics.detect_duration_anomalies(z_thresh=float(z))
    except HTTPException:
        raise
    except (ValueError, KeyError, ZeroDivisionError, TypeError) as e:
        logger.exception("duration anomaly error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/advanced/anomalies/success")
def success_anomalies(z: Optional[float] = 3.0, window_days: Optional[int] = 30):
    """Detect success rate anomalies."""
    from ..analytics.advanced_analytics import get_advanced_analytics

    try:
        analytics = get_advanced_analytics()
        return analytics.detect_success_rate_anomalies(
            window_days=int(window_days), z_thresh=float(z)
        )
    except HTTPException:
        raise
    except (ValueError, KeyError, ZeroDivisionError, TypeError) as e:
        logger.exception("success anomaly error")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/advanced/predict")
def predict_failure(body: dict = Body(...)):
    """Predict failure risk based on input parameters."""
    from ..analytics.advanced_analytics import get_advanced_analytics

    try:
        analytics = get_advanced_analytics()
        return analytics.predict_failure_risk(body)
    except HTTPException:
        raise
    except (ValueError, KeyError, ZeroDivisionError, TypeError) as e:
        logger.exception("predict error")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ["router"]
