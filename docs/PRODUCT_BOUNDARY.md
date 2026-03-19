# Production Shop — Product Boundary

## What This System Is

One sentence: A CNC lutherie workflow system covering design, validation, toolpath generation, safety gating, and manufacturing export for small shops and serious builders.

## What It Is Not

- Not a general CAD system
- Not a multi-tenant SaaS
- Not a research platform
- Not a certified safety system
- Designed for single-shop, single-operator use

## Deployment Model

- Single instance, single shop
- Local FastAPI backend + Vue frontend
- SQLite + file storage (intentional for simplicity)
- Supports: solo luthier, small CNC shop, boutique builder
- Does NOT support: concurrent multi-user, cloud deployment (yet)

## Production-Grade Modules (fully supported)

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

## Beta Modules (functional, less tested)

| Module | Status | Notes |
|--------|--------|-------|
| Photo Vectorizer | 🟡 Beta | rembg + potrace pipeline |
| Build Sequence Composer | 🟡 Beta | CONSTRUCTION-010 |
| Voicing History Tracker | 🟡 Beta | Tap-tone integration pending |

## Experimental (not in production path)

| Module | Status | Location |
|--------|--------|----------|
| Analytics | 🔬 Active dev | app/analytics/ |
| CNC Production | 🔬 Active dev | app/cam_core/ |

## Explicitly Out of Scope

- AI/ML advisory (removed)
- Job log system (removed)
- Multi-tenant auth
- Payment processing (future)

## Identity

- Product name: The Production Shop
- Repo name: luthiers-toolbox (historical)
- These refer to the same system
- All new docs use "Production Shop"
