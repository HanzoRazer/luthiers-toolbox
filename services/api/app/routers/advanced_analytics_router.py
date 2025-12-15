"""
Advanced Analytics API router (N9.1)

Endpoints:
- GET /api/analytics/advanced/correlation?x=...&y=...
- GET /api/analytics/advanced/anomalies/durations?z=3.0
- GET /api/analytics/advanced/anomalies/success?z=3.0
- POST /api/analytics/advanced/predict (JSON body)
"""
from fastapi import APIRouter, HTTPException, Body
from typing import Optional
import logging

from ..analytics.advanced_analytics import get_advanced_analytics

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/advanced/correlation")
def correlation(x: Optional[str] = None, y: Optional[str] = None):
    if not x or not y:
        raise HTTPException(status_code=400, detail="Query parameters 'x' and 'y' are required (e.g. job.duration_seconds, pattern.complexity_score)")
    try:
        analytics = get_advanced_analytics()
        return analytics.pearson_correlation(x, y)
    except Exception as e:
        logger.exception("correlation error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/advanced/anomalies/durations")
def duration_anomalies(z: Optional[float] = 3.0):
    try:
        analytics = get_advanced_analytics()
        return analytics.detect_duration_anomalies(z_thresh=float(z))
    except Exception as e:
        logger.exception("duration anomaly error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/advanced/anomalies/success")
def success_anomalies(z: Optional[float] = 3.0, window_days: Optional[int] = 30):
    try:
        analytics = get_advanced_analytics()
        return analytics.detect_success_rate_anomalies(window_days=int(window_days), z_thresh=float(z))
    except Exception as e:
        logger.exception("success anomaly error")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/advanced/predict")
def predict_failure(body: dict = Body(...)):
    try:
        analytics = get_advanced_analytics()
        return analytics.predict_failure_risk(body)
    except Exception as e:
        logger.exception("predict error")
        raise HTTPException(status_code=500, detail=str(e))
