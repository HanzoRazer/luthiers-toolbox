"""Live test: Photo Vectorizer v2 with Patches 14+13+15."""
import sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from photo_vectorizer_v2 import PhotoVectorizerV2

PLANS = Path(__file__).resolve().parent.parent.parent / "Guitar Plans"
OUT = Path(__file__).resolve().parent / "live_test_output"
OUT.mkdir(exist_ok=True)

v2 = PhotoVectorizerV2()

tests = [
    ("Smart Guitar_1_00_original.jpg", "smart_guitar", 444.5, 368.3),
    ("Black and White Benedetto_00_original.jpg", None, 482.6, 431.8),
    ("Jumbo Tiger Maple Archtop Guitar with a Florentine Cutaway_00_original.jpg", "jumbo_archtop", 520.0, 430.0),
]

print("=" * 80)
print("LIVE TEST: Photo Vectorizer v2 with Patches 14+13+15")
print("=" * 80)

for fname, spec, exp_h, exp_w in tests:
    img_path = PLANS / fname
    if not img_path.exists():
        print(f"SKIP: {fname} not found")
        continue
    label = spec if spec else "(none)"
    print(f"\n--- {fname} ---")
    print(f"  Spec: {label}  Expected: {exp_h:.1f} x {exp_w:.1f} mm")
    t0 = time.time()
    r = v2.extract(
        str(img_path), output_dir=str(OUT), spec_name=spec,
        export_dxf=True, export_svg=True, debug_images=True,
    )
    dt = time.time() - t0
    h, w = r.body_dimensions_mm
    h_err = abs(h - exp_h) / exp_h * 100
    w_err = abs(w - exp_w) / exp_w * 100
    cal = r.calibration
    print(f"  Measured: {h:.1f} x {w:.1f} mm")
    print(f"  Error:  H={h_err:.1f}%  W={w_err:.1f}%")
    src = cal.source.value if hasattr(cal.source, "value") else str(cal.source)
    print(f"  Calibration: {src} (conf={cal.confidence:.2f}) mpp={cal.mm_per_px:.4f}")
    print(f"  Time: {dt:.1f}s")
    if r.warnings:
        for warn in r.warnings:
            print(f"  WARN: {warn}")
    if r.output_dxf:
        print(f"  DXF: {r.output_dxf}")
    if r.output_svg:
        print(f"  SVG: {r.output_svg}")

print("\n" + "=" * 80)
print("DONE")
print("=" * 80)
