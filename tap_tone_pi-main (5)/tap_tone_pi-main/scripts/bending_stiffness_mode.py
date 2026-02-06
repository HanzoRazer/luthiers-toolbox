from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional


TOOL_ID = "tap_tone_pi"
TOOL_VERSION = os.getenv("TAP_TONE_PI_VERSION", "v1.0")


# ----------------------------
# Helpers (time + hashing + IO)
# ----------------------------
def utc_now_iso() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def write_text(path: Path, s: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(s, encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def append_jsonl(path: Path, obj: Any) -> None:
    """Append a single JSON object as one line to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, sort_keys=True))
        f.write("\n")


def _kinds_count(files: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count file kinds from manifest files list."""
    kinds: Dict[str, int] = {}
    for f in files:
        k = f.get("kind") or "unknown"
        kinds[k] = kinds.get(k, 0) + 1
    return kinds


def ensure_session_dir(out_root: Path, session_id: str, session_root_override: Optional[str]) -> Path:
    if session_root_override:
        return Path(session_root_override).expanduser().resolve()
    return (out_root / f"session_{session_id}").resolve()


# ----------------------------
# Parsing readings
# ----------------------------
def parse_pairs_list(pairs: List[str]) -> List[Tuple[float, float]]:
    """
    pairs: ["load,deflection", ...]
    """
    out: List[Tuple[float, float]] = []
    for p in pairs:
        parts = p.split(",")
        if len(parts) != 2:
            raise ValueError(f"Bad pair '{p}'. Expected 'load,deflection'.")
        out.append((float(parts[0]), float(parts[1])))
    return out


def parse_semicolon_pairs(s: str) -> List[Tuple[float, float]]:
    """
    "load,defl;load,defl;..."
    """
    chunks = [c.strip() for c in s.split(";") if c.strip()]
    return parse_pairs_list(chunks)


def read_csv_pairs(path: Path) -> List[Tuple[float, float]]:
    """
    CSV with headers: load,deflection
    """
    rows: List[Tuple[float, float]] = []
    with path.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        if not r.fieldnames or "load" not in r.fieldnames or "deflection" not in r.fieldnames:
            raise ValueError("CSV must contain headers: load,deflection")
        for row in r:
            if row.get("load") is None or row.get("deflection") is None:
                continue
            rows.append((float(row["load"]), float(row["deflection"])) )
    if not rows:
        raise ValueError("No valid rows found in CSV.")
    return rows


# ----------------------------
# Linear fit (least squares)
# ----------------------------
def fit_line_load_vs_deflection(samples: List[Tuple[float, float]]) -> Dict[str, float]:
    """
    Fit: load = k * deflection + b
    Returns: k, b, r2
    """
    ys = [p[0] for p in samples]  # load
    xs = [p[1] for p in samples]  # deflection
    n = len(xs)

    x_mean = sum(xs) / n
    y_mean = sum(ys) / n

    sxx = sum((x - x_mean) ** 2 for x in xs)
    sxy = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))

    if sxx == 0:
        raise ValueError("All deflection values are identical; cannot fit slope.")

    k = sxy / sxx
    b = y_mean - k * x_mean

    y_hat = [k * x + b for x in xs]
    ss_tot = sum((y - y_mean) ** 2 for y in ys)
    ss_res = sum((y - yh) ** 2 for y, yh in zip(ys, y_hat))
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0

    return {"k": float(k), "b": float(b), "r2": float(r2)}


def compute_ei_three_point(k_force_per_deflection: float, span_mm: float) -> float:
    """
    Three-point bending, center load, small deflection:
      EI = (P/δ) L^3 / 48
    Returns EI in N*mm^2 when k is N/mm and L is mm.
    """
    return (k_force_per_deflection * (span_mm ** 3)) / 48.0


# ----------------------------
# Statistics / Uncertainty
# ----------------------------
import math as _math


def mean_std(vals: List[float]) -> Tuple[float, float]:
    n = len(vals)
    m = sum(vals) / n
    if n < 2:
        return m, 0.0
    var = sum((v - m) ** 2 for v in vals) / (n - 1)
    return m, _math.sqrt(var)


def z_for_ci(ci_level: float) -> float:
    # Normal approx z-values (good enough for a micro; conservative in small n if you choose 0.95).
    # 90% -> 1.645, 95% -> 1.96, 99% -> 2.576
    if ci_level == 0.90:
        return 1.645
    if ci_level == 0.95:
        return 1.96
    if ci_level == 0.99:
        return 2.576
    raise ValueError("ci_level must be one of 0.90, 0.95, 0.99")


def uncertain_value(vals: List[float], ci_level: float) -> Dict[str, Any]:
    n = len(vals)
    m, s = mean_std(vals)
    se = s / _math.sqrt(n) if n > 0 else 0.0
    z = z_for_ci(ci_level)
    half = z * se
    return {
        "mean": float(m),
        "std": float(s),
        "se": float(se),
        "ci_low": float(m - half),
        "ci_high": float(m + half),
        "n": int(n),
    }


# ----------------------------
# Manifest + utilities
# ----------------------------
def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def pack_zip(bundle_dir: Path, zip_path: Path) -> None:
    import zipfile

    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in bundle_dir.rglob("*"):
            if p.is_file():
                rel = p.relative_to(bundle_dir)
                z.write(p, str(rel))


def strip_nulls(x: Any) -> Any:
    if isinstance(x, dict):
        return {k: strip_nulls(v) for k, v in x.items() if v is not None}
    if isinstance(x, list):
        return [strip_nulls(v) for v in x]
    return x


# ----------------------------
# CLI
# ----------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="Bending stiffness test (measurement-only) bundle logger + uncertainty micro")

    ap.add_argument("--out", required=True, help="Output directory (bundle root)")
    ap.add_argument("--test-id", default=None, help="Optional test id; if omitted, timestamp-based id is used")
    ap.add_argument("--method", choices=["three_point_bending", "cantilever"], default="three_point_bending")
    ap.add_argument("--units-length", choices=["mm", "in"], default="mm")
    ap.add_argument("--units-force", choices=["N", "lbf"], default="N")

    ap.add_argument("--specimen-id", required=True)
    ap.add_argument("--material-role", choices=["top", "back", "brace_stock", "unknown"], default="unknown")
    ap.add_argument("--wood-species", default=None)
    ap.add_argument("--grain-orientation", choices=["longitudinal", "cross", "unknown"], default="unknown")

    ap.add_argument("--span-mm", type=float, required=True, help="Support span in mm (or effective length).")

    # Base readings (single replicate)
    ap.add_argument("--readings-csv", default=None, help="CSV path with headers load,deflection")
    ap.add_argument(
        "--pair",
        action="append",
        default=[],
        help="Inline reading 'load,deflection' (repeatable). Example: --pair 5,0.20 --pair 10,0.41",
    )

    # Replicates: each item either "csv:/path/to.csv" or "pairs:load,defl;load,defl;..."
    ap.add_argument(
        "--replicate",
        action="append",
        default=[],
        help="Repeatable replicate spec: csv:/path OR pairs:load,defl;load,defl;...",
    )

    # Uncertainty inputs
    ap.add_argument("--dial-resolution-mm", type=float, default=None, help="Dial indicator resolution in mm (optional).")
    ap.add_argument("--load-resolution-force", type=float, default=None, help="Load resolution in same force units (optional).")
    ap.add_argument("--ci-level", type=float, choices=[0.90, 0.95, 0.99], default=0.95)

    # Calibration (optional)
    ap.add_argument("--dial-zeroed", action="store_true", help="Mark dial indicator as zeroed for this session.")
    ap.add_argument("--dial-zeroed-at-utc", default=None, help="UTC timestamp when dial was zeroed (ISO). If omitted and --dial-zeroed, uses now.")
    ap.add_argument("--dial-zero-method", choices=["manual_zero", "tare_block", "other"], default=None)
    ap.add_argument("--dial-zero-notes", default=None)

    ap.add_argument("--load-cell-present", action="store_true", help="Indicates a load cell was used for force measurement.")
    ap.add_argument("--load-cell-calibration-date-utc", default=None, help="ISO date/datetime (UTC) for last load cell calibration.")
    ap.add_argument("--load-cell-cal-provider", default=None)
    ap.add_argument("--load-cell-cert-id", default=None)
    ap.add_argument("--load-cell-cal-notes", default=None)

    ap.add_argument("--standard-used", action="store_true", help="If you ran a known standard specimen check.")
    ap.add_argument("--standard-specimen-id", default=None)
    ap.add_argument("--standard-expected-k", type=float, default=None)
    ap.add_argument("--standard-observed-k", type=float, default=None)
    ap.add_argument("--standard-tolerance", type=float, default=None)

    # Session calibration (shared capsule)
    ap.add_argument("--session-id", default=None, help="Optional session id for shared calibration capsule.")
    ap.add_argument("--session-root", default=None, help="Optional override for session folder root. Defaults to <out>/session_<session_id>/")
    ap.add_argument("--session-calibration", default=None, help="Path to an existing session_calibration.json to use.")
    ap.add_argument("--write-session-calibration", action="store_true", help="Write/overwrite session_calibration.json from CLI calibration flags.")

    ap.add_argument("--operator", default=None)
    ap.add_argument("--device-id", default=None)
    ap.add_argument("--notes", default=None)

    ap.add_argument("--pack", action="store_true", help="Create bundle.zip next to the bundle directory")

    args = ap.parse_args()

    started = utc_now_iso()
    bundle_id = args.test_id or f"bend_{dt.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"

    out_root = Path(args.out).expanduser().resolve()
    bundle_dir = out_root / bundle_id
    raw_dir = bundle_dir / "raw"
    analysis_dir = bundle_dir / "analysis"
    replicates_dir = raw_dir / "replicates"

    bundle_dir.mkdir(parents=True, exist_ok=True)

    # ----------------------------
    # Session calibration setup
    # ----------------------------
    session_cal_obj: Optional[Dict[str, Any]] = None
    session_cal_path: Optional[Path] = None

    session_manifest_path: Optional[Path] = None
    if args.session_id:
        session_dir = ensure_session_dir(out_root, args.session_id, args.session_root)
        session_dir.mkdir(parents=True, exist_ok=True)
        session_cal_path = session_dir / "session_calibration.json"
        session_manifest_path = session_dir / "session_manifest.jsonl"

    # Priority: 1) explicit --session-calibration, 2) existing session_<id>/session_calibration.json
    if args.session_calibration:
        p = Path(args.session_calibration).expanduser().resolve()
        session_cal_obj = read_json(p)
    elif session_cal_path and session_cal_path.exists():
        session_cal_obj = read_json(session_cal_path)

    # Determine replicates
    replicate_samples: List[List[Tuple[float, float]]] = []

    if args.replicate:
        for i, spec in enumerate(args.replicate, start=1):
            if spec.startswith("csv:"):
                p = Path(spec[len("csv:"):]).expanduser().resolve()
                replicate_samples.append(read_csv_pairs(p))
            elif spec.startswith("pairs:"):
                s = spec[len("pairs:"):]
                replicate_samples.append(parse_semicolon_pairs(s))
            else:
                raise SystemExit("Each --replicate must start with csv: or pairs:")
    else:
        # Use base readings as single replicate
        if args.readings_csv:
            replicate_samples.append(read_csv_pairs(Path(args.readings_csv).expanduser().resolve()))
        else:
            if not args.pair:
                raise SystemExit("Provide either --readings-csv or at least one --pair load,deflection")
            replicate_samples.append(parse_pairs_list(args.pair))

    # Write canonical readings.csv for overall (replicate 1) and each replicate
    raw_dir.mkdir(parents=True, exist_ok=True)
    replicates_dir.mkdir(parents=True, exist_ok=True)

    # Overall readings.csv = replicate 1
    readings_csv_path = raw_dir / "readings.csv"
    with readings_csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["load", "deflection"])
        for load, defl in replicate_samples[0]:
            w.writerow([f"{load:.10g}", f"{defl:.10g}"])

    # Replicate files
    rep_relpaths: List[str] = []
    for idx, samples in enumerate(replicate_samples, start=1):
        rp = replicates_dir / f"replicate_{idx:02d}.csv"
        with rp.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["load", "deflection"])
            for load, defl in samples:
                w.writerow([f"{load:.10g}", f"{defl:.10g}"])
        rep_relpaths.append(f"raw/replicates/replicate_{idx:02d}.csv")

    # Fit each replicate
    ks: List[float] = []
    r2s: List[float] = []
    eis: List[float] = []
    warnings: List[str] = []

    for samples in replicate_samples:
        fit = fit_line_load_vs_deflection(samples)
        ks.append(fit["k"])
        r2s.append(fit["r2"])

        if fit["r2"] < 0.98:
            warnings.append(f"low_linearity_r2:{fit['r2']:.4f}")

        # EI only when three-point AND SI/mm
        if args.method == "three_point_bending" and args.units_length == "mm" and args.units_force == "N":
            eis.append(compute_ei_three_point(k_force_per_deflection=fit["k"], span_mm=float(args.span_mm)))

    # Choose “primary” values as replicate 1 (keeps continuity)
    k_primary = ks[0]
    r2_primary = r2s[0]
    ei_primary = eis[0] if eis else None

    # Build uncertainty (optional)
    uncertainty_block: Optional[Dict[str, Any]] = None
    if len(ks) > 1 or args.dial_resolution_mm is not None or args.load_resolution_force is not None:
        # Method selection
        method = "replicates_normal_approx" if len(ks) > 1 else "quantization_only"

        uncertainty_block = {
            "method": method,
            "ci_level": float(args.ci_level),
            "inputs": {
                "dial_resolution_mm": float(args.dial_resolution_mm) if args.dial_resolution_mm is not None else 0.0,
                "load_resolution_force": float(args.load_resolution_force) if args.load_resolution_force is not None else None,
                "replicates": int(len(ks))
            },
            "k": uncertain_value(ks, args.ci_level),
            "ei_n_mm2": uncertain_value(eis, args.ci_level) if eis and len(eis) > 0 else None
        }
        # Conservative note: quantization-only is not rigorously propagated; it’s logged for traceability.
        if len(ks) == 1 and (args.dial_resolution_mm is not None or args.load_resolution_force is not None):
            warnings.append("uncertainty_quantization_only_logged_no_propagation")

    # EI assumptions
    ei_assumptions = None
    if args.method == "three_point_bending":
        if args.units_length == "mm" and args.units_force == "N":
            ei_assumptions = "EI computed using three-point bending small-deflection formula: EI=(P/δ)*L^3/48. Assumes central load, linear elastic response, negligible shear deflection."
        else:
            warnings.append("ei_not_computed_non_si_units")

    analysis_obj: Dict[str, Any] = {
        "schema": {"name": "bending_stiffness", "version": "1.1", "created_at_utc": utc_now_iso()},
        "test": {
            "test_id": bundle_id,
            "method": args.method,
            "units": {"length": args.units_length, "force": args.units_force},
            "notes": args.notes,
        },
        "specimen": {
            "specimen_id": args.specimen_id,
            "material_role": args.material_role,
            "wood_species": args.wood_species,
            "grain_orientation": args.grain_orientation,
        },
        "fixture": {
            "span_mm": float(args.span_mm),
            "support_type": "unknown",
            "load_nose_radius_mm": None,
            "dial_indicator_resolution_mm": float(args.dial_resolution_mm) if args.dial_resolution_mm is not None else None,
        },
        "readings": {
            "csv_relpath": "raw/readings.csv",
            "rows": [{"load": float(l), "deflection": float(d)} for l, d in replicate_samples[0]],
            "replicates": [
                {"csv_relpath": rp, "rows": [{"load": float(l), "deflection": float(d)} for l, d in rs]}
                for rp, rs in zip(rep_relpaths, replicate_samples)
            ]
        },
        "results": {
            "k_force_per_deflection": float(k_primary),
            "k_r2": float(r2_primary),
            "ei_n_mm2": float(ei_primary) if ei_primary is not None else None,
            "ei_method_assumptions": ei_assumptions,
            "warnings": warnings,
            "uncertainty": uncertainty_block,
        },
        "provenance": {
            "tool_id": TOOL_ID,
            "tool_version": TOOL_VERSION,
            "operator": args.operator,
            "device_id": args.device_id,
            "captured_at_utc": started,
        },
    }

    # ----------------------------
    # Calibration block (optional)
    # ----------------------------
    calibration = None
    if args.dial_zeroed or args.load_cell_present or args.standard_used:
        dial_zeroed_at = args.dial_zeroed_at_utc
        if args.dial_zeroed and not dial_zeroed_at:
            dial_zeroed_at = utc_now_iso()

        # Dial block only if dial-related flags used
        dial_block = None
        if args.dial_zeroed or args.dial_zero_method or args.dial_zero_notes:
            dial_block = {
                "zeroed": bool(args.dial_zeroed),
                "zeroed_at_utc": dial_zeroed_at or utc_now_iso(),
                "method": args.dial_zero_method,
                "notes": args.dial_zero_notes,
            }

        # Load cell block only if load cell-related flags used
        load_cell_block = None
        if args.load_cell_present or args.load_cell_calibration_date_utc or args.load_cell_cal_provider or args.load_cell_cert_id:
            load_cell_block = {
                "present": bool(args.load_cell_present),
                "calibration_date_utc": args.load_cell_calibration_date_utc or "unknown",
                "calibration_provider": args.load_cell_cal_provider,
                "certificate_id": args.load_cell_cert_id,
                "notes": args.load_cell_cal_notes,
            }

        # Standard specimen block only if standard flags used
        standard_block = None
        if args.standard_used or args.standard_specimen_id:
            pass_flag = None
            if (args.standard_expected_k is not None and args.standard_observed_k is not None and args.standard_tolerance is not None):
                pass_flag = abs(args.standard_observed_k - args.standard_expected_k) <= args.standard_tolerance

            standard_block = {
                "used": bool(args.standard_used),
                "specimen_id": args.standard_specimen_id or "unknown",
                "expected_k": args.standard_expected_k,
                "observed_k": args.standard_observed_k,
                "tolerance": args.standard_tolerance,
                "pass": pass_flag,
                "notes": None,
            }

        calibration = {
            "dial": dial_block or {"zeroed": False, "zeroed_at_utc": utc_now_iso()},
            "load_cell": load_cell_block or {"present": False, "calibration_date_utc": "unknown"},
            "standard_specimen": standard_block or {"used": False, "specimen_id": "unknown"}
        }

    # Write session calibration when requested
    if args.session_id and args.write_session_calibration and calibration:
        session_cal_obj = {
            "schema": {"name": "session_calibration", "version": "1.0", "created_at_utc": utc_now_iso()},
            "session": {
                "session_id": args.session_id,
                "operator": args.operator,
                "device_id": args.device_id,
                "notes": None
            },
            "calibration": calibration
        }
        write_json(session_cal_path, strip_nulls(session_cal_obj))

    # Apply session calibration if present and no per-run calibration flags provided
    run_has_cal_flags = any([
        args.dial_zeroed, args.dial_zero_method, args.dial_zero_notes,
        args.load_cell_present, args.load_cell_calibration_date_utc, args.load_cell_cal_provider, args.load_cell_cert_id,
        args.standard_used, args.standard_specimen_id, args.standard_expected_k, args.standard_observed_k, args.standard_tolerance
    ])

    if session_cal_obj and not run_has_cal_flags:
        calibration = session_cal_obj.get("calibration", calibration)

    analysis_obj["calibration"] = calibration

    # Add session reference pointer if session calibration is in use
    if args.session_id and session_cal_obj:
        if analysis_obj.get("calibration") is None:
            analysis_obj["calibration"] = {}
        analysis_obj["calibration"]["session_ref"] = {
            "session_id": args.session_id,
            "session_calibration_relpath": "calibration/session_calibration.json"
        }

    analysis_obj = strip_nulls(analysis_obj)

    analysis_path = analysis_dir / "bending_stiffness.json"
    write_json(analysis_path, analysis_obj)

    # Copy session calibration into bundle (self-contained)
    session_copy_rel: Optional[str] = None
    if session_cal_obj:
        session_copy_rel = "calibration/session_calibration.json"
        write_json(bundle_dir / session_copy_rel, session_cal_obj)

    finished = utc_now_iso()

    # Build manifest
    files: List[Dict[str, Any]] = []

    def add_file(rel: str, kind: str, mime: str) -> None:
        p = bundle_dir / rel
        files.append(
            {
                "relpath": rel,
                "sha256": sha256_file(p),
                "bytes": int(p.stat().st_size),
                "mime": mime,
                "kind": kind,
                "point_id": None,
            }
        )

    add_file("raw/readings.csv", "readings", "text/csv")
    for rp in rep_relpaths:
        add_file(rp, "readings_replicate", "text/csv")
    add_file("analysis/bending_stiffness.json", "analysis_summary", "application/json")
    if session_copy_rel:
        add_file(session_copy_rel, "session_calibration", "application/json")

    meta = {
        "bundle_id": bundle_id,
        "capture_started_at_utc": started,
        "capture_finished_at_utc": finished,
        "mode": "bending_stiffness",
        "units": {"length": args.units_length, "force": args.units_force},
        "specimen_id": args.specimen_id,
        "material_role": args.material_role,
        "method": args.method,
        "span_mm": float(args.span_mm),
        "replicates": int(len(replicate_samples)),
        "ci_level": float(args.ci_level),
        "calibration": {
            "dial_zeroed": bool(args.dial_zeroed),
            "load_cell_present": bool(args.load_cell_present),
            "load_cell_calibration_date_utc": args.load_cell_calibration_date_utc,
            "standard_used": bool(args.standard_used),
            "standard_specimen_id": args.standard_specimen_id
        },
        "session_id": args.session_id
    }

    manifest = {
        "manifest_version": "1.0",
        "bundle_id": meta["bundle_id"],
        "capture_started_at_utc": meta["capture_started_at_utc"],
        "capture_finished_at_utc": meta["capture_finished_at_utc"],
        "tool": {"tool_id": TOOL_ID, "tool_version": TOOL_VERSION},
        "meta": meta,
        "files": files,
    }

    manifest_path = bundle_dir / "manifest.json"
    write_json(manifest_path, manifest)

    bundle_sha = sha256_bytes(canonical_json_bytes(manifest))
    write_text(bundle_dir / "bundle_sha256.txt", bundle_sha + "\n")

    if args.pack:
        zip_path = out_root / f"{bundle_id}.zip"
        pack_zip(bundle_dir, zip_path)

    # ----------------------------
    # Append to session manifest ledger (JSONL)
    # ----------------------------
    if session_manifest_path:
        # Compute bundle_relpath relative to session_dir
        try:
            bundle_relpath = str(bundle_dir.relative_to(session_dir)).replace("\\", "/")
        except ValueError:
            # Bundle not under session_dir; use relative to out_root
            bundle_relpath = str(bundle_dir.relative_to(out_root)).replace("\\", "/")

        warnings_list = analysis_obj.get("results", {}).get("warnings", [])
        ledger_line = {
            "ts_utc": utc_now_iso(),
            "session_id": args.session_id,
            "bundle_id": bundle_id,
            "bundle_sha256": bundle_sha,
            "relpath_bundle_dir": bundle_relpath,
            "specimen_id": args.specimen_id,
            "mode": "bending_stiffness",
            "units": {"length": args.units_length, "force": args.units_force},
            "ok": len(warnings_list) == 0,
            "warnings": warnings_list,
            "files": {
                "count": len(files),
                "kinds": _kinds_count(files)
            }
        }
        append_jsonl(session_manifest_path, strip_nulls(ledger_line))

    print(f"Wrote bundle: {bundle_dir}")
    print(f"bundle_sha256: {bundle_sha}")


if __name__ == "__main__":
    main()
