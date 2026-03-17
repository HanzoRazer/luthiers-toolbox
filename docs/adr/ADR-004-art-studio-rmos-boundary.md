# ADR-004: Art Studio as User-Facing Interface, RMOS as Internal Spine

## Status
Accepted — 2026-03-17

## Context
RMOS originally stood for "Rosette Manufacturing Operations System."
It was built to design rosettes and evolved into the bidirectional
workflow hub of the entire platform — files flow into RMOS,
files flow out of RMOS. It is now the Resource Management
Operating System: the internal spine that governs all
manufacturing workflows with SHA256 audit chains,
candidate decision workflows, and safety gates.

The Art Studio originated in the Luthier's ToolBox as the
headstock and neck design environment. Both systems accumulated
features without a clear user-facing boundary.

## Decision

RMOS is internal infrastructure. It has no user-facing features.
It is the bidirectional workflow spine — every design decision
flows through it, every manufacturing output flows from it.
Users never see "RMOS" in the UI.

The Art Studio is the forward-facing creative interface.
It covers all decorative and design work:
  - Rosette design (drag-and-drop, 30-pattern premium library)
  - Headstock inlay design
  - Instrument body marquetry
  - Neck inlay
  - Binding and purfling
  - V-Carve and relief carving

The drag-and-drop engine is a new Python build converted from
the rosette generator prototypes, extended to cover all four
mounting surfaces: rosette, headstock, neck, body.

## Boundary Rules

RMOS (internal):
  - All manufacturing orchestration
  - SHA256 audit chains
  - Candidate decision workflows
  - Safety gates and feasibility checks
  - G-code approval and export governance
  - Never referenced in user-facing UI labels

Art Studio (user-facing):
  - All creative/decorative design tools
  - Pattern library (free: 8 recipes, premium: 30 patterns)
  - Drag-and-drop tile placement
  - BOM and manufacturing feasibility display
  - "Send to manufacturing" triggers RMOS workflow
  - The user sees Art Studio, not RMOS

## The New Art Studio Engine

The drag-and-drop engine becomes a unified Python backend:
  app/art_studio/services/pattern_engine/
  ├── engine.py          — unified tile geometry
  ├── surfaces.py        — rosette | headstock | neck | body
  ├── free_patterns.py   — 8 standard recipes (public API)
  ├── premium_patterns.py — 30 patterns (pro tier only)
  └── bom.py             — bill of materials across surfaces

Frontend: RosetteWheelView.vue becomes ArtStudioCanvas.vue
  — same drag-and-drop interaction
  — surface selector: rosette / headstock / neck / body
  — pattern library: free tier visible, premium gated

## Navigation
Art Studio nav (user sees):
  Soundhole & Rosette
  Headstock
  Neck Inlay
  Body Marquetry
  Binding & Purfling
  V-Carve & Relief

RMOS nav (internal/admin only):
  Manufacturing Runs
  Candidate Decisions
  Safety Gates
  Audit Log

## References
- PLATFORM_ARCHITECTURE.md
- ROSETTE_SYSTEM_AUDIT.md
- docs/SPRINT_BOARD.md TRACK 5
