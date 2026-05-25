# CAM Assist System Definition

## Product Identity

CAM Assist is a **strategy export assistant** for lutherie manufacturing.

It helps luthiers translate instrument design intent into explicit, reviewable manufacturing strategies that can be imported into any CAM system or executed manually.

## Core Function

```
Instrument Specification → CAM Assist → Strategy Package
```

A strategy package contains:
- **DXF geometry** — Machine-readable 2D/2.5D geometry
- **Strategy metadata** — Operation parameters, tool requirements, sequence constraints
- **Review checklist** — Human-readable verification points
- **Approval record** — Who approved, when, what they verified

## What CAM Assist Is

- A translation layer between lutherie intent and CAM input
- A strategy documentation system
- A human review workflow
- A portable output format generator
- A lutherie-specific manufacturing assistant

## What CAM Assist Is Not

| Excluded Capability | Reason |
|---------------------|--------|
| G-code generator | G-code is machine-specific; strategy packages are portable |
| Machine controller | We produce input for CAM systems, not machine commands |
| Autonomous CAM AI | Human authority over manufacturing decisions is non-negotiable |
| Full plugin runtime | We export strategies, not extend CAM software |
| Generic CAM replacement | We assist lutherie workflows, not general manufacturing |

## System Boundaries

### Input Boundary

CAM Assist accepts:
- Instrument specification JSON (from Blueprint Reader)
- Lutherie operation requests
- Material specifications
- Tool library references

CAM Assist does not accept:
- Raw G-code for modification
- Machine-specific configurations
- Real-time sensor data
- Autonomous operation queues

### Output Boundary

CAM Assist produces:
- DXF files with operation geometry
- Strategy JSON with parameters
- Review checklists (Markdown)
- Approval workflow records

CAM Assist does not produce:
- G-code or NC files
- Machine control signals
- Direct toolpath data
- Post-processed output

## First Implementation Slice

### Strategy Export Assistant

**Scope:** Single bounded lutherie operations

**First operation:** Fret slot strategy

**Output format:**
```
strategy-package/
  geometry.dxf           # Slot positions and dimensions
  strategy.json          # Operation parameters
  review-checklist.md    # Human verification points
  approval.json          # Approval workflow state
```

### Why Fret Slots First

| Criterion | Fret Slot Suitability |
|-----------|----------------------|
| Lutherie-specific | Yes — core instrument operation |
| Bounded | Yes — discrete slot positions |
| Mathematically clear | Yes — scale length calculations are precise |
| High-value | Yes — accuracy directly affects playability |
| Reviewable | Yes — positions can be verified against spec |
| No full 3D CAM | Yes — 2D slot positions, uniform depth |

## Success Criteria for CAM-A0

- [ ] Repository has clear product identity
- [ ] Non-goals are explicit and documented
- [ ] First operation slice (fret slots) is defined
- [ ] Strategy export model is documented
- [ ] Human authority model is documented
- [ ] Adopted CAM capabilities are mapped
- [ ] Sample strategy package exists
