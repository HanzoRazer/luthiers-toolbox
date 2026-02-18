# Luthier's ToolBox - Product Scope

**Last Updated:** 2026-02-18

This document defines the product boundary between shipped features and experimental modules.

---

## Core Product (Production-Ready)

These features are stable, tested, and supported for production use:

### DXF → G-code Pipeline
- **DXF Import v2.0** - Geometry validation, preflight checks, scale detection
- **Adaptive Pocketing v3.0** - Spiral toolpaths, island handling, trochoidal insertion
- **Multi-Post Support** - GRBL, Mach4, LinuxCNC, PathPilot, MASSO

### RMOS Safety System v2.0
- 22 feasibility rules (F001-F029) with risk bucketing
- GREEN/YELLOW/RED decision gating
- Immutable audit trail
- `@safety_critical` fail-closed decorator
- Override controls with governance

### Parametric Design Calculators
- Fret position calculator (12-TET, custom ratios)
- Scale length designer
- Chipload and feeds/speeds
- Neck taper geometry

### Saw Lab v1.0
- Batch sawing operations
- Cut plan generation
- G-code validation and linting
- Advisory signals

---

## Experimental (Not Production)

These features are in development and **not recommended for production use**:

### Smart Guitar IoT
- Device telemetry ingestion
- Real-time monitoring
- **Status:** Early development, no external users

### Audio Analyzer Integration
- Viewer pack import from tap-tone-pi
- Spectrum display
- **Status:** Integration testing

### AI Vision Features
- Blueprint AI image analysis
- Vision Engine prompt engineering
- **Status:** Beta, requires API keys

### Blueprint AI v1.0
- Image-to-DXF conversion
- Pattern recognition
- **Status:** Beta, accuracy varies

---

## Feature Classification

| Feature | Status | Flag | Default |
|---------|--------|------|---------|
| RMOS Core | Stable | `RMOS_RUNS_V2_ENABLED` | `true` |
| AI Context | Experimental | `AI_CONTEXT_ENABLED` | `true` |
| Vision Engine | Beta | N/A | Requires API key |
| Saw Lab Learning | Experimental | `SAW_LAB_LEARNING_HOOK_ENABLED` | `false` |

---

## API Surface

- **Production Routes:** `GET /api/features/catalog` (64 routers)
- **Route Analytics:** `GET /api/_analytics/summary`
- **Health Check:** `GET /api/health/detailed`

---

## What This Project Is NOT

1. **Not a full Fusion 360 replacement** - Focused on lutherie-specific CAM
2. **Not a general-purpose CAD tool** - Expects DXF input, not native design
3. **Not a CNC controller** - Generates G-code, doesn't stream to machines
4. **Not production-hardened for 24/7 operation** - Single-user workshop tool

---

## Getting Started

For new users:
1. Start with DXF → G-code workflow
2. Use RMOS safety gates (never override RED without understanding)
3. Test on scrap material first
4. Experimental features require explicit opt-in

**Quick Cut Workflow:** Coming soon - 3-screen DXF→machine→G-code flow for beginners.
