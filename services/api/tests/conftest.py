"""
Pytest configuration and shared fixtures for Luthier's Toolbox API tests.

This module provides test fixtures for FastAPI testing, including:
- TestClient for API endpoint testing
- Sample geometry data for CAM operations
- Mock database connections
- Common test utilities

Part of P3.1 - Test Coverage to 80% (A_N roadmap requirement)
"""

import pytest
import sys
import uuid
from pathlib import Path
from fastapi.testclient import TestClient
import json
import tempfile
import base64
import os

# Add parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# GLOBAL TEST ISOLATION (RMOS + Saw Lab + Workflow)
# =============================================================================

def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture(autouse=True)
def rmos_global_test_isolation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """
    Global per-test isolation for RMOS + Saw Lab + Workflow tests.

    Goals:
    - Every test gets its own artifact/attachments directory (no cross-test leakage)
    - Learned overrides path is stable and isolated (if enabled)
    - DB is isolated via a temp SQLite URL (for DB-backed workflow sessions)

    This fixture is autouse by design: it protects the whole suite by default.
    """

    # --- 1) Run artifacts / attachments isolation ---
    # Your repo already uses RMOS_RUN_ATTACHMENTS_DIR for deterministic tests.
    attachments_dir = tmp_path / "run_attachments"
    attachments_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("RMOS_RUN_ATTACHMENTS_DIR", str(attachments_dir))

    # Optional: if you also use a separate artifact root, isolate it too
    # (Safe even if your code ignores it)
    artifacts_dir = tmp_path / "run_artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("RMOS_ARTIFACT_ROOT", str(artifacts_dir))

    # --- 1b) RMOS runs_v2 store isolation ---
    # The runs_v2 store uses RMOS_RUNS_DIR (not RMOS_ARTIFACT_ROOT)
    runs_dir = tmp_path / "rmos_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("RMOS_RUNS_DIR", str(runs_dir))

    # Seed empty index for the split-store
    (runs_dir / "_index.json").write_text("{}", encoding="utf-8")

    # Reset the store singleton to pick up new path for this test
    try:
        from app.rmos.runs_v2 import store as runs_v2_store
        runs_v2_store._default_store = None
    except ImportError:
        pass  # runs_v2 module not available in all test contexts

    # --- 2) Learned overrides isolation (Saw Lab) ---
    # If the overrides hook is enabled, it will read this file.
    overrides_path = tmp_path / "learned_overrides.json"
    _write_text(overrides_path, "{}\n")
    monkeypatch.setenv("SAW_LAB_LEARNED_OVERRIDES_PATH", str(overrides_path))

    # --- 3) Temp SQLite DB isolation (workflow_sessions, artifacts index, etc.) ---
    # Only set DATABASE_URL if not already forced by the test runner/CI.
    # This keeps local/CI overrides possible while defaulting to safe isolation.
    if not os.getenv("DATABASE_URL"):
        db_path = tmp_path / "test.sqlite"
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    yield


# =============================================================================
# CLIENT FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def api_client():
    """
    FastAPI TestClient for testing API endpoints.

    Uses session scope to reuse across all tests.
    Imports app lazily to avoid import-time side effects.
    """
    from app.main import app
    return TestClient(app)


# =============================================================================
# REQUEST ID FIXTURES
# =============================================================================

@pytest.fixture()
def client():
    """
    TestClient that auto-injects X-Request-Id unless explicitly provided.

    Usage:
        def test_something(client):
            r = client.get("/health")
            assert r.headers.get("x-request-id")

    To override:
        client.get("/api/runs", headers={"x-request-id": "test_fixed"})
    """
    from app.main import app
    base = TestClient(app)
    orig_request = base.request

    def request_with_rid(method, url, **kwargs):
        headers = dict(kwargs.pop("headers", {}) or {})
        headers.setdefault("x-request-id", f"test_{uuid.uuid4().hex[:12]}")
        return orig_request(method, url, headers=headers, **kwargs)

    base.request = request_with_rid  # type: ignore[assignment]
    return base


@pytest.fixture(autouse=True)
def _clear_request_id_context():
    """
    Ensure request_id ContextVar is cleared between tests.

    Prevents cross-test leakage when logs fire outside request scope.
    This is the same class of hygiene as:
    - ASP.NET scoped services
    - Request-scoped DI containers
    - OpenTelemetry tracing
    """
    from app.util.request_context import clear_request_id
    clear_request_id()
    yield
    clear_request_id()


# =============================================================================
# SHADOW STATS / DEPRECATION BUDGET CI GATE
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def _shadow_stats_write_after_tests(tmp_path_factory):
    """
    Always writes ENDPOINT_STATS_PATH at end of test session (even if empty).
    This enables the CI budget gate to run deterministically.
    """
    from app.governance.shadow_stats import reset, write_shadow_stats_json

    # Respect CI-provided ENDPOINT_STATS_PATH if present
    configured = os.environ.get("ENDPOINT_STATS_PATH")
    if configured:
        stats_path = configured
    else:
        stats_dir = tmp_path_factory.mktemp("endpoint_shadow_stats")
        stats_path = str(stats_dir / "endpoint_shadow_stats.json")
        os.environ["ENDPOINT_STATS_PATH"] = stats_path

    reset()
    yield
    write_shadow_stats_json(stats_path)


# =============================================================================
# GEOMETRY & CAM FIXTURES
# =============================================================================

@pytest.fixture
def sample_geometry_simple():
    """
    Simple rectangular geometry for basic tests.

    Returns:
        dict: Canonical geometry format (mm units, closed rectangle)
    """
    return {
        "units": "mm",
        "paths": [
            {"type": "line", "x1": 0.0, "y1": 0.0, "x2": 100.0, "y2": 0.0},
            {"type": "line", "x1": 100.0, "y1": 0.0, "x2": 100.0, "y2": 60.0},
            {"type": "line", "x1": 100.0, "y1": 60.0, "x2": 0.0, "y2": 60.0},
            {"type": "line", "x1": 0.0, "y1": 60.0, "x2": 0.0, "y2": 0.0}
        ]
    }


@pytest.fixture
def sample_geometry_with_arcs():
    """
    Geometry with arcs for testing arc interpolation.

    Returns:
        dict: Geometry with LINE and ARC segments
    """
    return {
        "units": "mm",
        "paths": [
            {"type": "line", "x1": 0.0, "y1": 0.0, "x2": 50.0, "y2": 0.0},
            {"type": "arc", "x1": 50.0, "y1": 0.0, "x2": 50.0, "y2": 30.0,
             "cx": 50.0, "cy": 15.0, "r": 15.0, "cw": True},
            {"type": "line", "x1": 50.0, "y1": 30.0, "x2": 0.0, "y2": 30.0},
            {"type": "line", "x1": 0.0, "y1": 30.0, "x2": 0.0, "y2": 0.0}
        ]
    }


@pytest.fixture
def sample_pocket_loops():
    """
    Pocket boundary with island for adaptive pocketing tests.

    Returns:
        list: List of loops (first=outer, rest=islands)
    """
    return [
        # Outer boundary
        {"pts": [[0, 0], [120, 0], [120, 80], [0, 80]]},
        # Island (hole)
        {"pts": [[40, 20], [80, 20], [80, 60], [40, 60]]}
    ]


@pytest.fixture
def sample_bridge_params():
    """
    Bridge calculator parameters for testing.

    Returns:
        dict: Bridge calculation input parameters
    """
    return {
        "span_mm": 60.0,
        "string_spacing_mm": 10.5,
        "num_strings": 6,
        "bridge_type": "tune-o-matic",
        "scale_length_mm": 628.0
    }


@pytest.fixture
def sample_helical_params():
    """
    Helical ramping parameters for testing.

    Returns:
        dict: Helical entry toolpath parameters matching HelicalReq schema
    """
    return {
        "cx": 50.0,
        "cy": 30.0,
        "radius_mm": 5.0,
        "direction": "CW",
        "plane_z_mm": 5.0,
        "start_z_mm": 0.0,
        "z_target_mm": -3.0,
        "pitch_mm_per_rev": 0.5,
        "feed_xy_mm_min": 1200.0,
        "feed_z_mm_min": 400.0
    }


@pytest.fixture
def temp_dxf_file():
    """
    Temporary DXF file for testing exports.

    Yields:
        Path: Path to temporary DXF file (auto-cleaned after test)
    """
    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        yield tmp_path
        if tmp_path.exists():
            tmp_path.unlink()


@pytest.fixture
def temp_nc_file():
    """
    Temporary NC file for testing G-code exports.

    Yields:
        Path: Path to temporary NC file (auto-cleaned after test)
    """
    with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        yield tmp_path
        if tmp_path.exists():
            tmp_path.unlink()


@pytest.fixture
def mock_post_config():
    """
    Mock post-processor configuration for testing.

    Returns:
        dict: Post-processor config (GRBL format)
    """
    return {
        "id": "GRBL",
        "name": "GRBL 1.1",
        "header": [
            "G21",  # mm units
            "G90",  # absolute positioning
            "G17",  # XY plane
            "(GRBL post-processor)"
        ],
        "footer": [
            "M30",  # program end
            "(End of program)"
        ]
    }


@pytest.fixture
def sample_gcode_simple():
    """
    Simple G-code for parsing/validation tests.

    Returns:
        str: Basic G-code program
    """
    return """G21
G90
G17
G0 Z5.0000
G0 X10.0000 Y10.0000
G1 Z-1.5000 F400.0
G1 X50.0000 Y10.0000 F1200.0
G1 X50.0000 Y30.0000
G1 X10.0000 Y30.0000
G1 X10.0000 Y10.0000
G0 Z5.0000
M30
"""


@pytest.fixture
def encode_dxf_base64():
    """
    Helper function to encode DXF content as base64.

    Returns:
        callable: Function that takes DXF string and returns base64
    """
    def _encode(dxf_content: str) -> str:
        return base64.b64encode(dxf_content.encode('utf-8')).decode('utf-8')
    return _encode


@pytest.fixture
def decode_dxf_base64():
    """
    Helper function to decode base64 DXF content.

    Returns:
        callable: Function that takes base64 string and returns DXF
    """
    def _decode(b64_content: str) -> str:
        return base64.b64decode(b64_content.encode('utf-8')).decode('utf-8')
    return _decode


# Test data directory
@pytest.fixture(scope="session")
def test_data_dir():
    """
    Path to test data directory.

    Returns:
        Path: services/api/tests/test_data/
    """
    return Path(__file__).parent / "test_data"


# Utility functions for assertions
def assert_valid_geometry(geom: dict):
    """
    Assert that geometry dict is valid canonical format.

    Args:
        geom: Geometry dictionary to validate

    Raises:
        AssertionError: If geometry is invalid
    """
    assert "units" in geom, "Geometry missing units field"
    assert geom["units"] in ["mm", "inch"], f"Invalid units: {geom['units']}"
    assert "paths" in geom, "Geometry missing paths field"
    assert isinstance(geom["paths"], list), "Paths must be list"
    assert len(geom["paths"]) > 0, "Geometry has no paths"

    for i, path in enumerate(geom["paths"]):
        assert "type" in path, f"Path {i} missing type"
        assert path["type"] in ["line", "arc"], f"Path {i} invalid type: {path['type']}"        


def assert_valid_gcode(gcode: str):
    """
    Assert that G-code string is valid.

    Args:
        gcode: G-code string to validate

    Raises:
        AssertionError: If G-code is invalid
    """
    assert gcode, "G-code is empty"
    lines = gcode.strip().split('\n')
    assert len(lines) > 0, "G-code has no lines"

    # Check for common G-code patterns
    has_g_commands = any(line.strip().startswith('G') for line in lines)
    assert has_g_commands, "G-code has no G commands"


def assert_valid_moves(moves: list):
    """
    Assert that moves list is valid.

    Args:
        moves: List of move dictionaries

    Raises:
        AssertionError: If moves are invalid
    """
    assert isinstance(moves, list), "Moves must be list"
    assert len(moves) > 0, "Moves list is empty"

    for i, move in enumerate(moves):
        assert "code" in move, f"Move {i} missing code"
        assert move["code"] in ["G0", "G1", "G2", "G3"], f"Move {i} invalid code: {move['code']}"



def assert_request_id_header(response) -> str:
    """
    Assert that a response includes a valid X-Request-Id header.

    Works with FastAPI TestClient responses and requests.Response.

    Returns:
        str: The request_id value for downstream assertions/logging.
    """
    # FastAPI TestClient + requests both expose headers as a dict-like object
    headers = getattr(response, "headers", None)
    assert headers is not None, "Response object has no headers attribute"

    request_id = headers.get("X-Request-Id")

    assert request_id is not None, (
        "Missing X-Request-Id header on response. "
        "RequestIdMiddleware may not be installed or executed."
    )

    assert isinstance(request_id, str) and request_id.strip(), (
        "X-Request-Id header is present but empty or invalid"
    )

    return request_id


# Export for use in tests
__all__ = [
    # Client fixtures
    "api_client",
    "client",  # NEW: Auto-injects X-Request-Id
    "rmos_global_test_isolation",  # NEW: Global test isolation
    "_shadow_stats_write_after_tests",  # Shadow stats CI gate
    # Geometry fixtures
    "sample_geometry_simple",
    "sample_geometry_with_arcs",
    "sample_pocket_loops",
    "sample_bridge_params",
    "sample_helical_params",
    "temp_dxf_file",
    "temp_nc_file",
    "mock_post_config",
    "sample_gcode_simple",
    "encode_dxf_base64",
    "decode_dxf_base64",
    "test_data_dir",
    # Assertion utilities
    "assert_valid_geometry",
    "assert_valid_gcode",
    "assert_valid_moves",
    "assert_request_id_header",
]
