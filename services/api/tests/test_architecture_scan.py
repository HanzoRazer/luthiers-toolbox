"""
Architecture Scan Test Suite

Tests for:
1. Scanner unit tests (scan_architecture.py)
2. CBSP21 gate unit tests (check_cbsp21_gate.py)
3. Integration tests (output schema, determinism, exit codes)
"""

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Set

import pytest

# Get repo root for imports
# tests/test_architecture_scan.py -> tests/ -> api/ -> services/ -> repo_root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
SCANNER_PATH = SCRIPTS_DIR / "architecture" / "scan_architecture.py"
GATE_PATH = SCRIPTS_DIR / "ci" / "check_cbsp21_gate.py"

# Validate paths exist at import time
if not SCANNER_PATH.exists():
    raise FileNotFoundError(f"Scanner not found: {SCANNER_PATH}")
if not GATE_PATH.exists():
    raise FileNotFoundError(f"Gate not found: {GATE_PATH}")


def load_module_from_path(name: str, path: Path):
    """Load a Python module from a file path."""
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    # Must add to sys.modules for dataclass decorator to work
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Lazy load modules to avoid import-time side effects
_scanner_module = None
_gate_module = None


def get_scanner_module():
    """Get the scanner module, loading it lazily."""
    global _scanner_module
    if _scanner_module is None:
        _scanner_module = load_module_from_path("scan_architecture", SCANNER_PATH)
    return _scanner_module


def get_gate_module():
    """Get the gate module, loading it lazily."""
    global _gate_module
    if _gate_module is None:
        _gate_module = load_module_from_path("check_cbsp21_gate", GATE_PATH)
    return _gate_module


# =============================================================================
# Scanner Unit Tests
# =============================================================================

class TestDetectSignals:
    """Tests for detect_signals() function."""

    @pytest.fixture
    def detect_signals(self):
        """Import the detect_signals function."""
        return get_scanner_module().detect_signals

    def test_detect_gcode_keyword(self, detect_signals):
        """gcode keyword triggers GCODE signal."""
        text = "def generate_gcode(): pass"
        signals = detect_signals(text)
        assert "GCODE" in signals

    def test_detect_gcode_emit(self, detect_signals):
        """emit_gcode triggers GCODE_EMIT signal."""
        text = "result = emit_gcode(moves)"
        signals = detect_signals(text)
        assert "GCODE_EMIT" in signals

    def test_detect_gcode_file_extension(self, detect_signals):
        """'.nc' triggers GCODE_FILE signal."""
        text = 'filename = "output.nc"'
        signals = detect_signals(text)
        assert "GCODE_FILE" in signals

    def test_detect_dxf(self, detect_signals):
        """dxf keyword triggers DXF signal."""
        text = "export_dxf(geometry)"
        signals = detect_signals(text)
        assert "DXF" in signals

    def test_detect_dxf_lib(self, detect_signals):
        """ezdxf triggers DXF_LIB signal."""
        text = "import ezdxf"
        signals = detect_signals(text)
        assert "DXF_LIB" in signals

    def test_detect_persistence_store(self, detect_signals):
        """store_artifact triggers PERSISTENCE signal."""
        text = "store_artifact(run_id, data)"
        signals = detect_signals(text)
        assert "PERSISTENCE" in signals

    def test_detect_persistence_persist_run(self, detect_signals):
        """persist_run triggers PERSISTENCE signal."""
        text = "persist_run(run)"
        signals = detect_signals(text)
        assert "PERSISTENCE" in signals

    def test_detect_persistence_write(self, detect_signals):
        """write_run_artifact triggers PERSISTENCE signal."""
        text = "write_run_artifact(id, payload)"
        signals = detect_signals(text)
        assert "PERSISTENCE" in signals

    def test_detect_rmos_read(self, detect_signals):
        """read_run_artifact triggers RMOS_READ signal."""
        text = "data = read_run_artifact(artifact_id)"
        signals = detect_signals(text)
        assert "RMOS_READ" in signals

    def test_detect_direct_response(self, detect_signals):
        """Response( triggers DIRECT_RESPONSE signal."""
        text = 'return Response(content=gcode, media_type="text/plain")'
        signals = detect_signals(text)
        assert "DIRECT_RESPONSE" in signals

    def test_detect_plain_text_response(self, detect_signals):
        """PlainTextResponse triggers DIRECT_RESPONSE signal."""
        text = "return PlainTextResponse(data)"
        signals = detect_signals(text)
        assert "DIRECT_RESPONSE" in signals

    def test_detect_id_creation_uuid(self, detect_signals):
        """uuid.uuid4 triggers ID_CREATION signal."""
        text = "run_id = str(uuid.uuid4())"
        signals = detect_signals(text)
        assert "ID_CREATION" in signals

    def test_detect_id_creation_create_run(self, detect_signals):
        """create_run_id triggers ID_CREATION signal."""
        text = "new_id = create_run_id()"
        signals = detect_signals(text)
        assert "ID_CREATION" in signals

    def test_detect_risk_eval(self, detect_signals):
        """risk_bucket triggers RISK_EVAL signal."""
        text = 'bucket = risk_bucket("high")'
        signals = detect_signals(text)
        assert "RISK_EVAL" in signals

    def test_detect_safety_gate_should_block(self, detect_signals):
        """should_block triggers SAFETY_GATE signal."""
        text = "if should_block(params): raise Error()"
        signals = detect_signals(text)
        assert "SAFETY_GATE" in signals

    def test_detect_safety_gate_feasibility(self, detect_signals):
        """compute_feasibility triggers SAFETY_GATE signal."""
        text = "result = compute_feasibility(geometry)"
        signals = detect_signals(text)
        assert "SAFETY_GATE" in signals

    def test_detect_experimental(self, detect_signals):
        """_experimental triggers EXPERIMENTAL signal."""
        text = "from app._experimental.ai_graphics import module"
        signals = detect_signals(text)
        assert "EXPERIMENTAL" in signals

    def test_no_signals_plain_code(self, detect_signals):
        """Plain code without keywords returns empty set."""
        text = "def add(a, b): return a + b"
        signals = detect_signals(text)
        assert len(signals) == 0

    def test_multiple_signals(self, detect_signals):
        """Multiple keywords return multiple signals."""
        text = """
        import ezdxf
        from uuid import uuid4
        result = store_artifact(str(uuid.uuid4()), dxf_data)
        """
        signals = detect_signals(text)
        assert "DXF_LIB" in signals
        assert "ID_CREATION" in signals
        assert "PERSISTENCE" in signals


class TestStripComments:
    """Tests for strip_comments() function (docstring and comment removal)."""

    @pytest.fixture
    def strip_comments(self):
        """Import the strip_comments function."""
        return get_scanner_module().strip_comments

    def test_strips_python_line_comments(self, strip_comments):
        """Python # comments are stripped."""
        text = "code()  # this is a comment"
        result = strip_comments(text)
        assert "comment" not in result
        assert "code()" in result

    def test_strips_js_line_comments(self, strip_comments):
        """JavaScript // comments are stripped."""
        text = "function()  // this is a comment"
        result = strip_comments(text)
        assert "comment" not in result
        assert "function()" in result

    def test_strips_triple_double_quote_docstrings(self, strip_comments):
        """Python \"\"\"docstrings\"\"\" are stripped."""
        text = '''def foo():
    """This docstring mentions compute_feasibility()."""
    pass'''
        result = strip_comments(text)
        assert "compute_feasibility" not in result
        assert "def foo():" in result
        assert "pass" in result

    def test_strips_triple_single_quote_docstrings(self, strip_comments):
        """Python '''docstrings''' are stripped."""
        text = """def foo():
    '''This docstring mentions should_block().'''
    pass"""
        result = strip_comments(text)
        assert "should_block" not in result
        assert "def foo():" in result

    def test_preserves_code_outside_comments(self, strip_comments):
        """Code outside comments/docstrings is preserved."""
        text = '''should_block()  # just a comment
"""docstring mentioning run_id"""
real_code_with_run_id()'''
        result = strip_comments(text)
        # The actual code line should be preserved
        assert "real_code_with_run_id()" in result
        # But the comment and docstring contents should be gone
        assert "just a comment" not in result
        # docstring should be stripped, so run_id in docstring gone
        # but run_id in code should remain

    def test_strips_multiline_docstrings(self, strip_comments):
        """Multiline docstrings spanning many lines are stripped."""
        text = '''"""
        This is a long docstring
        that mentions compute_feasibility()
        and should_block()
        across multiple lines.
        """
actual_code()'''
        result = strip_comments(text)
        assert "compute_feasibility" not in result
        assert "should_block" not in result
        assert "actual_code()" in result


class TestIsExperimentalPath:
    """Tests for is_experimental_path() function."""

    @pytest.fixture
    def is_experimental_path(self):
        """Import the is_experimental_path function."""
        return get_scanner_module().is_experimental_path

    def test_experimental_in_middle(self, is_experimental_path):
        """Path with /_experimental/ in middle is detected."""
        assert is_experimental_path("services/api/app/_experimental/ai_graphics/module.py")

    def test_experimental_at_start(self, is_experimental_path):
        """Path starting with _experimental/ is detected."""
        assert is_experimental_path("_experimental/test.py")

    def test_non_experimental_path(self, is_experimental_path):
        """Regular paths are not flagged."""
        assert not is_experimental_path("services/api/app/routers/main.py")

    def test_experimental_backslash(self, is_experimental_path):
        """Windows paths with backslashes are detected."""
        assert is_experimental_path("services\\api\\app\\_experimental\\test.py")


class TestRiskFor:
    """Tests for risk_for() function."""

    @pytest.fixture
    def risk_for(self):
        """Import the risk_for function."""
        return get_scanner_module().risk_for

    def test_critical_experimental_persistence(self, risk_for):
        """Experimental + PERSISTENCE = critical."""
        signals = {"PERSISTENCE", "EXPERIMENTAL"}
        rel = "services/api/app/_experimental/store.py"
        risk = risk_for(signals, rel, "store_artifact()")
        assert risk == "critical"

    def test_critical_experimental_id_creation_with_run_id(self, risk_for):
        """Experimental + ID_CREATION + run_id = critical (RMOS authority)."""
        signals = {"ID_CREATION"}
        rel = "services/api/app/_experimental/ids.py"
        # Only critical if creating RMOS run IDs, not ephemeral suggestion UUIDs
        risk = risk_for(signals, rel, "run_id = uuid.uuid4()")
        assert risk == "critical"

    def test_not_critical_experimental_id_creation_without_run_id(self, risk_for):
        """Experimental + ID_CREATION without run_id = low (suggestion UUID OK)."""
        signals = {"ID_CREATION"}
        rel = "services/api/app/_experimental/ids.py"
        # Ephemeral suggestion UUIDs are not authority creation
        risk = risk_for(signals, rel, "suggestion_id = uuid.uuid4()")
        assert risk == "low"

    def test_critical_experimental_safety_gate(self, risk_for):
        """Experimental + SAFETY_GATE = critical."""
        signals = {"SAFETY_GATE"}
        rel = "_experimental/safety.py"
        risk = risk_for(signals, rel, "should_block()")
        assert risk == "critical"

    def test_high_gcode_direct_no_persist(self, risk_for):
        """GCODE + DIRECT_RESPONSE - PERSISTENCE = high."""
        signals = {"GCODE", "DIRECT_RESPONSE"}
        rel = "services/api/app/routers/export.py"
        risk = risk_for(signals, rel, "Response(gcode)")
        assert risk == "high"

    def test_high_dxf_direct_no_persist(self, risk_for):
        """DXF + DIRECT_RESPONSE - PERSISTENCE = high."""
        signals = {"DXF_LIB", "DIRECT_RESPONSE"}
        rel = "services/api/app/routers/dxf.py"
        risk = risk_for(signals, rel, "Response(dxf)")
        assert risk == "high"

    def test_not_high_when_persistence(self, risk_for):
        """GCODE + DIRECT_RESPONSE + PERSISTENCE != high."""
        signals = {"GCODE", "DIRECT_RESPONSE", "PERSISTENCE"}
        rel = "services/api/app/routers/export.py"
        risk = risk_for(signals, rel, "store then respond")
        # With persistence, it's not high (traceability maintained)
        assert risk != "high"

    def test_medium_advisory_no_linkage(self, risk_for):
        """Advisory without parent_id = medium."""
        signals: Set[str] = set()
        rel = "services/api/app/advisory/store.py"
        text = "def create_advisory(data): advisory = Advisory()"
        risk = risk_for(signals, rel, text)
        assert risk == "medium"

    def test_medium_multi_authority(self, risk_for):
        """3+ signals = medium."""
        signals = {"ID_CREATION", "PERSISTENCE", "RMOS_READ"}
        rel = "services/api/app/service.py"
        risk = risk_for(signals, rel, "complex service")
        assert risk == "medium"

    def test_low_simple_signals(self, risk_for):
        """Few signals without risk factors = low."""
        signals = {"RMOS_READ"}
        rel = "services/api/app/reader.py"
        risk = risk_for(signals, rel, "read_run_artifact()")
        assert risk == "low"


class TestInvariantViolation:
    """Tests for invariant_violation() function."""

    @pytest.fixture
    def invariant_violation(self):
        """Import the invariant_violation function."""
        return get_scanner_module().invariant_violation

    def test_inv001_gcode_traceable_violated(self, invariant_violation):
        """INV-001: GCODE + DIRECT - PERSIST = violation."""
        signals = {"GCODE", "DIRECT_RESPONSE"}
        rel = "services/api/app/routers/gcode.py"
        inv, note = invariant_violation(signals, rel, "Response(gcode)")
        assert inv == "GCODE_TRACEABLE"
        assert "Machine-executable" in note

    def test_inv001_not_violated_with_persistence(self, invariant_violation):
        """INV-001: Not violated when persistence present."""
        signals = {"GCODE", "DIRECT_RESPONSE", "PERSISTENCE"}
        rel = "services/api/app/routers/gcode.py"
        inv, note = invariant_violation(signals, rel, "store then respond")
        assert inv is None

    def test_inv002_ai_no_authority_violated_with_run_id(self, invariant_violation):
        """INV-002: Experimental + RMOS run_id authority = violation."""
        signals = {"ID_CREATION"}
        rel = "app/_experimental/ai_graphics/test.py"
        # Only violated if creating RMOS run IDs
        inv, note = invariant_violation(signals, rel, "run_id = uuid.uuid4()")
        assert inv == "AI_NO_AUTHORITY"
        assert "Experimental" in note

    def test_inv002_not_violated_with_suggestion_uuid(self, invariant_violation):
        """INV-002: Not violated for ephemeral suggestion UUIDs."""
        signals = {"ID_CREATION"}
        rel = "app/_experimental/ai_graphics/test.py"
        # Ephemeral suggestion UUIDs are not authority creation
        inv, note = invariant_violation(signals, rel, "suggestion_id = uuid.uuid4()")
        assert inv is None

    def test_inv002_not_violated_outside_experimental(self, invariant_violation):
        """INV-002: Not violated outside _experimental."""
        signals = {"ID_CREATION", "PERSISTENCE"}
        rel = "services/api/app/rmos/store.py"
        inv, note = invariant_violation(signals, rel, "authority code")
        assert inv is None

    def test_inv003_advisory_attached_violated(self, invariant_violation):
        """INV-003: Advisory without run linkage = violation."""
        signals: Set[str] = set()
        rel = "services/api/app/advisory/orphan.py"
        # Text has advisory keyword but no linkage markers
        text = "class Advisory: def create(self): return Advisory(data=input)"
        inv, note = invariant_violation(signals, rel, text)
        assert inv == "ADVISORY_ATTACHED"
        assert "parent run linkage" in note

    def test_inv003_not_violated_with_parent_id(self, invariant_violation):
        """INV-003: Not violated when parent_id present."""
        signals: Set[str] = set()
        rel = "services/api/app/advisory/linked.py"
        text = "advisory = Advisory(parent_id=run_id)"
        inv, note = invariant_violation(signals, rel, text)
        assert inv is None


# =============================================================================
# CBSP21 Gate Unit Tests
# =============================================================================

class TestValidateArchitectureScanBlock:
    """Tests for validate_architecture_scan_block() function."""

    @pytest.fixture
    def validate_block(self):
        """Import the validate function."""
        return get_gate_module().validate_architecture_scan_block

    def test_none_is_valid(self, validate_block):
        """None block is valid (optional)."""
        valid, errors = validate_block(None)
        assert valid
        assert len(errors) == 0

    def test_valid_complete_block(self, validate_block):
        """Complete valid block passes."""
        block = {
            "scan_id": "AS-20260105T120000Z",
            "risk_summary": {"critical": 0, "high": 1, "medium": 5, "low": 10},
            "findings": [],
            "acknowledged": False,
            "acknowledgement_notes": ""
        }
        valid, errors = validate_block(block)
        assert valid
        assert len(errors) == 0

    def test_missing_scan_id(self, validate_block):
        """Missing scan_id is invalid."""
        block = {
            "risk_summary": {"critical": 0, "high": 0, "medium": 0, "low": 0}
        }
        valid, errors = validate_block(block)
        assert not valid
        assert any("scan_id" in e for e in errors)

    def test_missing_risk_summary(self, validate_block):
        """Missing risk_summary is invalid."""
        block = {
            "scan_id": "AS-TEST"
        }
        valid, errors = validate_block(block)
        assert not valid
        assert any("risk_summary" in e for e in errors)

    def test_missing_risk_level(self, validate_block):
        """Missing risk level in risk_summary is invalid."""
        block = {
            "scan_id": "AS-TEST",
            "risk_summary": {"critical": 0, "high": 0, "medium": 0}  # missing low
        }
        valid, errors = validate_block(block)
        assert not valid
        assert any("low" in e for e in errors)

    def test_non_integer_risk_level(self, validate_block):
        """Non-integer risk level is invalid."""
        block = {
            "scan_id": "AS-TEST",
            "risk_summary": {"critical": "zero", "high": 0, "medium": 0, "low": 0}
        }
        valid, errors = validate_block(block)
        assert not valid
        assert any("integer" in e for e in errors)

    def test_findings_wrong_type(self, validate_block):
        """Non-array findings is invalid."""
        block = {
            "scan_id": "AS-TEST",
            "risk_summary": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "findings": "not an array"
        }
        valid, errors = validate_block(block)
        assert not valid
        assert any("array" in e for e in errors)

    def test_acknowledged_wrong_type(self, validate_block):
        """Non-boolean acknowledged is invalid."""
        block = {
            "scan_id": "AS-TEST",
            "risk_summary": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "acknowledged": "yes"
        }
        valid, errors = validate_block(block)
        assert not valid
        assert any("boolean" in e for e in errors)


class TestTouchedExperimental:
    """Tests for touched_experimental() function."""

    @pytest.fixture
    def touched_experimental(self):
        """Import the function."""
        return get_gate_module().touched_experimental

    def test_experimental_in_path(self, touched_experimental):
        """Detects _experimental/ in path."""
        files = ["services/api/app/_experimental/ai_graphics/test.py"]
        assert touched_experimental(files)

    def test_experimental_at_start(self, touched_experimental):
        """Detects _experimental/ at start."""
        files = ["_experimental/sandbox.py"]
        assert touched_experimental(files)

    def test_no_experimental(self, touched_experimental):
        """Returns False when no _experimental/."""
        files = ["services/api/app/main.py", "client/src/App.vue"]
        assert not touched_experimental(files)

    def test_empty_list(self, touched_experimental):
        """Returns False for empty list."""
        assert not touched_experimental([])

    def test_windows_paths(self, touched_experimental):
        """Handles Windows backslashes."""
        files = ["services\\api\\app\\_experimental\\test.py"]
        assert touched_experimental(files)

    def test_experimental_partial_match(self, touched_experimental):
        """Does not match partial (e.g., 'experimental' without underscore)."""
        files = ["services/api/app/experimental/test.py"]  # no underscore
        assert not touched_experimental(files)


class TestCheckArchitecturePolicyBreach:
    """Tests for check_architecture_policy_breach() function."""

    @pytest.fixture
    def check_breach(self):
        """Import the function."""
        return get_gate_module().check_architecture_policy_breach

    def test_no_scan_block_passes(self, check_breach):
        """No architecture_scan block = pass."""
        manifest = {"schema": "cbsp21_patch_input_v1", "files": []}
        passed, reason = check_breach(manifest, ["any/file.py"])
        assert passed
        assert reason is None

    def test_critical_zero_passes(self, check_breach):
        """critical=0 = pass."""
        manifest = {
            "schema": "cbsp21_patch_input_v1",
            "files": [],
            "architecture_scan": {
                "scan_id": "AS-TEST",
                "risk_summary": {"critical": 0, "high": 5, "medium": 10, "low": 20}
            }
        }
        passed, reason = check_breach(manifest, ["app/_experimental/test.py"])
        assert passed

    def test_no_experimental_passes(self, check_breach):
        """No _experimental/ touched = pass even with critical."""
        manifest = {
            "schema": "cbsp21_patch_input_v1",
            "files": [],
            "architecture_scan": {
                "scan_id": "AS-TEST",
                "risk_summary": {"critical": 5, "high": 0, "medium": 0, "low": 0}
            }
        }
        passed, reason = check_breach(manifest, ["services/api/app/main.py"])
        assert passed

    def test_critical_and_experimental_blocks(self, check_breach):
        """critical > 0 AND _experimental/ = block."""
        manifest = {
            "schema": "cbsp21_patch_input_v1",
            "files": [],
            "architecture_scan": {
                "scan_id": "AS-TEST",
                "risk_summary": {"critical": 2, "high": 0, "medium": 0, "low": 0},
                "acknowledged": False
            }
        }
        passed, reason = check_breach(manifest, ["app/_experimental/test.py"])
        assert not passed
        assert "policy breach" in reason.lower()
        assert "2 critical" in reason

    def test_acknowledged_passes(self, check_breach):
        """acknowledged=True = pass even with breach conditions."""
        manifest = {
            "schema": "cbsp21_patch_input_v1",
            "files": [],
            "architecture_scan": {
                "scan_id": "AS-TEST",
                "risk_summary": {"critical": 5, "high": 0, "medium": 0, "low": 0},
                "acknowledged": True,
                "acknowledgement_notes": "Risk accepted for migration"
            }
        }
        passed, reason = check_breach(manifest, ["app/_experimental/test.py"])
        assert passed


# =============================================================================
# Integration Tests
# =============================================================================

class TestScannerIntegration:
    """Integration tests for scan_architecture.py."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as td:
            yield Path(td)

    def test_scanner_output_schema(self, temp_dir):
        """Scanner output matches expected JSON schema."""
        # Create minimal test structure
        target_dir = temp_dir / "services" / "api" / "app"
        target_dir.mkdir(parents=True)

        test_file = target_dir / "test.py"
        test_file.write_text("# empty file", encoding="utf-8")

        output_file = temp_dir / "report.json"

        result = subprocess.run(
            [sys.executable, str(SCANNER_PATH),
             "--targets", "services/api/app",
             "--out", str(output_file)],
            cwd=str(temp_dir),
            capture_output=True,
            text=True
        )

        assert output_file.exists(), f"Output not created. stderr: {result.stderr}"

        with open(output_file) as f:
            report = json.load(f)

        # Verify schema
        assert "scan_id" in report
        assert report["scan_id"].startswith("AS-")
        assert "scan_type" in report
        assert report["scan_type"] == "architecture"
        assert "mode" in report
        assert report["mode"] == "read_only"
        assert "timestamp_utc" in report
        assert "targets" in report
        assert "risk_summary" in report
        assert all(k in report["risk_summary"] for k in ["critical", "high", "medium", "low"])
        assert "invariants_checked" in report
        assert "findings" in report
        assert "findings_count" in report

    def test_scanner_detects_signals(self, temp_dir):
        """Scanner detects signals in files."""
        target_dir = temp_dir / "services" / "api" / "app"
        target_dir.mkdir(parents=True)

        # Create file with signals
        test_file = target_dir / "gcode_export.py"
        test_file.write_text("""
from fastapi.responses import Response

def export():
    gcode = generate_gcode()
    return Response(content=gcode, media_type="text/plain")
""", encoding="utf-8")

        output_file = temp_dir / "report.json"

        subprocess.run(
            [sys.executable, str(SCANNER_PATH),
             "--targets", "services/api/app",
             "--out", str(output_file)],
            cwd=str(temp_dir),
            capture_output=True
        )

        with open(output_file) as f:
            report = json.load(f)

        # Should have at least one finding (high risk: GCODE + DIRECT_RESPONSE)
        assert report["findings_count"] > 0 or report["risk_summary"]["high"] > 0 or len(report["findings"]) > 0

    def test_scanner_deterministic(self, temp_dir):
        """Same input produces same output (deterministic)."""
        target_dir = temp_dir / "services" / "api" / "app"
        target_dir.mkdir(parents=True)

        test_file = target_dir / "service.py"
        test_file.write_text("def service(): store_artifact(data)", encoding="utf-8")

        output1 = temp_dir / "report1.json"
        output2 = temp_dir / "report2.json"

        # Run twice
        for out in [output1, output2]:
            subprocess.run(
                [sys.executable, str(SCANNER_PATH),
                 "--targets", "services/api/app",
                 "--out", str(out)],
                cwd=str(temp_dir),
                capture_output=True
            )

        with open(output1) as f:
            r1 = json.load(f)
        with open(output2) as f:
            r2 = json.load(f)

        # Compare (excluding timestamps and scan_id which may differ)
        assert r1["findings_count"] == r2["findings_count"]
        assert r1["risk_summary"] == r2["risk_summary"]
        assert len(r1["findings"]) == len(r2["findings"])


class TestGateIntegration:
    """Integration tests for check_cbsp21_gate.py."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test manifests."""
        with tempfile.TemporaryDirectory() as td:
            yield Path(td)

    def test_gate_exit_0_on_pass(self, temp_dir):
        """Gate exits 0 on pass."""
        manifest = {
            "schema": "cbsp21_patch_input_v1",
            "coverage_min": 0.0,
            "files": []
        }
        manifest_path = temp_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(GATE_PATH),
             "--manifest", str(manifest_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        assert result.returncode == 0
        assert "PASSED" in result.stdout

    def test_gate_exit_1_on_coverage_fail(self, temp_dir):
        """Gate exits 1 on coverage failure."""
        manifest = {
            "schema": "cbsp21_patch_input_v1",
            "coverage_min": 0.95,
            "files": []
        }
        manifest_path = temp_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(GATE_PATH),
             "--manifest", str(manifest_path),
             "--changed-files", "uncovered.py"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        assert result.returncode == 1
        assert "FAILED" in result.stdout

    def test_gate_exit_1_on_policy_breach(self, temp_dir):
        """Gate exits 1 on architecture policy breach."""
        manifest = {
            "schema": "cbsp21_patch_input_v1",
            "coverage_min": 0.0,
            "files": [{"path": "app/_experimental/test.py"}],
            "architecture_scan": {
                "scan_id": "AS-TEST",
                "risk_summary": {"critical": 3, "high": 0, "medium": 0, "low": 0},
                "acknowledged": False
            }
        }
        manifest_path = temp_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(GATE_PATH),
             "--manifest", str(manifest_path),
             "--changed-files", "app/_experimental/test.py"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        assert result.returncode == 1
        assert "policy breach" in result.stdout.lower() or "FAILED" in result.stdout

    def test_gate_exit_2_on_invalid_json(self, temp_dir):
        """Gate exits 2 on invalid JSON."""
        manifest_path = temp_dir / "manifest.json"
        manifest_path.write_text("{ invalid json", encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(GATE_PATH),
             "--manifest", str(manifest_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        assert result.returncode == 2

    def test_gate_exit_1_on_missing_manifest(self, temp_dir):
        """Gate exits 1 on missing manifest."""
        result = subprocess.run(
            [sys.executable, str(GATE_PATH),
             "--manifest", str(temp_dir / "nonexistent.json")],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        assert result.returncode == 1


class TestWorkflowArtifact:
    """Tests for CI workflow behavior (requires repo context)."""

    def test_workflow_file_exists(self):
        """Architecture scan workflow exists."""
        workflow_path = REPO_ROOT / ".github" / "workflows" / "architecture_scan.yml"
        assert workflow_path.exists(), "Workflow file not found"

    def test_workflow_is_non_blocking(self):
        """Workflow has continue-on-error: true."""
        workflow_path = REPO_ROOT / ".github" / "workflows" / "architecture_scan.yml"
        content = workflow_path.read_text(encoding="utf-8")
        assert "continue-on-error: true" in content

    def test_workflow_uploads_artifact(self):
        """Workflow uploads architecture_scan artifact."""
        workflow_path = REPO_ROOT / ".github" / "workflows" / "architecture_scan.yml"
        content = workflow_path.read_text(encoding="utf-8")
        assert "upload-artifact" in content
        assert "architecture_scan" in content
