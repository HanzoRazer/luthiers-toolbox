"""
CP-S57 — Saw G-Code API Router

FastAPI router for saw-based G-code generation endpoints.
Provides REST API for generating CNC programs for slice, batch, and contour operations.

Endpoints:
- POST /saw_gcode/generate - Generate G-code from toolpath specification

Usage:
```python
# In main.py
from routers import saw_gcode_router

app.include_router(saw_gcode_router.router)
```

Example Request:
```bash
curl -X POST http://localhost:8000/saw_gcode/generate \
  -H "Content-Type: application/json" \
  -d '{
    "op_type": "slice",
    "toolpaths": [{"points": [[0,0], [100,0]], "is_closed": false}],
    "total_depth_mm": 3.0,
    "doc_per_pass_mm": 1.0,
    "feed_ipm": 60,
    "plunge_ipm": 20
  }'
```
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

try:
    # FastAPI application import (normal deployment)
    from ..cam_core.gcode.gcode_models import SawGCodeRequest, SawGCodeResult
    from ..cam_core.gcode.saw_gcode_generator import generate_saw_gcode
except ImportError:
    # Direct testing import
    from cam_core.gcode.gcode_models import SawGCodeRequest, SawGCodeResult
    from cam_core.gcode.saw_gcode_generator import generate_saw_gcode

router = APIRouter(prefix="/saw_gcode", tags=["saw_gcode"])


@router.post("/generate", response_model=SawGCodeResult)
def generate_saw_gcode_api(req: SawGCodeRequest) -> SawGCodeResult:
    """
    Generate G-code for saw-based CNC operations.
    
    Supports three operation types:
    - **slice**: Single straight cut (e.g., ripping board)
    - **batch**: Multiple parallel cuts (e.g., veneer slicing)
    - **contour**: Arbitrary 2D shapes (e.g., curved rosette channel)
    
    Process:
    1. Validates input geometry and parameters
    2. Plans multi-pass depth strategy based on DOC
    3. Generates safe entry/exit moves (rapid → plunge → cut → retract)
    4. Converts feed rates to machine units (IPM → mm/min)
    5. Returns complete G-code program with statistics
    
    Args:
        req: Complete G-code generation request (see SawGCodeRequest model)
    
    Returns:
        SawGCodeResult with:
        - gcode: Complete CNC program text
        - op_type: Operation type (echoed)
        - depth_passes: Computed Z-levels for multi-pass
        - total_length_mm: Total cutting distance
    
    Raises:
        HTTPException 400: Invalid input (e.g., closed_paths_only violated)
        HTTPException 500: G-code generation failed
    
    Example:
        **Slice Operation** (single straight cut):
        ```json
        {
          "op_type": "slice",
          "toolpaths": [{"points": [[0,0], [100,0]], "is_closed": false}],
          "total_depth_mm": 3.0,
          "doc_per_pass_mm": 1.0,
          "feed_ipm": 60,
          "plunge_ipm": 20,
          "safe_z_mm": 5.0
        }
        ```
        
        **Batch Operation** (3 parallel cuts):
        ```json
        {
          "op_type": "batch",
          "toolpaths": [
            {"points": [[0,0], [100,0]], "is_closed": false},
            {"points": [[0,10], [100,10]], "is_closed": false},
            {"points": [[0,20], [100,20]], "is_closed": false}
          ],
          "total_depth_mm": 2.5,
          "doc_per_pass_mm": 1.25,
          "feed_ipm": 50,
          "plunge_ipm": 15
        }
        ```
        
        **Contour Operation** (closed shape):
        ```json
        {
          "op_type": "contour",
          "toolpaths": [{"points": [[0,0], [50,0], [50,30], [0,30]], "is_closed": true}],
          "total_depth_mm": 5.0,
          "doc_per_pass_mm": 1.5,
          "feed_ipm": 40,
          "plunge_ipm": 10,
          "closed_paths_only": true
        }
        ```
    """
    try:
        result = generate_saw_gcode(req)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(
            status_code=500,
            detail=f"G-code generation failed: {str(e)}"
        )
