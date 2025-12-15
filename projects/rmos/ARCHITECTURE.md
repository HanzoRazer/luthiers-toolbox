# 🏗️ RTL Architecture Documentation

**Version:** 0.1.0-alpha  
**Last Updated:** November 20, 2025  
**Status:** Design Complete, Implementation Pending

---

## 📑 Table of Contents

1. [System Overview](#system-overview)
2. [5-Domain Architecture](#5-domain-architecture)
3. [Core Data Structures](#core-data-structures)
4. [Strip Recipe System](#strip-recipe-system)
5. [Multi-Ring Circle Geometry](#multi-ring-circle-geometry)
6. [Manufacturing Planner Logic](#manufacturing-planner-logic)
7. [Risk Analysis Engine](#risk-analysis-engine)
8. [Pattern → CAM Mapping](#pattern--cam-mapping)
9. [JobLog Integration](#joblog-integration)
10. [Frontend Architecture](#frontend-architecture)
11. [Backend Architecture](#backend-architecture)
12. [Data Flow Diagrams](#data-flow-diagrams)
13. [Integration Points](#integration-points)
14. [Design Decisions](#design-decisions)

---

## 1. System Overview

### **Mission**
Enable luthiers to design arbitrarily complex rosette patterns and automatically generate CAM-ready toolpaths with manufacturing intelligence, safety guardrails, and production traceability.

### **Problem Space**
Rosette inlays require:
- **Ultra-thin strips** (0.3-0.8mm "thinner than toothpicks")
- **Angled slicing** to achieve desired geometries
- **Extreme precision** (±0.05mm tolerance)
- **Material planning** (minimize waste, prevent shortages)
- **Safety validation** (prevent tool deflection, strip breakage)

### **RMOS Solution**
Complete factory subsystem spanning:
- Creative pattern design (visual editor)
- CAM operation generation (G2/G3 arcs, linear moves)
- Manufacturing planning (material requirements)
- Production logging (yield tracking, analytics)
- Future: AI pattern generation, batch scheduling

---

## 2. 5-Domain Architecture

### **Domain 1: Creative Layer** 🎨

**Purpose:** Enable luthiers to design rosette patterns visually without CAM knowledge

**Components:**
- `RosetteTemplateLab.vue` - Visual pattern editor
- `RosettePatternStore.ts` - Pinia store for pattern management
- `RosettePattern` schema - Data model

**Key Features:**
- Concentric ring bands (arbitrary count)
- Per-ring strip family assignment
- Tile length overrides
- Slice angle controls (for angled tiles)
- Color hints for preview
- Drag-and-drop ring reordering

**User Workflow:**
```
1. Create new pattern
2. Add ring bands (innermost → outermost)
3. Assign strip families (wood species)
4. Set tile dimensions per ring
5. Preview colored design
6. Save to Pattern Library
```

**Data Flow:**
```
User Input
  ↓
RosetteTemplateLab
  ↓ emits pattern-changed
RosettePatternStore (Pinia)
  ↓ persists
Backend API (POST /rosette-patterns)
  ↓ saves
Database (SQLite)
```

---

### **Domain 2: CAM Layer** ⚙️

**Purpose:** Convert patterns to executable CNC operations with safety validation

**Components:**
- `SawSliceBatchOpCircle` schema - Multi-ring circular saw operation
- `SawSliceBatchOpLine` schema - Parallel line slicing
- `saw_gcode.py` - G-code generation (G2/G3 arcs + linear)
- `saw_risk.py` - Risk analysis engine

**Operation Types:**

#### **Circle Mode (Multi-Ring)**
Generates concentric circular cuts for rosette rings:
```typescript
{
  op_type: "saw_slice_batch",
  geometry_source: "circle_param",
  base_radius_mm: 20,        // Innermost ring
  num_rings: 5,
  radial_step_mm: 2.5,       // Ring spacing
  slice_thickness_mm: 0.8,
  tool_id: "thin_kerf_blade_001"
}
```

**G-Code Output:**
```gcode
G21               ; mm units
G90               ; absolute positioning
G17               ; XY plane
G0 Z5.0           ; safe height
G0 X20.0 Y0.0     ; start ring 1
G1 Z-0.8 F300     ; plunge
G2 X20.0 Y0.0 I-20.0 J0.0 F1200  ; full circle
G0 Z5.0           ; retract
G0 X22.5 Y0.0     ; start ring 2
G1 Z-0.8 F300
G2 X22.5 Y0.0 I-22.5 J0.0 F1200
; ... repeat for remaining rings
M30
```

#### **Line Mode (Parallel Strips)**
Generates parallel linear cuts for strip slicing:
```typescript
{
  op_type: "saw_slice_batch",
  geometry_source: "line_param",
  x_start_mm: 0,
  y_start_mm: 0,
  length_mm: 300,
  angle_deg: 0,           // or 30 for angled
  num_slices: 10,
  slice_spacing_mm: 6,
  slice_thickness_mm: 0.8
}
```

**Risk Analysis:**
Every operation analyzed for:
- **Rim speed** (max RPM for outer rings)
- **Gantry span** (max reach for large radii)
- **Deflection** (thin blades + long cuts)
- **Kerf width** (blade thickness vs desired strip width)

**Risk Grades:**
- 🟢 **GREEN**: Safe, proceed
- 🟡 **YELLOW**: Caution, review parameters
- 🔴 **RED**: Unsafe, requires modification

---

### **Domain 3: Manufacturing Planning Layer** 📊

**Purpose:** Calculate material requirements and optimize production

**Components:**
- `planner.py` - Manufacturing calculator
- `strip_family_optimizer.py` - Group by species
- `ManufacturingPlanPanel.vue` - UI for plan review

**Calculation Flow:**

#### **Step 1: Ring Requirements**
For each ring band:
```python
circumference = 2 * π * radius
tiles_per_ring = floor(circumference / tile_length)
adjustment_factor = tiles_per_ring / (circumference / tile_length)
adjusted_tile_length = tile_length * adjustment_factor
```

**Why Adjust?** Integer tile count must fit exact circumference (no gaps/overlaps)

#### **Step 2: Strip-Family Grouping**
Aggregate tiles by strip family:
```python
strip_plans = {}
for ring in rings:
    family_id = ring.strip_family_id
    if family_id not in strip_plans:
        strip_plans[family_id] = {
            tiles_needed: 0,
            strip_length_m: 0
        }
    strip_plans[family_id].tiles_needed += ring.tiles_per_ring
    strip_plans[family_id].strip_length_m += ring.tiles_per_ring * ring.tile_length / 1000
```

#### **Step 3: Stick Count Derivation**
```python
strip_cross_section = (width_mm, height_mm)  # from StripRecipe
usable_length_per_stick = stick_length - safety_margin
sticks_needed = ceil(strip_length_m / usable_length_per_stick) * scrap_factor
```

**Scrap Factor:** Typically 1.10-1.20 (10-20% waste)

#### **Step 4: Multi-Family Optimization**
For patterns using same family in multiple rings:
```python
# Sum all tiles for same family
total_tiles = sum(ring.tiles_per_ring for ring in rings if ring.family_id == family_id)

# Handle tile length conflicts
if multiple tile lengths for same family:
    use weighted_average(tile_lengths, counts)
    OR flag conflict for user resolution
```

**Example Output:**
```
Pattern: Celtic Knot 12-Ring
Guitars: 10
Total Tiles: 4,800

Strip Plans:
  Ebony Black:
    Tiles: 1,200
    Strip Length: 3.6 m
    Sticks: 5 (600mm each @ 1.15 scrap)
  
  Maple White:
    Tiles: 2,400
    Strip Length: 7.2 m
    Sticks: 10 (600mm each @ 1.15 scrap)
  
  Walnut Brown:
    Tiles: 1,200
    Strip Length: 3.6 m
    Sticks: 5 (600mm each @ 1.15 scrap)
```

---

### **Domain 4: Production/Logging Layer** 📝

**Purpose:** Track every operation with full context for analytics and optimization

**Components:**
- `JobLogEntry` schema - Unified job model
- `joblog.py` router - CRUD API
- `JobLogMiniList.vue` - History viewer

**Job Types:**

#### **Type 1: `saw_slice_batch`**
Actual CNC cuts (circle + line modes):
```typescript
{
  job_id: "job_20251120_143022",
  job_type: "saw_slice_batch",
  op_data: {
    geometry_source: "circle_param",
    base_radius_mm: 20,
    num_rings: 5,
    radial_step_mm: 2.5,
    slice_thickness_mm: 0.8
  },
  tool_id: "thin_kerf_blade_001",
  material: "ebony",
  num_slices: 5,
  total_length_m: 0.628,       // Σ(2πr) for all rings
  risk_summary: {
    grade: "YELLOW",
    rim_speed_rpm: 8500,
    gantry_span_mm: 250,
    deflection_mm: 0.03
  },
  yield_predicted: 96.0,
  yield_actual: 94.5,           // After cutting
  best_slice_index: 3,
  operator_notes: "Ring 5 had slight wobble, increased feed 10%",
  created_at: "2025-11-20T14:30:00Z"
}
```

#### **Type 2: `rosette_plan`**
Pre-production manufacturing plans:
```typescript
{
  job_id: "job_20251120_140500",
  job_type: "rosette_plan",
  plan_pattern_id: "pattern_uuid",
  plan_guitars: 10,
  plan_total_tiles: 4800,
  strip_plans: [
    {
      strip_family_id: "ebony_black",
      tiles_needed: 1200,
      strip_length_m: 3.6,
      sticks_needed: 5,
      scrap_factor: 1.15
    },
    // ... more families
  ],
  created_at: "2025-11-20T14:05:00Z"
}
```

**Analytics Queries:**
```sql
-- Find best-performing blade
SELECT tool_id, AVG(yield_actual) as avg_yield
FROM joblog
WHERE job_type = 'saw_slice_batch'
GROUP BY tool_id
ORDER BY avg_yield DESC;

-- Material usage by family
SELECT material, SUM(num_slices) as total_cuts
FROM joblog
WHERE job_type = 'saw_slice_batch'
GROUP BY material;

-- Risk grade distribution
SELECT risk_summary->>'grade' as grade, COUNT(*)
FROM joblog
WHERE job_type = 'saw_slice_batch'
GROUP BY grade;
```

---

### **Domain 5: Future Engineering Layer** 🚀

**Purpose:** Advanced physics modeling, AI, and optimization (roadmap features)

**Planned Components:**

#### **Kerf + Deflection Physics**
```python
def calculate_kerf_deflection(blade_thickness, cut_length, material_hardness):
    kerf_width = blade_thickness * (1 + deflection_coefficient)
    deflection_mm = (cut_length ** 2) * material_hardness / blade_rigidity
    return kerf_width, deflection_mm
```

#### **Arbor Hardware Jig Library**
```typescript
{
  jig_id: "angle_fixture_30deg",
  jig_type: "angle_fixture",
  max_stock_size: {w: 100, h: 50},
  angle_range: [15, 45],
  compatible_blades: ["thin_kerf_001", "ultra_thin_002"]
}
```

#### **AI Pattern Generator**
```python
def suggest_patterns(constraints):
    # Genetic algorithm or neural net
    # Input: ring count, symmetry, color families
    # Output: scored pattern candidates
    pass
```

#### **Batch Scheduling**
```python
def optimize_batch(patterns, material_inventory, deadline):
    # Linear programming or heuristic scheduler
    # Minimize material waste + setup time
    pass
```

---

## 3. Core Data Structures

### **RosettePattern**
```typescript
interface RosettePattern {
  pattern_id: string;           // uuid
  name: string;
  ring_bands: RosetteRingBand[];
  created_at: string;           // ISO 8601
  updated_at: string;
}
```

**Validation Rules:**
- `name` must be 3-50 characters
- `ring_bands` must have at least 1 ring
- Ring indices must be sequential (0, 1, 2, ...)
- No duplicate strip families in adjacent rings (optional rule)

---

### **RosetteRingBand**
```typescript
interface RosetteRingBand {
  id: string;                   // uuid
  index: number;                // 0 = innermost
  strip_family_id: string;      // "ebony_black", "maple_white"
  color_hint: string;           // "#1a1a1a" for preview
  tile_length_override_mm?: number;  // null = use default
  slice_angle_deg?: number;     // 0-45° for angled tiles
}
```

**Defaults:**
- `tile_length_override_mm`: Pattern-level default (e.g., 3mm)
- `slice_angle_deg`: 0° (straight cuts)

**Constraints:**
- `index` >= 0
- `slice_angle_deg` in [0, 45]
- `tile_length_override_mm` > 0 if present

---

### **SawSliceBatchOpCircle**
```typescript
interface SawSliceBatchOpCircle {
  op_type: "saw_slice_batch";
  geometry_source: "circle_param";
  base_radius_mm: number;       // Innermost ring
  num_rings: number;
  radial_step_mm: number;       // Spacing between rings
  slice_thickness_mm: number;
  tool_id: string;
  material: string;
  workholding: string;          // "vacuum", "tape", "clamps"
  passes: number;               // Usually 1 for saw
}
```

**G-Code Generation:**
```python
def generate_circle_gcode(op: SawSliceBatchOpCircle):
    gcode = ["G21", "G90", "G17"]  # mm, absolute, XY plane
    
    for ring_idx in range(op.num_rings):
        radius = op.base_radius_mm + (ring_idx * op.radial_step_mm)
        
        # Position at start
        gcode.append(f"G0 X{radius:.4f} Y0.0000")
        
        # Plunge
        gcode.append(f"G1 Z{-op.slice_thickness_mm:.4f} F{plunge_feed}")
        
        # Full circle (G2 = CW, I/J = center offset)
        gcode.append(f"G2 X{radius:.4f} Y0.0000 I{-radius:.4f} J0.0000 F{cut_feed}")
        
        # Retract
        gcode.append("G0 Z5.0000")
    
    gcode.append("M30")
    return "\n".join(gcode)
```

---

### **StripRecipe** (Future)
```typescript
interface StripRecipe {
  desired_cross_section: {
    width: number;              // Final strip width (mm)
    height: number;             // Final strip height (mm)
  };
  slice_angle_deg: number;      // Rotation angle (0-45°)
  slice_thickness_mm: number;   // Saw blade pass thickness
  source_stick_size: {
    w: number;                  // Stick width (mm)
    h: number;                  // Stick height (mm)
    l: number;                  // Stick length (mm)
  };
  jig_type: "angle_fixture" | "carrier_block";
  safety_checks: {
    min_strip_width: number;    // Fail if < 0.4mm
    requires_carrier: boolean;  // Use sacrificial backing
    blade_kerf_ratio: number;   // Kerf / strip width
    risk_grade: "GREEN" | "YELLOW" | "RED";
  };
}
```

**Example Calculation:**
```
Input:
  Desired rhombus tile: 0.5mm × 3mm
  Slice angle: 30°

Derived:
  Source stick: 6mm × 6mm × 300mm
  Jig: angle_fixture
  Kerf ratio: 0.2mm / 0.5mm = 0.4 (YELLOW)
  Carrier required: Yes (strip too thin)
```

---

## 4. Strip Recipe System

### **Problem: "Thinner Than a Toothpick"**

Luthiers create tiles as thin as 0.3-0.8mm by:
1. Rotating stock at angle (10-45°)
2. Slicing parallel to rotated plane
3. Resulting strip is thinner than source stick width

**Traditional Approach:** Trial and error (wasteful)

**RMOS Approach:** Geometric calculation

---

### **Algorithm: Derive Stick Dimensions**

Given desired tile cross-section (width × height) and slice angle:

```python
def derive_strip_recipe(
    desired_width: float,     # mm
    desired_height: float,    # mm
    slice_angle_deg: float    # 0-45°
) -> StripRecipe:
    angle_rad = math.radians(slice_angle_deg)
    
    # For angled slicing:
    # actual_width = stick_width * cos(angle)
    # Solve for stick_width:
    stick_width = desired_width / math.cos(angle_rad)
    
    # Height unchanged (perpendicular to slice)
    stick_height = desired_height
    
    # Standard stick length (typically 300-600mm)
    stick_length = 300
    
    # Select jig based on angle
    if slice_angle_deg == 0:
        jig_type = "straight_fence"
    elif slice_angle_deg <= 15:
        jig_type = "angle_fixture"
    else:
        jig_type = "angle_fixture_with_carrier"
    
    # Safety checks
    min_safe_width = 0.4  # mm
    requires_carrier = (desired_width < 0.6)
    kerf_width = 0.2      # typical thin-kerf blade
    kerf_ratio = kerf_width / desired_width
    
    # Risk grading
    if desired_width < 0.4:
        risk_grade = "RED"
    elif kerf_ratio > 0.4 or desired_width < 0.6:
        risk_grade = "YELLOW"
    else:
        risk_grade = "GREEN"
    
    return StripRecipe(
        desired_cross_section=(desired_width, desired_height),
        slice_angle_deg=slice_angle_deg,
        slice_thickness_mm=desired_width,  # one slice = one tile width
        source_stick_size=(stick_width, stick_height, stick_length),
        jig_type=jig_type,
        safety_checks={
            min_strip_width: min_safe_width,
            requires_carrier: requires_carrier,
            blade_kerf_ratio: kerf_ratio,
            risk_grade: risk_grade
        }
    )
```

**Example:**
```python
recipe = derive_strip_recipe(
    desired_width=0.5,    # 0.5mm wide strip
    desired_height=3.0,   # 3mm tall strip
    slice_angle_deg=30    # 30° rotation
)

# Result:
# stick_width = 0.5 / cos(30°) = 0.577mm
# jig_type = "angle_fixture_with_carrier"
# risk_grade = "YELLOW" (kerf ratio 0.4)
```

---

## 5. Multi-Ring Circle Geometry

### **Objective**
Generate concentric circular cuts with:
- Precise radial spacing
- Constant slice thickness
- Optimized toolpath (minimize air time)

### **Parameters**
- `base_radius_mm`: Innermost ring radius
- `num_rings`: Number of concentric rings
- `radial_step_mm`: Distance between rings
- `slice_thickness_mm`: Cut depth per pass

### **Geometry Calculation**

```python
def generate_ring_radii(base_radius, num_rings, radial_step):
    radii = []
    for i in range(num_rings):
        radius = base_radius + (i * radial_step)
        radii.append(radius)
    return radii

# Example:
# base_radius_mm = 20
# num_rings = 5
# radial_step_mm = 2.5
# → [20.0, 22.5, 25.0, 27.5, 30.0]
```

### **G-Code Toolpath**

**Option 1: Retract Between Rings** (Simple)
```gcode
; Ring 1
G0 X20.0 Y0.0
G1 Z-0.8 F300
G2 X20.0 Y0.0 I-20.0 J0.0 F1200
G0 Z5.0           ; Retract

; Ring 2
G0 X22.5 Y0.0
G1 Z-0.8 F300
G2 X22.5 Y0.0 I-22.5 J0.0 F1200
G0 Z5.0
```

**Option 2: Spiral Link** (Optimized, future)
Connect rings without retracting:
```gcode
; Ring 1
G0 X20.0 Y0.0
G1 Z-0.8 F300
G2 X20.0 Y0.0 I-20.0 J0.0 F1200  ; Full circle

; Spiral to Ring 2 (no retract)
G1 X22.5 F1200                    ; Move outward
G2 X22.5 Y0.0 I-22.5 J0.0 F1200  ; Ring 2
```

**Trade-offs:**
- Retract: Easier, more reliable, slightly slower
- Spiral: Faster, better surface finish, requires careful tuning

---

## 6. Manufacturing Planner Logic

### **Input**
- `RosettePattern` with N ring bands
- Per-ring: strip_family_id, tile_length (or override)
- Guitars to build (e.g., 10)

### **Output**
- Per strip family:
  - Total tiles needed
  - Total strip length (meters)
  - Sticks required (given stick dimensions)

### **Algorithm**

```python
def plan_manufacturing(pattern: RosettePattern, guitars: int, base_radius: float, radial_step: float):
    strip_plans = {}
    
    for ring in pattern.ring_bands:
        # Calculate ring radius
        radius = base_radius + (ring.index * radial_step)
        
        # Circumference
        circumference = 2 * math.pi * radius
        
        # Tile length (use override or default)
        tile_length = ring.tile_length_override_mm or DEFAULT_TILE_LENGTH
        
        # Tiles per ring (integer count)
        tiles_per_ring = math.floor(circumference / tile_length)
        
        # Adjust tile length to fit exact circumference
        adjusted_tile_length = circumference / tiles_per_ring
        
        # Total tiles for N guitars
        total_tiles = tiles_per_ring * guitars
        
        # Aggregate by strip family
        family_id = ring.strip_family_id
        if family_id not in strip_plans:
            strip_plans[family_id] = {
                "tiles_needed": 0,
                "strip_length_m": 0.0
            }
        
        strip_plans[family_id]["tiles_needed"] += total_tiles
        strip_plans[family_id]["strip_length_m"] += (total_tiles * adjusted_tile_length) / 1000.0
    
    # Derive stick counts
    for family_id, plan in strip_plans.items():
        stick_length_m = 0.6  # 600mm standard
        scrap_factor = 1.15   # 15% waste
        
        sticks_needed = math.ceil(plan["strip_length_m"] / stick_length_m) * scrap_factor
        plan["sticks_needed"] = int(sticks_needed)
    
    return strip_plans
```

**Example Output:**
```json
{
  "ebony_black": {
    "tiles_needed": 1200,
    "strip_length_m": 3.6,
    "sticks_needed": 7
  },
  "maple_white": {
    "tiles_needed": 2400,
    "strip_length_m": 7.2,
    "sticks_needed": 14
  }
}
```

---

## 7. Risk Analysis Engine

### **Purpose**
Flag unsafe operations before execution to prevent:
- Tool breakage (RPM too high for outer rings)
- Machine damage (gantry overreach)
- Poor quality (excessive deflection)

### **Risk Factors**

#### **1. Rim Speed (RPM Limit)**
```python
def check_rim_speed(radius_mm: float, spindle_rpm: int, max_rim_speed_mps: float) -> str:
    circumference_m = 2 * math.pi * (radius_mm / 1000)
    rim_speed_mps = (circumference_m * spindle_rpm) / 60
    
    if rim_speed_mps > max_rim_speed_mps:
        return "RED"
    elif rim_speed_mps > max_rim_speed_mps * 0.8:
        return "YELLOW"
    else:
        return "GREEN"
```

**Example:**
- Radius: 100mm (outer ring)
- RPM: 10,000
- Max safe rim speed: 50 m/s
- Actual: 104.7 m/s → **RED**

#### **2. Gantry Span (Machine Reach)**
```python
def check_gantry_span(radius_mm: float, max_reach_mm: float) -> str:
    required_reach = radius_mm * 2  # Diameter
    
    if required_reach > max_reach_mm:
        return "RED"
    elif required_reach > max_reach_mm * 0.9:
        return "YELLOW"
    else:
        return "GREEN"
```

#### **3. Deflection (Thin Blade + Long Cut)**
```python
def check_deflection(cut_length_mm: float, blade_thickness_mm: float, material_hardness: float) -> str:
    deflection_mm = (cut_length_mm ** 2) * material_hardness / (blade_thickness_mm ** 3)
    
    if deflection_mm > 0.5:
        return "RED"
    elif deflection_mm > 0.2:
        return "YELLOW"
    else:
        return "GREEN"
```

### **Overall Risk Grade**
```python
def calculate_overall_risk(rim_grade, span_grade, deflection_grade):
    if "RED" in [rim_grade, span_grade, deflection_grade]:
        return "RED"
    elif "YELLOW" in [rim_grade, span_grade, deflection_grade]:
        return "YELLOW"
    else:
        return "GREEN"
```

---

## 8. Pattern → CAM Mapping

### **Purpose**
Convert `RosettePattern` to `SawSliceBatchOpCircle` automatically

### **Algorithm**

```python
def rosette_pattern_to_batch_op_circle(
    pattern: RosettePattern,
    base_radius_mm: float,
    radial_step_mm: float,
    default_slice_thickness_mm: float,
    tool_id: str,
    material: str
) -> SawSliceBatchOpCircle:
    
    num_rings = len(pattern.ring_bands)
    
    return SawSliceBatchOpCircle(
        op_type="saw_slice_batch",
        geometry_source="circle_param",
        base_radius_mm=base_radius_mm,
        num_rings=num_rings,
        radial_step_mm=radial_step_mm,
        slice_thickness_mm=default_slice_thickness_mm,
        tool_id=tool_id,
        material=material,
        workholding="vacuum",
        passes=1
    )
```

**Usage in PipelineLab:**
```typescript
// User selects pattern in Rosette Manufacturing OS
const pattern = await rosettePatternStore.getById(pattern_id)

// Derive saw operation
const sawOp = rosettePatternToBatchOpCircle(
  pattern,
  20,     // base_radius_mm
  2.5,    // radial_step_mm
  0.8,    // slice_thickness_mm
  "thin_kerf_blade_001",
  "ebony"
)

// Add to pipeline
pipelineStore.addNode({
  id: "saw_multi_ring",
  type: "saw_slice_batch",
  operation: sawOp
})
```

---

## 9. JobLog Integration

### **Unified Job Model**
```python
class JobLogEntry(BaseModel):
    job_id: str
    job_type: str  # "saw_slice_batch" or "rosette_plan"
    
    # Common fields
    created_at: str
    operator_notes: Optional[str]
    
    # Saw batch fields
    op_data: Optional[dict]
    tool_id: Optional[str]
    material: Optional[str]
    num_slices: Optional[int]
    total_length_m: Optional[float]
    risk_summary: Optional[dict]
    yield_predicted: Optional[float]
    yield_actual: Optional[float]
    best_slice_index: Optional[int]
    
    # Planning fields
    plan_pattern_id: Optional[str]
    plan_guitars: Optional[int]
    plan_total_tiles: Optional[int]
    strip_plans: Optional[List[dict]]
```

### **Write Operations**

**After Saw Operation:**
```python
@router.post("/saw-ops/slice/execute")
async def execute_saw_slice(body: SawSliceBatchOpCircle):
    # Generate G-code
    gcode = generate_circle_gcode(body)
    
    # Calculate risk
    risk = analyze_risk(body)
    
    # Execute on machine
    result = machine.execute(gcode)
    
    # Write to JobLog
    job_entry = JobLogEntry(
        job_id=generate_job_id(),
        job_type="saw_slice_batch",
        op_data=body.dict(),
        tool_id=body.tool_id,
        material=body.material,
        num_slices=body.num_rings,
        total_length_m=sum(2 * math.pi * r for r in radii) / 1000,
        risk_summary=risk,
        yield_predicted=96.0,
        created_at=now()
    )
    
    await joblog_db.insert(job_entry)
    return {"job_id": job_entry.job_id}
```

**After Manufacturing Plan:**
```python
@router.post("/rosette-plans")
async def create_rosette_plan(body: RosettePlanIn):
    # Calculate strip requirements
    strip_plans = plan_manufacturing(body.pattern, body.guitars, ...)
    
    # Write to JobLog
    job_entry = JobLogEntry(
        job_id=generate_job_id(),
        job_type="rosette_plan",
        plan_pattern_id=body.pattern.pattern_id,
        plan_guitars=body.guitars,
        plan_total_tiles=sum(p["tiles_needed"] for p in strip_plans.values()),
        strip_plans=strip_plans,
        created_at=now()
    )
    
    await joblog_db.insert(job_entry)
    return {"job_id": job_entry.job_id}
```

---

## 10. Frontend Architecture

### **Component Hierarchy**

```
App.vue
├── MainNav.vue
└── RouterView
    ├── PipelineLab.vue
    │   ├── PipelineCanvas.vue
    │   ├── NodeInspector.vue
    │   └── OpPanels/
    │       ├── RosetteMultiRingOpPanel.vue  ← RMOS
    │       └── ...other panels
    │
    ├── RosetteTemplateLab.vue              ← RMOS
    │   ├── RingBandEditor.vue
    │   ├── PatternPreview.vue
    │   └── ColorPicker.vue
    │
    ├── ManufacturingPlanPanel.vue          ← RMOS
    │   ├── StripPlanTable.vue
    │   └── MaterialSummary.vue
    │
    └── JobLogView.vue
        └── JobLogMiniList.vue              ← RMOS enhanced
```

### **State Management (Pinia)**

```typescript
// rosettePatternStore.ts
export const useRosettePatternStore = defineStore('rosettePattern', () => {
  const patterns = ref<RosettePattern[]>([])
  const activePatternId = ref<string | null>(null)
  
  async function fetchPatterns() {
    const res = await fetch('/api/rosette-patterns')
    patterns.value = await res.json()
  }
  
  async function createPattern(pattern: RosettePattern) {
    const res = await fetch('/api/rosette-patterns', {
      method: 'POST',
      body: JSON.stringify(pattern)
    })
    const created = await res.json()
    patterns.value.push(created)
    return created
  }
  
  return { patterns, activePatternId, fetchPatterns, createPattern }
})
```

### **Deep Linking**

**Pattern Editor:**
```
/rosette-template?pattern_id=<uuid>
/rosette-template?new=true
```

**Manufacturing Plan:**
```
/manufacturing-plan?pattern_id=<uuid>&guitars=10
```

**JobLog Filter:**
```
/joblog?job_type=rosette_plan
/joblog?tool_id=thin_kerf_blade_001
```

---

## 11. Backend Architecture

### **Router Structure**

```
services/api/app/routers/
├── rosette_patterns.py      # CRUD for RosettePattern
├── saw_ops.py               # Saw slice operations + risk
├── manufacturing_plans.py   # Planning calculations
└── joblog.py                # Job history (enhanced)
```

### **Core Business Logic**

```
services/api/app/core/
├── saw_gcode.py             # G-code generation (circle + line)
├── saw_risk.py              # Risk analysis engine
├── pattern_mapper.py        # Pattern → CAM conversion
└── planner.py               # Manufacturing calculations
```

### **Schemas**

```
services/api/app/schemas/
├── rosette_pattern.py
├── saw_slice_batch_op.py
├── strip_recipe.py          # Future
└── job_log.py               # Enhanced with RMOS types
```

---

## 12. Data Flow Diagrams

### **Pattern Creation Flow**

```
RosetteTemplateLab (Vue)
  ↓ user creates pattern
  POST /api/rosette-patterns
  ↓ saves to database
RosettePatternStore (Pinia)
  ↓ updates local state
PatternLibrary (Vue)
  ↓ displays saved patterns
```

### **CAM Operation Flow**

```
PipelineLab (Vue)
  ↓ user selects pattern
  GET /api/rosette-patterns/{id}
  ↓ loads pattern data
Pattern → CAM Mapper (utils)
  ↓ derives SawSliceBatchOpCircle
RosetteMultiRingOpPanel (Vue)
  ↓ user reviews operation + risk
  POST /api/saw-ops/slice/preview
  ↓ returns G-code + risk analysis
User confirms
  ↓ executes pipeline
  POST /api/saw-ops/slice/execute
  ↓ runs machine
  POST /api/joblog
  ↓ logs job
JobLogMiniList (Vue)
  ↓ displays job history
```

### **Manufacturing Planning Flow**

```
ManufacturingPlanPanel (Vue)
  ↓ user enters pattern + quantity
  POST /api/manufacturing-plans/calculate
  ↓ backend calculates requirements
Planner Core (Python)
  ↓ returns strip plans
ManufacturingPlanPanel (Vue)
  ↓ displays material requirements
User confirms
  ↓ saves plan
  POST /api/joblog (job_type=rosette_plan)
  ↓ logs plan
JobLogMiniList (Vue)
  ↓ displays plan in history
```

---

## 13. Integration Points

### **PipelineLab Integration**

**Add RMOS Node Type:**
```typescript
// pipelineStore.ts
const nodeTypes = [
  // ... existing types
  {
    id: 'saw_multi_ring',
    label: 'Multi-Ring Saw',
    category: 'RMOS',
    component: 'RosetteMultiRingOpPanel'
  }
]
```

**Mapper Registration:**
```typescript
// pattern_to_batch.ts
export function rosettePatternToBatchOpCircle(
  pattern: RosettePattern,
  baseRadius: number,
  radialStep: number,
  sliceThickness: number,
  toolId: string,
  material: string
): SawSliceBatchOpCircle {
  // ... mapping logic
}
```

### **JobInt Integration**

**Extend JobLog Schema:**
```python
# job_log.py
class JobLogEntry(BaseModel):
    # ... existing fields
    
    # RMOS fields
    plan_pattern_id: Optional[str]
    plan_guitars: Optional[int]
    strip_plans: Optional[List[StripPlan]]
```

**Filter Endpoint:**
```python
@router.get("/joblog")
async def get_jobs(job_type: Optional[str] = None):
    if job_type:
        return [j for j in jobs if j.job_type == job_type]
    return jobs
```

### **Art Studio Integration**

**Risk Analytics:**
RMOS uses same risk grading system (GREEN/YELLOW/RED)

**Compare Mode:**
Compare pattern iterations side-by-side

**Preset Scorecards:**
Rate manufacturing approaches (fast/safe/precise)

---

## 14. Design Decisions

### **Why Separate RMOS Sandbox?**

1. **Modularity:** Can version RMOS independently (v0.1 → v1.0)
2. **Focus:** Dedicated space for rosette-specific features
3. **Testing:** Isolated test suite without main ToolBox interference
4. **Future Extraction:** Can become standalone product (Rosette Factory)
5. **Team Structure:** Separate teams can work on RMOS vs main CAM

### **Why Two Job Types?**

`saw_slice_batch` vs `rosette_plan` separation:
- Different lifecycles (plan → multiple executions)
- Different analytics (predictive vs actual)
- Different UIs (planning panel vs operation panel)
- Cleaner queries (filter by type without complex joins)

### **Why Strip Recipe System?**

Ultra-thin strips (0.3-0.8mm) require:
- Geometric derivation (can't guess stick dimensions)
- Safety validation (too thin = tool breakage)
- Jig recommendations (carrier blocks for < 0.6mm)
- Physics modeling (future: kerf + deflection)

Traditional "just cut it" approach wastes material and breaks tools.

### **Why Multi-Ring Circle Mode?**

Single-operation multi-ring cuts are:
- **Faster:** One setup, one execution
- **More accurate:** No repositioning errors
- **Easier to plan:** Single material + tool selection
- **Better for analytics:** All rings share same job context

Alternative (separate operations per ring) fragments data and slows workflow.

---

## 📚 See Also

- [README.md](./README.md) - Quick start and overview
- [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) - Step-by-step patches
- [docs/API_REFERENCE.md](./docs/API_REFERENCE.md) - Complete endpoint docs
- [docs/TECHNICAL_AUDIT.md](./docs/TECHNICAL_AUDIT.md) - Known issues
- [Main Handoff](../../CAM_CAD_DEVELOPER_HANDOFF.md) - Appendix E for RMOS

---

**Status:** ✅ Architecture Complete  
**Next:** Apply Patches A-D for v0.1 MVP  
**Timeline:** ~4-6 weeks for MVP
