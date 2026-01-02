# Fields and Policy Boundary

> This document defines what Luthier's ToolBox owns (fields, interpretation, CAM policy)
> and what it expects from the Analyzer (facts + provenance).

## Scope: ToolBox is the **Interpretation + Policy Layer**

This repo owns:
- **Field modules** that interpret measurement data
- **Coupling logic** that combines fields → geometry → CAM constraints
- **Policy schemas** that define manufacturing limits and no-cut zones

---

## What ToolBox Owns

### 1. Field Modules (`services/api/app/fields/`)

| Field | Purpose | Ingests From |
|-------|---------|--------------|
| `grain_field/` | Grain angle maps, runout detection, checking zones | tap_tone_pi provenance imports |
| `brace_graph/` | Brace layout topology, scallop zones, structural analysis | Internal geometry |
| `thickness_map/` | Thickness gradients, voicing zones, tap-tuned deltas | MOE results + geometry |

These modules **interpret** facts to produce **design-relevant outputs**.

### 2. CAM Policy (`services/api/app/cam/policy/`)

Defines per-region manufacturing constraints:
- Stepdown/stepover caps
- Minimum tool diameter
- Feed rate limits
- No-cut zones (critical grain, braces, sound ports)
- Climb vs. conventional routing zones

### 3. QA Core (`contracts/qa_core.schema.json`)

Couples multiple inputs into a quality assessment:
- Mesh healing status
- Thickness zone compliance
- Grain confidence scores
- Brace graph integrity
- Retopo metrics

### 4. Advisory/Recommendation Logic

ToolBox **can** output:
- "Reduce feed rate in this zone due to grain runout"
- "Add dwell at position X for chip clearing"
- "This brace intersection requires climb cut"

---

## What ToolBox Expects from Analyzer

| Artifact | Schema | Contains |
|----------|--------|----------|
| `tap_peaks.json` | tap_peaks.schema.json | Peak frequencies, amplitudes (facts) |
| `moe_result.json` | moe_result.schema.json | MOE, EI, deflection data (facts) |
| `manifest.json` | measurement_manifest.schema.json | Provenance, hashes, device info |

**Contract:** Analyzer artifacts are **facts only** with provenance. ToolBox adds interpretation.

---

## Coupling: The Novel Piece

The key innovation (from Mesh_Pipeline doc) is coupling:

```
[Grain Field] ──┐
                ├──► [Healing/Retopo] ──► [CAM Policy Caps]
[Brace Graph] ──┤
                │
[Thickness Map]─┘
```

Standard auto-retopo tools do NOT incorporate:
- Wood grain field orientation
- Brace graph structural constraints
- Thickness-driven policy caps

**This coupling is ToolBox-native.**

---

## Integration Flow

```
tap_tone_pi                         luthiers-toolbox
───────────                         ────────────────
  │                                       │
  ├─ Record tap ────────────────────────► │
  │                                       ├─ Ingest manifest
  ├─ Compute MOE ───────────────────────► │
  │                                       ├─ Populate grain_field
  └─ Export manifest ───────────────────► │
                                          ├─ Couple with brace_graph
                                          │
                                          ├─ Generate thickness_map
                                          │
                                          ├─ Run healing/retopo
                                          │
                                          └─ Export CAM policy
```

---

## CI Guardrail

The CI pipeline should:

1. **Allow** imports from `fields/*`, `cam/policy/*`
2. **Allow** ingestion of Analyzer manifests (via provenance module)
3. **Reject** embedding of audio capture / raw measurement code
4. **Validate** all policy outputs against `cam_policy.schema.json`

---

## Version

Schema version: `1.0.0`
Boundary policy version: `2025-12-28`
