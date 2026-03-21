"""
One-shot merge: Session A calculator files from archive into services/api.
Run from repo root: python scripts/merge_session_a_calculators.py
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / "docs/archive/photo_vectorizer_patches/files - 2026-03-20T023112.442 (2)"
CALC = ROOT / "services/api/app/calculators"


def main() -> None:
    # --- 1) neck_block (drop-in) ---
    src_nb = ARCH / "files - 2026-03-19T164605.777/neck_block_calc.py"
    if not src_nb.is_file():
        raise SystemExit(f"Missing {src_nb}")
    (CALC / "neck_block_calc.py").write_text(src_nb.read_text(encoding="utf-8"), encoding="utf-8")
    print("Wrote neck_block_calc.py")

    # --- 2) soundhole: large physics + GEOMETRY-002 placement API ---
    large_sh = ARCH / "files - 2026-03-19T124524.898/soundhole_calc.py"
    if not large_sh.is_file():
        raise SystemExit(f"Missing {large_sh}")
    placement_src = CALC / "soundhole_calc.py"
    placement_txt = placement_src.read_text(encoding="utf-8")
    # Extract router API block (constants + SoundholeSpec + helpers) from current file
    m = re.search(
        r"(# ─── Standard Diameters by Body Style ───.*)",
        placement_txt,
        re.DOTALL,
    )
    if not m:
        raise SystemExit("Could not extract placement API from soundhole_calc.py")
    placement_block = m.group(1).rstrip() + "\n"

    merged = large_sh.read_text(encoding="utf-8").rstrip() + "\n\n"
    merged += (
        "# ═══════════════════════════════════════════════════════════════════════════════\n"
        "# GEOMETRY-002 — Soundhole placement & sizing (router / tests)\n"
        "# Preserved from previous app.calculators.soundhole_calc API.\n"
        "# ═══════════════════════════════════════════════════════════════════════════════\n\n"
    )
    merged += placement_block
    placement_src.write_text(merged, encoding="utf-8")
    print("Wrote merged soundhole_calc.py")

    # --- 3) kerfing geometry engine (rename conflicting KerfingSpec) ---
    src_k = ARCH / "kerfing_calc (1).py"
    if not src_k.is_file():
        raise SystemExit(f"Missing {src_k}")
    ktxt = src_k.read_text(encoding="utf-8")
    # Rename geometry strip spec to avoid clashing with schedule KerfingSpec in kerfing_calc.py
    ktxt = re.sub(r"\bKerfingSpec\b", "KerfingStripGeometrySpec", ktxt)
    (CALC / "kerfing_geometry_engine.py").write_text(ktxt, encoding="utf-8")
    print("Wrote kerfing_geometry_engine.py")

    # --- 4) bracing physics core ---
    src_b = ARCH / "files - 2026-03-20T023112.442/bracing_calc.py"
    if not src_b.is_file():
        raise SystemExit(f"Missing {src_b}")
    btxt = src_b.read_text(encoding="utf-8")
    # Keep library functions only (drop CLI runner block)
    cut = btxt.find("\n# ── Report runner")
    if cut != -1:
        btxt = btxt[:cut].rstrip() + "\n"
    (CALC / "_bracing_physics.py").write_text(btxt, encoding="utf-8")
    print("Wrote _bracing_physics.py")

    # --- 5) fret wire + nut: full physics modules (parallel to router API files) ---
    src_fw = ARCH / "files - 2026-03-19T213759.333/fret_wire_calc.py"
    (CALC / "fret_wire_physics.py").write_text(
        src_fw.read_text(encoding="utf-8"), encoding="utf-8"
    )
    print("Wrote fret_wire_physics.py (full physics; catalog API remains in fret_wire_calc.py)")

    src_nut = ARCH / "files - 2026-03-19T222452.724/nut_compensation_calc.py"
    (CALC / "nut_compensation_physics.py").write_text(
        src_nut.read_text(encoding="utf-8"), encoding="utf-8"
    )
    print("Wrote nut_compensation_physics.py (full physics; router API remains in nut_compensation_calc.py)")

    print("Done.")


if __name__ == "__main__":
    main()
