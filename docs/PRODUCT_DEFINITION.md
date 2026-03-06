# Production Shop: Product Definition

*Formerly: Luthiers-ToolBox*

**Date:** 2026-02-23 (Updated: 2026-03-06)
**Status:** Authoritative
**Owner:** Product

---

## The ONE Core Job

**Production Shop converts design files (DXF/PDF) into safe, machine-ready G-code for CNC routers with verified geometry and pre-cut validation.**

Everything else is secondary.

---

## Product Hierarchy

### Tier 1: Core (Must Work Perfectly)

| Module | Purpose | Success Metric |
|--------|---------|----------------|
| **DXF Import** | Validate and parse design files | 100% of valid DXF files load without error |
| **CAM Toolpath** | Generate adaptive pocketing toolpaths | Toolpaths execute without collision |
| **G-code Export** | Output machine-specific G-code | G-code runs on target machine without modification |
| **RMOS Safety** | Prevent dangerous machining parameters | Zero RED-blocked jobs cause machine damage |

### Tier 2: Supporting (Should Work Well)

| Module | Purpose | Dependency |
|--------|---------|------------|
| **Calculators** | Fret positions, bridge geometry, rosette math | Feeds DXF generation |
| **Post-Processors** | Machine-specific G-code dialect | Required by G-code Export |
| **Tool Library** | Endmill/bit specifications | Required by CAM Toolpath |
| **Simulation** | Visual toolpath preview | Supports operator confidence |

### Tier 3: Optional (Nice to Have)

| Module | Purpose | Status |
|--------|---------|--------|
| **Art Studio** | Decorative pattern generation | Active |
| **Relief Carving** | Image-to-3D heightmap | Active |
| **Batch Sawing** | Multi-part cutting plans | Under review |
| **AI Integration** | LLM-assisted design | Experimental |

### Tier 4: Deprecated (Scheduled for Removal)

| Module | Reason | Sunset Date |
|--------|--------|-------------|
| **Streamlit Demo** | Superseded by Vue client | Immediate |
| **Legacy Client** | Duplicate of packages/client | Immediate |
| **Session Logs in /docs** | Not documentation | Immediate |

---

## What This Product IS

1. A **CAM system** for guitar-specific CNC operations
2. A **safety layer** that prevents dangerous machining parameters
3. A **calculator suite** for lutherie-specific geometry
4. A **multi-machine** tool supporting GRBL, Mach4, LinuxCNC, PathPilot, MASSO

## What This Product IS NOT

1. **Not a general-purpose CAM system** - Only guitar/instrument parts
2. **Not a CAD system** - We import DXF, we don't create geometry
3. **Not a machine controller** - We generate G-code, we don't send it
4. **Not an audio analyzer** - tap_tone_pi is a separate product
5. **Not a design marketplace** - No user-generated content sharing
6. **Not a cloud service** - Self-hosted or single-tenant only

---

## Primary User Journeys

### Journey 1: DXF to G-code (80% of usage)

```
1. Upload DXF file
2. Select tool (endmill diameter, flute count)
3. Set material (wood species, thickness)
4. Configure machine (post-processor, work envelope)
5. Run feasibility check (RMOS)
6. Generate toolpath
7. Preview simulation
8. Download G-code
```

**Target time:** < 5 minutes for experienced user

### Journey 2: Parametric Design to G-code (15% of usage)

```
1. Open calculator (fret slots, rosette, bridge)
2. Enter parameters (scale length, fret count, etc.)
3. Generate DXF
4. Continue with Journey 1
```

**Target time:** < 10 minutes including Journey 1

### Journey 3: Art Pattern to G-code (5% of usage)

```
1. Open Art Studio
2. Select pattern type (rosette, inlay, relief)
3. Configure parameters
4. Export DXF or direct to CAM
5. Continue with Journey 1
```

**Target time:** < 15 minutes including Journey 1

---

## Feature Acceptance Criteria

Before adding ANY new feature, answer these questions:

1. **Does it serve one of the 3 primary journeys?**
   - If no: Reject or defer to "future consideration"

2. **Does it require new API routes?**
   - If adding >5 routes: Requires architecture review
   - If adding >20 routes: Requires product review

3. **Does it increase safety risk?**
   - If it generates G-code: Must integrate with RMOS
   - If it bypasses RMOS: Reject

4. **Does it have a clear owner?**
   - If no maintainer identified: Reject

5. **What gets removed to make room?**
   - Net-zero LOC policy: New features must delete equivalent complexity

---

## Route Budget

| Category | Current | Target | Action |
|----------|---------|--------|--------|
| Tier 1 (Core) | ~200 | 150 | Consolidate |
| Tier 2 (Supporting) | ~150 | 100 | Consolidate |
| Tier 3 (Optional) | ~400 | 50 | Aggressive deprecation |
| Tier 4 (Deprecated) | ~310 | 0 | Delete |
| **Total** | **~1,060** | **300** | **-72%** |

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-23 | Saw Lab under review | 2,724 LOC single file suggests overscope |
| 2026-02-23 | AI Integration is experimental | Unbounded cost risk |
| 2026-02-23 | tap_tone_pi is separate product | Hard boundary enforced in CI |

---

## Success Metrics

| Metric | Current | Target | Timeframe |
|--------|---------|--------|-----------|
| Routes | 1,060 | 300 | 6 months |
| LOC | 411,000 | 200,000 | 12 months |
| Journey 1 completion time | Unknown | < 5 min | 3 months |
| RMOS false positive rate | Unknown | < 1% | 3 months |
| User interviews completed | 0 | 5 | 1 month |

---

*This document is the authoritative source for product scope decisions. All feature requests must be evaluated against this definition.*
