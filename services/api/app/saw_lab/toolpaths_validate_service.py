# services/api/app/saw_lab/toolpaths_validate_service.py
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


_RE_FLOAT = re.compile(r"([-+]?\d+(?:\.\d+)?)")


def _to_float(s: str) -> Optional[float]:
    try:
        return float(s)
    except Exception:
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
    except Exception:
        return {}


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
    lines_raw = (gcode_text or "").splitlines()
    lines = [_strip_comment(ln).upper() for ln in lines_raw]
    lines = [ln for ln in lines if ln]  # drop empty

    errors: List[str] = []
    warnings: List[str] = []

    saw_g21 = any("G21" in ln for ln in lines)
    saw_g20 = any("G20" in ln for ln in lines)
    saw_g90 = any("G90" in ln for ln in lines)
    saw_g91 = any("G91" in ln for ln in lines)
    saw_g17 = any("G17" in ln for ln in lines)

    saw_m3 = any(re.search(r"\bM3\b", ln) for ln in lines)
    saw_m4 = any(re.search(r"\bM4\b", ln) for ln in lines)
    saw_spindle_on = saw_m3 or saw_m4
    saw_m5 = any(re.search(r"\bM5\b", ln) for ln in lines)

    if require_units_mm:
        if not saw_g21:
            errors.append("Missing units command G21 (mm).")
        if saw_g20:
            errors.append("Found G20 (inches) but mm required.")
    else:
        if not (saw_g21 or saw_g20):
            warnings.append("No explicit units command (G20/G21) found.")

    if require_absolute:
        if not saw_g90:
            errors.append("Missing absolute mode command G90.")
        if saw_g91:
            errors.append("Found incremental mode G91 but absolute mode required.")
    else:
        if not (saw_g90 or saw_g91):
            warnings.append("No explicit distance mode (G90/G91) found.")

    if require_xy_plane and not saw_g17:
        errors.append("Missing plane selection G17 (XY).")

    if require_spindle_on and not saw_spindle_on:
        errors.append("Missing spindle on command (M3/M4).")

    bounds = Bounds()
    current_x: Optional[float] = None
    current_y: Optional[float] = None
    current_z: Optional[float] = None
    current_f: Optional[float] = None

    saw_any_retract_to_safe = False
    rapid_below_safe_violations: List[str] = []
    feed_missing_violations: List[str] = []

    g0_count = 0
    g1_count = 0

    for idx, ln in enumerate(lines):
        # Update "current feed" if any F appears
        f = _extract_f(ln)
        if f is not None:
            current_f = f

        is_g0 = ("G0" in ln) or ("G00" in ln)
        is_g1 = ("G1" in ln) or ("G01" in ln)

        if not (is_g0 or is_g1):
            continue

        if is_g0:
            g0_count += 1
        if is_g1:
            g1_count += 1

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
        bounds.update(x, y, z)

        # safe-Z: track retracts
        if z is not None and z >= safe_z_mm:
            saw_any_retract_to_safe = True

        # safe-Z: rapids below safe
        if is_g0 and z is not None and z < safe_z_mm:
            rapid_below_safe_violations.append(
                f"Line {idx+1}: Rapid (G0) at Z{z} below safe_z_mm={safe_z_mm}"
            )

        # feed checks on cutting moves
        if is_g1 and require_feed_on_cut:
            f_inline = _extract_f(ln)
            f_effective = f_inline if f_inline is not None else current_f
            if f_effective is None or f_effective <= 0:
                feed_missing_violations.append(
                    f"Line {idx+1}: Cutting move (G1) missing feed rate F..."
                )

    if require_feed_on_cut and feed_missing_violations:
        errors.extend(feed_missing_violations)

    if not saw_any_retract_to_safe:
        warnings.append(f"No retract found to safe Z >= {safe_z_mm}mm.")

    if rapid_below_safe_violations:
        warnings.extend(rapid_below_safe_violations)

    # Optional hard bounds enforcement
    hard = bounds_mm or {}
    if isinstance(hard, dict) and any(k in hard for k in ("min_x", "max_x", "min_y", "max_y", "min_z", "max_z")):

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

    ok = len(errors) == 0
    summary = {
        "units": "mm" if saw_g21 else ("in" if saw_g20 else None),
        "distance_mode": "absolute" if saw_g90 else ("incremental" if saw_g91 else None),
        "plane": "xy" if saw_g17 else None,
        "spindle_on": bool(saw_spindle_on),
        "spindle_off_present": bool(saw_m5),
        "bounds": bounds.as_dict(),
        "stats": {
            "line_count": len(lines),
            "g0_count": g0_count,
            "g1_count": g1_count,
        },
    }

    return {
        "ok": ok,
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
    }


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
            except Exception as e:
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
