"""
Unit tests for cost attribution mapper.

Tests the telemetry -> cost facts mapping logic.
"""

import pytest
from pathlib import Path
from datetime import datetime, timezone

# Import will work when run from services/api directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.cost_attribution.mapper import telemetry_to_cost_facts
from app.cost_attribution.models import CostFact


def create_test_policy(tmp_path: Path) -> None:
    """Create a test policy file in the temp directory."""
    (tmp_path / "contracts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "contracts" / "telemetry_cost_mapping_policy_v1.json").write_text(
        """
        {
          "schema_id": "telemetry_cost_mapping_policy",
          "schema_version": "v1",
          "allowed_mappings": {
            "hardware_performance.cpu_hours": "compute_cost_hours",
            "hardware_performance.amp_draw_avg": "energy_amp_hours",
            "lifecycle.power_cycles": "wear_cycles"
          },
          "forbidden_metric_key_substrings": [
            "player",
            "lesson",
            "practice",
            "accuracy",
            "timing"
          ]
        }
        """.strip(),
        encoding="utf-8",
    )


class TestTelemetryToCostFacts:
    """Test cases for telemetry_to_cost_facts mapper."""

    def test_maps_allowed_metrics_only(self, tmp_path: Path):
        """Only metrics in policy allowed_mappings should produce CostFacts."""
        create_test_policy(tmp_path)

        payload = {
            "schema_id": "smart_guitar_toolbox_telemetry",
            "schema_version": "v1",
            "emitted_at_utc": "2026-01-13T12:00:00Z",
            "instrument_id": "sg_ABC123",
            "manufacturing_batch_id": "batch_001",
            "telemetry_category": "hardware_performance",
            "metrics": {
                "cpu_hours": {"value": 1.25, "unit": "hours", "aggregation": "sum"},
                "memory_usage": {"value": 512, "unit": "bytes", "aggregation": "avg"},  # Not in policy
            }
        }

        facts, warnings = telemetry_to_cost_facts(tmp_path, payload)

        assert len(facts) == 1
        assert facts[0].cost_dimension == "compute_cost_hours"
        assert facts[0].value == 1.25
        assert facts[0].source_metric_key == "hardware_performance.cpu_hours"

    def test_blocks_forbidden_metric_keys(self, tmp_path: Path):
        """Metrics with forbidden substrings should be skipped with warning."""
        create_test_policy(tmp_path)

        payload = {
            "schema_id": "smart_guitar_toolbox_telemetry",
            "schema_version": "v1",
            "emitted_at_utc": "2026-01-13T12:00:00Z",
            "instrument_id": "sg_ABC123",
            "manufacturing_batch_id": "batch_001",
            "telemetry_category": "hardware_performance",
            "metrics": {
                "cpu_hours": {"value": 1.25, "unit": "hours", "aggregation": "sum"},
                "player_id_hash": {"value": 1, "unit": "count", "aggregation": "sum"},  # Forbidden
            }
        }

        facts, warnings = telemetry_to_cost_facts(tmp_path, payload)

        assert len(facts) == 1  # Only cpu_hours mapped
        assert len(warnings) == 1
        assert "player_id_hash" in warnings[0]
        assert "forbidden" in warnings[0].lower()

    def test_empty_metrics_returns_empty_facts(self, tmp_path: Path):
        """Empty metrics dict should return empty facts list."""
        create_test_policy(tmp_path)

        payload = {
            "schema_id": "smart_guitar_toolbox_telemetry",
            "schema_version": "v1",
            "emitted_at_utc": "2026-01-13T12:00:00Z",
            "instrument_id": "sg_ABC123",
            "manufacturing_batch_id": "batch_001",
            "telemetry_category": "hardware_performance",
            "metrics": {}
        }

        facts, warnings = telemetry_to_cost_facts(tmp_path, payload)

        assert len(facts) == 0
        assert len(warnings) == 0

    def test_unmapped_category_metric_ignored(self, tmp_path: Path):
        """Metrics from categories not in policy should be ignored."""
        create_test_policy(tmp_path)

        payload = {
            "schema_id": "smart_guitar_toolbox_telemetry",
            "schema_version": "v1",
            "emitted_at_utc": "2026-01-13T12:00:00Z",
            "instrument_id": "sg_ABC123",
            "manufacturing_batch_id": "batch_001",
            "telemetry_category": "environment",  # No mappings for this category
            "metrics": {
                "temperature_c": {"value": 25.0, "unit": "celsius", "aggregation": "avg"},
            }
        }

        facts, warnings = telemetry_to_cost_facts(tmp_path, payload)

        assert len(facts) == 0
        assert len(warnings) == 0

    def test_cost_fact_fields_populated_correctly(self, tmp_path: Path):
        """All CostFact fields should be populated from payload."""
        create_test_policy(tmp_path)

        payload = {
            "schema_id": "smart_guitar_toolbox_telemetry",
            "schema_version": "v1",
            "emitted_at_utc": "2026-01-13T12:00:00Z",
            "instrument_id": "sg_INST_001",
            "manufacturing_batch_id": "batch_XYZ",
            "telemetry_category": "hardware_performance",
            "metrics": {
                "cpu_hours": {"value": 2.5, "unit": "hours", "aggregation": "sum"},
            },
            "design_revision_id": "rev_123",
            "hardware_sku": "SKU_ABC",
            "component_lot_id": "LOT_456",
        }

        facts, warnings = telemetry_to_cost_facts(tmp_path, payload)

        assert len(facts) == 1
        cf = facts[0]
        assert cf.manufacturing_batch_id == "batch_XYZ"
        assert cf.instrument_id == "sg_INST_001"
        assert cf.cost_dimension == "compute_cost_hours"
        assert cf.value == 2.5
        assert cf.unit == "hours"
        assert cf.aggregation == "sum"
        assert cf.source_metric_key == "hardware_performance.cpu_hours"
        assert cf.telemetry_category == "hardware_performance"
        assert cf.telemetry_schema_version == "v1"
        assert cf.meta["design_revision_id"] == "rev_123"
        assert cf.meta["hardware_sku"] == "SKU_ABC"
        assert cf.meta["component_lot_id"] == "LOT_456"

    def test_multiple_metrics_multiple_facts(self, tmp_path: Path):
        """Multiple allowed metrics should produce multiple CostFacts."""
        create_test_policy(tmp_path)

        payload = {
            "schema_id": "smart_guitar_toolbox_telemetry",
            "schema_version": "v1",
            "emitted_at_utc": "2026-01-13T12:00:00Z",
            "instrument_id": "sg_ABC123",
            "manufacturing_batch_id": "batch_001",
            "telemetry_category": "hardware_performance",
            "metrics": {
                "cpu_hours": {"value": 1.5, "unit": "hours", "aggregation": "sum"},
                "amp_draw_avg": {"value": 0.75, "unit": "amps", "aggregation": "avg"},
            }
        }

        facts, warnings = telemetry_to_cost_facts(tmp_path, payload)

        assert len(facts) == 2
        dimensions = {f.cost_dimension for f in facts}
        assert dimensions == {"compute_cost_hours", "energy_amp_hours"}

    def test_datetime_parsing_with_z_suffix(self, tmp_path: Path):
        """ISO datetime with Z suffix should be parsed correctly."""
        create_test_policy(tmp_path)

        payload = {
            "schema_id": "smart_guitar_toolbox_telemetry",
            "schema_version": "v1",
            "emitted_at_utc": "2026-01-13T12:30:45Z",
            "instrument_id": "sg_ABC123",
            "manufacturing_batch_id": "batch_001",
            "telemetry_category": "hardware_performance",
            "metrics": {
                "cpu_hours": {"value": 1.0, "unit": "hours", "aggregation": "sum"},
            }
        }

        facts, warnings = telemetry_to_cost_facts(tmp_path, payload)

        assert len(facts) == 1
        assert facts[0].emitted_at_utc.hour == 12
        assert facts[0].emitted_at_utc.minute == 30
        assert facts[0].emitted_at_utc.second == 45

    def test_datetime_parsing_with_offset(self, tmp_path: Path):
        """ISO datetime with timezone offset should be parsed correctly."""
        create_test_policy(tmp_path)

        payload = {
            "schema_id": "smart_guitar_toolbox_telemetry",
            "schema_version": "v1",
            "emitted_at_utc": "2026-01-13T12:30:45+00:00",
            "instrument_id": "sg_ABC123",
            "manufacturing_batch_id": "batch_001",
            "telemetry_category": "hardware_performance",
            "metrics": {
                "cpu_hours": {"value": 1.0, "unit": "hours", "aggregation": "sum"},
            }
        }

        facts, warnings = telemetry_to_cost_facts(tmp_path, payload)

        assert len(facts) == 1
        assert facts[0].emitted_at_utc.hour == 12

    def test_lifecycle_category_mapping(self, tmp_path: Path):
        """Lifecycle category metrics should be mapped correctly."""
        create_test_policy(tmp_path)

        payload = {
            "schema_id": "smart_guitar_toolbox_telemetry",
            "schema_version": "v1",
            "emitted_at_utc": "2026-01-13T12:00:00Z",
            "instrument_id": "sg_ABC123",
            "manufacturing_batch_id": "batch_001",
            "telemetry_category": "lifecycle",
            "metrics": {
                "power_cycles": {"value": 150, "unit": "count", "aggregation": "sum"},
            }
        }

        facts, warnings = telemetry_to_cost_facts(tmp_path, payload)

        assert len(facts) == 1
        assert facts[0].cost_dimension == "wear_cycles"
        assert facts[0].value == 150

    def test_case_insensitive_forbidden_check(self, tmp_path: Path):
        """Forbidden substring check should be case-insensitive."""
        create_test_policy(tmp_path)

        payload = {
            "schema_id": "smart_guitar_toolbox_telemetry",
            "schema_version": "v1",
            "emitted_at_utc": "2026-01-13T12:00:00Z",
            "instrument_id": "sg_ABC123",
            "manufacturing_batch_id": "batch_001",
            "telemetry_category": "hardware_performance",
            "metrics": {
                "cpu_hours": {"value": 1.0, "unit": "hours", "aggregation": "sum"},
                "PLAYER_stats": {"value": 1, "unit": "count", "aggregation": "sum"},  # Should be blocked
            }
        }

        facts, warnings = telemetry_to_cost_facts(tmp_path, payload)

        assert len(facts) == 1  # Only cpu_hours
        assert len(warnings) == 1
        assert "PLAYER_stats" in warnings[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
