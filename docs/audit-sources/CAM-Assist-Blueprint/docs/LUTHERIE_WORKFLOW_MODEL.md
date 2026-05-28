# Lutherie Workflow Model

## Overview

Lutherie manufacturing follows a characteristic workflow that differs from general machining:

1. **Design drives everything** — Instrument specifications determine all manufacturing parameters
2. **Precision varies by operation** — Some operations require 0.001" tolerance, others 0.01"
3. **Sequence matters** — Operations must occur in specific order for dimensional stability
4. **Human judgment is continuous** — Material variations require real-time decisions
5. **Hybrid methods are normal** — CNC, hand tools, and templates combine in single builds

## Workflow Phases

### Phase 1: Specification

```
Design Intent → Instrument Specification → Operation Planning
```

The instrument specification defines:
- Scale length and fret positions
- Body outline and depth profiles
- Neck geometry and taper
- Hardware locations
- Material selections

### Phase 2: Operation Planning

```
Instrument Specification → Operation Sequence → Individual Operations
```

Operations are planned based on:
- Dimensional dependencies
- Material constraints
- Tool availability
- Precision requirements

### Phase 3: Strategy Development

```
Individual Operation → Strategy Package → Human Review
```

For each operation:
- Define geometry (what cuts where)
- Define parameters (speeds, feeds, depths)
- Define sequence (order within operation)
- Define verification points (what to check)

### Phase 4: Manufacturing

```
Approved Strategy → CAM Import → Machine Execution → Verification
```

CAM Assist scope ends at "Approved Strategy."

What happens after approval:
- Luthier imports strategy into their CAM system
- CAM system generates machine-specific toolpaths
- Machine executes under luthier supervision
- Luthier verifies against strategy checklist

## Operation Categories

### Category A: Precision Geometry

Operations where mathematical precision determines function.

| Operation | Typical Tolerance | CAM Assist Role |
|-----------|------------------|-----------------|
| Fret slots | ±0.002" | Position calculation, slot geometry |
| Intonation compensation | ±0.005" | Compensation calculation, saddle positions |
| Nut slot positions | ±0.003" | String spacing calculation |
| Bridge pin holes | ±0.005" | Position layout |
| Tuner holes | ±0.010" | Headstock drilling positions |

### Category B: Profile Geometry

Operations where smooth contours determine playability and aesthetics.

| Operation | Key Constraint | CAM Assist Role |
|-----------|----------------|-----------------|
| Neck carve | Ergonomic profile | Profile sections, blend guidance |
| Body contours | Arm/belly cuts | Contour boundaries, depth mapping |
| Headstock shape | Aesthetic outline | Perimeter geometry |
| Heel transition | Playability | Blend surface guidance |

### Category C: Pocket Operations

Material removal with defined boundaries.

| Operation | Key Constraint | CAM Assist Role |
|-----------|----------------|-----------------|
| Pickup routes | Hardware fit | Pocket boundaries, depth |
| Control cavity | Component fit | Pocket boundaries, depth |
| Truss rod channel | Hardware fit | Channel geometry |
| Neck pocket | Joint fit | Pocket geometry, depth steps |
| Bridge recess | Hardware fit | Pocket boundaries |

### Category D: Outline Operations

Perimeter cuts separating workpiece from stock.

| Operation | Key Constraint | CAM Assist Role |
|-----------|----------------|-----------------|
| Body cutout | Final outline | Perimeter geometry, tab positions |
| Headstock cutout | Final outline | Perimeter geometry |
| Peghead overlay | Trim to shape | Perimeter geometry |

## Workflow Integration Points

### Where CAM Assist Enters

```
                    ┌─────────────────┐
Instrument Spec ───→│   CAM Assist    │───→ Strategy Package
                    └─────────────────┘
                            ↓
                    Human Review & Approval
                            ↓
                    CAM System Import
                            ↓
                    Machine Execution
```

### What CAM Assist Receives

From upstream (Blueprint Reader or manual entry):
- Instrument type and variant
- Scale length and fret count
- Body dimensions and shape
- Neck specifications
- Hardware specifications
- Material specifications

### What CAM Assist Produces

To downstream (CAM system or manual layout):
- DXF geometry files
- Operation parameter JSON
- Human review checklists
- Approval workflow state

## Precision Classes

CAM Assist categorizes operations by precision class:

### Class I: Critical (±0.002")
- Fret slot positions
- Nut slot spacing
- Intonation compensation

### Class II: Structural (±0.005")
- Neck pocket fit
- Bridge placement
- Hardware mounting

### Class III: Ergonomic (±0.010")
- Neck profile
- Body contours
- Cutaway depth

### Class IV: Aesthetic (±0.020")
- Binding channels
- Purfling grooves
- Decorative inlays

## Material Considerations

Strategy packages include material-aware parameters:

| Material Class | Feed Adjustment | Speed Adjustment | Special Notes |
|---------------|-----------------|------------------|---------------|
| Softwood (spruce, cedar) | Base | Base | Grain tearout risk |
| Hardwood (maple, mahogany) | -20% | +10% | Heat buildup |
| Exotic (rosewood, ebony) | -30% | +15% | Dust extraction critical |
| Figured wood | -15% | Base | Grain direction varies |
| Laminate | -10% | +5% | Delamination at edges |
