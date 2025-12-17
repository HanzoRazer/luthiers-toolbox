# Art Studio Enhancement Roadmap 🎨

**Current Version:** v15.5 (Production-grade post-processor)  
**Date:** November 7, 2025  
**Status:** Enhancement Proposals

---

## 📊 Current Capabilities (v15.5)

✅ **4 Controller Presets** (GRBL, Mach3, Haas, Marlin)  
✅ **Lead-in/out Strategies** (Tangent linear, 90° arc, none)  
✅ **CRC Support** (G41/G42 tool radius compensation)  
✅ **Corner Smoothing** (Auto-fillet at sharp angles)  
✅ **Arc Optimization** (Controller-aware sweep limits)  
✅ **Modal Compression** (Suppress redundant coordinates)  
✅ **3D Preview** (Three.js WebGL toolpath visualization)

---

## 🚀 Proposed Enhancements

### **Phase 1: Advanced Toolpath Features (High Priority)**

#### **1.1 Helical Z-Ramping** ⭐⭐⭐⭐⭐
**What:** Spiral plunge instead of straight Z-axis moves  
**Why:** Better tool life, reduced load, smoother entry  
**Impact:** Critical for hardwoods and deep pockets

**Implementation:**
- Add `plunge_strategy` parameter: `"linear"`, `"ramp"`, `"helical"`
- Helical parameters:
  - `ramp_angle_deg` (default: 2-5°)
  - `ramp_radius_mm` (default: tool_d × 0.3)
  - `max_z_per_rev` (safety limit)

**Example:**
```json
{
  "plunge_strategy": "helical",
  "ramp_angle_deg": 3.0,
  "ramp_radius_mm": 2.0
}
```

**Output:**
```gcode
G0 Z5.0              ; Safe height
G0 X30.0 Y30.0       ; Position
; Helical ramp 0.0 to -3.0 mm
G3 X30.0 Y30.0 Z-0.5 I-2.0 J0.0 F400.0
G3 X30.0 Y30.0 Z-1.0 I-2.0 J0.0 F400.0
G3 X30.0 Y30.0 Z-1.5 I-2.0 J0.0 F400.0
...
```

---

#### **1.2 Chip Breaking / Peck Cycles** ⭐⭐⭐⭐
**What:** Periodic retract during deep cuts to clear chips  
**Why:** Prevents chip clogging, better surface finish  
**Impact:** Essential for deep mortises and inlays

**Implementation:**
- Add `chip_break_enabled` parameter
- Parameters:
  - `chip_break_depth` (retract every N mm)
  - `chip_break_retract` (retract distance, e.g., 0.5mm)
  - `chip_break_dwell` (pause in seconds)

**Example:**
```gcode
G1 Z-2.0 F400.0      ; Cut to depth
G0 Z-1.5             ; Partial retract (chip break)
G4 P0.5              ; Dwell 0.5s
G1 Z-2.0 F400.0      ; Resume
```

---

#### **1.3 Adaptive Feed Rate (Load-Aware)** ⭐⭐⭐⭐⭐
**What:** Dynamic feed adjustment based on engagement  
**Why:** Faster in open areas, slower in tight corners  
**Impact:** **Major time savings** (20-40% faster cycles)

**Integration:** Merge with **Patch N18** and **Module L.2**
- Use N18's `feed_floor_pct` concept
- Add Module L.2's curvature analysis
- Calculate engagement angle per move

**Parameters:**
```json
{
  "adaptive_feed_enabled": true,
  "feed_base_mm_min": 1200,
  "feed_min_pct": 0.50,     // 50% in tight corners
  "feed_max_pct": 1.50,     // 150% in straight runs
  "engagement_threshold": 90 // degrees
}
```

**Output:**
```gcode
G1 X50.0 Y10.0 F1800.0   ; 150% feed (straight)
G1 X50.0 Y30.0 F900.0    ; 75% feed (corner ahead)
G2 X60.0 Y40.0 I0.0 J10.0 F600.0  ; 50% feed (tight arc)
G1 X80.0 Y40.0 F1200.0   ; 100% feed (normal)
```

---

#### **1.4 Toolpath Optimization (Segment Merging)** ⭐⭐⭐
**What:** Combine collinear G1 moves into single command  
**Why:** Smaller files, smoother motion, less parser overhead  
**Impact:** 10-30% file size reduction

**Algorithm:**
```python
def merge_collinear_moves(moves, tolerance_deg=0.1):
    """Combine consecutive G1 moves on same line"""
    merged = []
    buffer = [moves[0]]
    
    for move in moves[1:]:
        if is_collinear(buffer[-1], move, tolerance_deg):
            buffer.append(move)  # Accumulate
        else:
            merged.append(merge(buffer))  # Emit merged
            buffer = [move]
    
    return merged
```

**Example:**
```gcode
; Before (3 moves):
G1 X10.0 Y10.0 F1200.0
G1 X20.0 Y20.0 F1200.0
G1 X30.0 Y30.0 F1200.0

; After (1 move):
G1 X30.0 Y30.0 F1200.0
```

---

#### **1.5 Arc Fitting (Line-to-Arc Conversion)** ⭐⭐⭐⭐
**What:** Convert polyline approximations to true arcs  
**Why:** Smoother motion, better finish, smaller files  
**Impact:** Essential for organic shapes (soundholes, bracing)

**Use Cases:**
- CAD exports with linear approximations
- Polygon offsetting results (Module L)
- DXF imports with dense polylines

**Algorithm:**
```python
def fit_arcs(points, tolerance_mm=0.05):
    """Detect circular segments in polyline"""
    arcs = []
    i = 0
    while i < len(points) - 2:
        arc = try_fit_arc(points[i:i+10], tolerance_mm)
        if arc:
            arcs.append(arc)
            i += arc.num_points
        else:
            arcs.append(Line(points[i], points[i+1]))
            i += 1
    return arcs
```

**Output:**
```gcode
; Before (10 linear moves):
G1 X10.0 Y0.0
G1 X9.8 Y2.0
G1 X9.2 Y3.9
...

; After (1 arc):
G2 X0.0 Y10.0 I0.0 J-10.0
```

---

### **Phase 2: Controller-Specific Features (Medium Priority)**

#### **2.1 Variable Spindle Speed (CSS)** ⭐⭐⭐
**What:** Constant surface speed for tapered tools  
**Why:** Better finish on variable-diameter features  
**Impact:** Professional-grade results

**Parameters:**
```json
{
  "spindle_mode": "rpm",  // or "css"
  "spindle_rpm": 12000,
  "css_surface_speed_m_min": 100,
  "css_max_rpm": 24000,
  "css_min_rpm": 1000
}
```

**Output:**
```gcode
G96 S100 M3          ; CSS mode, 100 m/min
G97 S12000 M3        ; Back to RPM mode
```

---

#### **2.2 Work Offset Management (G54-G59)** ⭐⭐⭐
**What:** Multi-fixture support with coordinate systems  
**Why:** Batch processing, multiple guitars on one table  
**Impact:** Production efficiency

**Parameters:**
```json
{
  "work_offset": "G54",  // G54-G59
  "fixtures": [
    {"name": "Guitar 1", "offset": "G54", "x": 0, "y": 0},
    {"name": "Guitar 2", "offset": "G55", "x": 650, "y": 0}
  ]
}
```

**Output:**
```gcode
G54                  ; Guitar 1 coordinates
G0 X50.0 Y100.0
; ... cut guitar 1 ...
G55                  ; Guitar 2 coordinates  
G0 X50.0 Y100.0     ; Same local coords, different position
; ... cut guitar 2 ...
```

---

#### **2.3 Probe Cycles (G38.2-G38.5)** ⭐⭐⭐⭐
**What:** Automatic Z-zero and surface mapping  
**Why:** Consistent depth across irregular stock  
**Impact:** Critical for figured tops and carved backs

**Implementation:**
```json
{
  "probe_enabled": true,
  "probe_feed": 100,    // mm/min
  "probe_retract": 2.0, // mm
  "probe_max_depth": -10.0
}
```

**Output:**
```gcode
G38.2 Z-10.0 F100.0  ; Probe down max 10mm
G92 Z0.0             ; Set current as Z zero
G0 Z5.0              ; Retract to safe
```

---

### **Phase 3: Integration with Module L & Patch N18 (High Priority)**

#### **3.1 Unified CAM Pipeline** ⭐⭐⭐⭐⭐
**What:** Art Studio as final post-processor for Module L  
**Why:** Single toolchain from design → CAM → G-code  
**Impact:** Seamless workflow

**Flow:**
```
User Input
  ↓
Module L (Adaptive Pocketing)
  → Generate toolpath with islands
  ↓
Patch N18 (Arc Linkers)
  → Smooth with G2/G3 arcs
  ↓
Art Studio v16 (Post-Processor)
  → Add lead-in/out
  → Apply CRC
  → Optimize for controller
  ↓
Final G-code
```

**New Endpoint:**
```python
POST /api/cam/unified/pocket_to_gcode
{
  "geometry": {...},        # From user
  "pocket_params": {...},   # Module L settings
  "arc_params": {...},      # Patch N18 settings
  "post_params": {...}      # Art Studio settings
}
```

---

#### **3.2 Toolpath Library** ⭐⭐⭐⭐
**What:** Reusable operation templates  
**Why:** Standardize common operations  
**Impact:** Faster setup, consistent quality

**Examples:**
- `"gibson_rosewood_bridge_slot.json"`
- `"martin_neck_pocket_mahogany.json"`
- `"binding_channel_maple.json"`

**Structure:**
```json
{
  "name": "Gibson Rosewood Bridge Slot",
  "description": "Standard 2.75\" × 0.375\" × 0.125\" deep",
  "tool": {
    "type": "end_mill",
    "diameter_mm": 3.175,
    "flutes": 2,
    "material": "carbide"
  },
  "feeds_speeds": {
    "spindle_rpm": 18000,
    "feed_mm_min": 800,
    "plunge_mm_min": 200
  },
  "toolpath": {
    "strategy": "adaptive",
    "stepover": 0.40,
    "stepdown": 0.8,
    "lead_in": "tangent_arc"
  },
  "post": "Haas"
}
```

---

### **Phase 4: Advanced Visualization (Medium Priority)**

#### **4.1 Material Removal Simulation** ⭐⭐⭐⭐
**What:** 3D stock visualization with progressive cuts  
**Why:** Catch collisions before running  
**Impact:** Prevent expensive mistakes

**Features:**
- Real-time WebGL rendering
- Color-coded depth map
- Collision detection
- Tool deflection warnings

**Tech Stack:**
- Three.js for 3D
- Web Workers for physics
- SharedArrayBuffer for performance

---

#### **4.2 Feed Rate Heatmap** ⭐⭐⭐
**What:** Visual overlay showing speed variations  
**Why:** Optimize cycle time at a glance  
**Impact:** Already in Module L.2, extend to Art Studio

**Integration:**
```json
{
  "visualization": {
    "heatmap_enabled": true,
    "color_scheme": "viridis",  // or "plasma", "turbo"
    "scale": "feed_rate"        // or "engagement", "chipload"
  }
}
```

---

#### **4.3 Time Estimation Dashboard** ⭐⭐⭐⭐
**What:** Detailed breakdown of cycle time  
**Why:** Accurate job quotes and scheduling  
**Impact:** Business critical

**Output:**
```json
{
  "total_time_min": 32.5,
  "breakdown": {
    "cutting": 18.2,
    "rapids": 4.3,
    "retracts": 2.8,
    "tool_changes": 5.0,
    "spindle_ramp": 2.2
  },
  "by_operation": [
    {"name": "Rough pocket", "time_min": 15.3},
    {"name": "Finish walls", "time_min": 8.7},
    {"name": "Chamfer edges", "time_min": 8.5}
  ]
}
```

---

### **Phase 5: AI/ML Enhancements (Future/Experimental)**

#### **5.1 Intelligent Feed Optimization** ⭐⭐⭐⭐⭐
**What:** ML model predicts optimal feeds from geometry  
**Why:** Better than manual tuning  
**Impact:** 30-50% time savings with same finish

**Training Data:**
- Historical jobs with actual cycle times
- Tool wear measurements
- Surface finish results
- Chip formation videos

**Model:** Random Forest or XGBoost
- Inputs: Geometry features, material, tool, engagement
- Output: Optimal feed rate per segment

---

#### **5.2 Collision Prediction** ⭐⭐⭐⭐
**What:** Pre-flight check for crashes  
**Why:** Catch errors before breaking tools  
**Impact:** Safety critical

**Features:**
- Fixture collision detection
- Holder interference warnings
- Workpiece flex prediction
- Tool deflection modeling

---

#### **5.3 Toolpath Learning** ⭐⭐⭐
**What:** System learns from user corrections  
**Why:** Continuously improve defaults  
**Impact:** Self-optimizing CAM

**Example:**
- User manually tweaks feed in tight corner
- System: "This corner type now gets 75% feed by default"
- Applies to future similar features automatically

---

## 📋 Implementation Priority Matrix

| Feature | Impact | Effort | Priority | Version |
|---------|--------|--------|----------|---------|
| **Helical Z-Ramping** | ⭐⭐⭐⭐⭐ | Medium | **1** | v16.0 |
| **Adaptive Feed Rate** | ⭐⭐⭐⭐⭐ | High | **2** | v16.0 |
| **Unified CAM Pipeline** | ⭐⭐⭐⭐⭐ | High | **3** | v16.0 |
| **Arc Fitting** | ⭐⭐⭐⭐ | Medium | **4** | v16.0 |
| **Toolpath Library** | ⭐⭐⭐⭐ | Low | **5** | v16.0 |
| **Chip Breaking** | ⭐⭐⭐⭐ | Low | **6** | v16.1 |
| **Probe Cycles** | ⭐⭐⭐⭐ | Medium | **7** | v16.1 |
| **Material Removal Sim** | ⭐⭐⭐⭐ | Very High | **8** | v17.0 |
| **Segment Merging** | ⭐⭐⭐ | Low | **9** | v16.1 |
| **Work Offsets** | ⭐⭐⭐ | Medium | **10** | v16.1 |
| **Time Dashboard** | ⭐⭐⭐⭐ | Medium | **11** | v16.1 |
| **Intelligent Feed (ML)** | ⭐⭐⭐⭐⭐ | Very High | **12** | v18.0 |

---

## 🎯 Recommended v16.0 Feature Set

**Theme:** "Production CAM Suite"

### **Core Features (Q1 2026)**
1. ✅ **Helical Z-Ramping** - Better plunge entry
2. ✅ **Adaptive Feed Rate** - Dynamic speed optimization
3. ✅ **Unified Pipeline** - Module L → N18 → Art Studio integration
4. ✅ **Arc Fitting** - Polyline-to-arc conversion
5. ✅ **Toolpath Library** - Preset operations

### **API Changes**
```python
# New unified endpoint
POST /api/cam/unified/complete
{
  "geometry": {...},
  "operation": "adaptive_pocket",  # or "profile", "drill", etc.
  "template": "gibson_bridge_slot", # optional preset
  "overrides": {...}                # custom params
}

# Enhanced post endpoint
POST /api/cam_gcode/post_v16
{
  "moves": [...],  # From Module L or N18
  "plunge_strategy": "helical",
  "adaptive_feed": true,
  "arc_fitting": true,
  "preset": "Haas"
}
```

---

## 🔗 Integration Points

### **With Module L (Adaptive Pocketing)**
```python
# Module L generates rough toolpath
pocket_path = module_l.plan_adaptive_l3(...)

# Patch N18 adds arc linkers
arc_path = patch_n18.add_arc_linkers(pocket_path, use_arcs=True)

# Art Studio v16 post-processes
gcode = art_studio_v16.post_process(
    moves=arc_path,
    plunge_strategy="helical",
    adaptive_feed=True,
    preset="GRBL"
)
```

### **With Patch N15 (Backplot)**
```python
# Generate G-code with Art Studio
gcode = art_studio_v16.post_process(...)

# Visualize with N15 backplot
svg = patch_n15.plot_gcode(gcode)
stats = patch_n15.estimate_time(gcode)
```

---

## 📚 Resources for Implementation

### **Books**
- "CAM Programming for CNC Machining" - Peter Smid
- "CNC Control Setup for Milling and Turning" - Peter Smid
- "Machinery's Handbook" (30th Edition) - Feed/speed tables

### **Standards**
- ISO 6983 (G-code standard)
- NIST RS274/NGC (LinuxCNC reference)
- Fanuc/Haas programming manuals

### **Open Source Projects**
- **LinuxCNC** - Reference implementation
- **GRBL** - Embedded G-code parser
- **PyCAM** - Python CAM toolkit
- **OpenCAMLib** - Geometric algorithms

---

## 🚀 Next Steps

### **Immediate (This Week)**
1. Review this roadmap with stakeholders
2. Prioritize v16.0 features
3. Create detailed specs for top 3 features
4. Set up v16 development branch

### **Short Term (1 Month)**
1. Implement helical ramping
2. Prototype adaptive feed rate
3. Design unified pipeline architecture
4. Build toolpath library structure

### **Long Term (3-6 Months)**
1. Complete v16.0 feature set
2. User testing with real guitar builds
3. Performance benchmarking
4. Documentation and tutorials

---

## ✅ Success Metrics

**v16.0 Goals:**
- ✅ 30% faster cycle times (adaptive feed)
- ✅ 50% better tool life (helical ramping)
- ✅ 90% fewer setup errors (unified pipeline)
- ✅ 10x faster operation setup (template library)
- ✅ 100% controller compatibility maintained

---

**Your Next Action:** Pick 2-3 features from Priority 1-5 for v16.0 development!

Would you like me to:
1. **Create detailed specs** for helical ramping?
2. **Prototype adaptive feed** with Module L integration?
3. **Design the unified pipeline** architecture?
4. **Build the toolpath library** structure?

Let me know what excites you most! 🎸🔧
