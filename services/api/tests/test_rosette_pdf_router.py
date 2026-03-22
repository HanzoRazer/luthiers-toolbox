"""Tests for POST /api/export/rosette-pdf (BACKEND-002)."""

from __future__ import annotations

import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

URL = "/api/export/rosette-pdf"


def _pdf_text(data: bytes) -> str:
    import pdfplumber

    with pdfplumber.open(io.BytesIO(data)) as pdf:
        return "\n".join(p.extract_text() or "" for p in pdf.pages)


class TestRosettePdfExport:
    def test_post_returns_pdf_200(self):
        payload = {
            "design": {
                "dimensions": {
                    "soundholeDiameter": 100,
                    "rosetteWidth": 20,
                    "channelDepth": 1.5,
                    "symmetryCount": 16,
                },
                "selectedTemplate": "classic",
                "selectedMaterial": "maple",
                "segments": [],
            },
            "title": "Test Rosette",
            "include_bom": False,
            "include_measurements": True,
        }
        r = client.post(URL, json=payload)
        assert r.status_code == 200, r.text
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert r.content.startswith(b"%PDF")
        text = _pdf_text(r.content)
        assert "Test Rosette" in text
        assert "Measurements" in text
        assert "Soundhole" in text

    def test_bom_section_when_segments_derived(self):
        payload = {
            "design": {
                "dimensions": {"soundholeDiameter": 90, "rosetteWidth": 18},
                "segments": [
                    {"id": "1", "material": "maple", "type": "strip"},
                    {"id": "2", "material": "maple", "type": "strip"},
                    {"id": "3", "material": "ebony", "type": "strip"},
                ],
            },
            "include_bom": True,
            "include_measurements": True,
        }
        r = client.post(URL, json=payload)
        assert r.status_code == 200, r.text
        text = _pdf_text(r.content)
        assert "Bill of materials" in text
        assert "maple" in text.lower()

    def test_missing_design_field_422(self):
        r = client.post(URL, json={"title": "x"})
        assert r.status_code == 422
