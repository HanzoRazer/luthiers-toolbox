# ADR-001: Fields and Policy Ownership

## Status
Accepted

## Date
2025-12-28

## Context

The Luthier's ToolBox provides design, geometry, and CAM capabilities for
instrument building. It needs to interpret measurement data and produce
actionable manufacturing guidance.

The mesh pipeline document identified a key innovation: **coupling grain fields,
brace graphs, and thickness maps with mesh healing/retopology to produce
CAM policy constraints.** Standard mesh tools don't do this.

We need to clearly define what ToolBox owns vs. what comes from tap_tone_pi.

## Decision

**ToolBox owns all interpretation, coupling, and policy generation.**

### What ToolBox Owns:

1. **Field Modules** (`services/api/app/fields/`)
   - `grain_field/`: Interprets grain data → runout zones, checking risk, CAM constraints
   - `brace_graph/`: Interprets brace topology → intersection zones, scallop areas, no-cut zones
   - `thickness_map/`: Interprets MOE data → voicing zones, compliance, thickness constraints

2. **CAM Policy** (`services/api/app/cam/policy/`)
   - Per-region constraints (stepdown, stepover, feed, tool limits)
   - No-cut zone definitions
   - Cut direction rules (climb vs. conventional)
   - Dwell and coolant policies

3. **QA Core** (`contracts/qa_core.schema.json`)
   - Mesh healing status
   - Thickness zone compliance
   - Grain confidence scores
   - Brace graph integrity
   - Retopo metrics

4. **Coupling Logic**
   - The novel piece: combining grain + brace + thickness → policy caps
   - This is what standard auto-retopo tools lack

### What ToolBox Expects from Analyzer:

| Artifact | Contains | Does NOT Contain |
|----------|----------|------------------|
| tap_peaks.json | Peak frequencies, amplitudes | Recommendations |
| moe_result.json | MOE, EI, deflection data | Design advice |
| manifest.json | Provenance, hashes | Policy constraints |

### Schema Contract:

ToolBox schemas in `contracts/`:
- `qa_core.schema.json` - Quality assessment coupling all fields
- `cam_policy.schema.json` - Manufacturing constraints

## Consequences

### Positive:
- Clear ownership of interpretation logic
- Novel coupling is explicit and documented
- Policy generation is auditable and versioned
- Can evolve fields independently

### Negative:
- More complex than monolithic approach
- Requires schema coordination with tap_tone_pi

### Neutral:
- Field modules are initially stubs; will evolve with use

## The Novel Coupling

Standard auto-retopo (Instant Meshes, QuadRemesher, ZRemesher) produces:
- Clean quad topology
- Optional UV preservation
- Polycount targeting

**They do NOT:**
- Incorporate wood grain field orientation
- Respect brace graph structural constraints
- Output per-region CAM policy caps

**ToolBox adds:**
```
[Grain Field] ──┐
                ├──► [Healing/Retopo] ──► [CAM Policy Caps]
[Brace Graph] ──┤
                │
[Thickness Map]─┘
```

This coupling is the differentiator.

## Enforcement

1. Field modules must not embed audio capture or raw measurement code
2. All policy outputs must validate against `cam_policy.schema.json`
3. Provenance tracking required for all ingested analyzer artifacts

## Related
- [FIELDS_AND_POLICY_BOUNDARY.md](../FIELDS_AND_POLICY_BOUNDARY.md)
- tap_tone_pi ADR-001: Measurement-Only Boundary
