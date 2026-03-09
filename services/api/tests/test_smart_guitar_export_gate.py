"""
Smart Guitar Export Gate tests.

These tests verify that the Smart Guitar export module follows boundary rules:
- No manufacturing artifacts (G-code, CAM, DXF)
- No RMOS authority artifacts (run IDs, decisions)
- No secrets (API keys, tokens)

Currently a stub - will be populated when smart_guitar_export module is implemented.
"""

import pytest


class TestSmartGuitarExportBoundary:
    """Verify export boundary rules are enforced."""

    def test_placeholder_export_boundary_ready(self):
        """Placeholder test - module not yet implemented."""
        # When app.smart_guitar_export is implemented, add real tests here
        assert True, "Smart Guitar Export module pending implementation"

    def test_schema_contract_exists(self):
        """Verify the schema contract file exists."""
        from pathlib import Path

        # Schema should be at contracts/toolbox_smart_guitar_safe_export_v1.schema.json
        repo_root = Path(__file__).parent.parent.parent.parent
        schema_path = repo_root / "contracts" / "toolbox_smart_guitar_safe_export_v1.schema.json"

        assert schema_path.exists(), f"Schema not found at {schema_path}"
