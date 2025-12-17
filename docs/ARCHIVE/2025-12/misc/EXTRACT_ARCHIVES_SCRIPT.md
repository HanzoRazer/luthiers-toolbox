# Extract Compressed Archives - PowerShell Script

## Purpose
Extract all ZIP files to search for complete String Spacing Calculator implementation.

---

## Quick Start (Copy-Paste)

```powershell
# Navigate to folder with ZIPs
cd "c:\Users\thepr\Downloads\Luthiers ToolBox\Guitar Design HTML app\10_06+2025"

# Extract all ZIP files
Get-ChildItem -Filter "*.zip" | ForEach-Object {
    $dest = "extracted_$($_.BaseName)"
    Write-Host "Extracting: $($_.Name) -> $dest"
    Expand-Archive -Path $_.FullName -DestinationPath $dest -Force
    Write-Host "✅ Done: $dest" -ForegroundColor Green
}

Write-Host "`n🔍 Searching for String Spacing implementation..." -ForegroundColor Yellow

# Find all Python files with "stringspacer" in name
$found = Get-ChildItem -Recurse -Filter "*stringspacer*.py" | ForEach-Object {
    $lines = (Get-Content $_.FullName | Measure-Object -Line).Lines
    [PSCustomObject]@{
        Path = $_.FullName
        Lines = $lines
        Status = if ($lines -gt 50) { "✅ COMPLETE" } else { "⚠️ STUB" }
    }
}

$found | Format-Table -AutoSize

# Search for implementation functions
Write-Host "`n🎯 Searching for 'def generate_geometry'..." -ForegroundColor Yellow
Get-ChildItem -Recurse -Filter "*.py" | Select-String -Pattern "def generate_geometry" -List | 
    ForEach-Object { 
        Write-Host "FOUND: $($_.Path)" -ForegroundColor Green
    }

Write-Host "`n✅ Extraction complete!" -ForegroundColor Green
```

---

## Expected ZIP Files

| File | Expected Contents | Status |
|------|-------------------|--------|
| `Luthiers_Tool_Box_Full_v1.zip` | Complete project snapshot (may contain string spacing) | Not extracted |
| `Luthiers_Tool_Box_Full_v2.zip` | Newer version | Not extracted |
| `J45_CAM_Import_Kit.zip` | J-45 template DXF files | Not extracted |
| `LesPaul_CAM_Import_Kit.zip` | Les Paul template DXF files | Not extracted |

---

## What to Look For

### **String Spacing Calculator Files**
```
stringspacer_fretfind_stewmac.py     # Should be 200-500 lines (not 36)
```

### **Required Functions** (must exist):
```python
def generate_geometry(spacing: SpacingInputs, scale: ScaleInputs, 
                      options: LayoutOptions = None) -> GeometryResult:
    """
    Calculate string positions, fret lines, and compensation.
    """
    # BenchMuse StringSpacer algorithm
    # FretFind2D fret positions
    # StewMac compensation lookup
    pass

def export_dxf(filename: str, geom: GeometryResult, 
               options: LayoutOptions = None):
    """
    Export to R12 DXF with layered geometry.
    Layers: NUT, FRETS_1..n, BRIDGE_BASE, BRIDGE_COMP, STRING_1..n
    """
    pass

def export_csv(filename: str, geom: GeometryResult):
    """
    Export tabular data to CSV.
    Columns: string, nut_x, nut_y, bridge_x, bridge_y, fret_*_x, fret_*_y
    """
    pass
```

---

## Alternative Search Locations

If not found in ZIP files, search these directories:

```powershell
# MVP builds
cd "c:\Users\thepr\Downloads\Luthiers ToolBox\MVP Build_10-11-2025"
Get-ChildItem -Recurse -Filter "*stringspacer*.py"

cd "c:\Users\thepr\Downloads\Luthiers ToolBox\MVP Build_1012-2025"
Get-ChildItem -Recurse -Filter "*stringspacer*.py"

# String Master Scaffolding
cd "c:\Users\thepr\Downloads\Luthiers ToolBox\Guitar Design HTML app\String Master Scaffolding"
Get-ChildItem -Recurse -Filter "*stringspacer*.py"

# Smart Guitar Build
cd "c:\Users\thepr\Downloads\Luthiers ToolBox\Smart Guitar Build"
Get-ChildItem -Recurse -Filter "*string*.py"

# Other variants
cd "c:\Users\thepr\Downloads\Luthiers ToolBox\Guitar Design HTML app-2"
Get-ChildItem -Recurse -Filter "*stringspacer*.py"
```

---

## If Implementation Not Found

### **Rebuild from Scratch**
**Estimated Time**: 1-2 days

**Step 1: Core Algorithm (4-6 hours)**
```python
# File: server/pipelines/string_spacing/string_spacing_calc.py

def benchmuse_string_spacing(nut_width, edge_left, edge_right, gauges):
    """
    BenchMuse StringSpacer: Equal gaps between string edges.
    Accounts for varying string diameters.
    """
    available = nut_width - edge_left - edge_right
    gap_space = available - sum(gauges)
    gap_size = gap_space / (len(gauges) - 1)
    
    positions = []
    x = edge_left + gauges[0]/2
    for i, d in enumerate(gauges):
        positions.append(x)
        if i < len(gauges) - 1:
            x += (d/2 + gap_size + gauges[i+1]/2)
    
    return positions

def fretfind_position(scale_length, fret_number):
    """
    FretFind2D: Equal temperament fret spacing.
    """
    return scale_length - (scale_length / (2 ** (fret_number / 12)))

def stewmac_compensation(gauge_in, action_height=0.08):
    """
    StewMac compensation lookup (approximate values).
    """
    base_comp = {
        0.010: 1.5,   # High E
        0.013: 1.8,   # B
        0.017: 2.2,   # G
        0.026: 3.0,   # D
        0.036: 3.5,   # A
        0.046: 4.0,   # Low E
    }
    comp = base_comp.get(gauge_in, 2.5)
    # Adjust for action height
    if action_height > 0.10:
        comp *= 1.2
    elif action_height < 0.06:
        comp *= 0.8
    return comp
```

**Step 2: DXF Export (2-3 hours)**
```python
# File: server/pipelines/string_spacing/string_spacing_to_dxf.py

def export_dxf(geom: GeometryResult, output_path: str):
    doc = ezdxf.new('R12', setup=True)
    msp = doc.modelspace()
    
    # Layer: NUT (line at x=0)
    for i, (x, y) in enumerate(geom.nut_points):
        msp.add_circle(center=(x, y), radius=0.5, 
                       dxfattribs={'layer': f'STRING_{i+1}', 'color': 6})
    
    # Layers: FRETS_1..n
    for fret_idx, fret_line in enumerate(geom.frets):
        msp.add_line(start=fret_line[0], end=fret_line[1],
                     dxfattribs={'layer': f'FRETS_{fret_idx+1}', 'color': 8})
    
    # Layer: BRIDGE_BASE (uncompensated)
    msp.add_lwpolyline(points=geom.bridge_points_base, close=False,
                       dxfattribs={'layer': 'BRIDGE_BASE', 'color': 3})
    
    # Layer: BRIDGE_COMP (compensated)
    msp.add_lwpolyline(points=geom.bridge_points_comp, close=False,
                       dxfattribs={'layer': 'BRIDGE_COMP', 'color': 2})
    
    doc.saveas(output_path)
```

**Step 3: Vue Component (4-6 hours)**
```vue
<!-- File: client/src/components/toolbox/StringSpacingCalculator.vue -->

<template>
  <div class="string-spacing">
    <h2>🎵 String Spacing Calculator</h2>
    
    <section class="inputs">
      <h3>Nut & Bridge Dimensions</h3>
      <div class="field">
        <label>Nut Width</label>
        <input type="number" v-model.number="nutWidth" />
        <span>{{ units }}</span>
      </div>
      <!-- Similar fields for bridge width, edges, scale length -->
    </section>
    
    <section class="gauges">
      <h3>String Gauges</h3>
      <div v-for="(g, i) in gauges" :key="i">
        <label>String {{ i+1 }}</label>
        <input type="number" v-model.number="gauges[i]" step="0.001" />
        <span>in</span>
      </div>
    </section>
    
    <section class="preview">
      <h3>Preview</h3>
      <svg :viewBox="viewBox">
        <!-- Nut line, string positions, fret lines, bridge -->
      </svg>
    </section>
    
    <section class="actions">
      <button @click="exportDXF">Export DXF</button>
      <button @click="exportCSV">Export CSV</button>
    </section>
  </div>
</template>

<script setup lang="ts">
// BenchMuse spacing calculations
// SVG preview generation
// API calls to backend
</script>
```

**Step 4: Integration (1-2 hours)**
- Add to `client/src/App.vue` navigation
- Create API endpoint in `server/app.py`
- Test with example data

---

## Success Criteria

After extraction, you should find:

- ✅ `stringspacer_fretfind_stewmac.py` with **200+ lines**
- ✅ Functions: `generate_geometry()`, `export_dxf()`, `export_csv()`
- ✅ Example usage in README or test files
- ✅ Working example outputs (CSV/DXF)

---

## Next Steps After Extraction

### **If Found**:
1. Copy complete file to `server/pipelines/string_spacing/`
2. Create API endpoint in `server/app.py`
3. Build Vue component (StringSpacingCalculator.vue)
4. Add to navigation
5. Test with example data
6. Update documentation

**Estimated Time**: 4-6 hours

### **If Not Found**:
1. Rebuild from scratch using documented algorithms
2. Implement BenchMuse + FretFind2D + StewMac compensation
3. Create DXF/CSV exporters
4. Build Vue component
5. Integrate and test

**Estimated Time**: 1-2 days

---

## Run This Now

Copy-paste this into PowerShell:

```powershell
cd "c:\Users\thepr\Downloads\Luthiers ToolBox\Guitar Design HTML app\10_06+2025"

Get-ChildItem -Filter "*.zip" | ForEach-Object {
    Write-Host "📦 Extracting: $($_.Name)" -ForegroundColor Cyan
    Expand-Archive -Path $_.FullName -DestinationPath "extracted_$($_.BaseName)" -Force
    Write-Host "✅ Done!`n" -ForegroundColor Green
}

Write-Host "🔍 Searching for String Spacing implementation...`n" -ForegroundColor Yellow

Get-ChildItem -Recurse -Filter "*stringspacer*.py" | ForEach-Object {
    $lines = (Get-Content $_.FullName | Measure-Object -Line).Lines
    $status = if ($lines -gt 50) { "✅ COMPLETE ($lines lines)" } else { "⚠️ STUB ($lines lines)" }
    Write-Host "$status : $($_.FullName)"
}

Write-Host "`n🎯 Searching for implementation functions...`n" -ForegroundColor Yellow
$implCount = 0
Get-ChildItem -Recurse -Filter "*.py" | Select-String -Pattern "def (generate_geometry|export_dxf|export_csv)" -List | 
    ForEach-Object { 
        Write-Host "FOUND: $($_.Path)" -ForegroundColor Green
        $implCount++
    }

if ($implCount -eq 0) {
    Write-Host "`n⚠️ No implementation found. Rebuild from scratch required (1-2 days).`n" -ForegroundColor Yellow
} else {
    Write-Host "`n✅ Implementation found! Ready to integrate (4-6 hours).`n" -ForegroundColor Green
}
```

---

## Status: Ready to Execute ▶️

This script will:
1. Extract all 4 ZIP files
2. Search for complete string spacing implementation
3. Report findings

**Estimated Run Time**: 2-5 minutes
