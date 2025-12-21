"""
Saw Lab Enhancement Tool: Per-Blade RPM Limits + Learned Overrides

This offline CLI tool:
1. Applies manufacturer RPM limits to blade library (from CSV/JSON specs)
2. Generates learned feed/speed overrides from historical run artifacts

Usage:
    cd services/api
    python -m scripts.saw_lab_enhance_blades_and_overrides \
        --blades-in ./data/saw_blades.json \
        --blades-out ./data/saw_blades.enriched.json \
        --rpm-specs-csv ./data/rpm_specs.csv

With learned overrides:
    python -m scripts.saw_lab_enhance_blades_and_overrides \
        --blades-in ./data/saw_blades.json \
        --blades-out ./data/saw_blades.enriched.json \
        --rpm-specs-csv ./data/rpm_specs.csv \
        --artifacts-dir ./run_artifacts \
        --overrides-out ./data/learned_overrides.json \
        --min-samples 6
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# -----------------------------
# IO helpers
# -----------------------------

def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _num(x: Any) -> Optional[float]:
    if x is None:
        return None
    s = str(x).strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


# -----------------------------
# Enhancement 1: RPM Limits
# -----------------------------

@dataclass(frozen=True)
class RpmSpec:
    blade_id: str
    rpm_max: Optional[float] = None
    rpm_min: Optional[float] = None
    rpm_recommended: Optional[float] = None
    source: str = ""  # vendor sheet link/code/notes


def load_rpm_specs_from_csv(path: Path) -> Dict[str, RpmSpec]:
    """
    CSV columns expected (minimal):
      blade_id,rpm_max
    Optional:
      rpm_min,rpm_recommended,source
    """
    specs: Dict[str, RpmSpec] = {}
    for row in read_csv_rows(path):
        blade_id = (row.get("blade_id") or "").strip()
        if not blade_id:
            continue
        specs[blade_id] = RpmSpec(
            blade_id=blade_id,
            rpm_max=_num(row.get("rpm_max")),
            rpm_min=_num(row.get("rpm_min")),
            rpm_recommended=_num(row.get("rpm_recommended")),
            source=(row.get("source") or "").strip(),
        )
    return specs


def load_rpm_specs_from_json(path: Path) -> Dict[str, RpmSpec]:
    """
    JSON format:
    {
      "blade_id_1": {"rpm_max": 24000, "rpm_min": 8000, "rpm_recommended": 18000, "source": "..."},
      ...
    }
    """
    raw = load_json(path)
    specs: Dict[str, RpmSpec] = {}
    if not isinstance(raw, dict):
        raise ValueError("RPM specs JSON must be an object keyed by blade_id.")
    for blade_id, d in raw.items():
        if not isinstance(d, dict):
            continue
        specs[str(blade_id)] = RpmSpec(
            blade_id=str(blade_id),
            rpm_max=_num(d.get("rpm_max")),
            rpm_min=_num(d.get("rpm_min")),
            rpm_recommended=_num(d.get("rpm_recommended")),
            source=str(d.get("source") or ""),
        )
    return specs


def apply_rpm_specs_to_blade_library(
    blades: List[Dict[str, Any]],
    specs: Dict[str, RpmSpec],
    *,
    id_field: str = "blade_id",
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Updates each blade entry with manufacturer RPM values.
    Writes into blade["manufacturer_limits"]["rpm_*"] fields.

    Returns (updated_blades, report).
    """
    updated = []
    touched = 0
    missing_specs = []
    malformed = 0

    for b in blades:
        if not isinstance(b, dict):
            malformed += 1
            continue
        blade_id = str(b.get(id_field) or b.get("id") or "").strip()
        if not blade_id:
            malformed += 1
            updated.append(b)
            continue

        spec = specs.get(blade_id)
        if not spec:
            missing_specs.append(blade_id)
            updated.append(b)
            continue

        limits = dict(b.get("manufacturer_limits") or {})
        # only set fields that are provided; preserve existing values otherwise
        if spec.rpm_max is not None:
            limits["rpm_max"] = spec.rpm_max
        if spec.rpm_min is not None:
            limits["rpm_min"] = spec.rpm_min
        if spec.rpm_recommended is not None:
            limits["rpm_recommended"] = spec.rpm_recommended
        if spec.source:
            limits["source"] = spec.source

        b2 = dict(b)
        b2["manufacturer_limits"] = limits
        updated.append(b2)
        touched += 1

    report = {
        "rpm_specs_applied": touched,
        "blades_missing_specs": sorted(set(missing_specs)),
        "malformed_blades": malformed,
        "total_blades": len(blades),
    }
    return updated, report


# -----------------------------
# Enhancement 2: Learned overrides
# -----------------------------

@dataclass(frozen=True)
class OverrideKey:
    material_id: str
    blade_id: str
    machine_id: str


@dataclass(frozen=True)
class FeedSpeedOverride:
    """
    Multipliers applied to baseline presets.
    Example: feed_mult=0.92 means reduce feed by 8%.
    """
    feed_mult: float
    rpm_mult: float
    reason: str
    sample_count: int


def _safe_mult(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _extract_training_samples_from_artifacts(artifact_dir: Path) -> List[Dict[str, Any]]:
    """
    Reads run artifacts and extracts any "signals" you choose to log.
    We keep this flexible:
      - tool_id/material_id/machine_id
      - baseline rpm/feed (if present)
      - outcome status
      - optional metrics: burn, chatter, deflection, cut_time, etc.

    This script does NOT assume you already have all metrics.
    It will learn only from what's present.
    """
    samples: List[Dict[str, Any]] = []
    if not artifact_dir.exists():
        return samples

    for p in artifact_dir.glob("**/*.json"):
        try:
            obj = load_json(p)
        except Exception:
            continue
        if not isinstance(obj, dict):
            continue

        status = str(obj.get("status") or "").upper()
        index_meta = obj.get("index_meta") or {}
        payload = obj.get("payload") or {}

        tool_id = str(index_meta.get("tool_id") or "")
        mat_id = str(index_meta.get("material_id") or "")
        mach_id = str(index_meta.get("machine_id") or "")

        # interpret tool_id as blade_id for saw lab context; adjust if you store differently
        blade_id = tool_id

        # attempt to find baseline values if recorded
        baseline = payload.get("baseline") or {}
        rpm = _num(baseline.get("rpm") or baseline.get("spindle_rpm"))
        feed = _num(baseline.get("feed") or baseline.get("feed_ipm"))

        # optional signals (any numeric fields you've started logging)
        metrics = payload.get("metrics") or {}
        burn = _num(metrics.get("burn"))
        chatter = _num(metrics.get("chatter"))
        deflection = _num(metrics.get("deflection"))
        cut_time = _num(metrics.get("cut_time_sec") or metrics.get("cut_time"))

        samples.append({
            "status": status,
            "material_id": mat_id,
            "blade_id": blade_id,
            "machine_id": mach_id,
            "rpm": rpm,
            "feed": feed,
            "burn": burn,
            "chatter": chatter,
            "deflection": deflection,
            "cut_time": cut_time,
        })

    return samples


def _group_key(s: Dict[str, Any]) -> Optional[OverrideKey]:
    mat = (s.get("material_id") or "").strip()
    blade = (s.get("blade_id") or "").strip()
    mach = (s.get("machine_id") or "").strip()
    if not (mat and blade and mach):
        return None
    return OverrideKey(material_id=mat, blade_id=blade, machine_id=mach)


def learn_overrides_from_samples(
    samples: List[Dict[str, Any]],
    *,
    min_samples: int = 6,
) -> Dict[str, Any]:
    """
    Lightweight "learning" that works without an ML stack:
    - If many runs end BLOCKED/ERROR and burn/chatter high, reduce feed and/or rpm.
    - If mostly OK and no negative signals, keep multipliers ~1.0.

    Output is a JSON-serializable dict mapping key->override.
    """
    # Aggregate by (material, blade, machine)
    buckets: Dict[OverrideKey, List[Dict[str, Any]]] = {}
    for s in samples:
        k = _group_key(s)
        if not k:
            continue
        buckets.setdefault(k, []).append(s)

    out: Dict[str, Any] = {}
    for k, rows in buckets.items():
        if len(rows) < min_samples:
            continue

        ok = sum(1 for r in rows if r["status"] == "OK")
        bad = sum(1 for r in rows if r["status"] in ("ERROR", "BLOCKED"))
        bad_rate = bad / max(1, len(rows))

        # crude signal averages (only among rows where signal exists)
        def avg(field: str) -> Optional[float]:
            vals = [r[field] for r in rows if r.get(field) is not None]
            return sum(vals) / len(vals) if vals else None

        burn = avg("burn")
        chatter = avg("chatter")
        deflection = avg("deflection")

        # Base multipliers
        feed_mult = 1.0
        rpm_mult = 1.0
        reasons: List[str] = []

        # Penalize based on failure rate
        if bad_rate >= 0.30:
            feed_mult *= 0.92
            reasons.append(f"bad_rate={bad_rate:.2f}")
        if bad_rate >= 0.50:
            feed_mult *= 0.90
            rpm_mult *= 0.95
            reasons.append("high_failure_rate")

        # Penalize based on signals (if present)
        if burn is not None and burn >= 0.6:
            rpm_mult *= 0.95
            reasons.append(f"burn_avg={burn:.2f}")
        if chatter is not None and chatter >= 0.6:
            feed_mult *= 0.93
            reasons.append(f"chatter_avg={chatter:.2f}")
        if deflection is not None and deflection >= 0.6:
            feed_mult *= 0.95
            reasons.append(f"deflection_avg={deflection:.2f}")

        # Keep in safe bounds: we don't want wild adjustments
        feed_mult = _safe_mult(feed_mult, 0.80, 1.10)
        rpm_mult = _safe_mult(rpm_mult, 0.85, 1.10)

        if not reasons:
            # No change; still allow emitting if you want; default is skip
            continue

        key_str = f"{k.material_id}::{k.blade_id}::{k.machine_id}"
        out[key_str] = {
            "feed_mult": feed_mult,
            "rpm_mult": rpm_mult,
            "reason": ",".join(reasons),
            "sample_count": len(rows),
            "ok": ok,
            "bad": bad,
        }

    return out


# -----------------------------
# Main: combined run
# -----------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Saw Lab enhancement tool: apply per-blade manufacturer RPM limits + generate learned feed/speed overrides."
    )

    ap.add_argument("--blades-in", required=True, help="Input blade library JSON (list of blades).")
    ap.add_argument("--blades-out", required=True, help="Output blade library JSON (enriched).")

    ap.add_argument("--rpm-specs-csv", default="", help="CSV of manufacturer RPM specs keyed by blade_id.")
    ap.add_argument("--rpm-specs-json", default="", help="JSON of manufacturer RPM specs keyed by blade_id.")

    ap.add_argument("--artifacts-dir", default="", help="Run artifacts directory for training learned overrides.")
    ap.add_argument("--overrides-out", default="", help="Write learned overrides JSON to this path.")
    ap.add_argument("--min-samples", type=int, default=6, help="Minimum samples per key to emit an override.")

    args = ap.parse_args()

    blades_in = Path(args.blades_in)
    blades_out = Path(args.blades_out)

    blades = load_json(blades_in)
    if not isinstance(blades, list):
        raise SystemExit("blades-in JSON must be a list of blade dicts.")

    # Enhancement 1: RPM specs
    specs: Dict[str, RpmSpec] = {}
    if args.rpm_specs_csv:
        specs.update(load_rpm_specs_from_csv(Path(args.rpm_specs_csv)))
    if args.rpm_specs_json:
        specs.update(load_rpm_specs_from_json(Path(args.rpm_specs_json)))

    blades2, rpm_report = apply_rpm_specs_to_blade_library(blades, specs, id_field="blade_id")
    save_json(blades_out, blades2)

    # Enhancement 2: Learned overrides
    overrides_report: Dict[str, Any] = {"generated": 0, "note": "skipped"}
    if args.artifacts_dir and args.overrides_out:
        samples = _extract_training_samples_from_artifacts(Path(args.artifacts_dir))
        overrides = learn_overrides_from_samples(samples, min_samples=args.min_samples)
        save_json(Path(args.overrides_out), overrides)
        overrides_report = {
            "generated": len(overrides),
            "samples_total": len(samples),
            "min_samples": args.min_samples,
        }

    # Print a concise report
    print("Saw Lab Enhancements Report")
    print("--------------------------")
    print(f"Blades in:  {blades_in}")
    print(f"Blades out: {blades_out}")
    print(f"RPM specs applied: {rpm_report['rpm_specs_applied']}/{rpm_report['total_blades']}")
    if rpm_report["blades_missing_specs"]:
        print(f"Missing RPM specs for {len(rpm_report['blades_missing_specs'])} blades (first 10): "
              f"{rpm_report['blades_missing_specs'][:10]}")

    if args.artifacts_dir and args.overrides_out:
        print(f"Artifacts dir: {args.artifacts_dir}")
        print(f"Overrides out: {args.overrides_out}")
        print(f"Overrides generated: {overrides_report['generated']} (from {overrides_report.get('samples_total', 0)} samples)")
    else:
        print("Learned overrides: skipped (provide --artifacts-dir and --overrides-out)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
