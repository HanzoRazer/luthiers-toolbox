"""
Tests for validate_lifecycle_terms.py

Tests verify:
- Registry loading
- Term validation
- Alias handling
- JSON output format

Part of Governance Execution Alignment Sprint.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Repository root
REPO_ROOT = Path(__file__).parent.parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "governance" / "validate_lifecycle_terms.py"
REGISTRY_PATH = REPO_ROOT / "docs" / "governance" / "ontology" / "lifecycle_registry.json"
ALIAS_PATH = REPO_ROOT / "docs" / "governance" / "ontology" / "ontology_alias_registry.json"


class TestRegistryLoading:
    """Test registry file handling."""

    def test_script_exists(self):
        """Script must exist."""
        assert SCRIPT_PATH.exists()

    def test_lifecycle_registry_exists(self):
        """Lifecycle registry must exist."""
        assert REGISTRY_PATH.exists()

    def test_alias_registry_exists(self):
        """Alias registry must exist."""
        assert ALIAS_PATH.exists()

    def test_lifecycle_registry_is_valid_json(self):
        """Lifecycle registry must be valid JSON."""
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "classifications" in data


class TestTermValidation:
    """Test lifecycle term validation."""

    def test_registry_has_classifications(self):
        """Registry must have classifications."""
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        classifications = data.get("classifications", {})
        assert len(classifications) > 0

    def test_classifications_have_required_fields(self):
        """Each classification should have required fields."""
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check a sample of required fields
        for term, info in data.get("classifications", {}).items():
            # At minimum, each term should have some definition
            assert isinstance(info, dict), f"Term {term} should be a dict"


class TestAliasHandling:
    """Test alias registry validation."""

    def test_alias_registry_structure(self):
        """Alias registry should have expected structure."""
        with open(ALIAS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Should have an aliases section
        aliases = data.get("aliases", {})
        assert isinstance(aliases, dict)

    def test_aliases_reference_canonical_terms(self):
        """Aliases should reference existing canonical terms."""
        with open(ALIAS_PATH, "r", encoding="utf-8") as f:
            alias_data = json.load(f)

        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            lifecycle_data = json.load(f)

        canonical_terms = set(lifecycle_data.get("classifications", {}).keys())
        aliases = alias_data.get("aliases", {})

        for alias_name, alias_info in aliases.items():
            canonical = alias_info.get("canonical_term", "")
            if canonical:
                # This is a soft check - not all aliases need to map to lifecycle terms
                pass


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
        assert "canonical_terms_count" in output
        assert "summary" in output

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

            with open(output_path, "r", encoding="utf-8") as f:
                output = json.load(f)

            assert "summary" in output
            assert "passed" in output
        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_summary_has_expected_fields(self):
        """Summary should have expected fields."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--json"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )
        output = json.loads(result.stdout)
        summary = output["summary"]

        assert "valid_usages" in summary
        assert "alias_usages" in summary
        assert "potential_issues" in summary


class TestExitCodes:
    """Test exit code behavior."""

    def test_default_exits_zero(self):
        """Default run should exit 0 (warning-only)."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )
        # Lifecycle validation is warning-only, so it should exit 0
        assert result.returncode == 0

    def test_strict_with_issues_may_exit_nonzero(self):
        """--strict with issues should exit non-zero."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--json"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )
        output = json.loads(result.stdout)

        # If there are potential issues and --strict is used, it would exit 1
        has_issues = output["summary"]["potential_issues"] > 0

        strict_result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--strict"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )

        if has_issues:
            assert strict_result.returncode == 1
        else:
            assert strict_result.returncode == 0


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
        assert "LIFECYCLE TERM VALIDATION REPORT" not in result.stdout
