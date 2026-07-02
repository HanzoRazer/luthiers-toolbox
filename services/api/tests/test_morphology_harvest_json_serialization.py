"""
Morphology Harvest JSON Serialization Tests
============================================

Regression tests for ContourCategory enum JSON serialization fix.

Test cases per handoff spec:
1. ContourCategory enum serializes to string
2. Nested dict containing ContourCategory serializes
3. List of candidate dicts containing enum values serializes
4. Dataclass containing enum field serializes
5. E2E validation report can be json.dumps() without TypeError

Author: Production Shop
Date: 2026-05-19
Sprint: IBG Morphology Harvest 1B Unblock
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest


class ContourCategory(Enum):
    """Mock of vectorizer ContourCategory for testing."""
    BODY_OUTLINE = "body_outline"
    NECK_POCKET = "neck_pocket"
    BRIDGE = "bridge"
    PICKUP = "pickup"
    SOUNDHOLE = "soundhole"
    BINDING = "binding"
    UNKNOWN = "unknown"


@dataclass
class MockCandidate:
    """Mock candidate with enum field."""
    category: ContourCategory
    confidence: float = 0.0
    area_mm2: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class TestJsonSafeImport:
    """Test json_safe utility can be imported."""

    def test_import_json_safe(self):
        from app.instrument_geometry.body.ibg.morphology_harvest.json_utils import json_safe
        assert callable(json_safe)

    def test_import_safe_json_encoder(self):
        from app.instrument_geometry.body.ibg.morphology_harvest.json_utils import SafeJSONEncoder
        assert issubclass(SafeJSONEncoder, json.JSONEncoder)

    def test_import_e2e_spine_runner_uses_phase4_dimension_adapter(self, tmp_path, monkeypatch):
        """E2ESpineRunner imports cleanly and wires the Phase 4 dimension adapter.

        Witnesses the #9 fix: the module previously imported adapter symbols that
        did not exist (dead-on-import). It now imports get_phase4_adapter and
        stores it under its semantic name, ``dimension_adapter``. OUTPUT_DIR is
        redirected to tmp_path so construction does not touch the repo tree.
        """
        from app.instrument_geometry.body.ibg.morphology_harvest import (
            e2e_spine_runner as mod,
        )

        monkeypatch.setattr(mod, "OUTPUT_DIR", tmp_path / "e2e_spine")

        runner = mod.E2ESpineRunner(corpus_root=str(tmp_path))

        # The adapter is the Phase 4 dimension-association adapter, exposed under
        # a role-accurate name (not aliased as a generic blueprint adapter).
        assert runner.dimension_adapter.name == "Phase4DimensionAssociation"
        assert callable(runner.dimension_adapter.extract_dimension_values)

    def test_e2e_spine_runner_requires_corpus_root(self):
        """corpus_root is required — no leaked hardcoded default path (#10 class)."""
        from app.instrument_geometry.body.ibg.morphology_harvest.e2e_spine_runner import (
            E2ESpineRunner,
        )

        with pytest.raises(ValueError):
            E2ESpineRunner()


class TestEnumSerialization:
    """Test ContourCategory enum serialization."""

    def test_enum_serializes_to_string(self):
        """ContourCategory enum serializes to its value string."""
        from app.instrument_geometry.body.ibg.morphology_harvest.json_utils import json_safe

        result = json_safe(ContourCategory.BODY_OUTLINE)
        assert result == "body_outline"
        assert isinstance(result, str)

    def test_enum_in_dict_serializes(self):
        """Dict containing ContourCategory serializes without error."""
        from app.instrument_geometry.body.ibg.morphology_harvest.json_utils import json_safe

        payload = {
            "category": ContourCategory.BODY_OUTLINE,
            "confidence": 0.95,
            "label": "main_body",
        }

        result = json_safe(payload)
        assert result["category"] == "body_outline"

        # Must not raise
        output = json.dumps(result)
        assert '"body_outline"' in output

    def test_nested_dict_with_enum_serializes(self):
        """Nested dict containing ContourCategory serializes."""
        from app.instrument_geometry.body.ibg.morphology_harvest.json_utils import json_safe

        payload = {
            "vectorizer_result": {
                "contours": [
                    {"category": ContourCategory.BODY_OUTLINE, "points": 100},
                    {"category": ContourCategory.NECK_POCKET, "points": 50},
                ],
                "metadata": {
                    "primary_category": ContourCategory.BODY_OUTLINE,
                }
            }
        }

        result = json_safe(payload)

        # Must not raise
        output = json.dumps(result)
        assert '"body_outline"' in output
        assert '"neck_pocket"' in output


class TestListSerialization:
    """Test lists containing enum values serialize."""

    def test_list_of_enums_serializes(self):
        """List of ContourCategory enums serializes."""
        from app.instrument_geometry.body.ibg.morphology_harvest.json_utils import json_safe

        payload = [
            ContourCategory.BODY_OUTLINE,
            ContourCategory.NECK_POCKET,
            ContourCategory.BRIDGE,
        ]

        result = json_safe(payload)
        assert result == ["body_outline", "neck_pocket", "bridge"]

        # Must not raise
        json.dumps(result)

    def test_list_of_candidate_dicts_serializes(self):
        """List of candidate dicts with enum values serializes."""
        from app.instrument_geometry.body.ibg.morphology_harvest.json_utils import json_safe

        candidates = [
            {
                "category": ContourCategory.BODY_OUTLINE,
                "confidence": 0.95,
                "area_mm2": 12500.0,
            },
            {
                "category": ContourCategory.NECK_POCKET,
                "confidence": 0.80,
                "area_mm2": 850.0,
            },
        ]

        result = json_safe(candidates)

        assert result[0]["category"] == "body_outline"
        assert result[1]["category"] == "neck_pocket"

        # Must not raise
        json.dumps(result)


class TestDataclassSerialization:
    """Test dataclass containing enum field serializes."""

    def test_dataclass_with_enum_serializes(self):
        """Dataclass containing enum field serializes via json_safe."""
        from app.instrument_geometry.body.ibg.morphology_harvest.json_utils import json_safe

        candidate = MockCandidate(
            category=ContourCategory.BODY_OUTLINE,
            confidence=0.95,
            area_mm2=12500.0,
            metadata={"source": "vectorizer"},
        )

        result = json_safe(candidate)

        assert isinstance(result, dict)
        assert result["category"] == "body_outline"
        assert result["confidence"] == 0.95

        # Must not raise
        json.dumps(result)


class TestSafeJSONEncoder:
    """Test SafeJSONEncoder class."""

    def test_encoder_handles_enum(self):
        """SafeJSONEncoder handles enum in json.dumps."""
        from app.instrument_geometry.body.ibg.morphology_harvest.json_utils import SafeJSONEncoder

        payload = {"category": ContourCategory.BODY_OUTLINE}

        # Must not raise
        output = json.dumps(payload, cls=SafeJSONEncoder)
        assert '"body_outline"' in output

    def test_encoder_handles_path(self):
        """SafeJSONEncoder handles Path objects."""
        from app.instrument_geometry.body.ibg.morphology_harvest.json_utils import SafeJSONEncoder

        payload = {"path": Path("/some/file.dxf")}

        # Must not raise
        output = json.dumps(payload, cls=SafeJSONEncoder)
        assert "file.dxf" in output


class TestHarvestRecordSerialization:
    """Test HarvestRecord serialization (integration)."""

    def test_harvest_record_to_dict_serializes(self):
        """HarvestRecord.to_dict() produces JSON-safe output."""
        from app.instrument_geometry.body.ibg.morphology_harvest.schema import (
            HarvestRecord,
            HarvestSource,
        )

        record = HarvestRecord(
            harvest_id="test_001",
            source_pdf="/test/blueprint.pdf",
            harvest_source=HarvestSource.VECTOR_TEXT,
        )

        result = record.to_dict()

        # Must not raise
        output = json.dumps(result)
        assert "test_001" in output

    def test_harvest_record_with_upstream_data_serializes(self):
        """HarvestRecord with upstream vectorizer data serializes."""
        from app.instrument_geometry.body.ibg.morphology_harvest.schema import (
            HarvestRecord,
            HarvestSource,
        )

        record = HarvestRecord(
            harvest_id="test_002",
            source_pdf="/test/blueprint.pdf",
            harvest_source=HarvestSource.VECTOR_TEXT,
        )

        # Simulate upstream data containing ContourCategory enum
        record.upstream_sources = {
            "vectorizer": {
                "contours": [
                    {"category": ContourCategory.BODY_OUTLINE, "points": 100},
                ],
            }
        }

        result = record.to_dict()

        # Must not raise
        output = json.dumps(result)
        assert "test_002" in output


class TestE2EResultSerialization:
    """Test E2E spine result serialization (integration)."""

    def test_e2e_result_to_dict_serializes(self):
        """E2ESpineResult.to_dict() produces JSON-safe output."""
        from app.instrument_geometry.body.ibg.morphology_harvest.e2e_spine_runner import (
            E2ESpineResult,
        )
        from app.instrument_geometry.body.ibg.morphology_harvest.json_utils import json_safe

        result = E2ESpineResult(
            run_id="e2e_test_001",
            source_file="test.pdf",
            source_mode="pdf",
            timestamp="2026-05-19T12:00:00",
            vectorizer_success=True,
        )

        # Add mock body evidence with enum
        result.body_evidence_summary = {
            "candidates": [
                {"category": ContourCategory.BODY_OUTLINE, "confidence": 0.9},
            ]
        }

        safe_result = json_safe(result.to_dict())

        # Must not raise
        output = json.dumps(safe_result)
        assert "e2e_test_001" in output


class TestSchemaEnumSafeEncoder:
    """Test schema.py _EnumSafeEncoder."""

    def test_schema_encoder_exists(self):
        """_EnumSafeEncoder exists in schema.py."""
        from app.instrument_geometry.body.ibg.morphology_harvest.schema import (
            _EnumSafeEncoder,
        )
        assert issubclass(_EnumSafeEncoder, json.JSONEncoder)

    def test_schema_sanitize_function_exists(self):
        """_sanitize_for_json exists in schema.py."""
        from app.instrument_geometry.body.ibg.morphology_harvest.schema import (
            _sanitize_for_json,
        )
        assert callable(_sanitize_for_json)
