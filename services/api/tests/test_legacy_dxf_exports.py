"""
Test DXF Export Endpoints (Migrated from ./server)

Tests for /exports/polyline_dxf and /exports/biarc_dxf endpoints
to ensure DXF files are generated correctly with proper format.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ============================================================================
# Polyline DXF Export Tests
# ============================================================================

def test_polyline_dxf_export():
    """Test polyline export to DXF format"""
    response = client.post('/exports/polyline_dxf', json={
        "polyline": {
            "points": [[0, 0], [100, 0], [100, 50]]
        },
        "layer": "TEST"
    })

    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/dxf'
    assert 'attachment' in response.headers['content-disposition']

    content = response.content
    assert content.startswith(b'0\nSECTION') or content.startswith(b'AutoCAD')
    assert b'ENTITIES' in content
    assert b'TEST' in content


def test_polyline_dxf_custom_layer():
    """Test polyline export with custom layer name"""
    response = client.post('/exports/polyline_dxf', json={
        "polyline": {
            "points": [[0, 0], [50, 50], [100, 0]]
        },
        "layer": "PICKUP_CAVITY"
    })

    assert response.status_code == 200
    content = response.content
    assert b'PICKUP_CAVITY' in content


def test_polyline_dxf_large_polyline():
    """Test polyline export with many points"""
    points = [[i, i % 10] for i in range(100)]

    response = client.post('/exports/polyline_dxf', json={
        "polyline": {"points": points},
        "layer": "LARGE"
    })

    assert response.status_code == 200
    assert b'ENTITIES' in response.content


def test_polyline_dxf_closed_curve():
    """Test polyline export with closed curve (square)"""
    response = client.post('/exports/polyline_dxf', json={
        "polyline": {
            "points": [[0, 0], [100, 0], [100, 100], [0, 100], [0, 0]]
        },
        "layer": "CLOSED"
    })

    assert response.status_code == 200
    assert b'CLOSED' in response.content


# ============================================================================
# Bi-arc DXF Export Tests
# ============================================================================

def test_biarc_dxf_export():
    """Test bi-arc export to DXF format"""
    response = client.post('/exports/biarc_dxf', json={
        "p0": [0, 0],
        "t0": [1, 0],
        "p1": [100, 50],
        "t1": [0, 1],
        "layer": "ARC"
    })

    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/dxf'
    assert 'attachment' in response.headers['content-disposition']

    content = response.content
    assert b'ENTITIES' in content
    assert b'ARC' in content


def test_biarc_dxf_custom_layer():
    """Test bi-arc export with custom layer name"""
    response = client.post('/exports/biarc_dxf', json={
        "p0": [0, 0],
        "t0": [1, 0],
        "p1": [50, 50],
        "t1": [1, 1],
        "layer": "NECK_TRANSITION"
    })

    assert response.status_code == 200
    content = response.content
    assert b'NECK_TRANSITION' in content


def test_biarc_dxf_parallel_tangents():
    """Test bi-arc with parallel tangents (degenerate case -> line)"""
    response = client.post('/exports/biarc_dxf', json={
        "p0": [0, 0],
        "t0": [1, 0],
        "p1": [100, 0],
        "t1": [1, 0],
        "layer": "LINE"
    })

    assert response.status_code == 200
    assert b'ENTITIES' in response.content


def test_biarc_dxf_opposite_tangents():
    """Test bi-arc with opposite tangents (180 degree turn)"""
    response = client.post('/exports/biarc_dxf', json={
        "p0": [0, 0],
        "t0": [1, 0],
        "p1": [100, 0],
        "t1": [-1, 0],
        "layer": "S_CURVE"
    })

    assert response.status_code == 200
    assert b'S_CURVE' in response.content


def test_biarc_dxf_90_degree_blend():
    """Test bi-arc with 90 degree tangent change (common use case)"""
    response = client.post('/exports/biarc_dxf', json={
        "p0": [0, 0],
        "t0": [1, 0],
        "p1": [50, 50],
        "t1": [0, 1],
        "layer": "CORNER"
    })

    assert response.status_code == 200
    content = response.content
    assert b'CORNER' in content
    assert content.count(b'ARC') >= 1 or content.count(b'POLYLINE') >= 1


# ============================================================================
# Error Handling Tests
# ============================================================================

def test_polyline_dxf_empty_points():
    """Test polyline with empty points list"""
    response = client.post('/exports/polyline_dxf', json={
        "polyline": {"points": []},
        "layer": "EMPTY"
    })

    assert response.status_code in [200, 400, 422]


def test_polyline_dxf_invalid_data():
    """Test polyline with invalid data structure"""
    response = client.post('/exports/polyline_dxf', json={
        "polyline": {"points": "not_a_list"},
        "layer": "INVALID"
    })

    assert response.status_code == 422


def test_biarc_dxf_missing_parameters():
    """Test bi-arc with missing required parameters"""
    response = client.post('/exports/biarc_dxf', json={
        "p0": [0, 0],
        "t0": [1, 0]
    })

    assert response.status_code == 422


# ============================================================================
# Health Check Tests
# ============================================================================

def test_dxf_health():
    """Test DXF export health check endpoint"""
    response = client.get('/exports/dxf/health')

    assert response.status_code == 200
    data = response.json()

    assert 'status' in data
    assert data['status'] == 'healthy'
    assert 'formats' in data
    assert len(data['formats']) > 0


def test_dxf_health_reports_ezdxf():
    """Test health check reports ezdxf availability"""
    response = client.get('/exports/dxf/health')
    data = response.json()

    assert 'ezdxf_version' in data

    if data['ezdxf_version']:
        assert 'ezdxf (native)' in str(data['formats'])
    else:
        assert 'fallback' in str(data['formats']).lower()


# ============================================================================
# Integration Tests
# ============================================================================

def test_export_workflow_polyline_then_biarc():
    """Test complete workflow: polyline + bi-arc export"""
    poly_response = client.post('/exports/polyline_dxf', json={
        "polyline": {"points": [[0, 0], [100, 0], [100, 100]]},
        "layer": "BODY"
    })
    assert poly_response.status_code == 200

    biarc_response = client.post('/exports/biarc_dxf', json={
        "p0": [100, 100],
        "t0": [0, 1],
        "p1": [150, 150],
        "t1": [1, 0],
        "layer": "NECK"
    })
    assert biarc_response.status_code == 200


# ============================================================================
# History Endpoint Tests
# ============================================================================

def test_export_history_list():
    """Test export history list endpoint"""
    response = client.get('/exports/history')

    assert response.status_code == 200
    data = response.json()
    assert 'items' in data
    assert isinstance(data['items'], list)


def test_export_history_with_limit():
    """Test export history with limit parameter"""
    response = client.get('/exports/history?limit=5')

    assert response.status_code == 200
    data = response.json()
    assert 'items' in data
    assert len(data['items']) <= 5


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
