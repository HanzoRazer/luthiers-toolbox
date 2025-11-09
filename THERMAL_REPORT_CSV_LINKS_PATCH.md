# Thermal Report CSV Links Patch

**Status:** ✅ Implemented  
**Date:** November 5, 2025  
**Component:** Module M.3 Thermal Analytics Enhancement

---

## 🎯 Overview

This patch adds an optional **CSV Downloads** footer section to thermal reports (Markdown), providing ready-to-run `curl` commands for downloading related CSV exports with the same job parameters.

**Key Features:**
- ✅ Optional footer controlled by `include_csv_links` boolean parameter
- ✅ Ready-to-run `curl` commands for 3 CSV endpoints
- ✅ Automatic filename prediction matching server CSV export logic
- ✅ UI checkbox (checked by default) in AdaptivePocketLab
- ✅ CI test validating footer generation

---

## 📋 Implementation

### **1. Server Enhancement**

**File:** `services/api/app/routers/cam_metrics_router.py`

**Added field to `ThermalReportIn` model:**
```python
class ThermalReportIn(BaseModel):
    # ... existing fields ...
    include_csv_links: bool = False  # Include CSV download commands in footer
```

**Added footer section in `/thermal_report_md` endpoint:**
```python
@router.post("/thermal_report_md")
def thermal_report_md(body: ThermalReportIn):
    # ... existing report generation ...
    
    # --- OPTIONAL FOOTER WITH CSV LINKS ---
    if body.include_csv_links:
        # Predict filenames (server uses these stems in CSV endpoints)
        energy_stem = safe_stem(body.job_name, prefix="energy")
        heat_stem   = safe_stem(body.job_name, prefix="heat_ts")
        bott_stem   = safe_stem(body.job_name, prefix="bottlenecks")

        w("\n---\n\n")
        w("## CSV Downloads\n")
        w("The following commands will download CSVs...")
        
        # Energy CSV
        w(f"**Energy per segment** → `{energy_stem}.csv`\n\n")
        w("```bash\n")
        w("curl -X POST $API/cam/metrics/energy_csv ...\n")
        w("```\n\n")
        
        # Heat CSV
        w(f"**Heat time-series** → `{heat_stem}.csv`\n\n")
        w("```bash\n")
        w("curl -X POST $API/cam/metrics/heat_timeseries_csv ...\n")
        w("```\n\n")
        
        # Bottleneck CSV
        w(f"**Bottleneck tags** → `{bott_stem}.csv`\n\n")
        w("```bash\n")
        w("curl -X POST $API/cam/metrics/bottleneck_csv ...\n")
        w("```\n\n")
        
        w("> Tip: in the app UI, you can also click **Export CSV** buttons...\n")
```

**Footer Generates:**
- Predicted filenames for all 3 CSV exports
- Complete `curl` commands with JSON payloads
- Placeholder `$API` for base URL substitution
- Hint to replace `<PASTE_MOVES_JSON>` with actual moves array

---

### **2. Client UI Enhancement**

**File:** `packages/client/src/components/AdaptivePocketLab.vue`

**Added ref variable:**
```typescript
const includeCsvLinks = ref(true)  // Include CSV download links in thermal report
```

**Added checkbox to Heat over Time card:**
```vue
<label class="text-xs flex items-center gap-2">
  <input type="checkbox" v-model="includeCsvLinks">
  Include CSV download links in report
</label>
```

**Updated `exportThermalReport()` function:**
```typescript
const body = {
  // ... existing fields ...
  include_csv_links: includeCsvLinks.value
}
```

**Default State:** Checkbox is **checked** by default (`ref(true)`)

---

### **3. CI Test**

**File:** `.github/workflows/adaptive_pocket.yml`

**New Test:** `M.3 - Thermal report includes CSV links section when requested`

**Validation Steps:**
1. Generate plan with moves (120×80mm pocket)
2. Request thermal report with `include_csv_links: true`
3. Validate `## CSV Downloads` section present
4. Validate all 3 endpoint references: `energy_csv`, `heat_timeseries_csv`, `bottleneck_csv`
5. Validate all 3 `curl` commands present

**Assertions:**
```python
assert "## CSV Downloads" in text
assert "energy_csv" in text
assert "heat_timeseries_csv" in text
assert "bottleneck_csv" in text
assert "curl -X POST $API/cam/metrics/energy_csv" in text
assert "curl -X POST $API/cam/metrics/heat_timeseries_csv" in text
assert "curl -X POST $API/cam/metrics/bottleneck_csv" in text
```

---

## 📖 Example Output

### **Thermal Report Footer (When Enabled)**

```markdown
---

## CSV Downloads
The following commands will download CSVs generated with the same inputs as this report.

**Energy per segment** → `energy_LP_test.csv`

```bash
curl -X POST $API/cam/metrics/energy_csv \
  -H 'Content-Type: application/json' \
  -d '{"moves":<PASTE_MOVES_JSON>,"material_id":"maple_hard","tool_d":6.0,"stepover":0.45,"stepdown":1.5,"job_name":"LP_test"}' -o energy_LP_test.csv
```

**Heat time-series** → `heat_ts_LP_test.csv`

```bash
curl -X POST $API/cam/metrics/heat_timeseries_csv \
  -H 'Content-Type: application/json' \
  -d '{"moves":<PASTE_MOVES_JSON>,"machine_profile_id":"Mach4_Router_4x8","material_id":"maple_hard","tool_d":6.0,"stepover":0.45,"stepdown":1.5,"bins":200,"job_name":"LP_test"}' -o heat_ts_LP_test.csv
```

**Bottleneck tags** → `bottlenecks_LP_test.csv`

```bash
curl -X POST $API/cam/metrics/bottleneck_csv \
  -H 'Content-Type: application/json' \
  -d '{"moves":<PASTE_MOVES_JSON>,"job_name":"LP_test"}' -o bottlenecks_LP_test.csv
```

> Tip: in the app UI, you can also click **Export CSV** buttons without using curl.
```

---

## 🧪 Testing

### **Local Testing**

1. **Start API server:**
```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

2. **Generate plan with moves:**
```powershell
$plan = @{
  loops = @(@{pts = @(@(0,0),@(120,0),@(120,80),@(0,80))})
  units = "mm"
  tool_d = 6.0
  stepover = 0.45
  stepdown = 1.5
  feed_xy = 1200
  safe_z = 5
  machine_profile_id = "Mach4_Router_4x8"
} | ConvertTo-Json -Depth 10

$r1 = Invoke-RestMethod -Uri "http://localhost:8000/cam/pocket/adaptive/plan" `
  -Method POST -Body $plan -ContentType "application/json"
```

3. **Request thermal report with CSV links:**
```powershell
$moves = $r1.moves | ConvertTo-Json -Depth 10 -Compress

$body = @{
  moves = $r1.moves
  machine_profile_id = "Mach4_Router_4x8"
  material_id = "maple_hard"
  tool_d = 6
  stepover = 0.45
  stepdown = 1.5
  bins = 120
  job_name = "test_pocket"
  include_csv_links = $true
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:8000/cam/metrics/thermal_report_md" `
  -Method POST -Body $body -ContentType "application/json" `
  -OutFile "thermal_test.md"

# View report
Get-Content thermal_test.md
```

4. **Verify footer sections:**
```powershell
$content = Get-Content thermal_test.md -Raw
$content -match "## CSV Downloads"  # Should be True
$content -match "energy_csv"        # Should be True
$content -match "curl -X POST"      # Should be True
```

---

## 🎨 UI Workflow

### **User Experience**

1. **Navigate to AdaptivePocketLab component**
2. **Run adaptive pocket plan** (generates moves)
3. **Scroll to "Heat over Time" section**
4. **Notice checkbox:** "Include CSV download links in report" (checked by default)
5. **Click "Export Report (MD)"** button
6. **Download `thermal_report_<job_name>.md`**
7. **Open Markdown file:**
   - If checkbox was **checked**: Footer section with 3 `curl` commands present
   - If checkbox was **unchecked**: No footer section

### **Checkbox States**

| Checkbox State | Result |
|----------------|--------|
| ✅ Checked (default) | Footer with CSV links included |
| ❌ Unchecked | No footer (clean report) |

---

## 🔧 Configuration

### **Server Defaults**

```python
class ThermalReportIn(BaseModel):
    include_csv_links: bool = False  # Server default: disabled
```

**Why disabled by default?** Server is conservative, client controls UX preference.

### **Client Defaults**

```typescript
const includeCsvLinks = ref(true)  // Client default: enabled
```

**Why enabled by default?** Most users benefit from ready-to-run CSV commands.

### **Filename Prediction**

All filenames use `safe_stem()` utility:
```python
energy_stem = safe_stem(job_name, prefix="energy")
# Example: job_name="LP Test!" → "energy_LP_Test.csv"
```

**Rules:**
- Lowercase prefix
- Job name sanitized (remove special chars, replace spaces with `_`)
- `.csv` extension appended

---

## 📊 Use Cases

### **1. Documentation & Reporting**

**Scenario:** Generate comprehensive analysis package for client review

**Workflow:**
1. Export thermal report with CSV links ✅
2. Share Markdown file with client
3. Client runs `curl` commands to get raw data
4. Client analyzes CSVs in Excel/Python

**Benefit:** Single report file contains both analysis and data retrieval instructions

---

### **2. Reproducibility**

**Scenario:** Team member needs to reproduce exact analysis from report

**Workflow:**
1. Open thermal report Markdown
2. Copy moves JSON from original plan response
3. Replace `<PASTE_MOVES_JSON>` in `curl` commands
4. Replace `$API` with base URL
5. Run commands to download identical CSVs

**Benefit:** Complete parameter preservation in report footer

---

### **3. Automation Pipelines**

**Scenario:** CI/CD pipeline generates thermal reports + CSVs

**Workflow:**
1. Pipeline runs adaptive pocket plan
2. Pipeline requests thermal report with `include_csv_links: true`
3. Pipeline extracts `curl` commands from Markdown
4. Pipeline executes commands to download CSVs
5. Pipeline archives report + CSVs together

**Benefit:** Self-documenting reports enable automated data retrieval

---

### **4. Training & Tutorials**

**Scenario:** Teach users how to access CSV exports

**Workflow:**
1. Generate example thermal report with CSV links
2. Use report as tutorial material
3. Students copy/paste commands to learn API

**Benefit:** Live examples with real parameters

---

## 🐛 Troubleshooting

### **Issue:** Footer not appearing in exported report

**Solution:**
1. Check checkbox state (must be ✅ checked)
2. Verify `include_csv_links: true` in request body
3. Check browser console for fetch errors
4. Verify server endpoint is `/thermal_report_md` (not `/thermal_report`)

---

### **Issue:** `curl` commands fail with "Invalid JSON"

**Solution:**
1. Replace `<PASTE_MOVES_JSON>` with actual moves array from plan response
2. Ensure JSON is properly escaped (use `jq` or JSON validator)
3. Replace `$API` with actual base URL (e.g., `http://localhost:8000`)

**Correct usage:**
```bash
# Extract moves from plan
MOVES=$(curl -X POST http://localhost:8000/cam/pocket/adaptive/plan \
  -H 'Content-Type: application/json' \
  -d '{"loops":[...]}' | jq -c '.moves')

# Use in CSV command
curl -X POST http://localhost:8000/cam/metrics/energy_csv \
  -H 'Content-Type: application/json' \
  -d "{\"moves\":$MOVES,\"material_id\":\"maple_hard\",\"tool_d\":6,\"stepover\":0.45,\"stepdown\":1.5}" \
  -o energy.csv
```

---

### **Issue:** Filename mismatch between report and actual CSV download

**Solution:**
- Server uses `safe_stem()` for filename sanitization
- Special characters removed, spaces replaced with underscores
- Report footer **predicts** filenames using same logic
- If mismatch occurs, check `job_name` parameter (case-sensitive)

**Example:**
```python
job_name = "Test Pocket!"  # Input
# Report predicts: energy_Test_Pocket.csv
# Server generates: energy_Test_Pocket.csv ✅ Match
```

---

## ✅ Integration Checklist

- [x] Add `include_csv_links` field to `ThermalReportIn` model
- [x] Implement CSV Downloads footer section in `/thermal_report_md`
- [x] Add `includeCsvLinks` ref in AdaptivePocketLab.vue
- [x] Add checkbox UI element in Heat over Time card
- [x] Update `exportThermalReport()` to pass `include_csv_links`
- [x] Add CI test validating footer generation
- [x] Document patch features and usage
- [ ] Test with real pocket geometry (user validation)
- [ ] Test `curl` commands with live API (user validation)

---

## 📚 See Also

- [Thermal Report Patch](./THERMAL_REPORT_PATCH.md) - Core thermal report feature
- [Module M.3 Complete](./MODULE_M3_COMPLETE.md) - Energy & heat analytics
- [Adaptive Pocketing Module L](./ADAPTIVE_POCKETING_MODULE_L.md) - Pocket planning

---

**Status:** ✅ Patch Complete  
**Backward Compatible:** Yes (new optional parameter, default `false`)  
**Breaking Changes:** None  
**Next Steps:** User testing with real geometry and live API validation
