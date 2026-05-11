"""
VECTOR-1A: R12 Compatibility and Deterministic Serialization Tests
===================================================================

Tests for dxf_compat layer to verify:
1. R12 output compliance (AC1009, no LWPOLYLINE, supported entities)
2. Semantic determinism (same input → same structure)
3. Coordinate precision stability
4. Layer name determinism

These tests validate that routes claiming R12 output meet R12 requirements.
"""

import io
import tempfile
from pathlib import Path

import pytest

try:
    import ezdxf
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False

pytestmark = pytest.mark.skipif(not EZDXF_AVAILABLE, reason="ezdxf not installed")


class TestR12Compliance:
    """Tests for R12 format compliance."""

    def test_r12_document_has_ac1009_header(self):
        """R12 document must have AC1009 version header."""
        from app.util.dxf_compat import create_document

        doc = create_document(version="R12")

        assert doc.dxfversion == "AC1009", f"Expected AC1009, got {doc.dxfversion}"

    def test_r12_polyline_uses_line_entities(self):
        """R12 polyline must use LINE entities, not LWPOLYLINE."""
        from app.util.dxf_compat import create_document, add_polyline

        doc = create_document(version="R12")
        msp = doc.modelspace()

        points = [(0, 0), (100, 0), (100, 50), (0, 50)]
        add_polyline(msp, points, layer="TEST", closed=True, version="R12")

        entities = list(msp)
        entity_types = [e.dxftype() for e in entities]

        assert "LWPOLYLINE" not in entity_types, "R12 must not contain LWPOLYLINE"
        assert "LINE" in entity_types, "R12 polyline should use LINE entities"

    def test_r12_closed_polyline_has_closing_segment(self):
        """Closed R12 polyline must have line segment back to start."""
        from app.util.dxf_compat import create_document, add_polyline

        doc = create_document(version="R12")
        msp = doc.modelspace()

        points = [(0, 0), (100, 0), (100, 50)]
        add_polyline(msp, points, layer="TEST", closed=True, version="R12")

        lines = [e for e in msp if e.dxftype() == "LINE"]

        # 3 points closed = 3 line segments
        assert len(lines) == 3, f"Expected 3 lines for closed triangle, got {len(lines)}"

    def test_r12_document_parseable(self):
        """R12 document must be parseable by ezdxf."""
        from app.util.dxf_compat import create_document, add_polyline

        doc = create_document(version="R12")
        msp = doc.modelspace()

        points = [(0, 0), (100, 0), (100, 50), (0, 50)]
        add_polyline(msp, points, layer="BODY", closed=True, version="R12")

        # Save to temp file and re-read
        with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            doc.saveas(tmp_path)
            reloaded = ezdxf.readfile(tmp_path)

            assert reloaded.dxfversion == "AC1009"
            assert len(list(reloaded.modelspace())) > 0
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_r12_layer_names_preserved(self):
        """Layer names must be preserved in R12 output."""
        from app.util.dxf_compat import create_document, add_polyline

        doc = create_document(version="R12")
        msp = doc.modelspace()

        add_polyline(msp, [(0, 0), (10, 10)], layer="CUSTOM_LAYER", version="R12")

        lines = [e for e in msp if e.dxftype() == "LINE"]
        assert len(lines) == 1
        assert lines[0].dxf.layer == "CUSTOM_LAYER"


class TestR2000Compliance:
    """Tests for R2000+ format features."""

    def test_r2000_document_has_ac1015_header(self):
        """R2000 document must have AC1015 version header."""
        from app.util.dxf_compat import create_document

        doc = create_document(version="R2000")

        assert doc.dxfversion == "AC1015", f"Expected AC1015, got {doc.dxfversion}"

    def test_r2000_polyline_uses_lwpolyline(self):
        """R2000 polyline can use LWPOLYLINE."""
        from app.util.dxf_compat import create_document, add_polyline

        doc = create_document(version="R2000")
        msp = doc.modelspace()

        points = [(0, 0), (100, 0), (100, 50), (0, 50)]
        add_polyline(msp, points, layer="TEST", closed=True, version="R2000")

        entities = list(msp)
        entity_types = [e.dxftype() for e in entities]

        assert "LWPOLYLINE" in entity_types, "R2000 should use LWPOLYLINE"


class TestSemanticDeterminism:
    """Tests for deterministic serialization (semantic, not byte-level)."""

    def _extract_entity_summary(self, doc):
        """Extract semantic summary of document entities."""
        summary = []
        for entity in doc.modelspace():
            entry = {
                "type": entity.dxftype(),
                "layer": entity.dxf.layer,
            }

            if entity.dxftype() == "LINE":
                entry["start"] = (
                    round(entity.dxf.start.x, 3),
                    round(entity.dxf.start.y, 3),
                )
                entry["end"] = (
                    round(entity.dxf.end.x, 3),
                    round(entity.dxf.end.y, 3),
                )
            elif entity.dxftype() == "LWPOLYLINE":
                entry["points"] = [
                    (round(p[0], 3), round(p[1], 3))
                    for p in entity.get_points("xy")
                ]
                entry["closed"] = entity.closed

            summary.append(entry)

        # Sort by type and layer for deterministic comparison
        return sorted(summary, key=lambda x: (x["type"], x["layer"]))

    def test_r12_deterministic_structure(self):
        """Same R12 input should produce same semantic structure."""
        from app.util.dxf_compat import create_document, add_polyline

        points = [(0, 0), (100, 0), (100, 50), (0, 50)]

        # First generation
        doc1 = create_document(version="R12")
        add_polyline(doc1.modelspace(), points, layer="BODY", closed=True, version="R12")
        summary1 = self._extract_entity_summary(doc1)

        # Second generation (same input)
        doc2 = create_document(version="R12")
        add_polyline(doc2.modelspace(), points, layer="BODY", closed=True, version="R12")
        summary2 = self._extract_entity_summary(doc2)

        assert summary1 == summary2, "R12 outputs should be semantically identical"

    def test_r2000_deterministic_structure(self):
        """Same R2000 input should produce same semantic structure."""
        from app.util.dxf_compat import create_document, add_polyline

        points = [(0, 0), (100, 0), (100, 50), (0, 50)]

        # First generation
        doc1 = create_document(version="R2000")
        add_polyline(doc1.modelspace(), points, layer="BODY", closed=True, version="R2000")
        summary1 = self._extract_entity_summary(doc1)

        # Second generation (same input)
        doc2 = create_document(version="R2000")
        add_polyline(doc2.modelspace(), points, layer="BODY", closed=True, version="R2000")
        summary2 = self._extract_entity_summary(doc2)

        assert summary1 == summary2, "R2000 outputs should be semantically identical"

    def test_coordinate_precision_stable(self):
        """Coordinate precision should be consistent (3 decimal places)."""
        from app.util.dxf_compat import create_document, add_polyline

        # Use coordinates that could have floating point issues
        points = [(0.1 + 0.2, 0), (100.123456789, 50.999999999)]

        doc = create_document(version="R12")
        add_polyline(doc.modelspace(), points, layer="TEST", version="R12")

        lines = [e for e in doc.modelspace() if e.dxftype() == "LINE"]
        assert len(lines) == 1

        # Verify coordinates are preserved (ezdxf handles internal precision)
        line = lines[0]
        assert abs(line.dxf.start.x - 0.3) < 0.001
        assert abs(line.dxf.end.x - 100.123456789) < 0.0001


class TestVersionValidation:
    """Tests for version validation."""

    def test_invalid_version_raises(self):
        """Invalid version should raise ValueError."""
        from app.util.dxf_compat import create_document

        with pytest.raises(ValueError, match="Invalid DXF version"):
            create_document(version="R1")

    def test_version_aliases_work(self):
        """Version aliases (R15, R16, etc.) should work."""
        from app.util.dxf_compat import validate_version

        assert validate_version("R15") == "R2000"
        assert validate_version("R16") == "R2004"
        assert validate_version("R17") == "R2007"
        assert validate_version("R18") == "R2010"

    def test_case_insensitive_versions(self):
        """Version strings should be case-insensitive."""
        from app.util.dxf_compat import validate_version

        assert validate_version("r12") == "R12"
        assert validate_version("R12") == "R12"
        assert validate_version("r2000") == "R2000"


class TestLayerDeterminism:
    """Tests for layer name determinism."""

    def test_multiple_layers_deterministic(self):
        """Multiple layers should be created deterministically."""
        from app.util.dxf_compat import create_document, add_polyline

        def create_multi_layer_doc():
            doc = create_document(version="R12")
            msp = doc.modelspace()
            add_polyline(msp, [(0, 0), (10, 10)], layer="LAYER_A", version="R12")
            add_polyline(msp, [(20, 20), (30, 30)], layer="LAYER_B", version="R12")
            add_polyline(msp, [(40, 40), (50, 50)], layer="LAYER_C", version="R12")
            return doc

        doc1 = create_multi_layer_doc()
        doc2 = create_multi_layer_doc()

        layers1 = sorted([e.dxf.layer for e in doc1.modelspace()])
        layers2 = sorted([e.dxf.layer for e in doc2.modelspace()])

        assert layers1 == layers2, "Layer assignments should be deterministic"
