"""
Governance Compliance Test Suite

Tests verify governance infrastructure is correctly configured and enforced.
Part of Governance Remediation Infrastructure.

Run with:
    pytest tests/test_governance_compliance.py -v
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Repository root
REPO_ROOT = Path(__file__).parent.parent


class TestGovernanceManifest:
    """Test governance manifest structure and content."""

    @pytest.fixture
    def manifest(self):
        """Load governance manifest."""
        manifest_path = REPO_ROOT / "docs" / "governance" / "governance_manifest.json"
        if not manifest_path.exists():
            pytest.skip("Governance manifest not found")
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_manifest_exists(self):
        """Governance manifest must exist."""
        manifest_path = REPO_ROOT / "docs" / "governance" / "governance_manifest.json"
        assert manifest_path.exists(), "Governance manifest not found"

    def test_manifest_has_version(self, manifest):
        """Manifest must have version field."""
        assert "manifest_version" in manifest
        assert manifest["manifest_version"] == "1.0.0"

    def test_manifest_has_protected_systems(self, manifest):
        """Manifest must have protected_systems list."""
        assert "protected_systems" in manifest
        assert isinstance(manifest["protected_systems"], list)
        assert len(manifest["protected_systems"]) > 0

    def test_protected_systems_have_required_fields(self, manifest):
        """Each protected system must have required fields."""
        required_fields = ["id", "protection_level", "paths", "governance_doc"]

        for system in manifest["protected_systems"]:
            for field in required_fields:
                assert field in system, f"System {system.get('id', 'UNKNOWN')} missing field: {field}"

    def test_protection_levels_are_valid(self, manifest):
        """Protection levels must be valid enum values."""
        valid_levels = {"LOCKED", "STABILIZED", "MONITORED"}

        for system in manifest["protected_systems"]:
            level = system.get("protection_level")
            assert level in valid_levels, f"Invalid protection level: {level}"

    def test_governance_docs_exist(self, manifest):
        """Governance documentation files must exist."""
        for system in manifest["protected_systems"]:
            doc_path = REPO_ROOT / system.get("governance_doc", "")
            if doc_path.suffix == ".md":
                assert doc_path.exists(), f"Governance doc missing: {system['governance_doc']}"


class TestProtectedPathScript:
    """Test protected path check script."""

    def test_script_exists(self):
        """Protected path check script must exist."""
        script_path = REPO_ROOT / "scripts" / "check_protected_paths.py"
        assert script_path.exists(), "check_protected_paths.py not found"

    def test_script_syntax_valid(self):
        """Script must have valid Python syntax."""
        script_path = REPO_ROOT / "scripts" / "check_protected_paths.py"
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(script_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Syntax error in check_protected_paths.py: {result.stderr}"

    def test_script_runs_clean(self):
        """Script should run without errors when no files staged."""
        script_path = REPO_ROOT / "scripts" / "check_protected_paths.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT)
        )
        # Should pass (exit 0) when no protected files staged
        assert result.returncode == 0, f"Script failed: {result.stderr}"


class TestSprintNamespaceScript:
    """Test sprint namespace check script."""

    def test_script_exists(self):
        """Sprint namespace check script must exist."""
        script_path = REPO_ROOT / "scripts" / "check_sprint_namespace.py"
        assert script_path.exists(), "check_sprint_namespace.py not found"

    def test_script_syntax_valid(self):
        """Script must have valid Python syntax."""
        script_path = REPO_ROOT / "scripts" / "check_sprint_namespace.py"
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(script_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr}"

    def test_valid_namespaces_defined(self):
        """Valid namespaces must be defined."""
        script_path = REPO_ROOT / "scripts" / "check_sprint_namespace.py"
        content = script_path.read_text()

        expected_namespaces = ["VECTOR", "IBG", "BOE", "DXF", "CAM", "RMOS", "SPIRAL", "MRP"]
        for ns in expected_namespaces:
            assert f'"{ns}"' in content, f"Namespace {ns} not defined in script"


class TestSemanticLeakageScript:
    """Test semantic leakage detection script."""

    def test_script_exists(self):
        """Semantic leakage check script must exist."""
        script_path = REPO_ROOT / "scripts" / "check_semantic_leakage.py"
        assert script_path.exists(), "check_semantic_leakage.py not found"

    def test_script_syntax_valid(self):
        """Script must have valid Python syntax."""
        script_path = REPO_ROOT / "scripts" / "check_semantic_leakage.py"
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(script_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr}"


class TestFeedbackCorrectionGate:
    """PR-3: submit_correction remains DEAD in production services/."""

    def test_feedback_correction_script_exists(self):
        path = REPO_ROOT / "scripts" / "governance" / "check_feedback_correction_calls.py"
        assert path.is_file()

    def test_feedback_correction_script_runs_clean(self):
        path = REPO_ROOT / "scripts" / "governance" / "check_feedback_correction_calls.py"
        result = subprocess.run(
            [sys.executable, str(path)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, result.stderr or result.stdout


class TestSemanticSandboxImportGate:
    """Phase 0.5: block Tier A cognition/grid imports in services/."""

    def test_script_exists(self):
        script_path = REPO_ROOT / "scripts" / "governance" / "check_semantic_sandbox_imports.py"
        assert script_path.exists(), "check_semantic_sandbox_imports.py not found"

    def test_script_runs_clean(self):
        script_path = REPO_ROOT / "scripts" / "governance" / "check_semantic_sandbox_imports.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, (
            f"Semantic sandbox import gate failed:\n{result.stdout}\n{result.stderr}"
        )


class TestCapabilityRegistryScript:
    """Test capability registry validation script."""

    def test_script_exists(self):
        """Capability registry check script must exist."""
        script_path = REPO_ROOT / "scripts" / "check_capability_registry.py"
        assert script_path.exists(), "check_capability_registry.py not found"

    def test_script_syntax_valid(self):
        """Script must have valid Python syntax."""
        script_path = REPO_ROOT / "scripts" / "check_capability_registry.py"
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(script_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr}"


class TestManifestIndex:
    """Test manifest index document."""

    def test_manifest_index_exists(self):
        """Manifest index must exist."""
        index_path = REPO_ROOT / "docs" / "governance" / "MANIFEST_INDEX.md"
        assert index_path.exists(), "MANIFEST_INDEX.md not found"

    def test_manifest_index_lists_governance_manifest(self):
        """Index must list governance_manifest.json."""
        index_path = REPO_ROOT / "docs" / "governance" / "MANIFEST_INDEX.md"
        content = index_path.read_text()
        assert "governance_manifest.json" in content


class TestGovernanceTopologyDocs:
    """Test governance topology audit documents."""

    def test_topology_map_exists(self):
        """Governance topology map must exist."""
        doc_path = REPO_ROOT / "docs" / "governance" / "GOVERNANCE_TOPOLOGY_MAP.md"
        assert doc_path.exists(), "GOVERNANCE_TOPOLOGY_MAP.md not found"

    def test_authority_hierarchy_exists(self):
        """Governance authority hierarchy must exist."""
        doc_path = REPO_ROOT / "docs" / "governance" / "GOVERNANCE_AUTHORITY_HIERARCHY.md"
        assert doc_path.exists(), "GOVERNANCE_AUTHORITY_HIERARCHY.md not found"

    def test_duplication_audit_exists(self):
        """Governance duplication audit must exist."""
        doc_path = REPO_ROOT / "docs" / "governance" / "GOVERNANCE_DUPLICATION_AUDIT.md"
        assert doc_path.exists(), "GOVERNANCE_DUPLICATION_AUDIT.md not found"


class TestImplementationGuide:
    """Test implementation guide document."""

    def test_implementation_guide_exists(self):
        """Implementation guide must exist."""
        doc_path = REPO_ROOT / "docs" / "handoffs" / "GOVERNANCE_REMEDIATION_IMPLEMENTATION_GUIDE.md"
        assert doc_path.exists(), "GOVERNANCE_REMEDIATION_IMPLEMENTATION_GUIDE.md not found"

    def test_implementation_guide_has_sections(self):
        """Implementation guide must have key sections."""
        doc_path = REPO_ROOT / "docs" / "handoffs" / "GOVERNANCE_REMEDIATION_IMPLEMENTATION_GUIDE.md"
        content = doc_path.read_text()

        required_sections = [
            "Governance Enforcement Infrastructure",
            "Adding Protected Systems",
            "Capability Registry Implementation",
            "Policy Engine Integration",
            "Semantic Authority Boundaries",
        ]

        for section in required_sections:
            assert section in content, f"Missing section: {section}"
