"""
Tests for build_governance_inventory.py

Tests verify:
- Script execution
- Classification categories
- Output file generation
- Report structure

Part of Governance Execution Alignment Sprint.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "governance" / "build_governance_inventory.py"
DEFAULT_JSON = REPO_ROOT / "reports" / "governance" / "governance_inventory.json"
DEFAULT_MD = REPO_ROOT / "reports" / "governance" / "governance_inventory.md"


class TestScriptExecution:
    """Test basic script execution."""

    def test_script_exists(self):
        """Script must exist."""
        assert SCRIPT_PATH.exists()


class TestExistingOutput:
    """Test existing output files from default run."""

    def test_json_output_exists(self):
        """JSON output should exist from default run."""
        assert DEFAULT_JSON.exists(), "Run build_governance_inventory.py first"

    def test_markdown_output_exists(self):
        """Markdown output should exist from default run."""
        assert DEFAULT_MD.exists(), "Run build_governance_inventory.py first"


class TestJsonStructure:
    """Test JSON output structure."""

    @pytest.fixture
    def inventory_data(self):
        """Load existing inventory JSON data."""
        if not DEFAULT_JSON.exists():
            pytest.skip("Inventory JSON not generated yet")
        with open(DEFAULT_JSON, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_has_generated_at(self, inventory_data):
        """JSON should have generated_at timestamp."""
        assert "generated_at" in inventory_data

    def test_has_summary(self, inventory_data):
        """JSON should have summary section."""
        assert "summary" in inventory_data

    def test_has_documents(self, inventory_data):
        """JSON should have documents list."""
        assert "documents" in inventory_data
        assert isinstance(inventory_data["documents"], list)

    def test_summary_has_category_counts(self, inventory_data):
        """Summary should have counts for each category."""
        summary = inventory_data["summary"]
        assert "enforced" in summary
        assert "consumed" in summary
        assert "advisory" in summary
        assert "orphaned" in summary
        assert "total_docs" in summary


class TestClassification:
    """Test document classification."""

    @pytest.fixture
    def inventory_data(self):
        """Load existing inventory JSON data."""
        if not DEFAULT_JSON.exists():
            pytest.skip("Inventory JSON not generated yet")
        with open(DEFAULT_JSON, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_all_docs_have_category(self, inventory_data):
        """All documents should have a category."""
        valid_categories = {"enforced", "consumed", "advisory", "orphaned"}
        for doc in inventory_data["documents"]:
            assert "category" in doc
            assert doc["category"] in valid_categories

    def test_all_docs_have_path(self, inventory_data):
        """All documents should have a path."""
        for doc in inventory_data["documents"]:
            assert "path" in doc
            assert doc["path"].startswith("docs/governance/")

    def test_category_totals_match(self, inventory_data):
        """Category counts should match total."""
        summary = inventory_data["summary"]
        expected_total = (
            summary["enforced"] +
            summary["consumed"] +
            summary["advisory"] +
            summary["orphaned"]
        )
        assert summary["total_docs"] == expected_total
        assert len(inventory_data["documents"]) == summary["total_docs"]

    def test_has_enforced_docs(self, inventory_data):
        """Should have at least some enforced docs."""
        summary = inventory_data["summary"]
        assert summary["enforced"] > 0, "Expected at least one enforced doc"

    def test_has_consumed_docs(self, inventory_data):
        """Should have at least some consumed docs."""
        summary = inventory_data["summary"]
        assert summary["consumed"] > 0, "Expected at least one consumed doc"


class TestDeterminism:
    """Test output determinism."""

    def test_json_output_is_deterministic(self, tmp_path):
        """Running scanner twice should produce identical JSON output."""
        output1 = tmp_path / "inventory1.json"
        output2 = tmp_path / "inventory2.json"

        # Run scanner twice (default mode, no timestamp)
        result1 = subprocess.run(
            [sys.executable, str(SCRIPT_PATH),
             "--json-output", str(output1),
             "--md-output", str(tmp_path / "md1.md"),
             "--quiet"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=120
        )
        assert result1.returncode == 0, f"First run failed: {result1.stderr}"

        result2 = subprocess.run(
            [sys.executable, str(SCRIPT_PATH),
             "--json-output", str(output2),
             "--md-output", str(tmp_path / "md2.md"),
             "--quiet"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=120
        )
        assert result2.returncode == 0, f"Second run failed: {result2.stderr}"

        # Compare outputs
        data1 = json.loads(output1.read_text())
        data2 = json.loads(output2.read_text())

        assert data1 == data2, "JSON outputs differ between runs"

    def test_no_timestamp_by_default(self, tmp_path):
        """Default mode should not include timestamp."""
        output = tmp_path / "inventory.json"

        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH),
             "--json-output", str(output),
             "--md-output", str(tmp_path / "md.md"),
             "--quiet"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=120
        )
        assert result.returncode == 0

        data = json.loads(output.read_text())
        assert "generated_at" not in data, "Timestamp present in default mode"

    def test_timestamp_with_flag(self, tmp_path):
        """--include-timestamp should add timestamp."""
        output = tmp_path / "inventory.json"

        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH),
             "--json-output", str(output),
             "--md-output", str(tmp_path / "md.md"),
             "--include-timestamp",
             "--quiet"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=120
        )
        assert result.returncode == 0

        data = json.loads(output.read_text())
        assert "generated_at" in data, "Timestamp missing with --include-timestamp"
