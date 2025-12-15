"""Saw Lab Legacy Fixture Compatibility Tests."""
import pytest
from pathlib import Path
from tests.helpers.load_fixtures import load_json, FIXTURES_DIR
from app.cnc_production.schemas.saw_lab_compat import SawRunsFileCompat, SawTelemetryFileCompat

LEGACY = FIXTURES_DIR / "cnc_production" / "saw_lab_legacy"

class TestSawRunsCompat:
    @pytest.fixture
    def runs(self):
        p = LEGACY / "saw_runs.legacy.json"
        return load_json(p) if p.exists() else pytest.skip("Fixture missing")

    def test_loads(self, runs):
        doc = SawRunsFileCompat.parse_payload(runs)
        assert len(doc.runs) > 0

    def test_has_ids(self, runs):
        doc = SawRunsFileCompat.parse_payload(runs)
        assert all(r.normalized_id() != "UNKNOWN_RUN" for r in doc.runs)

class TestSawTelemetryCompat:
    @pytest.fixture
    def telemetry(self):
        p = LEGACY / "saw_telemetry.legacy.json"
        return load_json(p) if p.exists() else pytest.skip("Fixture missing")

    def test_loads(self, telemetry):
        doc = SawTelemetryFileCompat.parse_payload(telemetry)
        assert len(doc.runs) > 0

    def test_dense_samples(self, telemetry):
        doc = SawTelemetryFileCompat.parse_payload(telemetry)
        assert doc.total_samples > 10
