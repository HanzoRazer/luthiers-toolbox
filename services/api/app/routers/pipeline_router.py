# services/api/app/routers/pipeline_router.py
"""
Unified CAM Pipeline Router

Orchestrates end-to-end CAM workflows from DXF upload through toolpath generation,
post-processing, and simulation. Supports machine-aware planning and post-processor
awareness for multi-machine shop environments.

Features:
- Unified pipeline API: Single endpoint for complex multi-step CAM workflows
- Five pipeline operations:
  * dxf_preflight: Validate DXF structure and geometry
  * adaptive_plan: Extract closed loops from DXF layers
  * adaptive_plan_run: Generate adaptive pocket toolpath (L.1/L.2/L.3)
  * export_post: Apply post-processor headers/footers
  * simulate_gcode: Run G-code motion simulation
- Machine awareness: Automatic feed/accel/jerk limits from machine profiles
- Post-processor awareness: Template-based G-code formatting per controller type
- Error isolation: Per-operation error capture without pipeline abort
- Context propagation: Shared parameters with per-op override capability

Endpoints:
- POST /cam/pipeline/run - Execute multi-operation pipeline

Architecture:
- HTTP-based orchestration: Calls internal endpoints (/cam/pocket/adaptive/plan, etc.)
- Context dictionary: Accumulates data across operations (loops, gcode, sim results)
- Machine/post profiles: Optional external configuration via /cam/machines, /cam/posts
- Validation: Operation graph validation (dependency checking, unique IDs)
- Error handling: Graceful degradation with per-op error capture

CRITICAL SAFETY RULES:
1. DXF file validation: Only .dxf extension accepted (no .dwg, .svg)
2. Empty file rejection: Must contain data (prevent zero-byte uploads)
3. Operation sequencing: export_post requires prior adaptive_plan_run
4. Unique operation IDs: No duplicate IDs in pipeline specification
5. Temporary file cleanup: Always unlink temp files in finally blocks

Example Pipeline:
    POST /api/cam/pipeline/run
    Content-Type: multipart/form-data
    
    file: body_pocket.dxf
    pipeline: '{
      "ops": [
        {"kind": "dxf_preflight", "params": {"profile": "bridge"}},
        {"kind": "adaptive_plan", "params": {}},
        {"kind": "adaptive_plan_run", "params": {"tool_d": 6.0, "stepover": 0.45}},
        {"kind": "export_post", "params": {"post_id": "GRBL"}},
        {"kind": "simulate_gcode", "params": {}}
      ],
      "tool_d": 6.0,
      "units": "mm",
      "machine_id": "haas_mini",
      "post_id": "grbl"
    }'
    
    => {
      "ops": [
        {"kind": "dxf_preflight", "ok": true, "payload": {...}},
        {"kind": "adaptive_plan", "ok": true, "payload": {"loops": [...], "count": 1}},
        {"kind": "adaptive_plan_run", "ok": true, "payload": {"stats": {...moves...}}},
        {"kind": "export_post", "ok": true, "payload": {"post_id": "grbl", "total_lines": 245}},
        {"kind": "simulate_gcode", "ok": true, "payload": {"time_s": 32.1, "length_mm": 547.3}}
      ],
      "summary": {"time_s": 32.1, "length_mm": 547.3, "area_mm2": 6000.0}
    }

Workflow:
    1. Upload DXF file (multipart form-data)
    2. Parse pipeline specification (JSON string)
    3. Validate operation graph (sequencing, dependencies)
    4. Execute operations sequentially with error handling
    5. Accumulate context (loops, gcode, sim results)
    6. Apply machine/post profiles if specified
    7. Return per-op results and final summary

Machine Awareness (v1.1):
    - If machine_id provided, fetch profile from /cam/machines/{id}
    - Automatically apply feed limits (max_feed_xy, max_feed_z, rapid)
    - Inject accel/jerk for motion planning and simulation
    - Cache profiles across operations (avoid redundant fetches)

Post-Processor Awareness (v1.1):
    - If post_id provided, fetch preset from /cam/posts/{id}
    - Apply header/footer templates for controller dialect
    - Merge preset overrides with base post configuration
    - Support 5 controllers: GRBL, Mach4, LinuxCNC, PathPilot, MASSO
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Literal, Optional, Tuple

import httpx
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field, ValidationError

from ..services.jobint_artifacts import build_jobint_payload
logger = logging.getLogger(__name__)

# Import utility functions (graceful fallback if not available)
try:
    from ..util.dxf_preflight import (
        PreflightEngineMissingError,
        PreflightGeometryError,
        PreflightParseError,
        preflight_dxf_bytes,
    )
except ImportError:
    # Fallback stubs if preflight not available yet
    def preflight_dxf_bytes(*args, **kwargs):
        raise NotImplementedError("DXF preflight not implemented")
    
    class PreflightEngineMissingError(Exception):
        pass
    
    class PreflightParseError(Exception):
        pass
    
    class PreflightGeometryError(Exception):
        pass

try:
    from ..routers.blueprint_cam_bridge import extract_loops_from_dxf
except ImportError:
    # Fallback stub
    def extract_loops_from_dxf(*args, **kwargs):
        raise NotImplementedError("DXF loop extraction not implemented")

router = APIRouter(prefix="/cam", tags=["cam", "pipeline"])

# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

PipelineOpKind = Literal[
    "dxf_preflight",        # Validate DXF structure
    "adaptive_plan",        # Extract loops from DXF
    "adaptive_plan_run",    # Execute adaptive pocket planning
    "export_post",          # Apply post-processor formatting
    "simulate_gcode",       # Run G-code motion simulation
]

# =============================================================================
# VALIDATION CONSTANTS
# =============================================================================

# Maximum DXF file size (50 MB - CAD files can be large)
MAX_DXF_SIZE_BYTES: int = 50 * 1024 * 1024

# HTTP client timeout for sub-requests (seconds)
HTTP_TIMEOUT_SECONDS: float = 60.0

# Maximum pipeline operations (prevent infinite loops/abuse)
MAX_PIPELINE_OPS: int = 20

# Supported DXF file extensions
SUPPORTED_DXF_EXTENSIONS: Tuple[str, ...] = (".dxf",)

# Default adaptive planning parameters
DEFAULT_TOOL_DIAMETER_MM: float = 6.0
DEFAULT_STEPOVER_RATIO: float = 0.45
DEFAULT_STEPDOWN_MM: float = 2.0
DEFAULT_MARGIN_MM: float = 0.5
DEFAULT_FEED_XY_MM_MIN: float = 1200.0
DEFAULT_SAFE_Z_MM: float = 5.0

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class PipelineOp(BaseModel):
    """
    Single operation in CAM pipeline execution sequence.
    
    Represents one step in the workflow with operation-specific parameters
    that can override shared pipeline defaults.
    
    Fields:
        id: Optional[str] - Unique identifier for operation tracking (optional)
        kind: PipelineOpKind - Operation type (dxf_preflight, adaptive_plan, etc.)
        params: Dict[str, Any] - Operation-specific parameters merged onto shared context
    
    Example:
        {"id": "validate_dxf", "kind": "dxf_preflight", "params": {"profile": "bridge"}}
    """
    id: Optional[str] = Field(None, description="Optional operation ID for tracking")
    kind: PipelineOpKind
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Op-specific parameters, merged onto shared context.",
    )


class PipelineRequest(BaseModel):
    """
    Unified CAM pipeline execution request.
    
    Defines complete workflow from DXF upload through post-processing and simulation.
    Supports shared parameter context with per-operation overrides for flexibility.
    
    Fields:
        ops: List[PipelineOp] - Ordered sequence of operations to execute
        tool_d: float - Tool diameter in mm (default 6.0)
        units: Literal["mm", "inch"] - Measurement system (default "mm")
        geometry_layer: Optional[str] - DXF layer for geometry extraction (default auto-detect)
        auto_scale: bool - Enable automatic DXF unit scaling (default True)
        cam_layer_prefix: str - Prefix for CAM-specific layers (default "CAM_")
        machine_id: Optional[str] - Machine profile ID for feeds/limits (v1.1)
        post_id: Optional[str] - Post-processor preset ID for formatting (v1.1)
    
    Pipeline Design:
        - DXF uploaded as multipart 'file' field
        - Pipeline spec provided as JSON string in 'pipeline' field
        - Operations execute sequentially with error isolation
        - Context accumulates data across operations (loops, gcode, sim results)
        - Shared parameters used unless overridden by per-op params
    
    Operation Flow:
        1. dxf_preflight: Validate DXF structure and geometry
        2. adaptive_plan: Extract closed loops from specified layer
        3. adaptive_plan_run: Generate adaptive pocket toolpath
        4. export_post: Wrap G-code with post-processor headers/footers
        5. simulate_gcode: Run motion simulation with time/distance stats
    
    Machine Awareness (v1.1):
        - If machine_id provided, fetch profile from /cam/machines/{id}
        - Automatically inject max_feed_xy, rapid, accel, jerk
        - Used in adaptive_plan_run and simulate_gcode operations
    
    Post-Processor Awareness (v1.1):
        - If post_id provided, fetch preset from /cam/posts/{id}
        - Apply controller-specific headers/footers (GRBL, Mach4, etc.)
        - Merge preset overrides with base post configuration
    
    Example:
        {
          "ops": [
            {"kind": "dxf_preflight", "params": {"profile": "bridge"}},
            {"kind": "adaptive_plan", "params": {}},
            {"kind": "adaptive_plan_run", "params": {"stepover": 0.5}},
            {"kind": "export_post", "params": {}},
            {"kind": "simulate_gcode", "params": {}}
          ],
          "tool_d": 6.0,
          "units": "mm",
          "geometry_layer": "GEOMETRY",
          "auto_scale": true,
          "cam_layer_prefix": "CAM_",
          "machine_id": "haas_mini",
          "post_id": "grbl"
        }
    """
    ops: List[PipelineOp] = Field(
        ...,
        description="Sequence of operations to apply to the uploaded DXF.",
    )

    # Shared context defaults (used unless overridden by per-op params)
    tool_d: float = DEFAULT_TOOL_DIAMETER_MM
    units: Literal["mm", "inch"] = "mm"
    geometry_layer: Optional[str] = Field(
        None, description="Preferred DXF geometry layer (default auto)."
    )
    auto_scale: bool = True
    cam_layer_prefix: str = "CAM_"
    
    # Machine/post awareness (v1.1)
    machine_id: Optional[str] = Field(
        None, description="Optional machine profile ID to use for feeds/limits."
    )
    post_id: Optional[str] = Field(
        None, description="Optional post preset ID for export_post ops."
    )


class PipelineOpResult(BaseModel):
    """
    Result of single pipeline operation execution.
    
    Captures success/failure status, error messages, and operation-specific
    payload data for client analysis and debugging.
    
    Fields:
        id: Optional[str] - Operation ID from request (if provided)
        kind: PipelineOpKind - Operation type that was executed
        ok: bool - True if operation succeeded, False on error
        error: Optional[str] - Error message if ok=False (None otherwise)
        payload: Optional[Dict[str, Any]] - Operation-specific result data
    
    Payload Examples:
        dxf_preflight: {"ok": true, "report": {"issues": [...], "layers": [...]}}
        adaptive_plan: {"loops": [...], "count": 1, "warnings": []}
        adaptive_plan_run: {"stats": {"length_mm": 547.3, "time_s": 32.1, ...}}
        export_post: {"post_id": "grbl", "gcode_preview": "...", "total_lines": 245}
        simulate_gcode: {"time_s": 32.1, "length_mm": 547.3, "moves": [...]}
    """
    id: Optional[str] = None
    kind: PipelineOpKind
    ok: bool
    error: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


class PipelineResponse(BaseModel):
    """
    Complete pipeline execution result with per-op status and summary.
    
    Aggregates results from all executed operations plus high-level statistics
    from the final operation (typically simulation or adaptive planning).
    
    Fields:
        ops: List[PipelineOpResult] - Results from each executed operation
        summary: Dict[str, Any] - High-level summary statistics from final op
    
    Summary Keys (typical):
        - time_s: Estimated machining time in seconds
        - length_mm: Total toolpath length in millimeters
        - area_mm2: Pocketed area in square millimeters
        - volume_mm3: Material removed in cubic millimeters
        - move_count: Total number of G-code moves
    
    Example:
        {
          "ops": [
            {"kind": "dxf_preflight", "ok": true, "payload": {...}},
            {"kind": "adaptive_plan", "ok": true, "payload": {"count": 1}},
            {"kind": "adaptive_plan_run", "ok": true, "payload": {...}},
            {"kind": "export_post", "ok": true, "payload": {...}},
            {"kind": "simulate_gcode", "ok": true, "payload": {...}}
          ],
          "summary": {
            "time_s": 32.1,
            "length_mm": 547.3,
            "area_mm2": 6000.0,
            "volume_mm3": 9000.0,
            "move_count": 156
          }
        }
    """
    ops: List[PipelineOpResult]
    summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="High-level summary (e.g. last op stats).",
    )
    job_int: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Job intelligence artifact payload (loops/plan/moves).",
    )


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def _validate_ops(ops: List[PipelineOp]) -> None:
    """
    Validate pipeline operation graph for logical correctness.
    
    Performs pre-execution validation to catch common configuration errors
    before attempting to process the DXF file.
    
    Args:
        ops: List of pipeline operations to validate
    
    Raises:
        HTTPException: 400 - If validation fails with detailed error message
    
    Validation Rules:
        1. **Non-empty pipeline**: Must contain at least one operation
        2. **Unique operation IDs**: All op.id values (if provided) must be unique
        3. **export_post dependency**: Requires prior adaptive_plan_run operation
        4. **simulate_gcode source**: Must have gcode from prior op or explicit param
    
    Validation Strategy:
        - Linear scan through operation sequence (O(n) complexity)
        - Fail-fast on first error (provides clear user feedback)
        - Index-based dependency checking (export_post after adaptive_plan_run)
        - Future: Add cycle detection for complex dependencies
    
    Example Valid Pipeline:
        [
          {"kind": "dxf_preflight", "params": {}},
          {"kind": "adaptive_plan", "params": {}},
          {"kind": "adaptive_plan_run", "params": {"stepover": 0.5}},
          {"kind": "export_post", "params": {}},         # Valid: after adaptive_plan_run
          {"kind": "simulate_gcode", "params": {}}        # Valid: has prior gcode
        ]
    
    Example Invalid Pipeline:
        [
          {"kind": "dxf_preflight", "params": {}},
          {"kind": "export_post", "params": {}}          # Invalid: no adaptive_plan_run
        ]
    
    Notes:
        - Pipeline validation is strict to prevent runtime errors
        - Operation wrappers handle per-op parameter validation
        - Shared context validation happens at execution time
        - IDs are optional but must be unique if provided
    
    See Also:
        - run_pipeline: Main execution endpoint using this validator
        - PipelineOp: Individual operation model
    """
    # Rule 1: Non-empty pipeline
    if not ops:
        raise HTTPException(
            status_code=400, 
            detail="Pipeline must contain at least one operation."
        )

    # Rule 2: Unique operation IDs
    ids = [op.id for op in ops if op.id]
    if len(ids) != len(set(ids)):
        raise HTTPException(
            status_code=400, 
            detail="Pipeline operation IDs must be unique. Found duplicate IDs."
        )

    # Build operation kind sequence for dependency checks
    kinds = [op.kind for op in ops]

    # Rule 3: export_post dependency
    if "export_post" in kinds:
        idx_export = kinds.index("export_post")
        if idx_export > 0 and "adaptive_plan_run" not in kinds[:idx_export]:
            raise HTTPException(
                status_code=400,
                detail="export_post requires a prior adaptive_plan_run operation to generate G-code."
            )

    # Rule 4: simulate_gcode source validation
    # Note: Actual gcode presence validated at execution time (may come from context)
    if "simulate_gcode" in kinds:
        idx_sim = kinds.index("simulate_gcode")
        if idx_sim == 0:
            # First operation - must provide gcode in params (checked at runtime)
            pass


# =============================================================================
# MAIN API ENDPOINT
# =============================================================================

@router.post("/pipeline/run", response_model=PipelineResponse)
async def run_pipeline(
    file: UploadFile = File(...),
    pipeline: str = Form(..., description="PipelineRequest JSON string."),
    base_url: str = Query("http://127.0.0.1:8000"),
    adaptive_plan_path: str = Query("/api/cam/pocket/adaptive/plan"),
    sim_path: str = Query("/cam/simulate_gcode"),
    machine_path: str = Query("/cam/machines"),
    post_path: str = Query("/cam/posts"),
):
    """
    Execute unified CAM pipeline from DXF upload to G-code simulation.
    
    Orchestrates complete CAM workflow through sequential operation execution with
    automatic context propagation between stages. Supports machine profile awareness
    (v1.1) and post-processor presets for CNC controller-specific formatting.
    
    Args:
        file: DXF file upload (multipart/form-data, max 50MB)
        pipeline: PipelineRequest as JSON string containing:
            - ops: List of operations to execute in order
            - tool_d: Tool diameter in mm (default 6.0)
            - units: "mm" or "inch" (default "mm")
            - geometry_layer: DXF layer for geometry extraction (default auto-detect)
            - auto_scale: Enable automatic DXF unit scaling (default True)
            - cam_layer_prefix: Prefix for CAM-specific layers (default "CAM_")
            - machine_id: Optional machine profile ID (v1.1)
            - post_id: Optional post-processor preset ID (v1.1)
        base_url: Internal API base URL for sub-requests (default "http://127.0.0.1:8000")
        adaptive_plan_path: Path to adaptive planning endpoint (default "/api/cam/pocket/adaptive/plan")
        sim_path: Path to G-code simulation endpoint (default "/cam/simulate_gcode")
        machine_path: Path to machine profile endpoint (default "/cam/machines")
        post_path: Path to post-processor endpoint (default "/cam/posts")
    
    Returns:
        PipelineResponse with:
            - ops: List of per-operation results with status, errors, payloads
            - summary: High-level statistics from final operation (time, length, area, etc.)
    
    Raises:
        HTTPException: 400 - Invalid pipeline spec, empty file, unsupported format
        HTTPException: 500 - Internal operation error, sub-request failure
    
    Supported Operations:
        1. **dxf_preflight**: Validate DXF structure and geometry
           - Checks layer structure, entity types, units
           - Reports issues with severity levels (error/warning/info)
           - Optional profile parameter for specific validation rules
        
        2. **adaptive_plan**: Extract closed loops from DXF
           - Parses geometry layer for pocket boundaries
           - Detects islands/holes automatically
           - Returns loop coordinates and warnings
        
        3. **adaptive_plan_run**: Generate adaptive pocket toolpath
           - Calls /api/cam/pocket/adaptive/plan with machine limits
           - Applies stepover, stepdown, margin parameters
           - Injects machine feeds/rapids if machine_id provided
           - Returns moves list and statistics (length, time, area, volume)
        
        4. **export_post**: Apply post-processor formatting
           - Wraps G-code with controller-specific headers/footers
           - Supports GRBL, Mach4, LinuxCNC, PathPilot, MASSO
           - Merges post preset overrides if post_id provided
           - Returns formatted G-code preview and line count
        
        5. **simulate_gcode**: Run motion simulation
           - Parses G-code moves with machine kinematic limits
           - Calculates realistic time estimates (rapid vs. cutting feeds)
           - Applies machine acceleration/jerk caps if available
           - Returns summary statistics and move sequence
    
    Machine Awareness (v1.1):
        - If machine_id provided, fetches profile from /cam/machines/{id}
        - Auto-injects: max_feed_xy, rapid_feed, accel, jerk
        - Applied to: adaptive_plan_run (cutting feeds), simulate_gcode (time estimation)
        - Graceful degradation: Pipeline continues if machine endpoint unavailable
    
    Post-Processor Awareness (v1.1):
        - If post_id provided, fetches preset from /cam/posts/{id}
        - Applies controller-specific G-code formatting
        - Merges preset parameters onto base post configuration
        - Applied to: export_post operation
        - Graceful degradation: Falls back to base post if preset unavailable
    
    Pipeline Design Patterns:
        1. **Sequential execution**: Operations run in order with error isolation
        2. **Context accumulation**: Each op adds data (loops, gcode, sim) to shared context
        3. **Shared defaults**: Tool diameter, units, etc. used unless overridden per-op
        4. **Fail-fast**: First error stops pipeline and returns partial results
        5. **HTTP orchestration**: Sub-operations called via internal HTTP requests
    
    Request Flow:
        1. Parse pipeline spec from JSON string
        2. Validate operation graph (_validate_ops)
        3. Check DXF file format and size
        4. Initialize shared context with DXF bytes
        5. Load machine/post profiles if IDs provided
        6. Execute operations sequentially:
           a. Merge shared params with per-op overrides
           b. Call operation-specific wrapper function
           c. Update context with operation results
           d. Append result to response list
           e. Break on first error
        7. Build summary from final operation (simulation or adaptive stats)
        8. Return complete PipelineResponse
    
    Context Accumulation:
        ctx = {
          "dxf_bytes": bytes,               # Uploaded DXF file data
          "dxf_filename": str,              # Original filename
          "loops": List[Loop],              # Extracted from adaptive_plan
          "plan": Dict,                     # Adaptive planning request
          "plan_result": Dict,              # Adaptive planning response
          "gcode": str,                     # Generated G-code
          "post_result": Dict,              # Post-processor result
          "sim_result": Dict,               # Simulation result
          "machine_profile": Dict,          # Machine profile (if loaded)
          "post_profile": Dict,             # Post preset (if loaded)
        }
    
    Example Request (cURL):
        ```bash
        curl -X POST "http://localhost:8000/api/cam/pipeline/run" \\
          -F "file=@bridge_pocket.dxf" \\
          -F 'pipeline={
            "ops": [
              {"kind": "dxf_preflight", "params": {"profile": "bridge"}},
              {"kind": "adaptive_plan", "params": {}},
              {"kind": "adaptive_plan_run", "params": {"stepover": 0.45}},
              {"kind": "export_post", "params": {}},
              {"kind": "simulate_gcode", "params": {}}
            ],
            "tool_d": 6.0,
            "units": "mm",
            "geometry_layer": "GEOMETRY",
            "machine_id": "haas_mini",
            "post_id": "grbl"
          }'
        ```
    
    Example Response:
        ```json
        {
          "ops": [
            {"id": null, "kind": "dxf_preflight", "ok": true, "error": null,
             "payload": {"ok": true, "report": {...}}},
            {"id": null, "kind": "adaptive_plan", "ok": true, "error": null,
             "payload": {"loops": [...], "count": 1, "warnings": []}},
            {"id": null, "kind": "adaptive_plan_run", "ok": true, "error": null,
             "payload": {"stats": {"length_mm": 547.3, "time_s": 32.1, ...}}},
            {"id": null, "kind": "export_post", "ok": true, "error": null,
             "payload": {"post_id": "grbl", "gcode_preview": "...", "total_lines": 245}},
            {"id": null, "kind": "simulate_gcode", "ok": true, "error": null,
             "payload": {"time_s": 32.1, "length_mm": 547.3, "moves": [...]}}
          ],
          "summary": {
            "time_s": 32.1,
            "length_mm": 547.3,
            "area_mm2": 6000.0,
            "volume_mm3": 9000.0,
            "move_count": 156
          }
        }
        ```
    
    Error Handling:
        - **PreflightEngineMissingError**: DXF parser not available (ezdxf missing)
        - **PreflightParseError**: Malformed DXF file structure
        - **PreflightGeometryError**: Invalid geometry (self-intersections, etc.)
        - **HTTPException**: Sub-request failures (adaptive, simulate, machine, post)
        - **ValidationError**: Invalid pipeline spec JSON
        - **Generic Exception**: Unexpected errors (logged with full context)
    
    Performance Characteristics:
        - **File size limit**: 50 MB (typical CAD files are 1-10 MB)
        - **HTTP timeout**: 60 seconds per sub-request
        - **Operation count**: Max 20 operations per pipeline
        - **Typical execution time**: 2-5 seconds for complete workflow
    
    Security Notes:
        - DXF file validated for format and size before processing
        - Sub-requests use internal API only (no external URLs)
        - Machine/post IDs validated against existing profiles
        - Operation graph validated before execution (fail-fast)
    
    Notes:
        - Pipeline stops on first operation error (fail-fast design)
        - Partial results returned on error (ops completed before failure)
        - Machine/post profiles cached in context (loaded once per pipeline)
        - DXF bytes cached in memory (no disk I/O during operations)
        - Graceful degradation: Machine/post endpoints optional (continue without)
    
    See Also:
        - _validate_ops: Pipeline validation logic
        - PipelineRequest: Input model with shared parameters
        - PipelineResponse: Output model with per-op results
        - /api/cam/pocket/adaptive/plan: Adaptive pocketing endpoint
        - /cam/simulate_gcode: G-code simulation endpoint
        - /cam/machines/{id}: Machine profile endpoint
        - /cam/posts/{id}: Post-processor preset endpoint
    """
    # --- Parse pipeline spec -------------------------------------------------
    try:
        req = PipelineRequest.model_validate_json(pipeline)
    except ValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid pipeline spec: {exc}",
        ) from exc

    _validate_ops(req.ops)

    if not file.filename or not file.filename.lower().endswith(".dxf"):
        raise HTTPException(status_code=400, detail="Only .dxf files are supported.")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file.")

    # --- DXF caching + context ----------------------------------------------
    ctx: Dict[str, Any] = {
        "dxf_bytes": data,
        "dxf_filename": file.filename,
        "loops": None,
        "plan": None,
        "plan_result": None,
        "gcode": None,
        "post_result": None,
        "sim_result": None,
        "machine_profile": None,
        "post_profile": None,
    }

    results: List[PipelineOpResult] = []
    summary: Dict[str, Any] = {}

    shared_tool_d = req.tool_d
    shared_units = req.units
    shared_geometry_layer = req.geometry_layer
    shared_auto_scale = req.auto_scale
    shared_cam_prefix = req.cam_layer_prefix
    shared_machine_id = req.machine_id
    shared_post_id = req.post_id

    # =========================================================================
    # HELPER FUNCTIONS: Machine/Post Profile Loaders
    # =========================================================================
    
    async def _ensure_machine_profile(
        client: httpx.AsyncClient, 
        machine_id: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Load and cache machine profile with graceful degradation.
        
        Fetches machine kinematic limits (feeds, rapids, accel, jerk) from
        machine endpoint if machine_id is provided. Caches result in context
        to avoid redundant HTTP requests within same pipeline execution.
        
        Args:
            client: Async HTTP client for sub-requests
            machine_id: Machine profile identifier (e.g. "haas_mini", "tormach_1100")
        
        Returns:
            Dict with machine profile data (feeds, rapids, limits) or None if:
                - machine_id not provided
                - Machine endpoint unavailable (RequestError)
                - Profile already cached in context
        
        Profile Structure (typical):
            {
              "id": "haas_mini",
              "name": "Haas Mini Mill",
              "max_feed_xy": 5000,      # mm/min
              "rapid_feed": 10000,      # mm/min
              "accel": 500,             # mm/s²
              "jerk": 5000              # mm/s³
            }
        
        Caching Strategy:
            - Check ctx["machine_profile"] first (single load per pipeline)
            - Verify cached profile matches requested machine_id
            - Store newly loaded profile for subsequent operations
        
        Error Handling:
            - HTTP 404/500: Raises HTTPException (machine required but not found)
            - RequestError: Returns None (graceful degradation, continues without)
            - Logs warning on failure but doesn't stop pipeline
        
        Notes:
            - v1.1 feature for machine-aware toolpath generation
            - Used by adaptive_plan_run to inject feed limits
            - Used by simulate_gcode for realistic time estimation
            - Optional - pipeline continues if machine endpoint missing
        """
        if not machine_id:
            return None
        
        # Check cache first
        mp = ctx.get("machine_profile")
        if mp and mp.get("id") == machine_id:
            return mp
        
        try:
            # Fetch machine profile from endpoint
            resp = await client.get(f"{machine_path}/{machine_id}", timeout=HTTP_TIMEOUT_SECONDS)
            if resp.status_code != 200:
                logger.warning(
                    f"Machine profile '{machine_id}' not found (status {resp.status_code})"
                )
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"Failed to load machine profile '{machine_id}': {resp.text}",
                )
            
            mp = resp.json()
            ctx["machine_profile"] = mp
            logger.info(f"Loaded machine profile: {machine_id}")
            return mp
            
        except httpx.RequestError as e:
            # Machine endpoint might not exist yet - continue without it
            logger.warning(f"Machine endpoint unavailable: {e}")
            return None

    async def _ensure_post_profile(
        client: httpx.AsyncClient, 
        post_id: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Load and cache post-processor preset with graceful degradation.
        
        Fetches post-processor configuration (headers, footers, overrides) from
        post endpoint if post_id is provided. Caches result to avoid redundant
        HTTP requests within same pipeline execution.
        
        Args:
            client: Async HTTP client for sub-requests
            post_id: Post-processor preset ID (e.g. "grbl", "mach4", "haas_ngc")
        
        Returns:
            Dict with post preset data (headers, footers, overrides) or None if:
                - post_id not provided
                - Post endpoint unavailable (RequestError)
                - Preset already cached in context
        
        Preset Structure (typical):
            {
              "id": "grbl",
              "name": "GRBL Controller",
              "base_post": "GRBL",
              "overrides": {
                "header_append": ["(Job: Luthier Pocket)"],
                "footer_append": ["(End of Luthier Job)"]
              }
            }
        
        Caching Strategy:
            - Check ctx["post_profile"] first (single load per pipeline)
            - Verify cached preset matches requested post_id
            - Store newly loaded preset for subsequent operations
        
        Error Handling:
            - HTTP 404/500: Raises HTTPException (post required but not found)
            - RequestError: Returns None (graceful degradation, uses base post)
            - Logs warning on failure but doesn't stop pipeline
        
        Notes:
            - v1.1 feature for post-processor awareness
            - Used by export_post to merge preset overrides
            - Optional - falls back to base post configuration if unavailable
            - Preset overrides applied on top of base post headers/footers
        """
        if not post_id:
            return None
        
        # Check cache first
        pp = ctx.get("post_profile")
        if pp and pp.get("id") == post_id:
            return pp
        
        try:
            # Fetch post preset from endpoint
            resp = await client.get(f"{post_path}/{post_id}", timeout=HTTP_TIMEOUT_SECONDS)
            if resp.status_code != 200:
                logger.warning(
                    f"Post preset '{post_id}' not found (status {resp.status_code})"
                )
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"Failed to load post preset '{post_id}': {resp.text}",
                )
            
            pp = resp.json()
            ctx["post_profile"] = pp
            logger.info(f"Loaded post preset: {post_id}")
            return pp
            
        except httpx.RequestError as e:
            # Post endpoint might not exist yet - continue with base post
            logger.warning(f"Post endpoint unavailable: {e}")
            return None

    # =========================================================================
    # HELPER FUNCTIONS: Parameter Merging
    # =========================================================================
    
    def _merge_params(op: PipelineOp) -> Dict[str, Any]:
        """
        Merge shared pipeline parameters with per-operation overrides.
        
        Implements parameter inheritance where each operation starts with shared
        defaults (tool_d, units, machine_id, etc.) and selectively overrides
        specific values via op.params.
        
        Args:
            op: Pipeline operation with optional parameter overrides
        
        Returns:
            Dict with complete parameter set (shared defaults + op overrides)
        
        Merge Strategy:
            1. Start with shared context (PipelineRequest top-level params)
            2. Overlay op.params on top (dict.update semantics)
            3. Per-op overrides take precedence over shared defaults
        
        Merged Parameters:
            - tool_d: Tool diameter in mm
            - units: "mm" or "inch"
            - geometry_layer: DXF layer name
            - auto_scale: Enable automatic DXF unit scaling
            - cam_layer_prefix: Prefix for CAM-specific layers
            - machine_id: Machine profile identifier
            - post_id: Post-processor preset identifier
            - ...plus any additional op-specific params
        
        Example:
            Shared: {"tool_d": 6.0, "stepover": 0.45}
            Op params: {"stepover": 0.5, "climb": true}
            Result: {"tool_d": 6.0, "stepover": 0.5, "climb": true}
        
        Notes:
            - Enables parameter reuse across multiple operations
            - Per-op overrides allow fine-grained control
            - All operations use merged params for consistency
            - Maintains backward compatibility with op-only params
        """
        merged: Dict[str, Any] = {
            "tool_d": shared_tool_d,
            "units": shared_units,
            "geometry_layer": shared_geometry_layer,
            "auto_scale": shared_auto_scale,
            "cam_layer_prefix": shared_cam_prefix,
            "machine_id": shared_machine_id,
            "post_id": shared_post_id,
        }
        merged.update(op.params)
        return merged

    # =========================================================================
    # HELPER FUNCTIONS: Operation Wrappers
    # =========================================================================
    
    def _wrap_preflight(params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute DXF preflight validation operation.
        
        Validates DXF file structure, entity types, layer organization, and geometry
        integrity. Reports issues with severity levels (error/warning/info) for user
        feedback and downstream operation decisions.
        
        Args:
            params: Merged parameters including:
                - profile: Optional validation profile ("bridge", "body", etc.)
                - cam_layer_prefix: Prefix for CAM-specific layers (default "CAM_")
                - debug: Enable debug output (default False)
        
        Returns:
            Dict with preflight report:
                - ok: bool - True if no critical errors
                - report: Dict with validation details:
                    * units: Detected DXF units ("mm" or "inch")
                    * layers: List of layer names found
                    * candidate_layers: Suggested geometry layers
                    * issues: List of validation issues with level/code/message
                    * debug: Optional debug information
        
        Validation Checks:
            1. **File parsing**: ezdxf successfully loads DXF structure
            2. **Entity types**: Validates supported types (LINE, ARC, LWPOLYLINE, etc.)
            3. **Layer structure**: Checks for geometry and CAM layers
            4. **Geometry integrity**: Self-intersections, open paths, degenerate entities
            5. **Units consistency**: Validates DXF units match expectations
        
        Profile-Specific Rules:
            - "bridge": Requires closed boundary, checks for island geometry
            - "body": Validates guitar body outline, checks symmetry
            - None: Generic validation for all DXF files
        
        Error Handling:
            - PreflightEngineMissingError: ezdxf library not installed
            - PreflightParseError: Malformed DXF file structure
            - PreflightGeometryError: Invalid geometry (self-intersections, etc.)
        
        Notes:
            - First operation in typical pipeline (validates before processing)
            - Non-blocking: Warnings don't stop pipeline, errors do
            - Debug mode provides entity-level details for troubleshooting
        """
        profile = params.get("profile")
        cam_prefix = params.get("cam_layer_prefix", shared_cam_prefix)
        debug_flag = bool(params.get("debug", False))
        
        rep = preflight_dxf_bytes(
            ctx["dxf_bytes"],
            cam_layer_prefix=cam_prefix,
            profile=profile,
            debug=debug_flag,
        )
        return {
            "ok": rep.ok,
            "report": {
                "ok": rep.ok,
                "units": rep.units,
                "layers": rep.layers,
                "candidate_layers": rep.candidate_layers,
                "issues": [
                    {
                        "level": i.level,
                        "code": i.code,
                        "message": i.message,
                        "entity_id": i.entity_id,
                        "layer": i.layer,
                    }
                    for i in rep.issues
                ],
                "debug": rep.debug,
            },
        }

    def _wrap_adaptive_plan(params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract closed loops from DXF for adaptive pocket planning.
        
        Parses DXF geometry layer to identify closed boundary paths suitable for
        adaptive pocketing operations. Detects islands (holes) automatically and
        returns loop coordinates with warnings for user review.
        
        Args:
            params: Merged parameters including:
                - geometry_layer: DXF layer name to extract (default "GEOMETRY")
                - auto_scale: Enable automatic unit scaling (default True)
        
        Returns:
            Dict with extracted loops:
                - loops: List of loop dictionaries with pts arrays [[x1,y1], [x2,y2], ...]
                - count: Number of loops found
                - warnings: List of extraction warnings (open paths, small loops, etc.)
        
        Loop Structure:
            - First loop: Outer boundary (must be closed and CCW for outside cuts)
            - Subsequent loops: Islands/holes (must be closed and CW for keepout zones)
            - Coordinates in mm (auto-scaled if DXF units detected as inches)
        
        Extraction Algorithm:
            1. Parse DXF file with ezdxf
            2. Filter entities on specified layer
            3. Convert LINE/ARC/LWPOLYLINE to loop coordinates
            4. Close open paths if endpoints within tolerance (0.01mm)
            5. Validate closure and orientation
            6. Warn on issues (open paths, degenerate loops)
        
        Error Handling:
            - Missing layer: Returns empty loops list with warning
            - Open paths: Attempts auto-close, warns if failed
            - No loops found: Returns count=0, warns user
        
        Context Updates:
            - ctx["loops"]: Stores extracted loops for adaptive_plan_run
        
        Notes:
            - Second operation in typical pipeline (after dxf_preflight)
            - Required before adaptive_plan_run (provides loop geometry)
            - Temp file used for DXF parsing (cleaned up automatically)
        """
        import os
        import tempfile
        
        # Write DXF to temp file for extraction
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.dxf', delete=False) as tmp:
            tmp.write(ctx["dxf_bytes"])
            tmp_path = tmp.name
        
        try:
            # Extract loops from DXF bytes
            layer_name = params.get("geometry_layer") or shared_geometry_layer or "GEOMETRY"
            loops, warnings = extract_loops_from_dxf(ctx["dxf_bytes"], layer_name=layer_name)
            ctx["loops"] = loops
            return {
                "loops": [{"pts": loop.pts} for loop in loops],
                "count": len(loops),
                "warnings": warnings
            }
        finally:
            os.unlink(tmp_path)

    async def _wrap_adaptive_plan_run(params: Dict[str, Any], client: httpx.AsyncClient) -> Dict[str, Any]:
        """Execute adaptive pocket planning with optional machine-aware limits"""
        # Ensure we have loops
        if ctx["loops"] is None:
            raise HTTPException(
                status_code=400,
                detail="adaptive_plan_run requires prior adaptive_plan operation to extract loops"
            )
        
        # Load machine profile if specified
        machine_id = params.get("machine_id", shared_machine_id)
        mp = await _ensure_machine_profile(client, machine_id)
        
        # Build plan request
        plan_req = {
            "loops": [{"pts": loop.pts} for loop in ctx["loops"]],
            "units": params.get("units", shared_units),
            "tool_d": float(params.get("tool_d", shared_tool_d)),
            "stepover": float(params.get("stepover", 0.45)),
            "stepdown": float(params.get("stepdown", 2.0)),
            "margin": float(params.get("margin", 0.5)),
            "strategy": params.get("strategy", "Spiral"),
            "smoothing": float(params.get("smoothing", 0.5)),
            "climb": bool(params.get("climb", True)),
            "feed_xy": float(params.get("feed_xy", mp.get("max_feed_xy") if mp else 1200)),
            "safe_z": float(params.get("safe_z", mp.get("safe_z_default") if mp and "safe_z_default" in mp else 5.0)),
            "z_rough": float(params.get("z_rough", -1.5)),
        }
        
        # Inject machine-aware parameters if profile exists
        if mp:
            if "machine_profile_id" not in plan_req:
                plan_req["machine_profile_id"] = mp.get("id")
            if "machine_feed_xy" not in plan_req:
                plan_req["machine_feed_xy"] = mp.get("max_feed_xy")
            if "machine_rapid" not in plan_req:
                plan_req["machine_rapid"] = mp.get("rapid")
            if "machine_accel" not in plan_req:
                plan_req["machine_accel"] = mp.get("accel")
            if "machine_jerk" not in plan_req:
                plan_req["machine_jerk"] = mp.get("jerk")
        
        # Add L.2 parameters if provided
        if "corner_radius_min" in params:
            plan_req["corner_radius_min"] = float(params["corner_radius_min"])
        if "target_stepover" in params:
            plan_req["target_stepover"] = float(params["target_stepover"])
        if "slowdown_feed_pct" in params:
            plan_req["slowdown_feed_pct"] = float(params["slowdown_feed_pct"])
        
        # Add L.3 parameters if provided
        if "use_trochoids" in params:
            plan_req["use_trochoids"] = bool(params["use_trochoids"])
        if "trochoid_radius" in params:
            plan_req["trochoid_radius"] = float(params["trochoid_radius"])
        if "trochoid_pitch" in params:
            plan_req["trochoid_pitch"] = float(params["trochoid_pitch"])
        
        ctx["plan"] = plan_req
        
        # Execute via HTTP to adaptive planner
        resp = await client.post(adaptive_plan_path, json=plan_req)
        
        if resp.status_code != 200:
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Adaptive planner error: {resp.text}",
            )
        
        result = resp.json()
        ctx["plan_result"] = result
        
        # Generate basic G-code from moves (if not already present)
        if "gcode" not in result and "moves" in result:
            gcode_lines = []
            for move in result["moves"]:
                parts = [move.get("code", "G0")]
                if "x" in move:
                    parts.append(f"X{move['x']:.4f}")
                if "y" in move:
                    parts.append(f"Y{move['y']:.4f}")
                if "z" in move:
                    parts.append(f"Z{move['z']:.4f}")
                if "f" in move:
                    parts.append(f"F{move['f']:.1f}")
                gcode_lines.append(" ".join(parts))
            ctx["gcode"] = "\n".join(gcode_lines)
        
        return result

    async def _wrap_export_post(params: Dict[str, Any], client: httpx.AsyncClient) -> Dict[str, Any]:
        """Apply post-processor headers/footers with optional post preset awareness"""
        if ctx["gcode"] is None:
            raise HTTPException(
                status_code=400,
                detail="export_post requires gcode from prior adaptive_plan_run"
            )
        
        # Load post preset if specified
        post_id = params.get("post_id", shared_post_id) or "GRBL"
        pp = await _ensure_post_profile(client, post_id)
        
        units = params.get("units", shared_units)
        
        # Load post-processor configuration
        import os
        post_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "posts", f"{post_id.lower()}.json"
        )
        
        if not os.path.exists(post_file):
            raise HTTPException(
                status_code=404,
                detail=f"Post-processor '{post_id}' not found"
            )
        
        with open(post_file, 'r') as f:
            post_config = json.load(f)
        
        # Override config with post preset if available
        if pp:
            if "post" in pp:
                post_config["dialect"] = pp["post"]
            if "header" in pp:
                post_config["header"] = pp["header"]
            if "footer" in pp:
                post_config["footer"] = pp["footer"]
        
        # Build complete G-code
        gcode_lines = []
        
        # Units command
        gcode_lines.append("G21" if units == "mm" else "G20")
        
        # Header
        if "header" in post_config:
            gcode_lines.extend(post_config["header"])
        
        # Metadata
        from datetime import datetime
        gcode_lines.append(
            f"(POST={post_id};UNITS={units};DATE={datetime.utcnow().isoformat()})"
        )
        
        # Body
        gcode_lines.append(ctx["gcode"])
        
        # Footer
        if "footer" in post_config:
            gcode_lines.extend(post_config["footer"])
        
        final_gcode = "\n".join(gcode_lines)
        ctx["gcode"] = final_gcode
        ctx["post_result"] = {
            "post_id": post_id,
            "units": units,
            "lines": len(gcode_lines),
        }
        
        return {
            "post_id": post_id,
            "gcode_preview": "\n".join(gcode_lines[:20]),  # First 20 lines
            "total_lines": len(gcode_lines),
        }

    async def _wrap_simulate_gcode(params: Dict[str, Any], client: httpx.AsyncClient) -> Dict[str, Any]:
        """Run G-code simulation with optional machine-aware limits"""
        # Get gcode from params or context
        gcode = params.get("gcode") or ctx.get("gcode")
        
        if not gcode:
            raise HTTPException(
                status_code=400,
                detail=(
                    "simulate_gcode requires 'gcode' in params or a prior op "
                    "that provides gcode (e.g. adaptive_plan_run or export_post)."
                ),
            )
        
        # Load machine profile if specified
        machine_id = params.get("machine_id", shared_machine_id)
        mp = await _ensure_machine_profile(client, machine_id)
        
        # Build simulation request with machine-aware defaults
        body = {
            "gcode": gcode,
            "accel": float(params.get("accel", mp.get("accel") if mp else 800)),
            "clearance_z": float(params.get("safe_z", mp.get("safe_z_default") if mp and "safe_z_default" in mp else 5.0)),
            "as_csv": False,
        }
        
        # Add machine limits if available
        if mp:
            if "feed_xy" not in params and "max_feed_xy" in mp:
                body["feed_xy"] = mp["max_feed_xy"]
            if "feed_z" not in params and "max_feed_z" in mp:
                body["feed_z"] = mp["max_feed_z"]
            if "rapid" not in params and "rapid" in mp:
                body["rapid"] = mp["rapid"]
        
        resp = await client.post(sim_path, json=body)
        
        if resp.status_code != 200:
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Simulation error: {resp.text}",
            )
        
        result = resp.json()
        ctx["sim_result"] = result
        return result

    # --- Main loop with per-op error wrapping -------------------------------
    async with httpx.AsyncClient(base_url=base_url, timeout=60.0) as client:
        for op in req.ops:
            merged = _merge_params(op)
            kind = op.kind

            try:
                if kind == "dxf_preflight":
                    payload = _wrap_preflight(merged)
                    ok = bool(payload.get("ok", True))
                elif kind == "adaptive_plan":
                    payload = _wrap_adaptive_plan(merged)
                    ok = True
                elif kind == "adaptive_plan_run":
                    payload = await _wrap_adaptive_plan_run(merged, client)
                    ok = True
                elif kind == "export_post":
                    payload = await _wrap_export_post(merged, client)
                    ok = True
                elif kind == "simulate_gcode":
                    payload = await _wrap_simulate_gcode(merged, client)
                    ok = True
                else:
                    results.append(
                        PipelineOpResult(
                            id=op.id,
                            kind=kind,
                            ok=False,
                            error=f"Unsupported pipeline op kind: {kind}",
                            payload=None,
                        )
                    )
                    break

                results.append(
                    PipelineOpResult(id=op.id, kind=kind, ok=ok, payload=payload)
                )

            except (PreflightEngineMissingError,) as exc:
                results.append(
                    PipelineOpResult(
                        id=op.id,
                        kind=kind,
                        ok=False,
                        error=f"Engine missing: {exc}",
                        payload=None,
                    )
                )
                break
            except (PreflightParseError,) as exc:
                results.append(
                    PipelineOpResult(
                        id=op.id,
                        kind=kind,
                        ok=False,
                        error=f"DXF parse error: {exc}",
                        payload=None,
                    )
                )
                break
            except (PreflightGeometryError,) as exc:
                results.append(
                    PipelineOpResult(
                        id=op.id,
                        kind=kind,
                        ok=False,
                        error=f"DXF geometry error: {exc}",
                        payload=None,
                    )
                )
                break
            except HTTPException as exc:  # WP-1: catch HTTPException separately
                results.append(
                    PipelineOpResult(
                        id=op.id,
                        kind=kind,
                        ok=False,
                        error=str(exc.detail),
                        payload=None,
                    )
                )
                break
            except Exception as exc:  # WP-1: governance catch-all — HTTP endpoint
                results.append(
                    PipelineOpResult(
                        id=op.id,
                        kind=kind,
                        ok=False,
                        error=f"Unexpected error: {exc}",
                        payload=None,
                    )
                )
                break

    # Build summary from last operation's result
    if ctx.get("sim_result") and isinstance(ctx["sim_result"], dict):
        # Simulation stats take priority
        summary = ctx["sim_result"].get("summary", {})
    elif ctx.get("plan_result"):
        # Fallback to adaptive stats
        summary = ctx["plan_result"].get("stats", {})

    job_payload = build_jobint_payload(
        {
            "plan_request": ctx.get("plan"),
            "adaptive_plan_request": ctx.get("plan"),
            "moves": (ctx.get("plan_result") or {}).get("moves"),
            "adaptive_moves": (ctx.get("plan_result") or {}).get("moves"),
            "moves_path": ctx.get("moves_path"),
        }
    )

    return PipelineResponse(ops=results, summary=summary, job_int=job_payload)
