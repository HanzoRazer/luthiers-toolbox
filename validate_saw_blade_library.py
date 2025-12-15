Here’s a solid, repo-friendly validate_saw_blade_library.py you can drop into scripts/. It performs hard validations (fail build) and soft validations (warnings) and returns a non-zero exit code on failures.

#!/usr/bin/env python3
"""
validate_saw_blade_library.py

Validates Saw Lab saw blade JSON libraries for:
- Required fields
- Type checks
- Unit sanity (mm, RPM)
- Physical plausibility checks (kerf > plate thickness, etc.)
- Optional: source_refs existence on disk
- Optional: rim speed warnings

Expected JSON formats:
A) {"blades": [ {...}, {...} ]}
B) [ {...}, {...} ]
C) {"<blade_id>": {...}, "<blade_id2>": {...} }

Usage:
  python scripts/validate_saw_blade_library.py path/to/saw_blades.json
  python scripts/validate_saw_blade_library.py path/to/saw_blades.json --strict
  python scripts/validate_saw_blade_library.py path/to/saw_blades.json --check-sources --repo-root .

Exit codes:
  0 = OK (no errors; may have warnings)
  2 = Validation errors found
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union


DATA_QUALITY_ALLOWED = {"VERIFIED", "PARTIAL", "ESTIMATED", "LEGACY"}

# Reasonable defaults (tunable)
MIN_DIAMETER_MM = 50.0
MAX_DIAMETER_MM = 600.0

MIN_KERF_MM = 0.2
MAX_KERF_MM = 10.0

MIN_PLATE_MM = 0.1
MAX_PLATE_MM = 8.0

MIN_TEETH = 8
MAX_TEETH = 200

MIN_RPM = 100
MAX_RPM = 30000  # sanity upper bound (warning unless strict)

# Rim speed sanity (m/s). Many woodworking blades operate well below ~100 m/s.
# We'll warn above this threshold, and error above an extreme threshold in strict mode.
RIM_SPEED_WARN_MS = 100.0
RIM_SPEED_STRICT_MAX_MS = 140.0


REQUIRED_FIELDS = [
    "blade_id",
    "manufacturer",
    "model",
    "diameter_mm",
    "kerf_mm",
    "plate_thickness_mm",
    "tooth_count",
    "max_rpm",
    "data_quality",
]

OPTIONAL_FIELDS = [
    "tooth_geometry",
    "hook_angle_deg",
    "intended_use",
    "notes",
    "source_refs",
]


@dataclass
class Issue:
    level: str  # "ERROR" | "WARN"
    blade_id: str
    message: str
    path: str  # dotted path for quick location


def _is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _rim_speed_ms(diameter_mm: float, rpm: float) -> float:
    # v = pi * D * rpm / 60
    return math.pi * (diameter_mm / 1000.0) * (rpm / 60.0)


def _as_str(x: Any) -> Optional[str]:
    return x if isinstance(x, str) else None


def _normalize_blades(payload: Any) -> List[Dict[str, Any]]:
    """
    Accept:
      - list of blade dicts
      - {"blades": [ ... ]}
      - dict keyed by blade_id -> blade dict
    Returns list of blade dicts.
    """
    if isinstance(payload, list):
        if all(isinstance(x, dict) for x in payload):
            return payload
        raise ValueError("Top-level list must contain objects (dicts).")

    if isinstance(payload, dict):
        if "blades" in payload:
            blades = payload["blades"]
            if not isinstance(blades, list) or not all(isinstance(x, dict) for x in blades):
                raise ValueError('"blades" must be a list of objects.')
            return blades

        # keyed dict form
        if all(isinstance(v, dict) for v in payload.values()):
            blades = []
            for k, v in payload.items():
                # Allow missing blade_id; inject from key (but still validate)
                if "blade_id" not in v:
                    v = dict(v)
                    v["blade_id"] = k
                blades.append(v)
            return blades

    raise ValueError("Unsupported JSON format. Expected list, {blades:[...]}, or {id:{...}}.")


def validate_blade(
    blade: Dict[str, Any],
    *,
    strict: bool,
    check_sources: bool,
    repo_root: Optional[str],
) -> List[Issue]:
    issues: List[Issue] = []

    blade_id = _as_str(blade.get("blade_id")) or "<missing blade_id>"

    # Required fields presence
    for f in REQUIRED_FIELDS:
        if f not in blade:
            issues.append(Issue("ERROR", blade_id, f"Missing required field: {f}", f))
    if any(i.level == "ERROR" for i in issues):
        return issues  # can't go further reliably

    # Types
    if not isinstance(blade["blade_id"], str) or not blade["blade_id"].strip():
        issues.append(Issue("ERROR", blade_id, "blade_id must be a non-empty string", "blade_id"))
    if not isinstance(blade["manufacturer"], str) or not blade["manufacturer"].strip():
        issues.append(Issue("ERROR", blade_id, "manufacturer must be a non-empty string", "manufacturer"))
    if not isinstance(blade["model"], str) or not blade["model"].strip():
        issues.append(Issue("ERROR", blade_id, "model must be a non-empty string", "model"))

    # Numeric required fields
    for nf in ["diameter_mm", "kerf_mm", "plate_thickness_mm", "max_rpm"]:
        if not _is_number(blade.get(nf)):
            issues.append(Issue("ERROR", blade_id, f"{nf} must be a number", nf))

    if not isinstance(blade.get("tooth_count"), int) or isinstance(blade.get("tooth_count"), bool):
        issues.append(Issue("ERROR", blade_id, "tooth_count must be an integer", "tooth_count"))

    # data_quality enum
    dq = blade.get("data_quality")
    if dq not in DATA_QUALITY_ALLOWED:
        issues.append(
            Issue(
                "ERROR",
                blade_id,
                f"data_quality must be one of {sorted(DATA_QUALITY_ALLOWED)}",
                "data_quality",
            )
        )

    # Optional: intended_use
    if "intended_use" in blade and blade["intended_use"] is not None:
        if not isinstance(blade["intended_use"], list) or not all(isinstance(x, str) for x in blade["intended_use"]):
            issues.append(Issue("ERROR", blade_id, "intended_use must be a list of strings", "intended_use"))

    # Optional: hook_angle_deg
    if "hook_angle_deg" in blade and blade["hook_angle_deg"] is not None:
        if not _is_number(blade["hook_angle_deg"]):
            issues.append(Issue("ERROR", blade_id, "hook_angle_deg must be a number", "hook_angle_deg"))
        else:
            ha = float(blade["hook_angle_deg"])
            # woodworking saw hook angles typically in ~[-10, 30], but keep wide bounds
            if ha < -30 or ha > 45:
                issues.append(Issue("WARN", blade_id, f"hook_angle_deg looks unusual: {ha}", "hook_angle_deg"))

    # Stop if hard type errors exist
    if any(i.level == "ERROR" for i in issues):
        return issues

    diameter_mm = float(blade["diameter_mm"])
    kerf_mm = float(blade["kerf_mm"])
    plate_mm = float(blade["plate_thickness_mm"])
    rpm = float(blade["max_rpm"])
    teeth = int(blade["tooth_count"])

    # Sanity ranges
    def range_check(val: float, lo: float, hi: float, field: str) -> None:
        if val < lo or val > hi:
            msg = f"{field} out of expected range [{lo}, {hi}]: {val}"
            issues.append(Issue("ERROR" if strict else "WARN", blade_id, msg, field))

    range_check(diameter_mm, MIN_DIAMETER_MM, MAX_DIAMETER_MM, "diameter_mm")
    range_check(kerf_mm, MIN_KERF_MM, MAX_KERF_MM, "kerf_mm")
    range_check(plate_mm, MIN_PLATE_MM, MAX_PLATE_MM, "plate_thickness_mm")
    range_check(rpm, MIN_RPM, MAX_RPM, "max_rpm")

    if teeth < MIN_TEETH or teeth > MAX_TEETH:
        msg = f"tooth_count out of expected range [{MIN_TEETH}, {MAX_TEETH}]: {teeth}"
        issues.append(Issue("ERROR" if strict else "WARN", blade_id, msg, "tooth_count"))

    # Physical plausibility: kerf should be >= plate thickness
    if kerf_mm <= plate_mm:
        issues.append(
            Issue(
                "ERROR",
                blade_id,
                f"kerf_mm ({kerf_mm}) must be > plate_thickness_mm ({plate_mm})",
                "kerf_mm",
            )
        )
    else:
        # warn if kerf is only barely larger (binding risk / unrealistic)
        if (kerf_mm - plate_mm) < 0.2:
            issues.append(
                Issue(
                    "WARN",
                    blade_id,
                    f"kerf_mm - plate_thickness_mm is very small ({kerf_mm - plate_mm:.3f}mm)",
                    "kerf_mm",
                )
            )

    # Rim speed
    v = _rim_speed_ms(diameter_mm, rpm)
    if v > RIM_SPEED_WARN_MS:
        issues.append(
            Issue(
                "WARN",
                blade_id,
                f"Rim speed is high: {v:.1f} m/s at {rpm:.0f} RPM and {diameter_mm:.1f}mm diameter",
                "max_rpm",
            )
        )
    if strict and v > RIM_SPEED_STRICT_MAX_MS:
        issues.append(
            Issue(
                "ERROR",
                blade_id,
                f"Rim speed exceeds strict limit: {v:.1f} m/s (>{RIM_SPEED_STRICT_MAX_MS:.1f})",
                "max_rpm",
            )
        )

    # source_refs existence
    if check_sources:
        refs = blade.get("source_refs", [])
        if refs is None:
            refs = []
        if not isinstance(refs, list) or not all(isinstance(x, str) for x in refs):
            issues.append(Issue("ERROR", blade_id, "source_refs must be a list of strings", "source_refs"))
        else:
            for idx, ref in enumerate(refs):
                # Allow repo-relative refs
                path = ref
                if repo_root and not os.path.isabs(path):
                    path = os.path.join(repo_root, ref)
                if not os.path.exists(path):
                    issues.append(
                        Issue(
                            "WARN" if not strict else "ERROR",
                            blade_id,
                            f"source_refs[{idx}] missing on disk: {ref}",
                            f"source_refs[{idx}]",
                        )
                    )

    return issues


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Saw Lab saw blade JSON library.")
    ap.add_argument("json_path", help="Path to saw blade JSON library file.")
    ap.add_argument("--strict", action="store_true", help="Treat warnings as errors where applicable.")
    ap.add_argument(
        "--check-sources",
        action="store_true",
        help="Check that source_refs paths exist on disk (warn or error in strict mode).",
    )
    ap.add_argument(
        "--repo-root",
        default=None,
        help="Repo root for resolving repo-relative source_refs (recommended when --check-sources).",
    )
    args = ap.parse_args()

    try:
        with open(args.json_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to read JSON: {args.json_path}\n  {e}", file=sys.stderr)
        return 2

    try:
        blades = _normalize_blades(payload)
    except Exception as e:
        print(f"[ERROR] Invalid JSON structure:\n  {e}", file=sys.stderr)
        return 2

    all_issues: List[Issue] = []
    seen_ids: Dict[str, int] = {}

    for i, blade in enumerate(blades):
        bid = blade.get("blade_id", f"<missing@{i}>")
        if isinstance(bid, str):
            seen_ids[bid] = seen_ids.get(bid, 0) + 1

        issues = validate_blade(
            blade,
            strict=args.strict,
            check_sources=args.check_sources,
            repo_root=args.repo_root,
        )
        all_issues.extend(issues)

    # Duplicate blade_id check
    for bid, count in seen_ids.items():
        if count > 1:
            all_issues.append(Issue("ERROR", bid, f"Duplicate blade_id appears {count} times", "blade_id"))

    # Print report
    errors = [i for i in all_issues if i.level == "ERROR"]
    warns = [i for i in all_issues if i.level == "WARN"]

    if warns:
        print(f"\n=== WARNINGS ({len(warns)}) ===")
        for w in warns:
            print(f"[WARN] {w.blade_id} :: {w.path} :: {w.message}")

    if errors:
        print(f"\n=== ERRORS ({len(errors)}) ===")
        for e in errors:
            print(f"[ERROR] {e.blade_id} :: {e.path} :: {e.message}")

    print("\n=== SUMMARY ===")
    print(f"Blades parsed: {len(blades)}")
    print(f"Warnings:     {len(warns)}")
    print(f"Errors:       {len(errors)}")

    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

Recommended placement

scripts/validate_saw_blade_library.py

Recommended usage patterns

During early migration (tolerant):

python scripts/validate_saw_blade_library.py services/api/app/saw_lab/data/saw_blades.json


During CI / pre-merge:

python scripts/validate_saw_blade_library.py services/api/app/saw_lab/data/saw_blades.json --strict 