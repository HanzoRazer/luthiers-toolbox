# MVP Build Features → Unified Scaffold Integration Guide

> Step-by-step instructions for extracting features from MVP builds and integrating into the main application scaffold.

**Last Updated**: November 3, 2025  
**Target Structure**: `server/pipelines/` + `client/src/components/`

---

## Table of Contents

1. [Integration Overview](#integration-overview)
2. [Scaffold Structure](#scaffold-structure)
3. [Feature Extraction Steps](#feature-extraction-steps)
4. [Pipeline Integration](#pipeline-integration)
5. [Client Integration](#client-integration)
6. [Testing Checklist](#testing-checklist)
7. [Deployment](#deployment)

---

## Integration Overview

### **Source Locations**

```
MVP Build_10-11-2025/
├── MVP_scaffold_bracing_hardware/   → server/pipelines/bracing/, hardware/
├── MVP_GCode_Explainer_Addon/       → server/pipelines/gcode_explainer/
├── rosette_pack/                    → server/pipelines/rosette/
└── qrm_pack/                        → tools/retopology/ (Blender-specific)

MVP Build_1012-2025/
├── Luthiers_Tool_Box_Full_GitHubReady_Plus_Integrated_Rosette_Queue/
│   ├── server/app.py                → server/app.py (merge)
│   ├── server/pipelines/rosette/    → server/pipelines/rosette/ (enhanced)
│   └── server/export_queue.py       → server/utils/export_queue.py
└── SmartGuitar_Pi5_Party_MVP_v0.1/  → Smart Guitar Build/ (separate project)

Lutherier Project/
├── Les Paul_Project/
│   └── clean_cam_*.py               → server/pipelines/dxf_cleaner/
└── Gibson J 45_ Project/
    └── clean_cam_*.py               → server/pipelines/dxf_cleaner/
```

---

## Scaffold Structure

### **Unified Application Layout**

```
Luthiers ToolBox/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                   # CI/CD pipeline
│   │   └── deploy.yml               # GitHub Pages deployment
│   └── copilot-instructions.md      # AI agent guide
│
├── server/
│   ├── app.py                       # FastAPI main application
│   ├── requirements.txt             # Python dependencies
│   ├── Dockerfile                   # Container image
│   ├── poller.py                    # Windows hot-folder watcher
│   │
│   ├── pipelines/                   # ⭐ INTEGRATED FEATURES
│   │   ├── rosette/
│   │   │   ├── __init__.py
│   │   │   ├── rosette_calc.py
│   │   │   ├── rosette_to_dxf.py
│   │   │   ├── rosette_make_gcode.py
│   │   │   └── README.md
│   │   │
│   │   ├── bracing/
│   │   │   ├── __init__.py
│   │   │   ├── bracing_calc.py
│   │   │   └── README.md
│   │   │
│   │   ├── hardware/
│   │   │   ├── __init__.py
│   │   │   ├── hardware_layout.py
│   │   │   └── README.md
│   │   │
│   │   ├── gcode_explainer/
│   │   │   ├── __init__.py
│   │   │   ├── explain_gcode_ai.py
│   │   │   ├── serve_explainer.py
│   │   │   └── gcode_explainer_web.html
│   │   │
│   │   └── dxf_cleaner/
│   │       ├── __init__.py
│   │       ├── clean_dxf.py         # Unified cleaner
│   │       └── README.md
│   │
│   ├── configs/
│   │   └── examples/
│   │       ├── rosette/
│   │       │   └── example_params.json
│   │       ├── bracing/
│   │       │   └── example_x_brace.json
│   │       └── hardware/
│   │           └── example_lp_hardware.json
│   │
│   ├── utils/
│   │   ├── export_queue.py          # Unified export management
│   │   └── dxf_utils.py             # Shared DXF helpers
│   │
│   └── storage/                     # Runtime data (gitignored)
│       ├── exports/
│       └── queue.json
│
├── client/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   │
│   └── src/
│       ├── main.ts                  # Vue app entry
│       ├── App.vue                  # Main layout
│       │
│       ├── components/
│       │   └── toolbox/
│       │       ├── CadCanvas.vue
│       │       ├── LuthierCalculator.vue
│       │       ├── RosetteDesigner.vue       # NEW
│       │       ├── BracingCalculator.vue     # NEW
│       │       ├── HardwareLayout.vue        # NEW
│       │       ├── GCodeExplainer.vue        # NEW
│       │       └── ExportQueue.vue           # NEW
│       │
│       └── utils/
│           ├── api.ts               # API client SDK
│           └── types.ts             # TypeScript definitions
│
├── docs/                            # Documentation
│   ├── README.md                    # Project overview
│   ├── ARCHITECTURE.md              # System design
│   ├── FEATURE_REPORT.md            # MVP analysis
│   └── INTEGRATION_GUIDE.md         # This file
│
├── docker-compose.yml               # Full stack deployment
├── .gitignore
└── LICENSE
```

---

## Feature Extraction Steps

### **Step 1: Copy Rosette Pipeline**

```powershell
# Source: MVP Build_1012-2025
$source = "Luthiers Tool Box 2\Luthiers Tool Box\MVP Build_1012-2025\Luthiers_Tool_Box_Full_GitHubReady_Plus_Integrated_Rosette_Queue (1)\Luthiers_Tool_Box_Full\server\pipelines\rosette"
$dest = "server\pipelines\rosette"

# Copy Python modules
Copy-Item "$source\rosette_calc.py" -Destination "$dest\"
Copy-Item "$source\rosette_to_dxf.py" -Destination "$dest\"
Copy-Item "$source\rosette_post_fill.py" -Destination "$dest\"
Copy-Item "$source\rosette_make_gcode.py" -Destination "$dest\"

# Copy config examples
$configSource = "Luthiers Tool Box 2\Luthiers Tool Box\MVP Build_1012-2025\Luthiers_Tool_Box_Full_GitHubReady_Plus_Integrated_Rosette_Queue (1)\Luthiers_Tool_Box_Full\server\configs\examples\rosette"
Copy-Item "$configSource\example_params.json" -Destination "server\configs\examples\rosette\"
```

**Verify**:
```powershell
cd server\pipelines\rosette
python rosette_calc.py ..\..\configs\examples\rosette\example_params.json --out-dir test_out
# Check: test_out/rosette_calc.json should exist
```

---

### **Step 2: Copy Bracing Pipeline**

```powershell
# Source: MVP Build_10-11-2025
$source = "Luthiers Tool Box 2\Luthiers Tool Box\MVP Build_10-11-2025\MVP_scaffold_bracing_hardware\mvp\pipelines\bracing"
$dest = "server\pipelines\bracing"

Copy-Item "$source\bracing_calc.py" -Destination "$dest\"
Copy-Item "$source\bracing_schema.json" -Destination "server\configs\examples\bracing\"

# Copy example configs
$examples = "Luthiers Tool Box 2\Luthiers Tool Box\MVP Build_10-11-2025\MVP_scaffold_bracing_hardware\mvp\configs\examples\bracing"
Copy-Item "$examples\example_x_brace.json" -Destination "server\configs\examples\bracing\"
```

**Verify**:
```powershell
cd server\pipelines\bracing
python bracing_calc.py ..\..\configs\examples\bracing\example_x_brace.json --out-dir test_out
# Check: test_out/*_bracing_report.json should exist
```

---

### **Step 3: Copy Hardware Pipeline**

```powershell
# Source: MVP Build_10-11-2025
$source = "Luthiers Tool Box 2\Luthiers Tool Box\MVP Build_10-11-2025\MVP_scaffold_bracing_hardware\mvp\pipelines\hardware"
$dest = "server\pipelines\hardware"

Copy-Item "$source\hardware_layout.py" -Destination "$dest\"
Copy-Item "$source\hardware_schema.json" -Destination "server\configs\examples\hardware\"

# Copy example configs
$examples = "Luthiers Tool Box 2\Luthiers Tool Box\MVP Build_10-11-2025\MVP_scaffold_bracing_hardware\mvp\configs\examples\hardware"
Copy-Item "$examples\example_lp_hardware.json" -Destination "server\configs\examples\hardware\"
```

**Verify**:
```powershell
cd server\pipelines\hardware
python hardware_layout.py ..\..\configs\examples\hardware\example_lp_hardware.json --out-dir test_out
# Check: test_out/*_hardware_layout.dxf.txt should exist
```

---

### **Step 4: Copy G-code Explainer**

```powershell
# Source: MVP Build_10-11-2025
$source = "Luthiers Tool Box 2\Luthiers Tool Box\MVP Build_10-11-2025\MVP_GCode_Explainer_Addon\mvp\pipelines\gcode_explainer"
$dest = "server\pipelines\gcode_explainer"

Copy-Item "$source\explain_gcode_ai.py" -Destination "$dest\"
Copy-Item "$source\serve_explainer.py" -Destination "$dest\"
Copy-Item "$source\gcode_explainer_web.html" -Destination "$dest\"
Copy-Item "$source\example_gcode.nc" -Destination "$dest\"
Copy-Item "$source\requirements.txt" -Destination "$dest\"
```

**Verify**:
```powershell
cd server\pipelines\gcode_explainer
pip install -r requirements.txt
python explain_gcode_ai.py --in example_gcode.nc --md --out test_out
# Check: test_out/example_gcode_explained.md should exist
```

---

### **Step 5: Copy DXF Cleaner**

```powershell
# Source: Lutherier Project/Les Paul_Project
$source = "Lutherier Project 2\Lutherier Project\Les Paul_Project"
$dest = "server\pipelines\dxf_cleaner"

Copy-Item "$source\clean_cam_ready_dxf_windows_all_layers.py" -Destination "$dest\clean_dxf.py"

# Copy GUI version
Copy-Item "Lutherier Project 2\Lutherier Project\Gibson J 45_ Project\clean_cam_closed_gui.py" -Destination "$dest\"
```

**Create unified interface**:
```powershell
# See "Unified DXF Cleaner" section below
```

---

### **Step 6: Copy Export Queue Utility**

```powershell
# Source: MVP Build_1012-2025
$source = "Luthiers Tool Box 2\Luthiers Tool Box\MVP Build_1012-2025\Luthiers_Tool_Box_Full_GitHubReady_Plus_Integrated_Rosette_Queue (1)\server"
$dest = "server\utils"

Copy-Item "$source\export_queue.py" -Destination "$dest\"
```

---

## Pipeline Integration

### **Creating `__init__.py` for Python Packages**

Each pipeline needs an `__init__.py` to be importable:

**`server/pipelines/rosette/__init__.py`**:
```python
"""Rosette calculator pipeline - parametric soundhole rosette design."""
from .rosette_calc import compute as calculate_rosette
from .rosette_to_dxf import export_dxf as rosette_to_dxf

__all__ = ['calculate_rosette', 'rosette_to_dxf']
```

**`server/pipelines/bracing/__init__.py`**:
```python
"""Bracing calculator pipeline - structural analysis."""
from .bracing_calc import run as calculate_bracing

__all__ = ['calculate_bracing']
```

**`server/pipelines/hardware/__init__.py`**:
```python
"""Hardware layout pipeline - electronics positioning."""
# Implementation varies by file structure

__all__ = []
```

**`server/pipelines/gcode_explainer/__init__.py`**:
```python
"""G-code explainer pipeline - line-by-line analysis."""
# Standalone CLI tools, no package exports

__all__ = []
```

**`server/pipelines/dxf_cleaner/__init__.py`**:
```python
"""DXF cleaner pipeline - CAM-ready geometry conversion."""
# Standalone utilities

__all__ = []
```

---

### **Unified DXF Cleaner**

Create a single interface for all DXF cleaning operations:

**`server/pipelines/dxf_cleaner/clean_dxf.py`**:
```python
#!/usr/bin/env python3
"""
Unified DXF Cleaner - CAM-Ready Geometry Conversion

Combines functionality from:
- clean_cam_ready_dxf_windows_all_layers.py
- clean_cam_closed_gui.py
- clean_cam_closed_any_dxf.py
"""

import argparse
import os
import sys
import ezdxf
from shapely.geometry import LineString, Polygon
from shapely.ops import linemerge, unary_union, polygonize
import math
import numpy as np

# Configuration
SKIP_TYPES = {"TEXT", "MTEXT", "DIMENSION", "HATCH", "LEADER"}
ARC_SEGS = 48
CIRCLE_SEGS = 96
SPLINE_SEGS = 300
DEFAULT_TOLERANCE = 0.12  # mm

def clean_dxf(
    input_path: str,
    output_path: str = None,
    tolerance: float = DEFAULT_TOLERANCE,
    layers: list = None
) -> str:
    """
    Clean DXF file for CAM compatibility.
    
    Args:
        input_path: Path to input DXF file
        output_path: Path to output DXF (auto-generated if None)
        tolerance: Snapping tolerance in mm
        layers: List of layers to process (None = all layers)
    
    Returns:
        Path to output DXF file
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Auto-generate output path
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_CAM_Ready{ext}"
    
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    print(f"Tolerance: {tolerance}mm")
    
    # Read DXF
    try:
        doc = ezdxf.readfile(input_path)
    except Exception as e:
        raise ValueError(f"Failed to read DXF: {e}")
    
    msp = doc.modelspace()
    
    # Process entities by layer
    entities_by_layer = {}
    for entity in msp:
        entity_type = entity.dxftype()
        layer_name = getattr(entity.dxf, 'layer', '0')
        
        # Skip non-machinable entities
        if entity_type in SKIP_TYPES:
            continue
        
        # Filter layers if specified
        if layers and layer_name not in layers:
            continue
        
        if layer_name not in entities_by_layer:
            entities_by_layer[layer_name] = []
        
        # Convert to segments
        segments = entity_to_segments(entity, entity_type)
        entities_by_layer[layer_name].extend(segments)
    
    # Create output DXF
    out_doc = ezdxf.new('R12')
    out_msp = out_doc.modelspace()
    
    # Process each layer
    closed_count = 0
    for layer_name, segments in entities_by_layer.items():
        if not segments:
            continue
        
        print(f"  Layer '{layer_name}': {len(segments)} segments")
        
        # Chain and close segments
        closed_polys = unify_and_close(segments, tolerance)
        
        # Add to output DXF
        for poly in closed_polys:
            if poly and len(poly) >= 3:
                out_msp.add_lwpolyline(
                    points=poly,
                    dxfattribs={'layer': layer_name, 'closed': True}
                )
                closed_count += 1
        
        print(f"    → {len(closed_polys)} closed polylines")
    
    # Set units to mm
    out_doc.header['$INSUNITS'] = 4
    
    # Save
    out_doc.saveas(output_path)
    print(f"\n✅ Saved {closed_count} closed polylines to {output_path}")
    
    return output_path


def entity_to_segments(entity, entity_type):
    """Convert DXF entity to line segments."""
    segments = []
    
    if entity_type == 'LINE':
        start = entity.dxf.start
        end = entity.dxf.end
        segments.append([(start.x, start.y), (end.x, end.y)])
    
    elif entity_type == 'ARC':
        center = entity.dxf.center
        radius = entity.dxf.radius
        start_angle = math.radians(entity.dxf.start_angle)
        end_angle = math.radians(entity.dxf.end_angle)
        
        # Handle angle wrap
        if end_angle < start_angle:
            end_angle += 2 * math.pi
        
        # Discretize arc
        angles = np.linspace(start_angle, end_angle, ARC_SEGS + 1)
        points = [(center.x + radius * math.cos(a), 
                   center.y + radius * math.sin(a)) for a in angles]
        
        for i in range(len(points) - 1):
            segments.append([points[i], points[i + 1]])
    
    elif entity_type == 'CIRCLE':
        center = entity.dxf.center
        radius = entity.dxf.radius
        
        # Discretize circle
        angles = np.linspace(0, 2 * math.pi, CIRCLE_SEGS + 1)
        points = [(center.x + radius * math.cos(a),
                   center.y + radius * math.sin(a)) for a in angles]
        
        for i in range(len(points) - 1):
            segments.append([points[i], points[i + 1]])
    
    elif entity_type in ('LWPOLYLINE', 'POLYLINE'):
        points = [(v[0], v[1]) for v in entity.get_points('xy')]
        if len(points) >= 2:
            for i in range(len(points) - 1):
                segments.append([points[i], points[i + 1]])
            # Close if flagged
            if getattr(entity.dxf, 'closed', False):
                segments.append([points[-1], points[0]])
    
    elif entity_type == 'SPLINE':
        # Approximate spline
        try:
            points = list(entity.flattening(SPLINE_SEGS / 100.0))
            for i in range(len(points) - 1):
                p1, p2 = points[i], points[i + 1]
                segments.append([(p1.x, p1.y), (p2.x, p2.y)])
        except:
            pass
    
    return segments


def unify_and_close(segments, tolerance):
    """Chain segments and close into polygons."""
    if not segments:
        return []
    
    # Build LineString geometries
    lines = [LineString(seg) for seg in segments if len(seg) >= 2]
    if not lines:
        return []
    
    # Merge connected lines
    try:
        merged = linemerge(lines)
    except:
        return []
    
    # Ensure iterable
    if hasattr(merged, '__iter__') and not isinstance(merged, (str, LineString)):
        geoms = list(merged.geoms) if hasattr(merged, 'geoms') else [merged]
    else:
        geoms = [merged]
    
    # Snap endpoints and polygonize
    buffered = [g.buffer(tolerance / 2) for g in geoms]
    try:
        union = unary_union(buffered)
        polys = list(polygonize(union.boundary))
    except:
        polys = []
    
    # Extract coordinates
    closed_polys = []
    for poly in polys:
        if poly.is_valid and not poly.is_empty:
            coords = list(poly.exterior.coords)
            if len(coords) >= 4:  # At least 3 unique points + closing point
                closed_polys.append(coords[:-1])  # Remove duplicate closing point
    
    return closed_polys


def main():
    parser = argparse.ArgumentParser(
        description="Clean DXF files for CAM compatibility"
    )
    parser.add_argument('input', help='Input DXF file path')
    parser.add_argument('-o', '--output', help='Output DXF file path')
    parser.add_argument('-t', '--tolerance', type=float, default=DEFAULT_TOLERANCE,
                       help=f'Snapping tolerance in mm (default: {DEFAULT_TOLERANCE})')
    parser.add_argument('-l', '--layers', nargs='+',
                       help='Specific layers to process (default: all)')
    
    args = parser.parse_args()
    
    try:
        output_path = clean_dxf(
            args.input,
            args.output,
            args.tolerance,
            args.layers
        )
        return 0
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
```

**Usage**:
```powershell
# Basic usage (auto-detect output name)
python clean_dxf.py input.dxf

# Specify output
python clean_dxf.py input.dxf -o output_cam_ready.dxf

# Adjust tolerance
python clean_dxf.py input.dxf -t 0.15

# Process specific layers
python clean_dxf.py input.dxf -l PROFILE POCKET DRILL
```

---

## Client Integration

### **Step 1: Create Vue Components**

#### **Rosette Designer Component**

**`client/src/components/toolbox/RosetteDesigner.vue`**:
```vue
<template>
  <div class="rosette-designer">
    <h3>Rosette Designer</h3>
    
    <div class="form-grid">
      <label>
        Soundhole Diameter (mm):
        <input v-model.number="params.soundhole_diameter_mm" type="number" step="0.1" />
      </label>
      
      <label>
        Exposure (mm):
        <input v-model.number="params.exposure_mm" type="number" step="0.01" />
      </label>
      
      <label>
        Glue Clearance (mm):
        <input v-model.number="params.glue_clearance_mm" type="number" step="0.01" />
      </label>
    </div>
    
    <h4>Central Band</h4>
    <div class="form-grid">
      <label>
        Width (mm):
        <input v-model.number="params.central_band.width_mm" type="number" step="0.1" />
      </label>
      
      <label>
        Thickness (mm):
        <input v-model.number="params.central_band.thickness_mm" type="number" step="0.1" />
      </label>
    </div>
    
    <div class="actions">
      <button @click="calculate">Calculate</button>
      <button @click="exportDXF" :disabled="!result">Export DXF</button>
      <button @click="exportGCode" :disabled="!result">Export G-code</button>
    </div>
    
    <div v-if="result" class="results">
      <h4>Results</h4>
      <dl>
        <dt>Channel Width:</dt>
        <dd>{{ result.channel_width_mm }} mm</dd>
        
        <dt>Channel Depth:</dt>
        <dd>{{ result.channel_depth_mm }} mm</dd>
      </dl>
    </div>
    
    <div v-if="status" class="status">{{ status }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const params = ref({
  soundhole_diameter_mm: 88.0,
  exposure_mm: 0.15,
  glue_clearance_mm: 0.08,
  central_band: {
    width_mm: 18.0,
    thickness_mm: 1.0
  },
  inner_purfling: [],
  outer_purfling: []
})

const result = ref<any>(null)
const status = ref('')

async function calculate() {
  status.value = 'Calculating...'
  try {
    const res = await fetch('/api/pipelines/rosette/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params.value)
    })
    result.value = await res.json()
    status.value = '✅ Calculation complete'
  } catch (e) {
    status.value = `❌ Error: ${e}`
  }
}

async function exportDXF() {
  status.value = 'Exporting DXF...'
  try {
    const res = await fetch('/api/pipelines/rosette/export-dxf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params.value)
    })
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'rosette.dxf'
    a.click()
    status.value = '✅ DXF downloaded'
  } catch (e) {
    status.value = `❌ Error: ${e}`
  }
}

async function exportGCode() {
  status.value = 'Generating G-code...'
  // Implementation
}
</script>

<style scoped>
.rosette-designer {
  padding: 1rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin: 1rem 0;
}

label {
  display: flex;
  flex-direction: column;
}

.actions {
  display: flex;
  gap: 0.5rem;
  margin: 1rem 0;
}

.results dl {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.5rem;
  margin: 1rem 0;
}

.status {
  margin-top: 1rem;
  padding: 0.5rem;
  background: #f0f0f0;
  border-radius: 4px;
}
</style>
```

#### **Export Queue Component**

**`client/src/components/toolbox/ExportQueue.vue`**:
```vue
<template>
  <div class="export-queue">
    <h3>Export Queue</h3>
    
    <div class="filters">
      <button :class="{active: filter === 'all'}" @click="filter = 'all'">
        All ({{ exports.length }})
      </button>
      <button :class="{active: filter === 'ready'}" @click="filter = 'ready'">
        Ready ({{ readyCount }})
      </button>
      <button :class="{active: filter === 'processing'}" @click="filter = 'processing'">
        Processing ({{ processingCount }})
      </button>
    </div>
    
    <div class="export-list">
      <div v-for="exp in filteredExports" :key="exp.id" class="export-item">
        <div class="export-info">
          <strong>{{ exp.type }}</strong>
          <span class="model">{{ exp.model }}</span>
          <span class="status" :class="exp.status">{{ exp.status }}</span>
        </div>
        
        <div class="export-actions">
          <button v-if="exp.status === 'ready'" @click="download(exp)">
            Download
          </button>
          <span v-else-if="exp.status === 'processing'">⏳</span>
          <span v-else>⌛</span>
        </div>
      </div>
    </div>
    
    <button @click="refresh" class="refresh-btn">Refresh</button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

interface Export {
  id: string
  type: string
  model: string
  file: string
  status: 'queued' | 'processing' | 'ready' | 'downloaded'
  queued_at: string
}

const exports = ref<Export[]>([])
const filter = ref<'all' | 'ready' | 'processing'>('all')

const filteredExports = computed(() => {
  if (filter.value === 'all') return exports.value
  return exports.value.filter(e => e.status === filter.value)
})

const readyCount = computed(() => 
  exports.value.filter(e => e.status === 'ready').length
)

const processingCount = computed(() =>
  exports.value.filter(e => e.status === 'processing').length
)

async function refresh() {
  try {
    const res = await fetch('/api/exports/list')
    exports.value = await res.json()
  } catch (e) {
    console.error('Failed to fetch exports:', e)
  }
}

async function download(exp: Export) {
  try {
    const res = await fetch(`/api/files/${exp.id}`)
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = exp.file
    a.click()
    
    // Mark as downloaded
    await fetch(`/api/exports/${exp.id}/downloaded`, { method: 'POST' })
    refresh()
  } catch (e) {
    console.error('Download failed:', e)
  }
}

onMounted(() => {
  refresh()
  // Auto-refresh every 5 seconds
  setInterval(refresh, 5000)
})
</script>

<style scoped>
.export-queue {
  padding: 1rem;
}

.filters {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.filters button {
  padding: 0.5rem 1rem;
  border: 1px solid #ccc;
  background: white;
  cursor: pointer;
}

.filters button.active {
  background: #007bff;
  color: white;
}

.export-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.export-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.export-info {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.status {
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  font-size: 0.875rem;
}

.status.ready {
  background: #d4edda;
  color: #155724;
}

.status.processing {
  background: #fff3cd;
  color: #856404;
}

.status.queued {
  background: #f8d7da;
  color: #721c24;
}

.refresh-btn {
  padding: 0.5rem 1rem;
}
</style>
```

### **Step 2: Update Main App**

**`client/src/App.vue`** (add new routes):
```vue
<template>
  <div class="app">
    <h2>Luthier's Tool Box</h2>
    
    <nav>
      <button @click="active = 'design'">Design</button>
      <button @click="active = 'rosette'">Rosette</button>
      <button @click="active = 'bracing'">Bracing</button>
      <button @click="active = 'hardware'">Hardware</button>
      <button @click="active = 'gcode'">G-code</button>
      <button @click="active = 'exports'">Exports</button>
    </nav>
    
    <main>
      <CadCanvas v-if="active === 'design'" />
      <RosetteDesigner v-else-if="active === 'rosette'" />
      <BracingCalculator v-else-if="active === 'bracing'" />
      <HardwareLayout v-else-if="active === 'hardware'" />
      <GCodeExplainer v-else-if="active === 'gcode'" />
      <ExportQueue v-else-if="active === 'exports'" />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import CadCanvas from './components/toolbox/CadCanvas.vue'
import RosetteDesigner from './components/toolbox/RosetteDesigner.vue'
import BracingCalculator from './components/toolbox/BracingCalculator.vue'
import HardwareLayout from './components/toolbox/HardwareLayout.vue'
import GCodeExplainer from './components/toolbox/GCodeExplainer.vue'
import ExportQueue from './components/toolbox/ExportQueue.vue'

const active = ref<string>('design')
</script>
```

---

## Testing Checklist

### **Backend Tests**

- [ ] Rosette calculation produces valid JSON
- [ ] Rosette DXF export creates R12 format with closed circles
- [ ] Bracing calculation computes mass correctly
- [ ] Hardware layout generates valid DXF coordinates
- [ ] G-code explainer parses example files without errors
- [ ] DXF cleaner converts test file to closed polylines
- [ ] Export queue tracks status correctly

### **Frontend Tests**

- [ ] Rosette designer form submits and displays results
- [ ] Export queue refreshes automatically
- [ ] DXF downloads work in browser
- [ ] Component navigation works correctly
- [ ] Form validation catches invalid inputs

### **Integration Tests**

- [ ] Full workflow: Design → Calculate → Export → Download
- [ ] Hot folder poller copies DXFs (Windows only)
- [ ] Multiple pipelines can run concurrently
- [ ] Queue handles concurrent exports

---

## Deployment

### **GitHub Actions Workflow**

**`.github/workflows/deploy.yml`**:
```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Build client
        run: |
          cd client
          npm ci
          npm run build
      
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./client/dist
```

### **Docker Deployment**

```powershell
# Build and run
docker compose up --build

# Access
# Client: http://localhost:8080
# API: http://localhost:8000
```

---

## Next Steps

1. **Extract MVP files** using the PowerShell commands above
2. **Test each pipeline** standalone to verify functionality
3. **Create FastAPI endpoints** for pipeline integration
4. **Build Vue components** for user interface
5. **Deploy to GitHub Pages** with Actions workflow

---

**Integration Status**: Ready for extraction and testing  
**Estimated Time**: 2-3 weeks for full integration  
**Priority Order**: Rosette → Export Queue → DXF Cleaner → G-code Explainer → Bracing → Hardware
