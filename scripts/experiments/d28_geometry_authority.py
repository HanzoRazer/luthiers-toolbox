#!/usr/bin/env python3
"""
D28 experiment-only geometry/authority utilities (shared by Runs 004K–004O)
===========================================================================

Small, dependency-light helpers factored out of the per-run scripts so the
corrected geometry chain (004K source-datum reconciliation → 004O curvature)
does not copy-paste provenance/arc-length/datum semantics into every file.

Scope rules (do NOT relax):
  * EXPERIMENT-ONLY. Never import this from production packages. It lives under
    scripts/experiments/ on purpose and reads only committed experiment inputs.
  * No PDF access, no network, no production/spec/authority writes.
  * Deterministic: pure numpy/csv/json; no randomness, no wall-clock in outputs.

The SourceDatum dataclass is the canonical representation of a reconciled source
dimension (004K). It carries the corrected meaning, provenance, evidence class,
whether the quantity participates in downstream geometry, and the prior
interpretation it supersedes (if any).
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
RESULTS_DIR = os.path.join(_REPO_ROOT, "docs", "experiments", "results")
ARNOLD_OUTLINE_CSV = os.path.join(RESULTS_DIR, "D28_65260_ARNOLD_OUTLINE.csv")


# =============================================================================
# Provenance primitives
# =============================================================================

def git_sha() -> str:
    """Current repository HEAD, or 'UNKNOWN' if git is unavailable."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=_REPO_ROOT).decode().strip()
    except Exception:
        return "UNKNOWN"


def sha256(path: str) -> str:
    """SHA-256 of a file, streamed in 64 KiB chunks (stable, large-file safe)."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def repo_root() -> str:
    return _REPO_ROOT


def results_dir() -> str:
    return RESULTS_DIR


# =============================================================================
# Deterministic writers
# =============================================================================

def wr_csv(path: str, fields: Sequence[str], rows: Sequence[Dict]) -> None:
    """Write a CSV deterministically (LF line terminator; explicit field order)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(fields), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def write_provenance_json(path: str, record: Dict) -> None:
    """Write a provenance record as pretty JSON (stable key order from caller)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(record, fh, indent=2)


# =============================================================================
# Source-datum authority model (004K)
# =============================================================================

@dataclass(frozen=True)
class SourceDatum:
    """A reconciled #65260 source dimension.

    name            machine-stable identifier (e.g. 'internal_block_to_block_length')
    value_in        numeric value in inches (None when deliberately unresolved)
    unit            physical unit string ('in')
    meaning         corrected human interpretation
    classification  evidence class (SOURCE_MEASURED / SOURCE_CAD_CONFIRMED /
                    SOURCE_PLAN_CORROBORATED / DRAWING_DERIVED / UNRESOLVED ...)
    source          where the value/interpretation comes from
    participates_in_geometry  does the corrected chain consume this quantity?
    prior_interpretation      the superseded meaning, if this corrects one
    axis            the geometric axis it describes (longitudinal / plan_radius /
                    side_depth / developed_arc ...), used to assert independence
    notes           free-form caveats (endpoint ambiguity, etc.)
    """
    name: str
    value_in: Optional[float]
    unit: str
    meaning: str
    classification: str
    source: str
    participates_in_geometry: bool
    prior_interpretation: Optional[str] = None
    axis: str = "unspecified"
    notes: str = ""

    def as_record(self) -> Dict:
        return asdict(self)


# =============================================================================
# Arnold / JD plan outline (XY authority) — one-side half-width profile
# =============================================================================

def load_arnold_outline(path: str = ARNOLD_OUTLINE_CSV) -> Dict:
    """Load the committed Arnold/JD one-side plan outline.

    Columns: y_from_neck_in, half_width_in. Returns y (longitudinal, strictly
    ascending from the neck endpoint y=0) and x (= half width from centerline).
    Fail-closed on a malformed outline. This is the SAME extracted outline used by
    Runs 003/004C/004D/004E — it is NOT retraced here (Run 004L input authority).
    """
    ys: List[float] = []
    hw: List[float] = []
    with open(path) as fh:
        next(fh)  # header
        for line in fh:
            if not line.strip():
                continue
            a, b = line.strip().split(",")
            ys.append(float(a))
            hw.append(float(b))
    y = np.asarray(ys, float)
    x = np.asarray(hw, float)
    if y.size < 10:
        raise ValueError("STOP: outline too short")
    if y[0] != 0.0:
        raise ValueError("STOP: outline does not start at the neck (y=0)")
    if not np.all(np.diff(y) > 0):
        raise ValueError("STOP: outline y not strictly ascending")
    return {"y": y, "x": x, "L": float(y[-1])}


def compute_polyline_arclength(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Cumulative polyline (Euclidean) arc length along the (y, x) contour.

    ds_i = sqrt((x_{i+1}-x_i)^2 + (y_{i+1}-y_i)^2); S_j = sum_{i<j} ds_i.
    For the one-side plan outline this is the developed one-side rim distance.
    No smoothing is applied: the raw polyline length is the working quantity
    (004L); any smoothed value is a diagnostic only.
    """
    y = np.asarray(y, float)
    x = np.asarray(x, float)
    ds = np.hypot(np.diff(x), np.diff(y))
    return np.concatenate([[0.0], np.cumsum(ds)])


def boxcar_half_width(x: np.ndarray, frac: float = 0.02) -> np.ndarray:
    """Replicate the legacy 003/004C boxcar smoothing (mode='same').

    Provided ONLY so Run 004L can reproduce and explicitly flag the inflated
    smoothed half-perimeter (~26.73 in) as an endpoint artifact — never as the
    working developed-rim authority.
    """
    k = max(3, int(frac * len(x)) | 1)
    return np.convolve(x, np.ones(k) / k, mode="same")


def sample_curve_by_arclength(s: np.ndarray, values: np.ndarray,
                              targets: Sequence[float]) -> np.ndarray:
    """Linear interpolation of `values` at the arc-length `targets`.

    `s` must be non-decreasing; targets are clipped to [s[0], s[-1]] so endpoint
    queries never extrapolate. Used to place landmarks on the plan outline.
    """
    s = np.asarray(s, float)
    values = np.asarray(values, float)
    t = np.clip(np.asarray(targets, float), s[0], s[-1])
    return np.interp(t, s, values)


def boundary_residuals(z_surface: np.ndarray, z_boundary: np.ndarray) -> Dict:
    """REAL boundary residuals e_i = z_surface_i - z_boundary_i (never a forced 0).

    Returns max |e|, RMSE, sample count. Caller is responsible for evaluating the
    tested surface at the ACTUAL boundary coordinates (004N replaces the 004G
    `* 0.0` placeholder with this).
    """
    zs = np.asarray(z_surface, float)
    zb = np.asarray(z_boundary, float)
    if zs.shape != zb.shape:
        raise ValueError("boundary residual arrays must have equal shape")
    e = zs - zb
    n = int(e.size)
    return {
        "residuals": e,
        "max_abs": float(np.max(np.abs(e))) if n else float("nan"),
        "rmse": float(np.sqrt(np.mean(e ** 2))) if n else float("nan"),
        "n_samples": n,
    }


# =============================================================================
# Monotone landmark registration (shared by 004M)
# =============================================================================

def validate_monotone_pairs(a: Sequence[float], b: Sequence[float]) -> None:
    """Fail-closed check that paired anchors are strictly increasing in both axes."""
    a = list(a)
    b = list(b)
    if len(a) != len(b) or len(a) < 2:
        raise ValueError("need >=2 paired anchors")
    if any(y <= x for x, y in zip(a, a[1:])):
        raise ValueError("anchor domain not strictly increasing")
    if any(y <= x for x, y in zip(b, b[1:])):
        raise ValueError("anchor range not strictly increasing")
