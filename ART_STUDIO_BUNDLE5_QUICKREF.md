# Art Studio Bundle 5: Quick Reference

**Status:** Backend Complete ✅ | Frontend Pending ⏸️  
**Progress:** 8/15 files (53%)

---

## 🚀 Quick Start

### **Start API Server**
```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

### **Run Tests**
```powershell
pytest tests/test_rosette_cam_bridge.py -v
pytest tests/test_cam_pipeline_rosette_op.py -v
```

---

## 📡 API Endpoints

### **Toolpath Planning**
```http
POST /api/art/rosette/cam/plan_toolpath
Content-Type: application/json

{
  "inner_radius": 25.0,
  "outer_radius": 50.0,
  "units": "mm",
  "tool_d": 6.0,
  "stepover": 0.45,
  "stepdown": 1.5,
  "feed_xy": 1200,
  "feed_z": 400,
  "safe_z": 5.0,
  "cut_depth": 3.0
}
```

**Response:**
```json
{
  "moves": [...],
  "stats": {
    "rings": 5,
    "z_passes": 2,
    "length_mm": 450.5,
    "move_count": 127
  }
}
```

---

### **G-code Generation**
```http
POST /api/art/rosette/cam/post_gcode
Content-Type: application/json

{
  "moves": [...],
  "units": "mm",
  "spindle_rpm": 18000
}
```

**Response:**
```json
{
  "gcode": "G21\nG90\n...\nM30\n",
  "stats": {
    "lines": 127,
    "bytes": 3456
  }
}
```

---

### **Job Creation**
```http
POST /api/art/rosette/jobs/cam_job
Content-Type: application/json

{
  "job_id": "rosette_cam_001",
  "post_preset": "grbl",
  "rings": 5,
  "z_passes": 2,
  "length_mm": 450.5,
  "gcode_lines": 127,
  "meta": {}
}
```

**Response:**
```json
{
  "job_id": "rosette_cam_001",
  "message": "CAM job 'rosette_cam_001' created successfully"
}
```

---

### **Job Retrieval**
```http
GET /api/art/rosette/jobs/{job_id}
```

**Response:**
```json
{
  "id": "rosette_cam_001",
  "job_type": "rosette_cam",
  "created_at": "2025-01-15T14:23:45Z",
  "post_preset": "grbl",
  "rings": 5,
  "z_passes": 2,
  "length_mm": 450.5,
  "gcode_lines": 127,
  "meta": {}
}
```

---

### **Pipeline Execution**
```http
POST /api/cam/pipeline/run
Content-Type: application/json

{
  "ops": [
    {
      "op": "RosetteCam",
      "input": {
        "job_id": "rosette_cam_001",
        "post_preset": "grbl"
      }
    }
  ],
  "meta": {}
}
```

**Response:**
```json
{
  "steps": [
    {
      "step_index": 0,
      "op_type": "RosetteCam",
      "result": {
        "success": true,
        "job_id": "rosette_cam_001",
        "stats": {
          "rings": 5,
          "z_passes": 2,
          "length_mm": 450.5,
          "gcode_lines": 127
        }
      }
    }
  ]
}
```

---

### **Risk Report Creation**
```http
POST /api/cam/risk/reports
Content-Type: application/json

{
  "report_id": "risk_001",
  "lane": "rosette",
  "job_id": "rosette_cam_001",
  "preset": "grbl",
  "source": "art_studio",
  "steps": [
    {
      "op": "RosetteCam",
      "stats": {
        "rings": 5,
        "z_passes": 2,
        "length_mm": 450.5
      }
    }
  ],
  "summary": {
    "total_length_mm": 450.5,
    "estimated_time_s": 90
  },
  "meta": {}
}
```

**Response:**
```json
{
  "report_id": "risk_001",
  "created_at": "2025-01-15T14:25:00Z",
  "message": "Risk report saved successfully"
}
```

---

### **Risk Report Listing**
```http
GET /api/cam/risk/reports?lane=rosette&preset=grbl&limit=20
```

**Response:**
```json
[
  {
    "id": "risk_001",
    "created_at": "2025-01-15T14:25:00Z",
    "lane": "rosette",
    "job_id": "rosette_cam_001",
    "preset": "grbl",
    "source": "art_studio",
    "summary": {
      "total_length_mm": 450.5,
      "estimated_time_s": 90
    }
  }
]
```

---

## 🔄 Integration Flow

```
1. Design Rosette
   ArtStudioRosette.vue
   ↓ Configure inner/outer radius, segments

2. Generate Toolpath
   POST /api/art/rosette/cam/plan_toolpath
   ↓ Returns moves[] + stats{}

3. Generate G-code
   POST /api/art/rosette/cam/post_gcode
   ↓ Returns gcode text + stats{}

4. Create Job
   POST /api/art/rosette/jobs/cam_job
   ↓ Stores job for pipeline

5. Send to Pipeline
   Navigate to /lab/pipeline?lane=rosette&job_id=X&preset=grbl

6. Load Job
   PipelineLab.vue
   GET /api/art/rosette/jobs/{job_id}
   ↓ Display job stats

7. Execute Pipeline
   POST /api/cam/pipeline/run
   ↓ Returns step results

8. Save Risk Report
   POST /api/cam/risk/reports
   ↓ Stores report for timeline

9. View Timeline
   Navigate to /lab/risk
   CamRiskTimeline.vue
   GET /api/cam/risk/reports?lane=rosette
   ↓ Display all reports with filters
```

---

## 📁 File Locations

**Backend Services:**
- `services/api/app/services/rosette_cam_bridge.py` - Toolpath + G-code
- `services/api/app/services/art_jobs_store.py` - Job storage
- `services/api/app/services/pipeline_ops_rosette.py` - Pipeline op
- `services/api/app/services/risk_reports_store.py` - Risk storage

**Backend Routers:**
- `services/api/app/routers/art_studio_rosette_router.py` - CAM endpoints
- `services/api/app/routers/cam_pipeline_router.py` - Pipeline API
- `services/api/app/routers/cam_risk_router.py` - Risk API

**Tests:**
- `services/api/tests/test_rosette_cam_bridge.py` - CAM bridge tests
- `services/api/tests/test_cam_pipeline_rosette_op.py` - Pipeline op tests

**Storage:**
- `data/art_jobs.json` - CAM jobs (auto-created)
- `data/cam_risk_reports.json` - Risk reports (auto-created)

---

## 🧪 Testing Checklist

### **Unit Tests**
- [ ] `pytest tests/test_rosette_cam_bridge.py -v`
  - Toolpath generation
  - G-code post-processing
  - Inch/mm units
  - Multiple Z passes
  - Edge cases

- [ ] `pytest tests/test_cam_pipeline_rosette_op.py -v`
  - Basic pipeline op
  - Missing job handling
  - Metadata preservation
  - Multiple jobs

### **Manual API Tests**
- [ ] Plan toolpath (POST /cam/plan_toolpath)
- [ ] Post G-code (POST /cam/post_gcode)
- [ ] Create job (POST /jobs/cam_job)
- [ ] Get job (GET /jobs/{job_id})
- [ ] Run pipeline (POST /api/cam/pipeline/run)
- [ ] Create risk report (POST /api/cam/risk/reports)
- [ ] List risk reports (GET /api/cam/risk/reports)

### **End-to-End Workflow**
- [ ] Design → Plan → Post → Create Job → Pipeline → Risk Report → Timeline
- [ ] Navigation with query params (lane, job_id, preset)
- [ ] Breadcrumb navigation back to source
- [ ] Auto-filtering by preset in compare view

---

## 🐛 Troubleshooting

### **Issue: Module not found errors**
**Solution:**
```powershell
cd services/api
pip install -r requirements.txt
```

### **Issue: Router not loaded**
**Check:**
1. Import statement in `main.py` (lines ~273-285)
2. Router registration (lines ~369-377)
3. Console output for warning messages

### **Issue: Jobs not persisting**
**Check:**
1. `data/` directory exists
2. Write permissions on `data/art_jobs.json`
3. Console logs for storage errors

### **Issue: Risk reports not showing**
**Check:**
1. `data/cam_risk_reports.json` exists
2. Query params match report attributes (lane, preset, source)
3. Limit parameter (default 200)

---

## 📝 Parameters Reference

### **Toolpath Planning**
| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `center_x` | float | any | 0.0 | Center X coordinate |
| `center_y` | float | any | 0.0 | Center Y coordinate |
| `inner_radius` | float | > 0 | required | Inner radius (mm or inch) |
| `outer_radius` | float | > inner | required | Outer radius (mm or inch) |
| `units` | string | mm/inch | "mm" | Unit system |
| `tool_d` | float | > 0 | required | Tool diameter |
| `stepover` | float | 0.1-0.9 | 0.45 | Stepover fraction (45%) |
| `stepdown` | float | > 0 | 1.5 | Z stepdown per pass (mm) |
| `feed_xy` | float | > 0 | 1200 | XY feed rate (mm/min) |
| `feed_z` | float | > 0 | 400 | Z plunge rate (mm/min) |
| `safe_z` | float | > 0 | 5.0 | Safe retract height (mm) |
| `cut_depth` | float | > 0 | 3.0 | Total cut depth (mm) |
| `circle_segments` | int | 16-256 | 64 | Circle approximation |

### **G-code Post-Processing**
| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `moves` | array | required | - | Toolpath moves list |
| `units` | string | mm/inch | "mm" | Unit system |
| `spindle_rpm` | int | 0-30000 | 18000 | Spindle speed |

---

## 🔮 Future Enhancements

### **Pipeline Operations**
- [ ] AdaptivePocket operation
- [ ] ReliefRoughing operation
- [ ] HelicalRamping operation
- [ ] Multi-operation sequencing

### **Post-Processors**
- [ ] Mach4 post-processor
- [ ] LinuxCNC post-processor
- [ ] PathPilot post-processor
- [ ] Integration with existing multi-post system

### **Storage**
- [ ] Migrate to SQLite (optional)
- [ ] Add job search/filtering
- [ ] Add job archiving/cleanup
- [ ] Export reports as CSV/JSON

### **Analytics**
- [ ] Toolpath optimization suggestions
- [ ] Cut time prediction accuracy tracking
- [ ] Risk score trending
- [ ] Preset performance comparison

---

**Status:** Backend Complete ✅  
**Next:** Frontend Vue component extensions  
**Estimated Remaining:** 3-4 hours for frontend implementation
