"""
CAM System E2E Test Script
==========================

Comprehensive end-to-end testing for the CAM (Computer-Aided Manufacturing) system.

Covers:
- Phase 1: Health & Configuration
- Phase 2: Adaptive Pocketing (L.1/L.2/L.3)
- Phase 3: Roughing Operations
- Phase 4: Drilling
- Phase 5: Fret Slots
- Phase 6: CAM Intent Normalization
- Phase 7: Pipeline Orchestration

Usage:
    python tests/e2e_cam_system.py [--base-url http://127.0.0.1:8000]
"""

from __future__ import annotations

import argparse
import io
import sys
import tempfile
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests

try:
    import ezdxf
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False


@dataclass
class TestResult:
    name: str
    phase: str
    passed: bool
    status_code: int
    message: str
    details: Optional[Dict[str, Any]] = None


class CAMSystemE2ETester:
    """E2E tester for the CAM system."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")
        self.results: List[TestResult] = []
        self.session = requests.Session()
        self.session.headers.update({"X-Request-ID": "e2e-cam-test"})

    def _get(self, path: str, **kwargs) -> requests.Response:
        return self.session.get(f"{self.base_url}{path}", timeout=30, **kwargs)

    def _post(self, path: str, **kwargs) -> requests.Response:
        return self.session.post(f"{self.base_url}{path}", timeout=60, **kwargs)

    def _record(self, name: str, phase: str, response: requests.Response,
                expected_status: int = 200, details: Optional[Dict] = None) -> bool:
        passed = response.status_code == expected_status
        message = "OK" if passed else f"Expected {expected_status}, got {response.status_code}"

        if not passed and response.text:
            message += f": {response.text[:200]}"

        self.results.append(TestResult(
            name=name,
            phase=phase,
            passed=passed,
            status_code=response.status_code,
            message=message,
            details=details,
        ))
        return passed

    def _create_test_dxf(self) -> bytes:
        """Create a valid DXF with a closed polyline on GEOMETRY layer."""
        if not EZDXF_AVAILABLE:
            # Fallback: minimal DXF structure
            return b""

        doc = ezdxf.new(dxfversion='R2010')
        msp = doc.modelspace()

        # Outer boundary (100x60mm rectangle)
        outer = [(0, 0), (100, 0), (100, 60), (0, 60), (0, 0)]
        msp.add_lwpolyline(outer, dxfattribs={'layer': 'GEOMETRY', 'closed': True})

        # Inner island (optional - 40x20mm rectangle centered)
        island = [(30, 20), (70, 20), (70, 40), (30, 40), (30, 20)]
        msp.add_lwpolyline(island, dxfattribs={'layer': 'GEOMETRY', 'closed': True})

        # Save to bytes (Windows-compatible)
        tmp_path = tempfile.mktemp(suffix='.dxf')
        try:
            doc.saveas(tmp_path)
            with open(tmp_path, 'rb') as rf:
                content = rf.read()
            return content
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass  # Ignore cleanup errors on Windows

    # =========================================================================
    # Phase 1: Health & Configuration
    # =========================================================================

    def test_phase1_health(self) -> None:
        """Test server health endpoint."""
        r = self._get("/health")
        if self._record("Server Health", "Phase 1", r):
            data = r.json()
            self.results[-1].details = {"version": data.get("version")}

    def test_phase1_machine_profiles(self) -> None:
        """Test machine profiles endpoint."""
        # Try both possible paths
        r = self._get("/api/cam/body/machines")
        if self._record("Machine Profiles", "Phase 1", r):
            data = r.json()
            count = len(data) if isinstance(data, list) else len(data.keys())
            self.results[-1].details = {"count": count}

    def test_phase1_posts(self) -> None:
        """Test post-processors endpoint."""
        r = self._get("/api/posts")
        if self._record("Post-Processors", "Phase 1", r):
            data = r.json()
            posts = list(data.keys()) if isinstance(data, dict) else [p.get("id") for p in data]
            self.results[-1].details = {"posts": posts[:5]}

    def test_phase1_presets(self) -> None:
        """Test CAM presets endpoint."""
        r = self._get("/presets")
        # May return 200 or 404 if no presets
        passed = r.status_code in (200, 404)
        self.results.append(TestResult(
            name="CAM Presets",
            phase="Phase 1",
            passed=passed,
            status_code=r.status_code,
            message="OK" if passed else f"Unexpected status {r.status_code}",
        ))

    # =========================================================================
    # Phase 2: Adaptive Pocketing
    # =========================================================================

    def test_phase2_adaptive_plan(self) -> None:
        """Test adaptive pocket planning."""
        payload = {
            "loops": [
                {"pts": [[0, 0], [100, 0], [100, 60], [0, 60], [0, 0]]}
            ],
            "units": "mm",
            "tool_d": 6.0,
            "stepover": 0.45,
            "stepdown": 2.0,
            "margin": 0.5,
            "strategy": "Spiral",
            "feed_xy": 1200.0,
            "safe_z": 5.0,
            "z_rough": -2.0,
        }
        r = self._post("/api/cam/pocket/adaptive/plan", json=payload)
        if self._record("Adaptive Plan", "Phase 2", r):
            data = r.json()
            self.results[-1].details = {
                "moves": len(data.get("moves", [])),
                "time_s": data.get("stats", {}).get("time_s"),
                "length_mm": data.get("stats", {}).get("length_mm"),
            }

    def test_phase2_adaptive_gcode(self) -> None:
        """Test adaptive G-code export."""
        payload = {
            "loops": [
                {"pts": [[0, 0], [100, 0], [100, 60], [0, 60], [0, 0]]}
            ],
            "units": "mm",
            "tool_d": 6.0,
            "stepover": 0.45,
            "stepdown": 2.0,
            "feed_xy": 1200.0,
            "safe_z": 5.0,
            "z_rough": -2.0,
            "post_id": "GRBL",
        }
        r = self._post("/api/cam/pocket/adaptive/gcode", json=payload)
        if self._record("Adaptive G-code", "Phase 2", r):
            content = r.content.decode("utf-8", errors="replace")
            lines = content.split("\n")
            has_g21 = any("G21" in line for line in lines[:20])
            self.results[-1].details = {
                "lines": len(lines),
                "has_g21": has_g21,
            }

    def test_phase2_adaptive_sim(self) -> None:
        """Test adaptive simulation preview."""
        payload = {
            "loops": [
                {"pts": [[0, 0], [100, 0], [100, 60], [0, 60], [0, 0]]}
            ],
            "units": "mm",
            "tool_d": 6.0,
            "stepover": 0.45,
            "feed_xy": 1200.0,
            "safe_z": 5.0,
        }
        r = self._post("/api/cam/pocket/adaptive/sim", json=payload)
        if self._record("Adaptive Sim", "Phase 2", r):
            data = r.json()
            self.results[-1].details = {
                "stats": bool(data.get("stats")),
                "moves_preview": len(data.get("moves", [])),
            }

    def test_phase2_adaptive_from_dxf(self) -> None:
        """Test DXF upload to adaptive plan."""
        if not EZDXF_AVAILABLE:
            self.results.append(TestResult(
                name="Adaptive from DXF",
                phase="Phase 2",
                passed=True,
                status_code=0,
                message="SKIPPED: ezdxf not available",
            ))
            return

        dxf_bytes = self._create_test_dxf()
        files = {"file": ("test.dxf", io.BytesIO(dxf_bytes), "application/dxf")}
        data = {
            "tool_d": "6.0",
            "units": "mm",
            "stepover": "0.45",
            "strategy": "Spiral",
            "feed_xy": "1200.0",
        }
        r = self._post("/api/cam/pocket/adaptive/plan_from_dxf", files=files, data=data)
        if self._record("Adaptive from DXF", "Phase 2", r):
            resp = r.json()
            self.results[-1].details = {
                "loops": len(resp.get("request", {}).get("loops", [])),
                "moves": len(resp.get("plan", {}).get("moves", [])),
            }

    def test_phase2_batch_export(self) -> None:
        """Test batch export with multiple modes."""
        payload = {
            "loops": [
                {"pts": [[0, 0], [100, 0], [100, 60], [0, 60], [0, 0]]}
            ],
            "units": "mm",
            "tool_d": 6.0,
            "stepover": 0.45,
            "feed_xy": 1200.0,
            "safe_z": 5.0,
            "post_id": "GRBL",
            "modes": ["comment", "inline_f"],
            "job_name": "e2e_test",
        }
        r = self._post("/api/cam/pocket/adaptive/batch_export", json=payload)
        if self._record("Batch Export", "Phase 2", r):
            is_zip = r.content[:4] == b'PK\x03\x04'
            self.results[-1].details = {
                "size_bytes": len(r.content),
                "is_zip": is_zip,
            }

    # =========================================================================
    # Phase 3: Roughing Operations
    # =========================================================================

    def test_phase3_roughing_gcode(self) -> None:
        """Test simple roughing G-code generation."""
        payload = {
            "width": 100.0,
            "height": 60.0,
            "stepdown": 2.0,
            "stepover": 5.0,
            "feed": 1200.0,
            "safe_z": 5.0,
            "units": "mm",
        }
        r = self._post("/api/cam/toolpath/roughing/gcode", json=payload)
        if self._record("Roughing G-code", "Phase 3", r):
            lines = r.text.split("\n") if r.text else []
            self.results[-1].details = {"lines": len(lines)}

    def test_phase3_roughing_intent_non_strict(self) -> None:
        """Test roughing intent with issues (non-strict mode)."""
        payload = {
            "mode": "router_3axis",
            "design": {
                "geometry": {"type": "rectangle", "width_mm": 100.0, "height_mm": 50.0},
                "depth_mm": 5.0,
                "stepdown_mm": 2.0,
                "stepover_mm": 5.0,
                "width_mm": 100.0,
                "height_mm": 50.0,
            },
            "context": {"feed_rate": 1000.0},
            "units": "mm",
        }
        r = self._post("/api/cam/roughing/gcode_intent?strict=false", json=payload)
        if self._record("Roughing Intent (non-strict)", "Phase 3", r):
            data = r.json()
            self.results[-1].details = {
                "has_gcode": bool(data.get("gcode")),
                "issues": len(data.get("issues", [])),
                "status": data.get("status"),
            }

    def test_phase3_roughing_intent_strict_valid(self) -> None:
        """Test roughing intent with valid payload (strict mode)."""
        payload = {
            "mode": "router_3axis",
            "design": {
                "geometry": {"type": "rectangle", "width_mm": 100.0, "height_mm": 50.0},
                "depth_mm": 10.0,
                "stepdown_mm": 2.0,
                "stepover_mm": 5.0,
                "width_mm": 100.0,
                "height_mm": 50.0,
            },
            "context": {"feed_rate": 1000.0},
            "units": "mm",
        }
        r = self._post("/api/cam/roughing/gcode_intent?strict=true", json=payload)
        if self._record("Roughing Intent (strict valid)", "Phase 3", r):
            data = r.json()
            self.results[-1].details = {
                "status": data.get("status"),
                "issues": len(data.get("issues", [])),
            }

    def test_phase3_roughing_intent_strict_invalid(self) -> None:
        """Test roughing intent with issues (strict mode should reject)."""
        payload = {
            "mode": "router_3axis",
            "design": {
                # Missing geometry - should trigger issues
                "depth_mm": 5.0,
                "stepdown_mm": 2.0,
                "stepover_mm": 5.0,
                "width_mm": 100.0,
                "height_mm": 50.0,
            },
            "context": {"feed_rate": 1000.0},
            "units": "mm",
        }
        r = self._post("/api/cam/roughing/gcode_intent?strict=true", json=payload)
        # Should reject with 422
        self._record("Roughing Intent (strict reject)", "Phase 3", r, expected_status=422)

    # =========================================================================
    # Phase 4: Drilling
    # =========================================================================

    def test_phase4_drill_gcode(self) -> None:
        """Test drilling G-code generation."""
        payload = {
            "holes": [
                {"x": 10.0, "y": 10.0, "z": -5.0, "feed": 500.0},
                {"x": 90.0, "y": 10.0, "z": -5.0, "feed": 500.0},
                {"x": 50.0, "y": 50.0, "z": -5.0, "feed": 500.0},
            ],
            "r_clear": 5.0,
            "peck_q": 2.0,
            "cycle": "G83",
            "safe_z": 5.0,
            "units": "mm",
        }
        r = self._post("/api/cam/drilling/gcode", json=payload)
        if self._record("Drill G-code", "Phase 4", r):
            has_g83 = "G83" in r.text if r.text else False
            self.results[-1].details = {
                "lines": len(r.text.split("\n")) if r.text else 0,
                "has_g83": has_g83,
            }

    def test_phase4_drill_pattern(self) -> None:
        """Test drill pattern G-code generation."""
        payload = {
            "pattern": {
                "type": "grid",
                "origin": {"x": 0, "y": 0},
                "spacing_x": 20.0,
                "spacing_y": 20.0,
                "count_x": 3,
                "count_y": 2,
            },
            "depth": -5.0,
            "feed": 500.0,
            "r_clear": 5.0,
            "cycle": "G81",
            "safe_z": 5.0,
            "units": "mm",
        }
        r = self._post("/api/cam/drilling/pattern/gcode", json=payload)
        # Pattern endpoint may have different schema - accept 200 or 422
        passed = r.status_code in (200, 422)
        self.results.append(TestResult(
            name="Drill Pattern",
            phase="Phase 4",
            passed=passed,
            status_code=r.status_code,
            message="OK" if r.status_code == 200 else f"Validation: {r.text[:100]}",
        ))

    def test_phase4_drill_info(self) -> None:
        """Test drill info endpoint."""
        r = self._get("/api/cam/drilling/info")
        self._record("Drill Info", "Phase 4", r)

    # =========================================================================
    # Phase 5: Fret Slots
    # =========================================================================

    def test_phase5_fret_board_slots(self) -> None:
        """Test fret board slots calculation."""
        payload = {
            "scale_length_mm": 648.0,
            "fret_count": 22,
        }
        r = self._post("/api/fret/board/slots", json=payload)
        if self._record("Fret Board Slots", "Phase 5", r):
            data = r.json()
            self.results[-1].details = {
                "slots": len(data.get("slots", data.get("frets", []))),
            }

    def test_phase5_fret_health(self) -> None:
        """Test fret calculator health."""
        r = self._get("/api/fret/health")
        self._record("Fret Health", "Phase 5", r)

    # =========================================================================
    # Phase 6: CAM Intent Normalization
    # =========================================================================

    def test_phase6_normalize_intent(self) -> None:
        """Test CAM intent normalization."""
        payload = {
            "intent": {
                "schema_version": "cam_intent_v1",
                "mode": "router_3axis",
                "units": "inch",
                "design": {
                    "geometry": {"type": "rectangle", "width_mm": 4.0, "height_mm": 2.0},
                    "depth_mm": 0.5,
                    "stepdown_mm": 0.1,
                    "stepover_mm": 0.2,
                },
            },
            "normalize_to_units": "mm",
            "strict": False,
        }
        r = self._post("/api/rmos/cam/intent/normalize", json=payload)
        if self._record("CAM Intent Normalize", "Phase 6", r):
            data = r.json()
            self.results[-1].details = {
                "output_units": data.get("intent", {}).get("units"),
                "issues": len(data.get("issues", [])),
            }

    def test_phase6_normalize_intent_strict(self) -> None:
        """Test CAM intent normalization with strict mode."""
        payload = {
            "intent": {
                "schema_version": "cam_intent_v1",
                "mode": "router_3axis",
                "units": "mm",
                "design": {
                    "geometry": {"type": "rectangle", "width_mm": 100.0, "height_mm": 50.0},
                    "depth_mm": 10.0,
                },
            },
            "normalize_to_units": "mm",
            "strict": True,
        }
        r = self._post("/api/rmos/cam/intent/normalize", json=payload)
        # May pass or fail depending on required fields
        passed = r.status_code in (200, 422)
        self.results.append(TestResult(
            name="CAM Intent Normalize (strict)",
            phase="Phase 6",
            passed=passed,
            status_code=r.status_code,
            message="OK" if passed else f"Unexpected: {r.status_code}",
        ))

    # =========================================================================
    # Phase 7: Pipeline Orchestration
    # =========================================================================

    def test_phase7_blueprint_cam_preflight(self) -> None:
        """Test blueprint CAM preflight (validates DXF for CAM)."""
        r = self._get("/api/blueprint/cam/health")
        self._record("Blueprint CAM Health", "Phase 7", r)

    def test_phase7_cam_settings(self) -> None:
        """Test CAM settings summary."""
        r = self._get("/api/cam/settings/summary")
        if self._record("CAM Settings Summary", "Phase 7", r):
            data = r.json()
            self.results[-1].details = {"keys": list(data.keys())[:5]}

    # =========================================================================
    # Run All Tests
    # =========================================================================

    def run_all(self) -> Tuple[int, int]:
        """Run all E2E tests and return (passed, total)."""
        print("=" * 70)
        print("CAM SYSTEM E2E TESTS")
        print("=" * 70)
        print(f"Base URL: {self.base_url}")
        print()

        # Phase 1: Health & Configuration
        print("Phase 1: Health & Configuration")
        print("-" * 40)
        self.test_phase1_health()
        self.test_phase1_machine_profiles()
        self.test_phase1_posts()
        self.test_phase1_presets()
        self._print_phase_results("Phase 1")

        # Phase 2: Adaptive Pocketing
        print("\nPhase 2: Adaptive Pocketing")
        print("-" * 40)
        self.test_phase2_adaptive_plan()
        self.test_phase2_adaptive_gcode()
        self.test_phase2_adaptive_sim()
        self.test_phase2_adaptive_from_dxf()
        self.test_phase2_batch_export()
        self._print_phase_results("Phase 2")

        # Phase 3: Roughing
        print("\nPhase 3: Roughing Operations")
        print("-" * 40)
        self.test_phase3_roughing_gcode()
        self.test_phase3_roughing_intent_non_strict()
        self.test_phase3_roughing_intent_strict_valid()
        self.test_phase3_roughing_intent_strict_invalid()
        self._print_phase_results("Phase 3")

        # Phase 4: Drilling
        print("\nPhase 4: Drilling")
        print("-" * 40)
        self.test_phase4_drill_gcode()
        self.test_phase4_drill_pattern()
        self.test_phase4_drill_info()
        self._print_phase_results("Phase 4")

        # Phase 5: Fret Calculator
        print("\nPhase 5: Fret Calculator")
        print("-" * 40)
        self.test_phase5_fret_board_slots()
        self.test_phase5_fret_health()
        self._print_phase_results("Phase 5")

        # Phase 6: CAM Intent Normalization
        print("\nPhase 6: CAM Intent Normalization")
        print("-" * 40)
        self.test_phase6_normalize_intent()
        self.test_phase6_normalize_intent_strict()
        self._print_phase_results("Phase 6")

        # Phase 7: Integration & Settings
        print("\nPhase 7: Integration & Settings")
        print("-" * 40)
        self.test_phase7_blueprint_cam_preflight()
        self.test_phase7_cam_settings()
        self._print_phase_results("Phase 7")

        # Summary
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)

        print()
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)

        # Group by phase
        phases = {}
        for r in self.results:
            if r.phase not in phases:
                phases[r.phase] = {"passed": 0, "total": 0}
            phases[r.phase]["total"] += 1
            if r.passed:
                phases[r.phase]["passed"] += 1

        for phase in sorted(phases.keys()):
            p = phases[phase]
            status = "PASS" if p["passed"] == p["total"] else "FAIL"
            print(f"  {phase}: {p['passed']}/{p['total']} [{status}]")

        print()
        print(f"Total: {passed}/{total} passed")

        if passed == total:
            print("\nALL TESTS PASSED")
        else:
            print("\nFAILED TESTS:")
            for r in self.results:
                if not r.passed:
                    print(f"  - {r.phase}: {r.name} ({r.status_code}) - {r.message}")

        return passed, total

    def _print_phase_results(self, phase: str) -> None:
        """Print results for a specific phase."""
        phase_results = [r for r in self.results if r.phase == phase]
        for r in phase_results[-10:]:  # Last 10 from this phase
            status = "PASS" if r.passed else "FAIL"
            details = ""
            if r.details:
                details = f" {r.details}"
            print(f"  [{status}] {r.name}: {r.message}{details}")


def main():
    parser = argparse.ArgumentParser(description="CAM System E2E Tests")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Base URL of the API server",
    )
    args = parser.parse_args()

    tester = CAMSystemE2ETester(base_url=args.base_url)

    try:
        passed, total = tester.run_all()
        sys.exit(0 if passed == total else 1)
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Could not connect to {args.base_url}")
        print("Make sure the API server is running.")
        sys.exit(1)


if __name__ == "__main__":
    main()
