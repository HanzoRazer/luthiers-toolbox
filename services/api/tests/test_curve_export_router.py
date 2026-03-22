"""Tests for POST /api/export/curve-dxf (BACKEND-001)."""

from __future__ import annotations

import io

import ezdxf
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

URL = "/api/export/curve-dxf"


class TestCurveExportDxf:
    def test_post_two_point_curve_returns_dxf_200(self):
        """Open LWPOLYLINE path (fewer than 4 points)."""
        payload = {
            "curves": [
                {
                    "points": [{"x": 0, "y": 0}, {"x": 10, "y": 5}],
                    "label": "line",
                }
            ],
            "scale_mm_per_unit": 1.0,
            "filename": "my_curve",
        }
        r = client.post(URL, json=payload)
        assert r.status_code == 200, r.text
        assert r.headers.get("content-type", "").startswith("application/dxf")
        assert "attachment" in r.headers.get("content-disposition", "").lower()
        assert "my_curve.dxf" in r.headers.get("content-disposition", "")
        data = r.content
        assert b"SECTION" in data
        assert b"LWPOLYLINE" in data
        # Round-trip parse (ASCII DXF string — use text stream for ezdxf loader)
        text = data.decode("ascii", errors="replace")
        doc = ezdxf.read(io.StringIO(text))
        assert doc.layers.get("line") is not None
        assert len(list(doc.modelspace())) >= 1

    def test_post_four_point_curve_uses_spline(self):
        """Four or more points → SPLINE entity."""
        payload = {
            "curves": [
                {
                    "points": [
                        {"x": 0, "y": 0},
                        {"x": 1, "y": 1},
                        {"x": 2, "y": 0},
                        {"x": 3, "y": 1},
                    ],
                    "label": "spline_test",
                }
            ],
            "scale_mm_per_unit": 2.0,
            "filename": "curve_export",
        }
        r = client.post(URL, json=payload)
        assert r.status_code == 200, r.text
        assert b"SPLINE" in r.content
        text = r.content.decode("ascii", errors="replace")
        doc = ezdxf.read(io.StringIO(text))
        splines = [e for e in doc.modelspace() if e.dxftype() == "SPLINE"]
        assert len(splines) == 1

    def test_empty_curves_returns_422(self):
        r = client.post(URL, json={"curves": []})
        assert r.status_code == 422

    def test_too_few_points_returns_422(self):
        r = client.post(
            URL,
            json={"curves": [{"points": [{"x": 0, "y": 0}], "label": "bad"}]},
        )
        assert r.status_code == 422
