"""
Dormant CAM-Core router.

Do NOT register this in main.py yet. Subrouters will be added in CP-S40+.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/cam-core", tags=["cam-core"])
