# CAM Tooling and Stock Model

**Date:** 2026-05-07  
**Status:** FUTURE ABSTRACTION DEFINITION  
**Scope:** Defines future models for tools and stock — no implementation yet

---

## Purpose

This document defines the abstraction boundaries for tooling and stock models. The current system uses primitive numeric fields; this document specifies what a future structured model should include.

---

## Current State

### Tooling (Primitive)

Current tooling is numeric-only:

```python
# nut_slot_cam.py
tool_diameter_mm: float = Field(..., gt=0, description="Cutting tool diameter")
```

No structured tool model. No tool library. No material-aware feeds/speeds.

### Stock (Primitive)

Current stock is a single thickness:

```python
# nut_slot_cam.py
stock_thickness_mm: float = Field(..., gt=0, description="Thickness of nut blank")
```

No material type. No grain direction. No workholding model.

---

## Future Tool Model

### Tool Schema (Definition Only)

```typescript
interface Tool {
  // Identity
  id: string;
  name: string;
  manufacturer?: string;
  part_number?: string;
  
  // Geometry
  type: 'end_mill' | 'ball_end' | 'v_bit' | 'drill' | 'slot_cutter' | 'custom';
  diameter_mm: number;
  flute_length_mm: number;
  overall_length_mm: number;
  shank_diameter_mm: number;
  flute_count: number;
  helix_angle_deg?: number;
  
  // V-bit specific
  v_angle_deg?: number;
  tip_diameter_mm?: number;
  
  // Ball end specific
  ball_radius_mm?: number;
  
  // Material
  substrate: 'hss' | 'carbide' | 'cobalt' | 'ceramic';
  coating?: 'TiN' | 'TiAlN' | 'AlTiN' | 'ZrN' | 'diamond' | 'none';
  
  // Recommended parameters (per material)
  recommendations: ToolRecommendation[];
}

interface ToolRecommendation {
  material_class: 'softwood' | 'hardwood' | 'plywood' | 'mdf' | 'acrylic' | 'aluminum';
  surface_speed_m_min: number;
  chip_load_mm: number;
  max_doc_mm: number;  // depth of cut
  max_woc_mm: number;  // width of cut
}
```

### Tool Library (Not Implemented)

Future location:

```
data/tools/
├── index.json
├── end_mills/
│   ├── 3mm_2flute_carbide.json
│   └── 6mm_3flute_upcut.json
├── v_bits/
│   ├── 60deg_carbide.json
│   └── 90deg_hss.json
└── slot_cutters/
    └── nut_file_0.5mm.json
```

### Tool Validation Rules

| Check | Condition | Gate |
|-------|-----------|------|
| Tool fits slot | diameter ≤ slot_width | RED if fails |
| Flute length | flute_length > cut_depth | YELLOW if marginal |
| Tool reach | overall_length > stock_thickness + clearance | RED if fails |

---

## Future Stock Model

### Stock Schema (Definition Only)

```typescript
interface Stock {
  // Dimensions
  length_mm: number;
  width_mm: number;
  thickness_mm: number;
  
  // Material
  material_type: 'bone' | 'tusq' | 'brass' | 'graphite' | 'wood' | 'plastic';
  material_name?: string;  // e.g., "Bone", "Graph Tech TUSQ"
  
  // Properties
  density_kg_m3?: number;
  hardness_shore_d?: number;
  
  // Grain (for wood/bone)
  grain_direction?: 'parallel_to_length' | 'parallel_to_width' | 'end_grain' | 'n/a';
  
  // Workholding
  secured_by?: 'vise' | 'clamps' | 'tape' | 'vacuum' | 'fixture';
  overhang_mm?: number;
}
```

### Stock-Material Interactions

| Material | Considerations |
|----------|---------------|
| Bone | Brittle — slow feeds, sharp tools, avoid climb cutting |
| TUSQ | Synthetic — can use higher feeds than bone |
| Brass | Soft metal — use cutting fluid, avoid rubbing |
| Graphite | Abrasive — carbide only, dust extraction required |
| Wood | Check grain — end grain harder, cross-grain tears |

### Stock Validation Rules

| Check | Condition | Gate |
|-------|-----------|------|
| Cut depth | slot_depth < 0.8 × thickness | RED if fails |
| Overhang | overhang < 0.5 × clamped_length | YELLOW if marginal |
| Material hardness | hardness compatible with tool | YELLOW warning |

---

## Kerf and Clearance Model

### Kerf Definition

```
Kerf = tool_diameter (for slotting)
Kerf = tool_diameter × engagement_ratio (for pocketing)
```

### Clearance Model

| Clearance Type | Definition | Typical Value |
|----------------|------------|---------------|
| Slot clearance | slot_width - string_diameter | 0.05-0.10mm |
| Z clearance | safe_z - stock_top | 2.0-5.0mm |
| Side clearance | wall_offset - tool_radius | 0.1-0.5mm |

---

## Depth Constraints

### Maximum Depth Rules

| Constraint | Formula |
|------------|---------|
| Stock limit | depth ≤ 0.8 × stock_thickness |
| Flute limit | depth ≤ flute_length - 1mm |
| Rigidity limit | depth ≤ 3 × tool_diameter (rough) |

### Step-Down Strategy (Future)

For deep slots exceeding single-pass limits:

```
total_depth = 3.0mm
max_step_down = 1.5mm
passes = ceil(total_depth / max_step_down) = 2
pass_depths = [1.5mm, 3.0mm]
```

---

## Migration Strategy

### Phase 1: Structured Metadata (No Behavior Change)

Add optional structured fields alongside primitives:

```python
class NutSlotPreviewRequest(BaseModel):
    # Existing primitive fields
    tool_diameter_mm: float
    stock_thickness_mm: float
    
    # New optional structured fields
    tool_metadata: Optional[ToolMetadata] = None
    stock_metadata: Optional[StockMetadata] = None
```

### Phase 2: Tool Library Integration

- Create tool library JSON files
- Add tool selection endpoint
- Map tool IDs to parameters

### Phase 3: Material-Aware Feeds/Speeds

- Add material class to stock
- Lookup recommended parameters from tool library
- Apply adjustments based on material

### Phase 4: Validation Enhancement

- Check tool vs material compatibility
- Validate kerf vs slot width
- Check depth constraints

---

## What This Document Does NOT Define

- Actual tool library content
- Feeds/speeds engine implementation
- Chip load calculation
- Heat modeling
- Tool wear tracking
- Automatic tool selection

---

## Cross-Reference

| Document | Relevance |
|----------|-----------|
| `CAM_MACHINE_READINESS_PLAN.md` | Machine limits affect tool parameters |
| `CAM_EXPORT_GOVERNANCE_POLICY.md` | Tool validation before export |
| `nut_slot_calc.py` | Existing slot width calculations |

---

*Model defined: 2026-05-07*
