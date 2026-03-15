"""Quick re-run: just the archtop + summary comparison table."""
import sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from photo_vectorizer_v2 import PhotoVectorizerV2

PLANS = Path(__file__).resolve().parent.parent.parent / "Guitar Plans"
OUT = Path(__file__).resolve().parent / "live_test_output"

v2 = PhotoVectorizerV2()

tests = [
    ("Smart Guitar_1_00_original.jpg", "smart_guitar", 444.5, 368.3),
    ("Black and White Benedetto_00_original.jpg", None, 482.6, 431.8),
    ("Jumbo Tiger Maple Archtop Guitar with a Florentine Cutaway_00_original.jpg", "jumbo_archtop", 520.0, 430.0),
]

rows = []
for fname, spec, exp_h, exp_w in tests:
    img_path = PLANS / fname
    if not img_path.exists():
        continue
    t0 = time.time()
    r = v2.extract(str(img_path), output_dir=str(OUT), spec_name=spec)
    dt = time.time() - t0
    h, w = r.body_dimensions_mm
    h_err = abs(h - exp_h) / exp_h * 100
    w_err = abs(w - exp_w) / exp_w * 100
    cal = r.calibration
    src = cal.source.value if hasattr(cal.source, "value") else str(cal.source)
    short = fname.split("_00")[0]
    rows.append((short, spec or "(none)", exp_h, exp_w, h, w, h_err, w_err, src, cal.confidence, dt))

print()
print("=" * 110)
print(f"{'Image':<35} {'Spec':<14} {'Exp HxW':>14} {'Got HxW':>14} {'H err':>7} {'W err':>7} {'Source':<18} {'Conf':>5} {'Time':>6}")
print("-" * 110)
for r in rows:
    short, spec, eh, ew, gh, gw, he, we, src, conf, dt = r
    print(f"{short:<35} {spec:<14} {eh:6.1f}x{ew:<6.1f} {gh:6.1f}x{gw:<6.1f} {he:6.1f}% {we:6.1f}% {src:<18} {conf:5.2f} {dt:5.1f}s")
print("=" * 110)

# Compare with pre-patch baseline (from test_real_image_comparison.py results)
print()
print("COMPARISON WITH PRE-PATCH BASELINE:")
print("-" * 70)
baseline = [
    ("Smart Guitar", 41.3, 5.2),
    ("Benedetto", 67.9, 58.9),
    ("Archtop", 12.0, 111.7),  # pre-patch-17 baseline (post patches 14+13+15)
]
for i, (name, old_h, old_w) in enumerate(baseline):
    if i < len(rows):
        _, _, _, _, _, _, new_h, new_w, _, _, _ = rows[i]
        h_delta = new_h - old_h
        w_delta = new_w - old_w
        h_arrow = "improved" if h_delta < 0 else "same" if abs(h_delta) < 0.5 else "worse"
        w_arrow = "improved" if w_delta < 0 else "same" if abs(w_delta) < 0.5 else "worse"
        print(f"  {name:<20} H: {old_h:5.1f}% -> {new_h:5.1f}% ({h_arrow})  W: {old_w:5.1f}% -> {new_w:5.1f}% ({w_arrow})")
print()
