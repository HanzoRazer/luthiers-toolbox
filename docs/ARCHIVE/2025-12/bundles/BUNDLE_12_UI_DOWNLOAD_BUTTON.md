# Bundle #12 — Surfacing job_id + UI Download Button (N14.x)

**Status:** ✅ COMPLETE  
**Date:** December 2025  
**Module:** RMOS Rosette CNC Export

---

## 🎯 Overview

Bundle #12 completes the end-to-end operator report workflow by exposing the `job_id` in API responses and adding a user-friendly "Download Operator PDF" button to the RMOS Studio UI. Operators can now generate CNC exports and immediately download print-ready PDF checklists.

**Key Features:**
- ✅ `job_id` surfaced in `/export-cnc` API response
- ✅ Frontend stores `job_id` for each CNC export
- ✅ "Download Operator PDF" button in CNCExportPanel
- ✅ One-click PDF download via browser
- ✅ Job ID displayed in export summary for traceability

---

## 📁 Files Modified

### **Backend (1 file):**

1. **`services/api/app/api/routes/rmos_rosette_api.py`** (UPDATED)
   - Added `job_id: str` as first field in `CNCExportResponse` model
   - Return `job_id=job_id` in `export_cnc_for_ring()` endpoint response

### **Frontend (2 files):**

2. **`packages/client/src/stores/useRosetteDesignerStore.ts`** (UPDATED)
   - Added `job_id: string` to `CNCExportResult` interface

3. **`packages/client/src/components/rmos/CNCExportPanel.vue`** (UPDATED)
   - Added "Download Operator PDF" button (visible when `cncExport.job_id` exists)
   - Added `job_id` display in Export Summary section
   - Added `onDownloadReport()` handler function
   - Added button styling (blue theme with hover states)

---

## 🔌 API Changes

### **CNCExportResponse Model (Before):**

```python
class CNCExportResponse(BaseModel):
    ring_id: int
    toolpaths: List[CNCSegmentModel]
    jig_alignment: JigAlignmentModel
    safety: CNCSafetyModel
    simulation: CNCSimulationModel
    metadata: Dict[str, Any]
    operator_report_md: Optional[str] = None
```

### **CNCExportResponse Model (After):**

```python
class CNCExportResponse(BaseModel):
    job_id: str = Field(..., description="JobLog identifier for traceability and report retrieval")
    ring_id: int
    toolpaths: List[CNCSegmentModel]
    jig_alignment: JigAlignmentModel
    safety: CNCSafetyModel
    simulation: CNCSimulationModel
    metadata: Dict[str, Any]
    operator_report_md: Optional[str] = Field(None, description="Markdown operator checklist")
```

### **Response Example:**

```json
{
  "job_id": "JOB-ROSETTE-20251201-153045-abc123",
  "ring_id": 0,
  "toolpaths": [...],
  "jig_alignment": {...},
  "safety": {...},
  "simulation": {...},
  "metadata": {...},
  "operator_report_md": "# RMOS Studio – Operator Checklist..."
}
```

---

## 🎨 UI Changes

### **CNCExportPanel Layout (Before):**

```
[Export CNC for Selected Ring] [Exporting...]

Export Summary
Ring ID: 0
Toolpath segments: 156
Estimated runtime: 32.1 s (1 pass)
```

### **CNCExportPanel Layout (After):**

```
[Export CNC for Selected Ring] [Exporting...] [Download Operator PDF]

Export Summary
Job ID: JOB-ROSETTE-20251201-153045-abc123
Ring ID: 0
Toolpath segments: 156
Estimated runtime: 32.1 s (1 pass)
```

### **Button Styling:**

- **Color:** Blue (`#0066cc`)
- **Hover:** Darker blue (`#0052a3`)
- **Active:** Darkest blue (`#004080`)
- **Padding:** 0.5rem × 1rem
- **Border Radius:** 4px
- **Text:** White, 0.9rem

---

## 🧪 Testing Bundle #12

### **1. Start Full Stack:**

```powershell
# Backend
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd packages/client
npm run dev  # Opens http://localhost:5173
```

### **2. Test End-to-End Workflow:**

1. **Open RMOS Studio UI:**
   - Navigate to Rosette Designer view
   - Add a ring (radius: 45mm, width: 3mm, tile length: 5mm)

2. **Generate Segmentation:**
   - Click "Segment Ring" button
   - Verify tiles generated

3. **Generate Slices:**
   - Click "Generate Slices" button
   - Verify slice batch created

4. **Export CNC:**
   - Select material (e.g., "Hardwood")
   - Configure jig origin (X: 0, Y: 0, Rotation: 0°)
   - Click "Export CNC for Selected Ring"

5. **Verify Response:**
   - Check Export Summary shows:
     - ✅ **Job ID:** `JOB-ROSETTE-20251201-...`
     - ✅ Ring ID: 0
     - ✅ Toolpath segments: 156
     - ✅ Estimated runtime: ~32 s

6. **Download PDF:**
   - Click "Download Operator PDF" button (should appear after export)
   - Browser should open new tab with PDF download
   - Verify filename: `rmos_operator_report_JOB-ROSETTE-20251201-....pdf`

7. **Verify PDF Content:**
   - Open downloaded PDF
   - Check for all 6 sections (Header, Setup, Safety, Runtime, Checklists, Notes)
   - Verify Job ID matches UI display

---

## 📊 Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ User Action: Click "Export CNC for Selected Ring"          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ POST /api/rmos/rosette/export-cnc                          │
│   - Creates JobLog entry (gets job_id)                     │
│   - Generates toolpaths, safety, simulation                │
│   - Generates operator report Markdown                     │
│   - Stores everything in JobLog results                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Response: CNCExportResponse                                 │
│   - job_id: "JOB-ROSETTE-20251201-..."                    │
│   - toolpaths, safety, simulation, metadata               │
│   - operator_report_md (Markdown text)                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Frontend: useRosetteDesignerStore                          │
│   - Stores full response in cncExport.value               │
│   - job_id now available for PDF download                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ UI: CNCExportPanel                                          │
│   - Displays Job ID in summary                             │
│   - Shows "Download Operator PDF" button                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ User Action: Click "Download Operator PDF"                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Browser: window.open(url, '_blank')                        │
│   - GET /api/rmos/rosette/operator-report-pdf/{job_id}    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Backend: download_operator_report_pdf(job_id)              │
│   - Fetches JobLog entry by job_id                        │
│   - Reads operator_report_md from results                 │
│   - Converts Markdown → PDF                                │
│   - Returns PDF with Content-Disposition header           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Browser: Downloads PDF                                      │
│   - Filename: rmos_operator_report_{job_id}.pdf           │
│   - User saves to disk for printing                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Implementation Details

### **Backend Changes:**

```python
# 1. Add job_id to response model
class CNCExportResponse(BaseModel):
    job_id: str  # NEW: First field for traceability

# 2. Return job_id in endpoint
return CNCExportResponse(
    job_id=job_id,  # NEW: Surface JobLog ID
    ring_id=export_bundle.ring_id,
    # ... rest of fields
)
```

### **Frontend TypeScript Changes:**

```typescript
// 1. Add job_id to interface
export interface CNCExportResult {
  job_id: string  // NEW: JobLog identifier

// 2. Store automatically captures it (no code change needed)
const data = await resp.json()
cncExport.value = data as CNCExportResult  // job_id included
```

### **Frontend Vue Changes:**

```vue
<!-- 1. Show job_id in summary -->
<p>
  <strong>Job ID:</strong> {{ cncExport.job_id }}<br />

<!-- 2. Add download button -->
<button
  v-if="cncExport && cncExport.job_id"
  @click="onDownloadReport"
  class="download-pdf-btn"
>
  Download Operator PDF
</button>

<!-- 3. Add handler -->
<script setup>
function onDownloadReport() {
  const url = `/api/rmos/rosette/operator-report-pdf/${encodeURIComponent(
    cncExport.value.job_id
  )}`
  window.open(url, '_blank')
}
</script>
```

---

## 🚀 Usage in Production

### **Operator Workflow (Complete):**

1. **Design rosette ring** in RMOS Studio
   - Configure radius, width, tile length, kerf, angles

2. **Generate segmentation**
   - Computes tile count and angular distribution

3. **Generate slices**
   - Applies kerf compensation, herringbone, twist

4. **Export CNC**
   - Selects material type (hardwood/softwood/composite)
   - Configures jig origin and rotation
   - Clicks "Export CNC for Selected Ring"

5. **Review results**
   - Views toolpath segment count
   - Checks safety decision (allow/block/override)
   - Reviews estimated runtime

6. **Download operator PDF** ⭐ NEW
   - Clicks "Download Operator PDF" button
   - Browser downloads PDF checklist
   - Operator prints PDF for shop floor

7. **Execute physical job**
   - Uses printed checklist during CNC operation
   - Fills in pre-run checklist (6 items)
   - Records post-run notes

8. **Archive documentation**
   - Job ID links PDF to digital JobLog record
   - Enables historical lookup and reprint

---

## 🎯 Design Decisions

### **Why window.open() for Download?**
- ✅ Simplest browser API for file downloads
- ✅ Works across all modern browsers
- ✅ No need for blob handling or anchor elements
- ✅ Opens in new tab (user can decide to save or view)

**Alternative Considered:**
```typescript
// Fetch + Blob approach (more complex, same result)
const response = await fetch(url)
const blob = await response.blob()
const link = document.createElement('a')
link.href = URL.createObjectURL(blob)
link.download = filename
link.click()
```

### **Why job_id First in Response Model?**
- ✅ Most important field for traceability
- ✅ Establishes clear primary key pattern
- ✅ Aligns with API best practices (ID fields first)
- ✅ Makes debugging easier (ID visible in logs)

### **Why v-if on Download Button?**
- ✅ Progressive enhancement (only appears after export)
- ✅ Guards against undefined job_id
- ✅ Clean UI (no disabled button clutter)
- ✅ Clear user flow (export → review → download)

### **Why Blue Button Color?**
- ✅ Distinguishes from primary action (green export button)
- ✅ Industry standard for download/info actions
- ✅ High contrast with white text
- ✅ Accessible (WCAG AA compliant)

---

## ✅ Integration Checklist

- [x] Add `job_id` field to `CNCExportResponse` Pydantic model
- [x] Return `job_id` in `/export-cnc` endpoint response
- [x] Add `job_id` to `CNCExportResult` TypeScript interface
- [x] Add "Download Operator PDF" button to `CNCExportPanel.vue`
- [x] Add `job_id` display in Export Summary
- [x] Add `onDownloadReport()` handler function
- [x] Add button styling (blue theme)
- [x] Test end-to-end workflow
- [ ] Add user documentation/tutorial (optional)
- [ ] Add download confirmation toast (future enhancement)

---

## 🔮 Future Enhancements

### **Bundle #13 (N14.x): Download Bundle (ZIP)**
- Multi-file export:
  - Operator checklist (PDF)
  - G-code program (NC file)
  - DXF/SVG geometry (visual reference)
  - Job summary (JSON metadata)
- Single ZIP download with all files

### **Bundle #14 (N10.x): JobLog History Panel**
- Table view of past CNC exports
- Columns: Job ID, Date, Ring ID, Material, Runtime, Status
- Action buttons: "Download PDF", "Rerun", "View Details"
- Filter by date range, ring ID, material

### **Bundle #15 (N14.x): PDF Customization UI**
- Add company logo upload
- Select CSS theme (light/dark, color schemes)
- Configure margins and page size
- Add custom header/footer text
- Preview PDF before download

### **Bundle #16 (N10.x): Batch Operations**
- Select multiple rings for export
- Generate combined PDF with all checklists
- Download multi-ring ZIP bundle
- Bulk status updates

---

## 📚 See Also

- [Bundle #11 — Operator Report PDF Export](./BUNDLE_11_OPERATOR_REPORT_PDF.md)
- [Bundle #10 — Operator Report Skeleton](./BUNDLE_10_OPERATOR_REPORT.md)
- [Bundle #9 — RMOS Studio CNC Export UI](./BUNDLE_9_CNC_EXPORT_UI.md)
- [Bundle #8 — N10/N14 JobLog Integration](./BUNDLE_8_N10_N14_JOBLOG.md)
- [JobLog Store Documentation](./services/api/app/stores/sqlite_joblog_store.py)
- [RMOS Rosette API Documentation](./services/api/app/api/routes/rmos_rosette_api.py)

---

**Status:** ✅ Bundle #12 Complete  
**Backend Changes:** 2 lines (model + return statement) ✅  
**Frontend Changes:** 25 lines (interface, button, handler, styles) ✅  
**End-to-End Flow:** Complete (design → export → download → print) ✅  
**Ready for Production:** Yes ✅  
**Next Bundle:** #13 (Download Bundle ZIP) or #14 (JobLog History UI) 🚀
