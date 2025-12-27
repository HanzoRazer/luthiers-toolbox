"""
Tests for the Endpoint Truth Gate CI utility.
"""
from __future__ import annotations

from app.ci.endpoint_truth_gate import parse_expected_endpoints, _parse_method_path_token


def test_parse_expected_endpoints_bullets_and_tables():
    md = """
    # Example
    - GET /api/rmos/runs
    - POST `/api/rmos/runs`
    Some text

    | Method | Path | Notes |
    |--------|------|-------|
    | GET    | /api/vision/providers | list |
    | PATCH  | `/api/rmos/runs/{run_id}/meta` | patch |
    """

    expected = parse_expected_endpoints(md)

    assert ("GET", "/api/rmos/runs") in expected
    assert ("POST", "/api/rmos/runs") in expected
    assert ("GET", "/api/vision/providers") in expected
    assert ("PATCH", "/api/rmos/runs/{run_id}/meta") in expected

    # Ensure we did not accidentally include table headers
    assert ("METHOD", "/Path") not in expected  # type: ignore


def test_parse_expected_endpoints_various_formats():
    md = """
    ## Section
    GET /api/health
    * DELETE /api/rmos/runs/{run_id}
    - PUT `/api/rmos/profiles/{profile_id}`

    | POST | /api/workflow/sessions |
    |OPTIONS|/api/cors-check|
    """

    expected = parse_expected_endpoints(md)

    assert ("GET", "/api/health") in expected
    assert ("DELETE", "/api/rmos/runs/{run_id}") in expected
    assert ("PUT", "/api/rmos/profiles/{profile_id}") in expected
    assert ("POST", "/api/workflow/sessions") in expected
    assert ("OPTIONS", "/api/cors-check") in expected


def test_parse_expected_endpoints_normalizes_trailing_slash():
    md = """
    GET /api/runs/
    POST /api/runs
    """

    expected = parse_expected_endpoints(md)

    # Both should normalize to /api/runs (no trailing slash)
    assert ("GET", "/api/runs") in expected
    assert ("POST", "/api/runs") in expected
    assert len(expected) == 2


def test_parse_expected_endpoints_ignores_invalid_lines():
    md = """
    This is just text
    # Header
    | Column1 | Column2 |
    |---------|---------|
    Not a valid endpoint
    INVALID /api/foo
    """

    expected = parse_expected_endpoints(md)
    assert len(expected) == 0


def test_parse_method_path_token_valid():
    assert _parse_method_path_token("GET:/api/runs") == ("GET", "/api/runs")
    assert _parse_method_path_token("post:/api/runs") == ("POST", "/api/runs")
    assert _parse_method_path_token("  DELETE : /api/runs/{id}  ") == ("DELETE", "/api/runs/{id}")


def test_parse_method_path_token_invalid():
    assert _parse_method_path_token("") is None
    assert _parse_method_path_token("GET") is None
    assert _parse_method_path_token("GET:api/runs") is None  # missing leading /
    assert _parse_method_path_token("INVALID:/api/runs") is None
    assert _parse_method_path_token("just text") is None
