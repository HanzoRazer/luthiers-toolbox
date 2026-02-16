# services/api/app/saw_lab/toolpaths_validate_service.py
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.safety import safety_critical


_RE_FLOAT = re.compile(r"([-+]?\d+(?:\.\d+)?)")
_RE_M3 = re.compile(r"\bM3\b")
_RE_M4 = re.compile(r"\bM4\b")
_RE_M5 = re.compile(r"\bM5\b")


def _to_float(s: str) -> Optional[float]:
    try:
        return float(s)
    except (ValueError, TypeError):  # WP-1: narrowed from except Exception
        return None


def _extract_axis(line: str, axis: str) -> Optional[float]:
    """
    Extract an axis value like X12.34 from a G-code line.
    Returns float or None.
    """
    i = line.find(axis)
    if i < 0:
        return None
    m = _RE_FLOAT.search(line[i + 1 :])
    if not m:
        return None
    return _to_float(m.group(1))


def _extract_f(line: str) -> Optional[float]:
    i = line.find("F")
    if i < 0:
        return None
    m = _RE_FLOAT.search(line[i + 1 :])
    if not m:
        return None
    return _to_float(m.group(1))


def _strip_comment(line: str) -> str:
    # remove ";" comments
    if ";" in line:
        line = line.split(";", 1)[0]
    # remove (...) comments (best effort)
    out: List[str] = []
    depth = 0
    for ch in line:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(depth - 1, 0)
        elif depth == 0:
            out.append(ch)
    return "".join(out).strip()


@dataclass
class Bounds:
    min_x: Optional[float] = None
    max_x: Optional[float] = None
    min_y: Optional[float] = None
    max_y: Optional[float] = None
    min_z: Optional[float] = None
    max_z: Optional[float] = None

    def update(self, x: Optional[float], y: Optional[float], z: Optional[float]) -> None:
        if x is not None:
            self.min_x = x if self.min_x is None else min(self.min_x, x)
            self.max_x = x if self.max_x is None else max(self.max_x, x)
        if y is not None:
            self.min_y = y if self.min_y is None else min(self.min_y, y)
            self.max_y = y if self.max_y is None else max(self.max_y, y)
        if z is not None:
            self.min_z = z if self.min_z is None else min(self.min_z, z)
            self.max_z = z if self.max_z is None else max(self.max_z, z)

    def as_dict(self) -> Dict[str, Optional[float]]:
        return {
            "min_x": self.min_x,
            "max_x": self.max_x,
            "min_y": self.min_y,
            "max_y": self.max_y,
            "min_z": self.min_z,
            "max_z": self.max_z,
        }


# -----------------------------------------------------------------------------
# Modal Detection Helpers
# -----------------------------------------------------------------------------

@dataclass
class GCodeModals:
    """Detected modal states from G-code scan."""
    saw_g21: bool = False  # mm units
    saw_g20: bool = False  # inch units
    saw_g90: bool = False  # absolute mode
    saw_g91: bool = False  # incremental mode
    saw_g17: bool = False  # XY plane
    saw_m3: bool = False   # spindle CW
    saw_m4: bool = False   # spindle CCW
    saw_m5: bool = False   # spindle stop

    @property
    def spindle_on(self) -> bool:
        return self.saw_m3 or self.saw_m4


def _detect_modals(lines: List[str]) -> GCodeModals:
    """Scan lines for modal G-code commands."""
    modals = GCodeModals()
    for ln in lines:
        if "G21" in ln:
            modals.saw_g21 = True
        if "G20" in ln:
            modals.saw_g20 = True
        if "G90" in ln:
            modals.saw_g90 = True
        if "G91" in ln:
            modals.saw_g91 = True
        if "G17" in ln:
            modals.saw_g17 = True
        if _RE_M3.search(ln):
            modals.saw_m3 = True
        if _RE_M4.search(ln):
            modals.saw_m4 = True
        if _RE_M5.search(ln):
            modals.saw_m5 = True
    return modals


# -----------------------------------------------------------------------------
# Validation Rule Functions
# -----------------------------------------------------------------------------

def _check_units(
    modals: GCodeModals,
    require_units_mm: bool,
    errors: List[str],
    warnings: List[str],
) -> None:
    """Validate units (G20/G21) based on requirements."""
    if require_units_mm:
        if not modals.saw_g21:
            errors.append("Missing units command G21 (mm).")
        if modals.saw_g20:
            errors.append("Found G20 (inches) but mm required.")
    else:
        if not (modals.saw_g21 or modals.saw_g20):
            warnings.append("No explicit units command (G20/G21) found.")


def _check_distance_mode(
    modals: GCodeModals,
    require_absolute: bool,
    errors: List[str],
    warnings: List[str],
) -> None:
    """Validate distance mode (G90/G91) based on requirements."""
    if require_absolute:
        if not modals.saw_g90:
            errors.append("Missing absolute mode command G90.")
        if modals.saw_g91:
            errors.append("Found incremental mode G91 but absolute mode required.")
    else:
        if not (modals.saw_g90 or modals.saw_g91):
            warnings.append("No explicit distance mode (G90/G91) found.")


def _check_plane(
    modals: GCodeModals,
    require_xy_plane: bool,
    errors: List[str],
) -> None:
    """Validate plane selection (G17) if required."""
    if require_xy_plane and not modals.saw_g17:
        errors.append("Missing plane selection G17 (XY).")


def _check_spindle(
    modals: GCodeModals,
    require_spindle_on: bool,
    errors: List[str],
) -> None:
    """Validate spindle command (M3/M4) if required."""
    if require_spindle_on and not modals.spindle_on:
        errors.append("Missing spindle on command (M3/M4).")


# -----------------------------------------------------------------------------
# Motion Line Scanning
# -----------------------------------------------------------------------------

@dataclass
class MotionScanResult:
    """Results from scanning motion lines (G0/G1)."""
    bounds: Bounds = field(default_factory=Bounds)
    g0_count: int = 0
    g1_count: int = 0
    saw_any_retract_to_safe: bool = False
    rapid_below_safe_violations: List[str] = field(default_factory=list)
    feed_missing_violations: List[str] = field(default_factory=list)


def _is_rapid(ln: str) -> bool:
    """Check if line is a G0/G00 rapid move."""
    return "G0" in ln or "G00" in ln


def _is_linear(ln: str) -> bool:
    """Check if line is a G1/G01 linear move."""
    return "G1" in ln or "G01" in ln


def _scan_motion_lines(
    lines: List[str],
    safe_z_mm: float,
    require_feed_on_cut: bool,
) -> MotionScanResult:
    """
    Scan all motion lines (G0/G1) to collect:
    - Bounds (min/max X/Y/Z)
    - Safe-Z violations
    - Feed rate violations
    - Motion counts
    """
    result = MotionScanResult()

    current_x: Optional[float] = None
    current_y: Optional[float] = None
    current_z: Optional[float] = None
    current_f: Optional[float] = None

    for idx, ln in enumerate(lines):
        # Update "current feed" if any F appears
        f = _extract_f(ln)
        if f is not None:
            current_f = f

        is_g0 = _is_rapid(ln)
        is_g1 = _is_linear(ln)

        if not (is_g0 or is_g1):
            continue

        if is_g0:
            result.g0_count += 1
        if is_g1:
            result.g1_count += 1

        x = _extract_axis(ln, "X")
        y = _extract_axis(ln, "Y")
        z = _extract_axis(ln, "Z")

        # carry forward modal values (absolute mode assumed by default)
        if x is None:
            x = current_x
        if y is None:
            y = current_y
        if z is None:
            z = current_z

        current_x, current_y, current_z = x, y, z
        result.bounds.update(x, y, z)

        # safe-Z: track retracts
        if z is not None and z >= safe_z_mm:
            result.saw_any_retract_to_safe = True

        # safe-Z: rapids below safe
        if is_g0 and z is not None and z < safe_z_mm:
            result.rapid_below_safe_violations.append(
                f"Line {idx+1}: Rapid (G0) at Z{z} below safe_z_mm={safe_z_mm}"
            )

        # feed checks on cutting moves
        if is_g1 and require_feed_on_cut:
            f_inline = _extract_f(ln)
            f_effective = f_inline if f_inline is not None else current_f
            if f_effective is None or f_effective <= 0:
                result.feed_missing_violations.append(
                    f"Line {idx+1}: Cutting move (G1) missing feed rate F..."
                )

    return result


# -----------------------------------------------------------------------------
# Hard Bounds Checking
# -----------------------------------------------------------------------------

def _check_hard_bounds(
    bounds: Bounds,
    bounds_mm: Optional[Dict[str, float]],
    errors: List[str],
) -> None:
    """Check observed bounds against hard limits."""
    hard = bounds_mm or {}
    if not isinstance(hard, dict):
        return

    if not any(k in hard for k in ("min_x", "max_x", "min_y", "max_y", "min_z", "max_z")):
        return

    def _chk(name: str, observed: Optional[float], lo: Optional[float], hi: Optional[float]) -> None:
        if observed is None:
            return
        if lo is not None and observed < lo:
            errors.append(f"{name} below hard bound: {observed} < {lo}")
        if hi is not None and observed > hi:
            errors.append(f"{name} above hard bound: {observed} > {hi}")

    _chk("min_x", bounds.min_x, hard.get("min_x"), None)
    _chk("max_x", bounds.max_x, None, hard.get("max_x"))
    _chk("min_y", bounds.min_y, hard.get("min_y"), None)
    _chk("max_y", bounds.max_y, None, hard.get("max_y"))
    _chk("min_z", bounds.min_z, hard.get("min_z"), None)
    _chk("max_z", bounds.max_z, None, hard.get("max_z"))


# -----------------------------------------------------------------------------
# Summary Builder
# -----------------------------------------------------------------------------

def _build_summary(
    modals: GCodeModals,
    bounds: Bounds,
    line_count: int,
    g0_count: int,
    g1_count: int,
) -> Dict[str, Any]:
    """Build the summary dict for validation result."""
    return {
        "units": "mm" if modals.saw_g21 else ("in" if modals.saw_g20 else None),
        "distance_mode": "absolute" if modals.saw_g90 else ("incremental" if modals.saw_g91 else None),
        "plane": "xy" if modals.saw_g17 else None,
        "spindle_on": modals.spindle_on,
        "spindle_off_present": modals.saw_m5,
        "bounds": bounds.as_dict(),
        "stats": {
            "line_count": line_count,
            "g0_count": g0_count,
            "g1_count": g1_count,
        },
    }


# -----------------------------------------------------------------------------
# Main Validation Function (Simplified)
# -----------------------------------------------------------------------------

def validate_gcode_static(
    *,
    gcode_text: str,
    safe_z_mm: float = 5.0,
    bounds_mm: Optional[Dict[str, float]] = None,
    require_units_mm: bool = True,
    require_absolute: bool = True,
    require_xy_plane: bool = False,
    require_spindle_on: bool = True,
    require_feed_on_cut: bool = True,
) -> Dict[str, Any]:
    """
    Static (non-simulated) G-code validation.

    Checks:
      - Units (G21) if require_units_mm
      - Absolute mode (G90) if require_absolute
      - XY plane (G17) if require_xy_plane
      - Spindle on (M3/M4) if require_spindle_on
      - Feed rate presence for G1 cuts if require_feed_on_cut
      - Bounds (min/max X/Y/Z) and optional hard bounds checks
      - Safe-Z:
          * warns if never retracts to Z >= safe_z_mm
          * warns if any G0 rapid sets Z < safe_z_mm (static hazard)

    bounds_mm schema (optional):
      {
        "min_x": 0, "max_x": 300,
        "min_y": 0, "max_y": 300,
        "min_z": -30, "max_z": 50
      }
    """
    # Preprocess lines
    lines_raw = (gcode_text or "").splitlines()
    lines = [_strip_comment(ln).upper() for ln in lines_raw]
    lines = [ln for ln in lines if ln]  # drop empty

    errors: List[str] = []
    warnings: List[str] = []

    # Detect modal states
    modals = _detect_modals(lines)

    # Run validation checks
    _check_units(modals, require_units_mm, errors, warnings)
    _check_distance_mode(modals, require_absolute, errors, warnings)
    _check_plane(modals, require_xy_plane, errors)
    _check_spindle(modals, require_spindle_on, errors)

    # Scan motion lines
    scan = _scan_motion_lines(lines, safe_z_mm, require_feed_on_cut)

    # Collect feed violations
    if require_feed_on_cut and scan.feed_missing_violations:
        errors.extend(scan.feed_missing_violations)

    # Safe-Z warnings
    if not scan.saw_any_retract_to_safe:
        warnings.append(f"No retract found to safe Z >= {safe_z_mm}mm.")
    if scan.rapid_below_safe_violations:
        warnings.extend(scan.rapid_below_safe_violations)

    # Hard bounds check
    _check_hard_bounds(scan.bounds, bounds_mm, errors)

    # Build result
    ok = len(errors) == 0
    summary = _build_summary(
        modals, scan.bounds, len(lines), scan.g0_count, scan.g1_count
    )

    return {
        "ok": ok,
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
    }


# -----------------------------------------------------------------------------
# Attachment Helpers (unchanged)
# -----------------------------------------------------------------------------

def _attachments_root() -> Path:
    # Keep consistent with runs_v2/attachments.py default
    default_root = "services/api/data/run_attachments"
    root = os.getenv("RMOS_RUN_ATTACHMENTS_DIR", default_root)
    return Path(root)


def _read_attachment_bytes(sha256: str) -> bytes:
    """
    Reads content-addressed attachment data from RMOS_RUN_ATTACHMENTS_DIR.
    Compatible with content-addressed store:
      <root>/<sha256> for data bytes
      <root>/<sha256>.json for meta
    """
    root = _attachments_root()
    p = root / sha256
    if p.exists():
        return p.read_bytes()

    # fallback for legacy writers that included extensions
    for ext in (".txt", ".diff", ".gcode", ".json"):
        p2 = root / f"{sha256}{ext}"
        if p2.exists():
            return p2.read_bytes()

    raise FileNotFoundError(f"attachment not found: {sha256}")


def _read_attachment_meta(sha256: str) -> Dict[str, Any]:
    root = _attachments_root()
    meta_path = root / f"{sha256}.json"
    if not meta_path.exists():
        return {}
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except (IOError, OSError, json.JSONDecodeError, ValueError):  # WP-1: narrowed from except Exception
        return {}


@safety_critical
def validate_toolpaths_artifact_static(
    *,
    toolpaths_artifact_id: str,
    safe_z_mm: float = 5.0,
    bounds_mm: Optional[Dict[str, float]] = None,
    require_units_mm: bool = True,
    require_absolute: bool = True,
    require_xy_plane: bool = False,
    require_spindle_on: bool = True,
    require_feed_on_cut: bool = True,
) -> Dict[str, Any]:
    """
    Loads toolpaths artifact, extracts gcode_text either:
      - directly from payload["gcode_text"]
      - or from payload["attachments"]["gcode_sha256"] (content-addressed)
    then validates via validate_gcode_static.
    """
    from app.rmos.runs_v2 import store as runs_store

    art = runs_store.get_run(toolpaths_artifact_id)
    if not isinstance(art, dict):
        return {
            "ok": False,
            "errors": [f"toolpaths artifact not found: {toolpaths_artifact_id}"],
            "warnings": [],
            "summary": {},
        }

    payload = art.get("payload") or art.get("data") or {}
    if not isinstance(payload, dict):
        payload = {}

    gcode_text = payload.get("gcode_text")
    if isinstance(gcode_text, str) and gcode_text.strip():
        return validate_gcode_static(
            gcode_text=gcode_text,
            safe_z_mm=safe_z_mm,
            bounds_mm=bounds_mm,
            require_units_mm=require_units_mm,
            require_absolute=require_absolute,
            require_xy_plane=require_xy_plane,
            require_spindle_on=require_spindle_on,
            require_feed_on_cut=require_feed_on_cut,
        )

    attachments = payload.get("attachments")
    if isinstance(attachments, dict):
        sha = attachments.get("gcode_sha256") or attachments.get("gcode") or attachments.get("sha256")
        if isinstance(sha, str) and sha:
            try:
                data = _read_attachment_bytes(sha)
                # best-effort decode
                txt = data.decode("utf-8", errors="replace")
                out = validate_gcode_static(
                    gcode_text=txt,
                    safe_z_mm=safe_z_mm,
                    bounds_mm=bounds_mm,
                    require_units_mm=require_units_mm,
                    require_absolute=require_absolute,
                    require_xy_plane=require_xy_plane,
                    require_spindle_on=require_spindle_on,
                    require_feed_on_cut=require_feed_on_cut,
                )
                out["summary"] = out.get("summary") or {}
                out["summary"]["attachment_sha256"] = sha
                meta = _read_attachment_meta(sha)
                if meta:
                    out["summary"]["attachment_meta"] = meta
                return out
            except (IOError, OSError, FileNotFoundError, ValueError, UnicodeDecodeError) as e:  # WP-1: narrowed from except Exception
                return {
                    "ok": False,
                    "errors": [f"failed to read gcode attachment: {sha}: {type(e).__name__}: {e}"],
                    "warnings": [],
                    "summary": {},
                }

    return {
        "ok": False,
        "errors": [f"toolpaths artifact missing gcode_text and gcode attachment: {toolpaths_artifact_id}"],
        "warnings": [],
        "summary": {},
    }
