"""
Rosette Prototypes — Reference implementations from AI design sessions.

BOUNDARY: These are standalone validation and reference scripts.
Production code must NEVER import from this package.
Run individual prototypes via ``python -m app.cam.rosette.prototypes.<name>``.

Active prototypes:
    generate_wave_rosette.py       — Crashing wave (asymmetric arch formula)
    generate_spanish_rosette.py    — Spanish right-angle (23×15 grid)
    rope_twist_rosette.py          — Rope twist (7×5 diagonal staircase)
    rope_twist_rosette_v2.py       — Rope twist v2 (portable output paths)
    rosette_jsx_eval.py            — JSX algorithm evaluator (matplotlib)

Ported from JSX prototypes (docs/rosette-prototypes/jsx/):
    wave_simple_sine.py            — Pure sinusoidal wave (from wave-rosette-v1.jsx)
    wave_segment_arches.py         — Discrete segment arches: sine/tri/flat (from v2.jsx)
    wave_vertical_strand.py        — Single strand vertical topology (from v4.jsx)
    spanish_ladder_parametric.py   — Parametric ladder builder (from spanish-ladder-rosette.jsx)
    celtic_parametric_knots.py     — 6-tile library + 3-mode parametric knots (from v2/v3/v4.jsx)
    herringbone_parametric.py      — Parity-rotation herringbone (from v4-mothership.jsx)

Data assets:
    herringbone_embedded_quads.py  — Pre-computed tile coordinates (1198 quads)
    shape_library.py               — Shape primitives library
    wood_materials.py              — Wood material definitions

Archived (see __archived__/):
    *_viewer.py files              — Standalone visualization tools

JSX reference files live in docs/rosette-prototypes/jsx/.
"""
