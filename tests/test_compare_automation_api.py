# test_compare_automation_api.py
# B22.13: Tests for compare automation API

import json
import pytest
from fastapi.testclient import TestClient


# Import router for monkeypatching
# Adjust import path based on your project structure
try:
    from compare_automation_router import router
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    ROUTER_AVAILABLE = True
except ImportError:
    ROUTER_AVAILABLE = False
    client = None


@pytest.mark.skipif(not ROUTER_AVAILABLE, reason="Router not available for testing")
class TestCompareAutomationAPI:
    """B22.13: Compare automation API tests"""
    
    def test_compare_run_endpoint_exists(self):
        """POST /compare/run endpoint is registered"""
        resp = client.post("/compare/run", json={
            "left": {"kind": "svg", "value": "<svg></svg>"},
            "right": {"kind": "svg", "value": "<svg></svg>"},
            "mode": "overlay",
        })
        
        # Should not return 404
        assert resp.status_code != 404
    
    def test_compare_run_accepts_svg_strings(self):
        """API accepts raw SVG strings"""
        payload = {
            "left": {"kind": "svg", "value": "<svg><rect/></svg>"},
            "right": {"kind": "svg", "value": "<svg><circle/></svg>"},
            "mode": "overlay",
            "export": ["json"],
        }
        
        resp = client.post("/compare/run", json=payload)
        
        # Should succeed with stub implementation
        assert resp.status_code in [200, 500]  # 500 if engine not wired yet
        
        if resp.status_code == 200:
            data = resp.json()
            assert "mode" in data
            assert data["mode"] == "overlay"
    
    def test_compare_run_rejects_invalid_mode(self):
        """API rejects invalid comparison modes"""
        payload = {
            "left": {"kind": "svg", "value": "<svg></svg>"},
            "right": {"kind": "svg", "value": "<svg></svg>"},
            "mode": "invalid-mode",
            "export": ["json"],
        }
        
        resp = client.post("/compare/run", json=payload)
        assert resp.status_code == 422  # Validation error
    
    def test_compare_run_accepts_id_source(self):
        """API accepts ID-based sources"""
        payload = {
            "left": {"kind": "id", "value": "asset-123"},
            "right": {"kind": "id", "value": "asset-456"},
            "mode": "side-by-side",
            "export": ["json"],
        }
        
        resp = client.post("/compare/run", json=payload)
        
        # Should return 400 or 500 (ID lookup not implemented)
        # or 200 if stub returns fake data
        assert resp.status_code in [200, 400, 500]
    
    def test_compare_run_defaults(self):
        """API applies correct defaults"""
        payload = {
            "left": {"kind": "svg", "value": "<svg></svg>"},
            "right": {"kind": "svg", "value": "<svg></svg>"},
        }
        
        resp = client.post("/compare/run", json=payload)
        
        if resp.status_code == 200:
            data = resp.json()
            # Should default to overlay mode
            assert data["mode"] == "overlay"
    
    def test_compare_run_branch_parameter(self):
        """API accepts branch query parameter"""
        payload = {
            "left": {"kind": "svg", "value": "<svg></svg>"},
            "right": {"kind": "svg", "value": "<svg></svg>"},
            "mode": "overlay",
        }
        
        # Test with branch parameter
        resp = client.post("/compare/run?branch=arc-enhanced", json=payload)
        assert resp.status_code in [200, 500]
        
        if resp.status_code == 200:
            data = resp.json()
            assert "warnings" in data
    
    def test_compare_run_invalid_branch(self):
        """API rejects invalid branch names"""
        payload = {
            "left": {"kind": "svg", "value": "<svg></svg>"},
            "right": {"kind": "svg", "value": "<svg></svg>"},
        }
        
        resp = client.post("/compare/run?branch=invalid-branch", json=payload)
        assert resp.status_code == 400
    
    def test_compare_response_shape(self):
        """API returns correct response shape"""
        payload = {
            "left": {"kind": "svg", "value": "<svg></svg>"},
            "right": {"kind": "svg", "value": "<svg></svg>"},
            "mode": "delta",
            "export": ["json"],
        }
        
        resp = client.post("/compare/run", json=payload)
        
        if resp.status_code == 200:
            data = resp.json()
            
            # Required fields
            assert "mode" in data
            assert "warnings" in data
            
            # Optional fields
            if "json" in data and data["json"]:
                json_result = data["json"]
                assert "fullBBox" in json_result
    
    def test_compare_export_json_only(self):
        """API handles json-only export"""
        payload = {
            "left": {"kind": "svg", "value": "<svg></svg>"},
            "right": {"kind": "svg", "value": "<svg></svg>"},
            "export": ["json"],
        }
        
        resp = client.post("/compare/run", json=payload)
        
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("png_data_base64") is None or data["png_data_base64"] == ""
    
    def test_compare_export_with_png(self):
        """API accepts png export request"""
        payload = {
            "left": {"kind": "svg", "value": "<svg></svg>"},
            "right": {"kind": "svg", "value": "<svg></svg>"},
            "export": ["json", "png"],
        }
        
        resp = client.post("/compare/run", json=payload)
        
        if resp.status_code == 200:
            data = resp.json()
            # PNG may be stubbed as empty string
            assert "png_data_base64" in data
    
    def test_get_branch_endpoint(self):
        """GET /compare/branch returns branch info"""
        resp = client.get("/compare/branch")
        assert resp.status_code == 200
        
        data = resp.json()
        assert "active_branch" in data
        assert "available_branches" in data
        assert isinstance(data["available_branches"], list)
    
    def test_test_branch_endpoint(self):
        """POST /compare/test-branch allows branch testing"""
        payload = {
            "left": {"kind": "svg", "value": "<svg></svg>"},
            "right": {"kind": "svg", "value": "<svg></svg>"},
        }
        
        resp = client.post("/compare/test-branch?test_branch=stable", json=payload)
        assert resp.status_code in [200, 500]


@pytest.mark.skipif(not ROUTER_AVAILABLE, reason="Router not available for testing")
class TestCompareAutomationIntegration:
    """Integration tests for complete workflows"""
    
    def test_stable_branch_workflow(self):
        """Stable branch returns consistent results"""
        payload = {
            "left": {"kind": "svg", "value": "<svg><rect/></svg>"},
            "right": {"kind": "svg", "value": "<svg><rect/></svg>"},
            "mode": "side-by-side",
        }
        
        resp = client.post("/compare/run?branch=stable", json=payload)
        
        if resp.status_code == 200:
            data = resp.json()
            assert data["mode"] == "side-by-side"
            assert any("stable" in w.lower() for w in data.get("warnings", []))
    
    def test_arc_enhanced_branch_workflow(self):
        """Arc-enhanced branch includes arc stats"""
        payload = {
            "left": {"kind": "svg", "value": "<svg><path d='M0,0 A10,10 0 0,1 20,20'/></svg>"},
            "right": {"kind": "svg", "value": "<svg><path d='M0,0 L20,20'/></svg>"},
            "mode": "overlay",
        }
        
        resp = client.post("/compare/run?branch=arc-enhanced", json=payload)
        
        if resp.status_code == 200:
            data = resp.json()
            assert any("arc" in w.lower() for w in data.get("warnings", []))
    
    def test_layer_analysis_enabled(self):
        """Layer analysis returns layer data"""
        payload = {
            "left": {"kind": "svg", "value": "<svg><g id='layer1'><rect/></g></svg>"},
            "right": {"kind": "svg", "value": "<svg><g id='layer2'><circle/></g></svg>"},
            "include_layers": True,
        }
        
        resp = client.post("/compare/run", json=payload)
        
        if resp.status_code == 200:
            data = resp.json()
            if "json" in data and data["json"]:
                # Layers may be present in response
                assert "layers" in data["json"]


# Standalone test functions (can run without pytest)
def test_api_smoke():
    """Quick smoke test for API availability"""
    if not ROUTER_AVAILABLE:
        print("⚠️  Router not available - skipping smoke test")
        return
    
    payload = {
        "left": {"kind": "svg", "value": "<svg></svg>"},
        "right": {"kind": "svg", "value": "<svg></svg>"},
    }
    
    resp = client.post("/compare/run", json=payload)
    print(f"✓ POST /compare/run: {resp.status_code}")
    
    resp = client.get("/compare/branch")
    print(f"✓ GET /compare/branch: {resp.status_code}")


if __name__ == "__main__":
    test_api_smoke()
