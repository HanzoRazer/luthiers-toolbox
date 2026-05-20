"""
Tests for list_semantic_owners.py

Tests verify:
- Script execution
- Registry loading
- Domain filtering
- Term lookup
- JSON output format
- Deterministic output via --include-timestamp flag

Part of Governance Execution Alignment Sprint.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "governance" / "list_semantic_owners.py"
REGISTRY_PATH = REPO_ROOT / "docs" / "governance" / "ontology" / "semantic_registry.json"


class TestScriptExecution:
    """Test basic script execution."""

    def test_script_exists(self):
        """Script must exist."""
        assert SCRIPT_PATH.exists()

    def test_registry_exists(self):
        """Semantic registry must exist."""
        assert REGISTRY_PATH.exists()

    def test_default_run_exits_zero(self):
        """Default run should exit 0."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )
        assert result.returncode == 0


class TestRegistryLoading:
    """Test registry loading."""

    def test_registry_is_valid_json(self):
        """Registry must be valid JSON."""
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "terms" in data

    def test_terms_have_owner_domain(self):
        """Each term should have an owner_domain."""
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        for term_name, term_data in data.get("terms", {}).items():
            assert "owner_domain" in term_data, f"Term {term_name} missing owner_domain"


class TestJsonOutput:
    """Test JSON output functionality."""

    def test_json_flag_produces_valid_json(self):
        """--json flag should produce valid JSON."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--json"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )
        output = json.loads(result.stdout)
        assert "summary" in output
        assert "findings" in output

    def test_json_has_normalized_fields(self):
        """JSON output should have normalized fields."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--json"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )
        output = json.loads(result.stdout)
        assert output["script"] == "scripts/governance/list_semantic_owners.py"
        assert output["passed"] is True
        assert output["severity"] == "informational"
        assert "summary" in output
        assert "findings" in output
        assert "generated_at" in output

    def test_json_output_file(self):
        """--json-output should write to file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--json-output", output_path],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
                timeout=60,
            )
            assert result.returncode == 0

            with open(output_path, "r", encoding="utf-8") as f:
                output = json.load(f)

            assert "summary" in output
            assert "findings" in output
        finally:
            Path(output_path).unlink(missing_ok=True)


class TestDeterministicOutput:
    """Test deterministic output for CI reproducibility."""

    def test_default_has_no_timestamp(self):
        """Default run should have null generated_at for determinism."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--json"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )
        output = json.loads(result.stdout)
        assert output["generated_at"] is None

    def test_include_timestamp_adds_timestamp(self):
        """--include-timestamp should add generated_at."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--json", "--include-timestamp"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )
        output = json.loads(result.stdout)
        assert output["generated_at"] is not None
        assert "T" in output["generated_at"]  # ISO format


class TestDomainFilter:
    """Test domain filtering."""

    def test_domain_filter_returns_matching_terms(self):
        """--domain should filter terms by domain."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--json", "--domain", "Governance Layer"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )
        output = json.loads(result.stdout)
        assert output["summary"]["domain"] == "Governance Layer"
        assert output["summary"]["terms_found"] > 0

    def test_domain_filter_case_insensitive(self):
        """Domain filter should be case insensitive."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--json", "--domain", "governance layer"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )
        output = json.loads(result.stdout)
        assert output["summary"]["terms_found"] > 0


class TestTermLookup:
    """Test single term lookup."""

    def test_term_lookup_returns_details(self):
        """--term should return details for a specific term."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--json", "--term", "intent"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )
        output = json.loads(result.stdout)
        assert output["summary"]["terms_found"] == 1
        assert len(output["findings"]) == 1
        assert output["findings"][0]["term"] == "intent"

    def test_term_lookup_unknown_term(self):
        """Unknown term should return empty findings."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--json", "--term", "nonexistent_term_xyz"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )
        output = json.loads(result.stdout)
        assert output["summary"]["terms_found"] == 0
        assert len(output["findings"]) == 0


class TestQuietMode:
    """Test quiet mode behavior."""

    def test_quiet_suppresses_human_output(self):
        """--quiet should suppress human-readable output."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--quiet"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )
        assert "SEMANTIC TERM OWNERSHIP" not in result.stdout

    def test_quiet_with_json_still_outputs_json(self):
        """--quiet --json should still output JSON."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--quiet", "--json"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )
        output = json.loads(result.stdout)
        assert "summary" in output


class TestSummaryContent:
    """Test summary content for default run."""

    def test_summary_has_totals(self):
        """Summary should have total counts."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--json"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )
        output = json.loads(result.stdout)
        summary = output["summary"]
        assert "total_domains" in summary
        assert "total_terms" in summary
        assert "terms_by_domain" in summary

    def test_findings_grouped_by_domain(self):
        """Findings should be grouped by domain."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--json"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )
        output = json.loads(result.stdout)
        for finding in output["findings"]:
            assert "domain" in finding
            assert "terms" in finding
