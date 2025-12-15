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
from pathlib import Path
from fastapi.testclient import TestClient
import json
import tempfile
import base64

# Add parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def api_client():
    """
    FastAPI TestClient for testing API endpoints.
    
    Uses session scope to reuse across all tests.
    Imports app lazily to avoid import-time side effects.
    """
    from app.main import app
    return TestClient(app)


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


# Export for use in tests
__all__ = [
    "api_client",
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
    "assert_valid_geometry",
    "assert_valid_gcode",
    "assert_valid_moves",
]
