"""tap_tone gold-run -- One-command Gold Standard Run.

Automates: capture N points -> export viewer pack -> validate -> ingest to ToolBox.

Auto-ingest is ON by default. Use --no-ingest to skip.

Usage:
    # Full workflow (capture + export + ingest):
    python -m tap_tone.cli.gold_run --specimen-id plate_A1 --device "USB Audio"

    # Skip ingest (export ZIP only):
    python -m tap_tone.cli.gold_run --specimen-id plate_A1 --device 1 --out-dir ./exports --no-ingest

Exit codes:
    0 = Success
    2 = Validation failed
    3 = Capture failed / retries exceeded
    4 = Device configuration error
    5 = Unexpected exception
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional, TYPE_CHECKING

# Defer hardware-dependent imports to runtime
if TYPE_CHECKING:
    from tap_tone.capture import list_devices, record_audio
    from tap_tone.analysis import analyze_tap
    from tap_tone.config import AnalysisConfig


@dataclass
class GoldRunConfig:
    """Configuration for a gold run."""

    specimen_id: str
    device: int | str | None
    out_dir: Path
    points: int = 3
    session_id: Optional[str] = None
    batch_label: Optional[str] = None
    tap_timeout_s: float = 8.0
    max_retries: int = 3
    min_peak_hz: float = 50.0
    max_peak_hz: float = 3000.0
    sample_rate: int = 48000
    capture_seconds: float = 2.5
    audio_required: bool = False
    export_zip: bool = True
    ingest: bool = True  # ON by default; opt-out via --no-ingest
    ingest_url: str = "http://localhost:8000"
    open_browser: bool = True  # ON by default; opt-out via --no-open
    open_viewer: bool = False  # OFF by default; opt-in via --open-viewer
    dry_run: bool = False
    json_output: bool = False

    # Auto-trigger options
    auto_trigger: bool = False
    warmup_s: float = 0.5
    peak_mult: float = 10.0
    rms_mult: float = 3.0
    debounce_frames: int = 2
    pre_ms: float = 50.0
    post_ms: float = 1500.0
    reject_clipping: bool = True
    min_impulse_ms: float = 2.0


@dataclass
class GoldRunResult:
    """Result of a gold run."""

    specimen_id: str
    points: List[str] = field(default_factory=list)
    session_dir: Optional[str] = None
    zip_path: Optional[str] = None
    validation_passed: bool = False
    validation_errors: int = 0
    validation_warnings: int = 0
    validation_report_path: Optional[str] = None
    ingest_attempted: bool = False
    ingest_ok: bool = False
    ingest_run_id: Optional[str] = None
    ingest_http_status: Optional[int] = None
    ingest_error: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": "tap_tone_gold_run_out_v1",
            "specimen_id": self.specimen_id,
            "points": self.points,
            "session_dir": self.session_dir,
            "zip_path": self.zip_path,
            "validation": {
                "passed": self.validation_passed,
                "errors": self.validation_errors,
                "warnings": self.validation_warnings,
                "report_path": self.validation_report_path,
            },
            "ingest": {
                "attempted": self.ingest_attempted,
                "ok": self.ingest_ok,
                "run_id": self.ingest_run_id,
                "http_status": self.ingest_http_status,
                "error": self.ingest_error,
            },
            "error": self.error_message,
        }


def _ts() -> str:
    """ISO timestamp for folder naming."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def pick_open_url(
    ingest_url: str,
    payload: Optional[dict],
    *,
    open_browser: bool,
    open_viewer: bool,
) -> Optional[str]:
    """Pick the URL to open after successful ingest.

    Pure function for clean testing.

    Args:
        ingest_url: Base ToolBox URL
        payload: Ingest response payload (may contain bundle_sha256)
        open_browser: Whether browser opening is enabled (--no-open disables)
        open_viewer: Whether to prefer Viewer deep-link (--open-viewer enables)

    Returns:
        URL to open, or None if browser opening is disabled.

    Rules:
        - If not open_browser: return None
        - If open_viewer AND bundle_sha256 exists: return Viewer URL
        - Otherwise: return Library URL
    """
    if not open_browser:
        return None

    base = ingest_url.rstrip("/")
    bundle_sha = payload.get("bundle_sha256") if isinstance(payload, dict) else None

    if open_viewer and bundle_sha:
        return f"{base}/tools/audio-analyzer?sha256={bundle_sha}"

    return f"{base}/tools/audio-analyzer/library"


def _resolve_device(device_spec: int | str | None) -> int | None:    return viewer_url, library_url


def _resolve_device(device_spec: int | str | None) -> int | None:
    """Resolve device spec to index."""
    from tap_tone.capture import list_devices  # Lazy import

    if device_spec is None:
        return None

    if isinstance(device_spec, int):
        return device_spec

    # Try parsing as int
    try:
        return int(device_spec)
    except ValueError:
        pass

    # Search by name (substring match)
    devices = list_devices()
    matches = [d for d in devices if device_spec.lower() in d["name"].lower()]
    if len(matches) == 1:
        return matches[0]["index"]
    elif len(matches) > 1:
        raise ValueError(
            f"Ambiguous device '{device_spec}': matches {[d['name'] for d in matches]}"
        )
    else:
        raise ValueError(f"No device matching '{device_spec}' found")


def _generate_point_labels(n: int) -> List[str]:
    """Generate point labels A1..AN."""
    return [f"A{i+1}" for i in range(n)]


def _capture_point_auto_trigger(
    device: int | None,
    cfg: GoldRunConfig,
    label: str,
    point_idx: int,
    total_points: int,
) -> tuple[Any, dict] | None:
    """Capture a single point using auto-trigger detection.

    Returns (audio_array, trigger_provenance) or None on failure.
    """
    from tap_tone.capture.auto_trigger import (
        AutoTriggerConfig,
        capture_one_impulse,
    )

    # Build auto-trigger config from gold-run config
    trigger_cfg = AutoTriggerConfig(
        warmup_s=cfg.warmup_s,
        tap_timeout_s=cfg.tap_timeout_s,
        max_retries=cfg.max_retries,
        peak_mult=cfg.peak_mult,
        rms_mult=cfg.rms_mult,
        debounce_frames=cfg.debounce_frames,
        pre_ms=cfg.pre_ms,
        post_ms=cfg.post_ms,
        reject_clipping=cfg.reject_clipping,
        min_impulse_ms=cfg.min_impulse_ms,
    )

    # Progress callback for console output
    def on_progress(msg: str) -> None:
        prefix = f"[{point_idx+1}/{total_points}] {label}"
        print(f"    {msg}")

    print(f"\n[{point_idx+1}/{total_points}] {label}: Armed. Tap now (timeout {cfg.tap_timeout_s}s)...")

    try:
        result = capture_one_impulse(
            device=device,
            sample_rate=cfg.sample_rate,
            cfg=trigger_cfg,
            progress_cb=on_progress,
        )
    except TimeoutError as e:
        print(f"    ✗ Timeout: {e}")
        return None
    except RuntimeError as e:
        print(f"    ✗ Audio error: {e}")
        return None

    wave = result.audio
    metrics = result.trigger_metrics
    print(f"    ✓ Captured {len(wave)} samples (SNR≈{metrics.snr_est_db:.1f} dB)")
    return wave, metrics.to_provenance_dict()["auto_trigger"]


def _capture_point(
    device: int | None,
    sample_rate: int,
    seconds: float,
    an_cfg: "AnalysisConfig",
) -> tuple[Any, Any]:
    """Capture and analyze a single point. Returns (capture, analysis)."""
    from tap_tone.capture import record_audio
    from tap_tone.analysis import analyze_tap

    cap = record_audio(
        device=device,
        sample_rate=sample_rate,
        channels=1,
        seconds=seconds,
    )

    res = analyze_tap(
        cap.audio,
        cap.sample_rate,
        highpass_hz=an_cfg.highpass_hz,
        peak_min_hz=an_cfg.peak_min_hz,
        peak_max_hz=an_cfg.peak_max_hz,
        peak_min_prominence=an_cfg.peak_min_prominence,
        peak_min_spacing_hz=an_cfg.peak_min_spacing_hz,
        max_peaks=an_cfg.max_peaks,
    )

    return cap, res


def _is_capture_acceptable(analysis: Any) -> bool:
    """Check if capture meets minimum quality threshold."""
    # Basic checks: not clipped, has some confidence
    if analysis.clipped:
        return False
    if analysis.confidence < 0.3:
        return False
    if analysis.rms < 0.001:
        return False
    return True


def run_gold_run(cfg: GoldRunConfig) -> GoldRunResult:
    """Execute the gold run workflow."""
    result = GoldRunResult(specimen_id=cfg.specimen_id)

    # Generate session directory
    ts = _ts()
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    session_key = cfg.session_id or f"session_{ts}"
    session_dir = Path("runs/gold") / date_str / cfg.specimen_id / session_key
    result.session_dir = str(session_dir)

    point_labels = _generate_point_labels(cfg.points)
    result.points = point_labels

    # Dry run: just report what would happen
    if cfg.dry_run:
        if not cfg.json_output:
            print(f"[DRY RUN] Would create session: {session_dir}")
            print(f"[DRY RUN] Would capture points: {point_labels}")
            print(f"[DRY RUN] Would export to: {cfg.out_dir}")
            # Skip device resolution in pure dry-run (no hardware check)
            if cfg.device is not None:
                try:
                    device_idx = int(cfg.device)
                    print(f"[DRY RUN] Device index (assumed): {device_idx}")
                except ValueError:
                    print(f"[DRY RUN] Device name: {cfg.device} (would resolve at runtime)")
        return result

    # Resolve device
    try:
        device_idx = _resolve_device(cfg.device)
    except ValueError as e:
        result.error_message = str(e)
        return result

    # Create session directory
    session_dir.mkdir(parents=True, exist_ok=True)

    # Analysis config (lazy import)
    from tap_tone.config import AnalysisConfig
    an_cfg = AnalysisConfig(
        peak_min_hz=cfg.min_peak_hz,
        peak_max_hz=cfg.max_peak_hz,
    )

    # Capture points
    from tap_tone.storage import persist_capture

    # Auto-trigger provenance (collected per-point)
    auto_trigger_provenance: list[dict] = []

    captured_dirs = []
    for i, label in enumerate(point_labels):
        if cfg.auto_trigger:
            # Auto-trigger capture mode
            cap_result = _capture_point_auto_trigger(
                device_idx, cfg, label, i, len(point_labels)
            )
            if cap_result is None:
                result.error_message = f"Failed to capture point {label} (auto-trigger)"
                return result

            cap_audio, trigger_prov = cap_result
            auto_trigger_provenance.append({"point": label, **trigger_prov})

            # Analyze the captured audio
            from tap_tone.analysis import analyze_tap
            analysis = analyze_tap(
                cap_audio,
                cfg.sample_rate,
                highpass_hz=an_cfg.highpass_hz,
                peak_min_hz=an_cfg.peak_min_hz,
                peak_max_hz=an_cfg.peak_max_hz,
                peak_min_prominence=an_cfg.peak_min_prominence,
                peak_min_spacing_hz=an_cfg.peak_min_spacing_hz,
                max_peaks=an_cfg.max_peaks,
            )

            # Persist
            persisted = persist_capture(
                out_dir=str(session_dir / "points" / f"point_{label}"),
                label=label,
                sample_rate=cfg.sample_rate,
                audio=cap_audio,
                analysis=analysis,
            )
            captured_dirs.append(persisted.capture_dir)
            print(f"    ✓ Captured: dominant={analysis.dominant_hz:.1f}Hz, "
                  f"confidence={analysis.confidence:.2f}")
        else:
            # Manual capture mode (original behavior)
            print(f"\n[{i+1}/{len(point_labels)}] Capturing point {label}...")
            print(f"    Tap the specimen now (timeout: {cfg.tap_timeout_s}s)")

            success = False
            for attempt in range(cfg.max_retries):
                try:
                    cap, analysis = _capture_point(
                        device_idx,
                        cfg.sample_rate,
                        cfg.capture_seconds,
                        an_cfg,
                    )

                    if _is_capture_acceptable(analysis):
                        success = True
                        # Persist to session directory
                        persisted = persist_capture(
                            out_dir=str(session_dir / "points" / f"point_{label}"),
                            label=label,
                            sample_rate=cap.sample_rate,
                            audio=cap.audio,
                            analysis=analysis,
                        )
                        captured_dirs.append(persisted.capture_dir)
                        print(f"    ✓ Captured: dominant={analysis.dominant_hz:.1f}Hz, "
                              f"confidence={analysis.confidence:.2f}")
                        break
                    else:
                        reason = "clipped" if analysis.clipped else "low signal"
                        print(f"    ⚠ Attempt {attempt+1}: {reason}, retrying...")

                except Exception as e:
                    print(f"    ⚠ Attempt {attempt+1} failed: {e}")

            if not success:
                result.error_message = f"Failed to capture point {label} after {cfg.max_retries} attempts"
                return result

    # Restructure for Phase 2 export compatibility
    # The persist_capture creates capture_<ts> subdirs, but export expects point_<PID>/
    # We need to create the expected structure
    points_dir = session_dir / "points"
    for label in point_labels:
        point_dir = points_dir / f"point_{label}"
        if point_dir.exists():
            # Find the capture subdir and flatten
            for subdir in point_dir.iterdir():
                if subdir.is_dir() and subdir.name.startswith("capture_"):
                    # Move files up
                    for f in subdir.iterdir():
                        f.rename(point_dir / f.name)
                    subdir.rmdir()

    # Create minimal grid.json for export
    grid = {
        "schema_version": "grid_v1",
        "points": [{"id": label, "x_mm": 0, "y_mm": 0} for label in point_labels],
    }
    (session_dir / "grid.json").write_text(json.dumps(grid, indent=2), encoding="utf-8")

    # Create minimal metadata.json
    metadata = {
        "schema_version": "session_meta_v1",
        "specimen_id": cfg.specimen_id,
        "created_utc": ts,
        "gold_run": True,
        "batch_label": cfg.batch_label,
    }
    (session_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"\n[gold-run] All points captured to: {session_dir}")

    # Export
    if cfg.export_zip:
        try:
            # Import the exporter
            sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "phase2"))
            from export_viewer_pack_v1 import export_viewer_pack

            cfg.out_dir.mkdir(parents=True, exist_ok=True)

            # Generate output filename
            date_stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
            zip_name = f"gold_standard_viewer_pack_v1_{cfg.specimen_id}_{date_stamp}.zip"

            zip_path = export_viewer_pack(
                session_dir,
                cfg.out_dir,
                as_zip=True,
            )

            # Rename to canonical name
            final_path = cfg.out_dir / zip_name
            if zip_path.exists() and zip_path != final_path:
                zip_path.rename(final_path)
                zip_path = final_path

            result.zip_path = str(zip_path)
            result.validation_passed = True  # Export succeeded = validation passed
            result.validation_errors = 0
            result.validation_warnings = 0
            result.validation_report_path = str(session_dir / "viewer_pack_v1" / "validation_report.json")

            print(f"[gold-run] ✓ Exported: {zip_path}")

        except ValueError as e:
            # Validation failed
            result.validation_passed = False
            result.error_message = str(e)
            print(f"[gold-run] ✗ Export failed: {e}")
            return result

        except Exception as e:
            result.error_message = f"Export error: {e}"
            print(f"[gold-run] ✗ Export error: {e}")
            return result

    # Ingest (ON by default)
    if cfg.ingest and result.zip_path and result.validation_passed:
        result.ingest_attempted = True
        print(f"[gold-run] Ingesting to {cfg.ingest_url}...")

        from tap_tone.ingest import ingest_zip

        ingest_result = ingest_zip(
            zip_path=result.zip_path,
            ingest_url=cfg.ingest_url,
            session_id=cfg.session_id,
            batch_label=cfg.batch_label,
        )

        result.ingest_ok = ingest_result.ok
        result.ingest_http_status = ingest_result.http_status
        result.ingest_run_id = ingest_result.run_id
        result.ingest_error = ingest_result.error

        if ingest_result.ok:
            print(f"[gold-run] ✓ Ingested: run_id={ingest_result.run_id}")

            # Show bundle_sha256 if present
            bundle_sha = ingest_result.payload.get("bundle_sha256") if ingest_result.payload else None
            if bundle_sha:
                print(f"    Viewer pack hash: {bundle_sha[:16]}...")

            # Pick URL and open browser
            url = pick_open_url(
                cfg.ingest_url,
                ingest_result.payload,
                open_browser=cfg.open_browser,
                open_viewer=cfg.open_viewer,
            )

            # Always print the library URL for reference
            library_url = f"{cfg.ingest_url.rstrip('/')}/tools/audio-analyzer/library"
            print(f"    Library: {library_url}")

            if url:
                from tap_tone.util import try_open_url

                # Note if falling back to library when --open-viewer was requested
                if cfg.open_viewer and not bundle_sha:
                    print("    ℹ Viewer deep-link unavailable (no bundle_sha256). Opening Library instead.")

                # Always print the canonical URL for copy/share
                print(f"    URL: {url}")

                # Print shortened bundle SHA for quick identity verification
                if bundle_sha:
                    print(f"    Bundle SHA: {bundle_sha[:16]}…")

                opened = try_open_url(url)
                if opened:
                    print("    Browser: opened")
                else:
                    print("    Browser: could not open (headless or blocked).")
            else:
                print("    Browser: skipped (--no-open)")
        else:
            # Ingest failed — report but do not delete ZIP
            status_str = f"({ingest_result.http_status})" if ingest_result.http_status else ""
            print(f"[gold-run] ✗ Ingest failed {status_str}: {ingest_result.error}")
            print(f"    ZIP preserved at: {result.zip_path}")
            # Note: error_message is NOT set — ingest failure is non-fatal for ZIP

    elif cfg.ingest and not result.validation_passed:
        # Validation failed — skip ingest
        result.ingest_error = "validation did not pass"
        print("[gold-run] ⚠ Skipping ingest: validation did not pass")

    elif not cfg.ingest and result.zip_path:
        print("[gold-run] ℹ Ingest skipped (--no-ingest)")

    return result


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="tap_tone gold-run",
        description="One-command Gold Standard Run: capture → export → validate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Required
    p.add_argument("--specimen-id", required=True, help="Specimen identifier for naming")
    p.add_argument("--device", required=True, help="Audio device (index or name substring)")
    p.add_argument("--out-dir", required=True, type=Path, help="Output directory for ZIP")

    # Capture options
    p.add_argument("--points", type=int, default=3, help="Number of points to capture (default: 3)")
    p.add_argument("--tap-timeout-s", type=float, default=8.0, help="Timeout per tap (default: 8)")
    p.add_argument("--max-retries", type=int, default=3, help="Max retries per point (default: 3)")
    p.add_argument("--sample-rate", type=int, default=48000, help="Sample rate (default: 48000)")
    p.add_argument("--capture-seconds", type=float, default=2.5, help="Capture window (default: 2.5)")

    # Analysis options
    p.add_argument("--min-peak-hz", type=float, default=50.0, help="Min peak frequency (default: 50)")
    p.add_argument("--max-peak-hz", type=float, default=3000.0, help="Max peak frequency (default: 3000)")

    # Auto-trigger options
    auto_grp = p.add_argument_group("auto-trigger", "Hands-free impulse detection")
    auto_grp.add_argument("--auto-trigger", action="store_true",
                          help="Enable auto-trigger mode (detect impulse automatically)")
    auto_grp.add_argument("--warmup-s", type=float, default=0.5,
                          help="Noise floor warmup period (default: 0.5)")
    auto_grp.add_argument("--peak-mult", type=float, default=10.0,
                          help="Peak must exceed noise * this (default: 10)")
    auto_grp.add_argument("--rms-mult", type=float, default=3.0,
                          help="RMS must exceed noise * this (default: 3)")
    auto_grp.add_argument("--debounce-frames", type=int, default=2,
                          help="Consecutive trigger frames required (default: 2)")
    auto_grp.add_argument("--pre-ms", type=float, default=50.0,
                          help="Pre-roll before trigger in ms (default: 50)")
    auto_grp.add_argument("--post-ms", type=float, default=1500.0,
                          help="Post-roll after trigger in ms (default: 1500)")
    auto_grp.add_argument("--reject-clipping", action="store_true", default=True,
                          help="Reject and retry clipped captures (default: True)")
    auto_grp.add_argument("--no-reject-clipping", action="store_false", dest="reject_clipping",
                          help="Accept clipped captures with warning")
    auto_grp.add_argument("--min-impulse-ms", type=float, default=2.0,
                          help="Ignore ultra-short glitches (default: 2)")

    # Export options
    p.add_argument("--session-id", help="Custom session ID")
    p.add_argument("--batch-label", help="Batch label for grouping")
    p.add_argument("--audio-required", action="store_true", help="Treat missing audio as error")
    p.add_argument("--no-zip", action="store_true", help="Skip ZIP export (stage only)")

    # Ingest options (ON by default)
    p.add_argument("--no-ingest", action="store_true",
                   help="Skip auto-ingest to ToolBox")
    p.add_argument("--ingest-url", default="http://localhost:8000",
                   help="ToolBox API URL (default: http://localhost:8000)")
    p.add_argument("--no-open", action="store_true",
                   help="Skip opening ToolBox library in browser after ingest")
    p.add_argument("--open-viewer", action="store_true",
                   help="Open Viewer deep-link (if sha256 available) instead of Library")

    # Diagnostics
    p.add_argument("--dry-run", action="store_true", help="Show what would happen, don't capture")
    p.add_argument("--json", action="store_true", help="Output machine-readable JSON summary")

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    cfg = GoldRunConfig(
        specimen_id=args.specimen_id,
        device=args.device,
        out_dir=args.out_dir,
        points=args.points,
        session_id=args.session_id,
        batch_label=args.batch_label,
        tap_timeout_s=args.tap_timeout_s,
        max_retries=args.max_retries,
        min_peak_hz=args.min_peak_hz,
        max_peak_hz=args.max_peak_hz,
        sample_rate=args.sample_rate,
        capture_seconds=args.capture_seconds,
        audio_required=args.audio_required,
        export_zip=not args.no_zip,
        ingest=not args.no_ingest,
        ingest_url=args.ingest_url,
        open_browser=not args.no_open,
        open_viewer=args.open_viewer,
        dry_run=args.dry_run,
        json_output=args.json,
        # Auto-trigger options
        auto_trigger=args.auto_trigger,
        warmup_s=args.warmup_s,
        peak_mult=args.peak_mult,
        rms_mult=args.rms_mult,
        debounce_frames=args.debounce_frames,
        pre_ms=args.pre_ms,
        post_ms=args.post_ms,
        reject_clipping=args.reject_clipping,
        min_impulse_ms=args.min_impulse_ms,
    )

    try:
        result = run_gold_run(cfg)
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"[gold-run] Unexpected error: {e}", file=sys.stderr)
        return 5

    # Output
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        if result.error_message:
            print(f"\n[gold-run] ✗ Failed: {result.error_message}")
        elif args.dry_run:
            print(f"\n[gold-run] ✓ Dry run complete (no capture)")
        elif result.validation_passed:
            print(f"\n[gold-run] ✓ Gold run completed")
            print(f"✓ Validation passed")
            if result.ingest_ok:
                print(f"✓ Ingested into ToolBox")
                print(f"")
                print(f"Run ID: {result.ingest_run_id}")
                print(f"Library: {cfg.ingest_url}/tools/audio-analyzer/library")
            elif result.ingest_attempted and not result.ingest_ok:
                print(f"✗ Ingest failed (see above)")
            print(f"")
            print(f"ZIP saved at:")
            print(f"  {result.zip_path}")
        else:
            print(f"\n[gold-run] Validation pending or incomplete")

    # Exit codes
    if result.error_message:
        if "device" in result.error_message.lower():
            return 4
        elif "capture" in result.error_message.lower() or "attempts" in result.error_message.lower():
            return 3
        elif "validation" in result.error_message.lower():
            return 2
        return 5

    # Dry run always succeeds
    if args.dry_run:
        return 0

    return 0 if result.validation_passed else 2


if __name__ == "__main__":
    sys.exit(main())
