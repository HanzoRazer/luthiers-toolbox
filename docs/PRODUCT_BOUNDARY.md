# Production Shop — Product Boundary

## What This System Is

A CNC lutherie workflow system covering design, validation, toolpath generation, safety gating, and manufacturing export for small shops and serious builders.

## What It Is Not

- Not a general CAD system
- Not a multi-tenant SaaS (yet)
- Not a research platform
- Not a certified safety system
- Designed for single-shop, single-operator use

## Deployment Model

- Single instance, single shop
- Local FastAPI backend + Vue frontend
- SQLite + file storage (intentional for simplicity)
- Supports: solo luthier, small CNC shop, boutique builder
- Does NOT support: concurrent multi-user, cloud deployment (yet)

## Identity

- Product name: The Production Shop
- Repo name: luthiers-toolbox (historical)
- These refer to the same system
- All new documentation uses "Production Shop"

## Production-Grade Modules

| Module | Status | Entry Point |
|--------|--------|-------------|
| DXF Import → Validation → CAM | ✅ Production | /cam |
| Rosette Design + CNC Export | ✅ Production | /art-studio |
| Neck/Body Generator + Toolpath | ✅ Production | /cam/workspace |
| Safety Preflight + RMOS Gating | ✅ Production | /safety |
| Instrument Geometry Calculators | ✅ Production | /design |
| Bridge/Saddle/Nut Setup Chain | ✅ Production | /design |
| Smart Guitar Module | ✅ Production | /smart-guitar |
| Acoustic Plate Design | ✅ Production | /acoustics |
| String Tension Calculator | ✅ Production | /design |
| Wood Movement Calculator | ✅ Production | /design |
| Electronics Layout | ✅ Production | /design |
| Build Sequence Composer | ✅ Production | /design |

## Beta Modules

| Module | Status | Notes |
|--------|--------|-------|
| Photo Vectorizer | 🟡 Beta | rembg + potrace pipeline |
| Voicing History Tracker | 🟡 Beta | Tap-tone integration pending |
| Analytics | 🟡 Beta | Graduated from experimental |

## Experimental (active development)

| Module | Status | Location |
|--------|--------|----------|
| CNC Production core | 🔬 Active | app/cam_core/ |

## Explicitly Removed

- AI/ML advisory (removed 2026-02)
- Job log system (removed 2026-02)
- Archived rosette prototypes (removed 2026-03)

## Out of Scope

- Multi-tenant enterprise deployment
- Non-luthier woodworking
- General audio production
- Real-time machine feedback/control

## What "Production-Grade" Means Here

A module is production-grade when it has:
- Endpoint tests passing
- Safety-critical paths covered (≥60%)
- Pydantic schema validation
- GREEN/YELLOW/RED gate logic where applicable
- No NotImplementedError in primary path
