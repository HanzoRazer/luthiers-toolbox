#!/usr/bin/env python3
"""viewer_pack_diff.py — Compare two viewer packs for measurement regression.

Enables the engineering workflow:
    measure → remove wood → measure again → quantify change

This script computes RAW DELTAS only — no interpretation, no "better/worse" language.

Alignment requirements:
- Same grid point IDs (fails if point sets differ)
- Same freq_hz bins (fails if bin count/values differ beyond tolerance)

Outputs:
- diff/delta_summary.json — per-point and global summary statistics
- diff/delta_curves.csv — per-frequency deltas for all metrics
- diff/plots/*.png — overlay plots (if matplotlib available)

Usage:
    python scripts/viewer_pack_diff.py baseline.zip after.zip --out diff_out/
    python scripts/viewer_pack_diff.py baseline.zip after.zip --out diff_out/ --plots

Exit codes:
    0 = Diff computed successfully
    1 = Alignment failure or processing error
    2 = Usage/argument error
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tap_tone.viewer_pack.manifest import (
    load_viewer_pack,
    find_files_by_kind,
    read_file_from_pack,
    get_points,
    ViewerPackHandle,
)

# Plotting is optional
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


FREQ_TOLERANCE_HZ = 0.1  # Max allowed difference in frequency bins


@dataclass(frozen=True)
class SpectrumData:
    """Parsed spectrum data from a single point."""
    point_id: str
    freq_hz: np.ndarray
    H_mag: np.ndarray
    coherence: np.ndarray
    phase_deg: np.ndarray


@dataclass(frozen=True)
class WSICurveData:
    """Parsed WSI curve data from session level."""
    freq_hz: np.ndarray
    wsi: np.ndarray
    coh_mean: np.ndarray
    admissible: np.ndarray  # boolean


@dataclass
class DiffResult:
    """Container for diff computation results."""
    success: bool
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    # Alignment info
    shared_points: List[str] = field(default_factory=list)
    baseline_only_points: List[str] = field(default_factory=list)
    modified_only_points: List[str] = field(default_factory=list)
    freq_hz: Optional[np.ndarray] = None

    # Per-point deltas: point_id -> {metric: array}
    point_deltas: Dict[str, Dict[str, np.ndarray]] = field(default_factory=dict)

    # Session-level WSI deltas
    wsi_delta: Optional[np.ndarray] = None
    coh_mean_delta: Optional[np.ndarray] = None

    # Summary statistics (measurement-only, no interpretation)
    summary: Dict[str, float] = field(default_factory=dict)


def parse_spectrum_csv(data: bytes, point_id: str) -> SpectrumData:
    """Parse spectrum.csv into structured data."""
    text = data.decode("utf-8")
    reader = csv.DictReader(StringIO(text))

    rows = list(reader)
    n = len(rows)

    freq_hz = np.zeros(n, dtype=np.float32)
    H_mag = np.zeros(n, dtype=np.float32)
    coherence = np.zeros(n, dtype=np.float32)
    phase_deg = np.zeros(n, dtype=np.float32)

    for i, row in enumerate(rows):
        freq_hz[i] = float(row.get("freq_hz", 0))
        H_mag[i] = _safe_float(row.get("H_mag", "nan"))
        coherence[i] = _safe_float(row.get("coherence", "nan"))
        phase_deg[i] = _safe_float(row.get("phase_deg", "nan"))

    return SpectrumData(
        point_id=point_id,
        freq_hz=freq_hz,
        H_mag=H_mag,
        coherence=coherence,
        phase_deg=phase_deg,
    )


def parse_wsi_curve_csv(data: bytes) -> WSICurveData:
    """Parse wsi_curve.csv into structured data."""
    text = data.decode("utf-8")
    reader = csv.DictReader(StringIO(text))

    rows = list(reader)
    n = len(rows)

    freq_hz = np.zeros(n, dtype=np.float32)
    wsi = np.zeros(n, dtype=np.float32)
    coh_mean = np.zeros(n, dtype=np.float32)
    admissible = np.zeros(n, dtype=bool)

    for i, row in enumerate(rows):
        freq_hz[i] = float(row.get("freq_hz", 0))
        wsi[i] = _safe_float(row.get("wsi", "nan"))
        coh_mean[i] = _safe_float(row.get("coh_mean", "nan"))
        adm_str = row.get("admissible", "false").lower()
        admissible[i] = adm_str in ("true", "1", "yes")

    return WSICurveData(freq_hz=freq_hz, wsi=wsi, coh_mean=coh_mean, admissible=admissible)


def _safe_float(s: str) -> float:
    """Parse float, returning NaN for invalid values."""
    try:
        return float(s)
    except (ValueError, TypeError):
        return np.nan


def load_spectra(handle: ViewerPackHandle) -> Dict[str, SpectrumData]:
    """Load all spectrum CSVs from a viewer pack."""
    spectra = {}
    files = find_files_by_kind(handle.manifest, "spectrum_csv")

    for f in files:
        # Extract point ID from path: spectra/points/{POINT_ID}/spectrum.csv
        parts = f.relpath.split("/")
        if len(parts) >= 3 and parts[0] == "spectra" and parts[1] == "points":
            point_id = parts[2]
            data = read_file_from_pack(handle, f.relpath)
            spectra[point_id] = parse_spectrum_csv(data, point_id)

    return spectra


def load_wsi_curve(handle: ViewerPackHandle) -> Optional[WSICurveData]:
    """Load WSI curve from viewer pack if present."""
    files = find_files_by_kind(handle.manifest, "wsi_curve")
    if not files:
        return None

    data = read_file_from_pack(handle, files[0].relpath)
    return parse_wsi_curve_csv(data)


def check_freq_alignment(
    freq_a: np.ndarray,
    freq_b: np.ndarray,
    tolerance: float = FREQ_TOLERANCE_HZ,
) -> Tuple[bool, str]:
    """Check if two frequency arrays are aligned."""
    if len(freq_a) != len(freq_b):
        return False, f"Bin count mismatch: {len(freq_a)} vs {len(freq_b)}"

    max_diff = np.max(np.abs(freq_a - freq_b))
    if max_diff > tolerance:
        return False, f"Frequency bin mismatch: max delta = {max_diff:.3f} Hz"

    return True, ""


def compute_diff(
    baseline_path: Path,
    modified_path: Path,
) -> DiffResult:
    """Compute measurement diff between two viewer packs.

    Args:
        baseline_path: Path to baseline viewer pack ZIP
        modified_path: Path to modified (after intervention) viewer pack ZIP

    Returns:
        DiffResult with deltas and summary statistics
    """
    result = DiffResult(success=True)

    # Load both packs
    try:
        baseline = load_viewer_pack(baseline_path)
        modified = load_viewer_pack(modified_path)
    except Exception as e:
        return DiffResult(success=False, error=f"Failed to load packs: {e}")

    try:
        # Get point sets
        baseline_points = set(get_points(baseline.manifest))
        modified_points = set(get_points(modified.manifest))

        result.shared_points = sorted(baseline_points & modified_points)
        result.baseline_only_points = sorted(baseline_points - modified_points)
        result.modified_only_points = sorted(modified_points - baseline_points)

        if not result.shared_points:
            return DiffResult(success=False, error="No shared points between packs")

        if result.baseline_only_points:
            result.warnings.append(
                f"Points only in baseline: {result.baseline_only_points}"
            )
        if result.modified_only_points:
            result.warnings.append(
                f"Points only in modified: {result.modified_only_points}"
            )

        # Load spectra
        baseline_spectra = load_spectra(baseline)
        modified_spectra = load_spectra(modified)

        # Verify frequency alignment using first shared point
        first_point = result.shared_points[0]
        if first_point not in baseline_spectra or first_point not in modified_spectra:
            return DiffResult(
                success=False,
                error=f"Missing spectrum for shared point {first_point}",
            )

        freq_baseline = baseline_spectra[first_point].freq_hz
        freq_modified = modified_spectra[first_point].freq_hz

        aligned, msg = check_freq_alignment(freq_baseline, freq_modified)
        if not aligned:
            return DiffResult(success=False, error=f"Frequency alignment failed: {msg}")

        result.freq_hz = freq_baseline.copy()

        # Compute per-point deltas
        all_H_mag_deltas = []
        all_coh_deltas = []

        for point_id in result.shared_points:
            if point_id not in baseline_spectra or point_id not in modified_spectra:
                result.warnings.append(f"Missing spectrum data for point {point_id}")
                continue

            sp_b = baseline_spectra[point_id]
            sp_m = modified_spectra[point_id]

            # Verify per-point frequency alignment
            aligned, _ = check_freq_alignment(sp_b.freq_hz, sp_m.freq_hz)
            if not aligned:
                result.warnings.append(f"Frequency mismatch for point {point_id}")
                continue

            # Compute deltas (modified - baseline)
            delta_H_mag = sp_m.H_mag - sp_b.H_mag
            delta_coh = sp_m.coherence - sp_b.coherence
            delta_phase = sp_m.phase_deg - sp_b.phase_deg

            result.point_deltas[point_id] = {
                "delta_H_mag": delta_H_mag,
                "delta_coherence": delta_coh,
                "delta_phase_deg": delta_phase,
            }

            all_H_mag_deltas.append(delta_H_mag)
            all_coh_deltas.append(delta_coh)

        # WSI curve diff (if both have it)
        wsi_baseline = load_wsi_curve(baseline)
        wsi_modified = load_wsi_curve(modified)

        if wsi_baseline is not None and wsi_modified is not None:
            aligned, msg = check_freq_alignment(wsi_baseline.freq_hz, wsi_modified.freq_hz)
            if aligned:
                result.wsi_delta = wsi_modified.wsi - wsi_baseline.wsi
                result.coh_mean_delta = wsi_modified.coh_mean - wsi_baseline.coh_mean
            else:
                result.warnings.append(f"WSI frequency alignment failed: {msg}")

        # Compute summary statistics (measurement-only, no interpretation)
        if all_H_mag_deltas:
            stacked_H = np.vstack(all_H_mag_deltas)
            result.summary["mean_delta_H_mag"] = float(np.nanmean(stacked_H))
            result.summary["std_delta_H_mag"] = float(np.nanstd(stacked_H))
            result.summary["max_abs_delta_H_mag"] = float(np.nanmax(np.abs(stacked_H)))
            result.summary["rms_delta_H_mag"] = float(
                np.sqrt(np.nanmean(stacked_H ** 2))
            )

        if all_coh_deltas:
            stacked_coh = np.vstack(all_coh_deltas)
            result.summary["mean_delta_coherence"] = float(np.nanmean(stacked_coh))

        if result.wsi_delta is not None:
            result.summary["mean_delta_wsi"] = float(np.nanmean(result.wsi_delta))
            result.summary["max_abs_delta_wsi"] = float(
                np.nanmax(np.abs(result.wsi_delta))
            )

        result.summary["shared_point_count"] = len(result.shared_points)
        result.summary["freq_bin_count"] = len(result.freq_hz)

    finally:
        baseline.close()
        modified.close()

    return result


def write_outputs(result: DiffResult, out_dir: Path, generate_plots: bool) -> None:
    """Write diff outputs to directory."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. delta_summary.json
    summary_data = {
        "alignment": {
            "shared_points": result.shared_points,
            "baseline_only_points": result.baseline_only_points,
            "modified_only_points": result.modified_only_points,
            "freq_bin_count": len(result.freq_hz) if result.freq_hz is not None else 0,
        },
        "summary_statistics": result.summary,
        "warnings": result.warnings,
    }

    with open(out_dir / "delta_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, sort_keys=True)

    # 2. delta_curves.csv — global mean deltas per frequency
    if result.freq_hz is not None and result.point_deltas:
        n_freq = len(result.freq_hz)

        # Stack all point deltas and compute mean per frequency
        all_H = np.full((len(result.point_deltas), n_freq), np.nan)
        all_coh = np.full((len(result.point_deltas), n_freq), np.nan)

        for i, (pid, deltas) in enumerate(result.point_deltas.items()):
            all_H[i, :] = deltas["delta_H_mag"]
            all_coh[i, :] = deltas["delta_coherence"]

        mean_delta_H = np.nanmean(all_H, axis=0)
        mean_delta_coh = np.nanmean(all_coh, axis=0)

        with open(out_dir / "delta_curves.csv", "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            header = ["freq_hz", "mean_delta_H_mag", "mean_delta_coherence"]
            if result.wsi_delta is not None:
                header.append("delta_wsi")
            writer.writerow(header)

            for i in range(n_freq):
                row = [
                    f"{result.freq_hz[i]:.6f}",
                    f"{mean_delta_H[i]:.8f}",
                    f"{mean_delta_coh[i]:.8f}",
                ]
                if result.wsi_delta is not None:
                    row.append(f"{result.wsi_delta[i]:.8f}")
                writer.writerow(row)

    # 3. Plots (if requested and matplotlib available)
    if generate_plots and HAS_MATPLOTLIB and result.freq_hz is not None:
        plots_dir = out_dir / "plots"
        plots_dir.mkdir(exist_ok=True)

        # Mean delta H_mag plot
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.axhline(0, color="gray", linestyle="--", linewidth=0.5)
        ax.plot(result.freq_hz, mean_delta_H, "b-", linewidth=0.8)
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Δ|H| (modified − baseline)")
        ax.set_title("Mean Transfer Function Magnitude Delta")
        ax.set_xlim(result.freq_hz[0], result.freq_hz[-1])
        fig.tight_layout()
        fig.savefig(plots_dir / "delta_H_mag.png", dpi=150)
        plt.close(fig)

        # WSI delta plot (if available)
        if result.wsi_delta is not None:
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.axhline(0, color="gray", linestyle="--", linewidth=0.5)
            ax.plot(result.freq_hz, result.wsi_delta, "r-", linewidth=0.8)
            ax.set_xlabel("Frequency (Hz)")
            ax.set_ylabel("ΔWSI (modified − baseline)")
            ax.set_title("Wolf Stress Index Delta")
            ax.set_xlim(result.freq_hz[0], result.freq_hz[-1])
            fig.tight_layout()
            fig.savefig(plots_dir / "delta_wsi.png", dpi=150)
            plt.close(fig)

    elif generate_plots and not HAS_MATPLOTLIB:
        print("Warning: matplotlib not available; skipping plots", file=sys.stderr)


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Compare two viewer packs for measurement regression.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Outputs (measurement-only, no interpretation):
    delta_summary.json   — alignment info + summary statistics
    delta_curves.csv     — per-frequency mean deltas
    plots/*.png          — overlay visualizations (with --plots)

Examples:
    python scripts/viewer_pack_diff.py baseline.zip after.zip --out diff_out/
    python scripts/viewer_pack_diff.py pre.zip post.zip --out results/ --plots
        """,
    )
    parser.add_argument("baseline", type=Path, help="Baseline viewer pack ZIP")
    parser.add_argument("modified", type=Path, help="Modified viewer pack ZIP")
    parser.add_argument(
        "--out", "-o",
        type=Path,
        default=Path("diff_out"),
        help="Output directory (default: diff_out/)",
    )
    parser.add_argument(
        "--plots",
        action="store_true",
        help="Generate overlay plots (requires matplotlib)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result summary as JSON to stdout",
    )

    args = parser.parse_args(argv)

    # Compute diff
    result = compute_diff(args.baseline, args.modified)

    if not result.success:
        print(f"Error: {result.error}", file=sys.stderr)
        return 1

    # Write outputs
    write_outputs(result, args.out, args.plots)

    # Report
    if args.json:
        output = {
            "success": result.success,
            "shared_points": len(result.shared_points),
            "summary": result.summary,
            "warnings": result.warnings,
            "output_dir": str(args.out),
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"\nViewer Pack Diff Complete")
        print(f"{'='*40}")
        print(f"Baseline: {args.baseline.name}")
        print(f"Modified: {args.modified.name}")
        print(f"Shared points: {len(result.shared_points)}")
        print(f"Frequency bins: {len(result.freq_hz) if result.freq_hz is not None else 0}")
        print(f"\nOutputs written to: {args.out}/")

        if result.warnings:
            print(f"\nWarnings:")
            for w in result.warnings:
                print(f"  ⚠ {w}")

        if result.summary:
            print(f"\nSummary Statistics:")
            for k, v in sorted(result.summary.items()):
                if isinstance(v, float):
                    print(f"  {k}: {v:.6f}")
                else:
                    print(f"  {k}: {v}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
