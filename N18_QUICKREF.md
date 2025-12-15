# N18 Quick Reference

**Production-Ready CAM Infrastructure**

---

## 🚀 Quick Start

### **Start Server:**
```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
pip install pyclipper==1.3.0.post5  # N18 dependency
uvicorn app.main:app --reload --port 8000
```

### **Start Client:**
```powershell
cd packages/client
npm install
npm run dev  # Runs on http://localhost:5173
```

---

## 📡 API Endpoints

### **CAM Settings:**
- `GET /api/cam/settings/summary` - Counts
- `GET /api/cam/settings/export` - Full JSON
- `POST /api/cam/settings/import?overwrite=bool` - Restore

### **CAM Backup:**
- `POST /api/cam/backup/snapshot` - Force backup
- `GET /api/cam/backup/list` - List backups
- `GET /api/cam/backup/download/{name}` - Download

### **Simulation:**
- `POST /api/cam/sim/metrics` - Calculate energy/time

### **Intelligence:**
- `GET /api/cam/job_log/insights/{job_id}` - Analyze job
- `GET /api/cam/job_log/insights?severity=warn` - Filter list

---

## 🧪 Test Commands

### **Export Settings:**
```powershell
curl http://localhost:8000/api/cam/settings/export -o settings.json
```

### **Create Backup:**
```powershell
curl -X POST http://localhost:8000/api/cam/backup/snapshot
```

### **List Backups:**
```powershell
curl http://localhost:8000/api/cam/backup/list
```

### **Simulate G-code:**
```powershell
curl -X POST http://localhost:8000/api/cam/sim/metrics \
  -H 'Content-Type: application/json' \
  -d '{
    "gcode_text": "G1 X10 Y10 F1200\nG1 X20 Y20\n",
    "tool_d_mm": 6.0
  }'
```

### **Get Job Insights:**
```powershell
# Create mock job first:
mkdir data/cam_jobs -Force
echo '{"name":"test_job","note":"maple","actual_time_s":180,"estimated_time_s":150}' > data/cam_jobs/job_001.json

curl http://localhost:8000/api/cam/job_log/insights/job_001
```

---

## 🎨 Vue Components

### **CamSettingsView** (`/lab/settings`)
```vue
<CamSettingsView />
```
- Export/import CAM configuration
- Summary cards (machines/posts/presets)
- Overwrite toggle

### **CamBackupPanel**
```vue
<CamBackupPanel />
```
- Auto-backup list (14-day retention)
- Manual snapshot button
- Download links

### **CamJobInsightsPanel**
```vue
<CamJobInsightsPanel job-id="job_001" />
```
- Severity analysis (ok/warn/error)
- Gate/review percentages
- Recommendations

---

## 📂 Key Files

### **Server:**
- `app/util/poly_offset_spiral.py` - N18 spiral pocketing
- `app/services/cam_backup_service.py` - Daily backups
- `app/routers/cam_backup_router.py` - Backup endpoints
- `app/services/sim_energy.py` - Energy simulation
- `app/routers/sim_metrics_router.py` - Metrics endpoint
- `app/routers/job_insights_router.py` - Intelligence

### **Client:**
- `views/CamSettingsView.vue` - Settings hub
- `components/CamBackupPanel.vue` - Backup UI
- `components/CamJobInsightsPanel.vue` - Insights UI
- `views/PipelineLabView.vue` - Main lab (includes backup panel)

---

## 🔧 Configuration

### **Backup Retention:**
Edit `app/services/cam_backup_service.py`:
```python
RETENTION_DAYS = 14  # Change to 7, 30, etc.
```

### **Simulation Defaults:**
Edit `app/models/sim_metrics.py`:
```python
sce_j_per_mm3: float = 1.4  # Hardwood default
feed_xy_max: float = 3000.0  # mm/min
accel_xy: float = 800.0      # mm/s²
```

### **Intelligence Thresholds:**
Edit `app/routers/job_insights_router.py`:
```python
review_threshold_s: float = 300.0   # 5 minutes
critical_gate_s: float = 600.0      # 10 minutes
```

---

## 🐛 Troubleshooting

### **Import Error: pyclipper**
```powershell
pip install pyclipper==1.3.0.post5
```

### **Backup Directory Missing**
```powershell
mkdir data/backups/cam -Force
```

### **Job Files Missing**
```powershell
mkdir data/cam_jobs -Force
# Create sample job:
echo '{"name":"sample","note":"test","actual_time_s":100,"estimated_time_s":90}' > data/cam_jobs/sample.json
```

### **Router Not Found**
Check `main.py` has:
```python
from .routers.cam_backup_router import router as cam_backup_router
app.include_router(cam_backup_router)
```

---

## 📊 Status

**Integrated Systems:** 5 of 6 (83%)

| System | Status |
|--------|--------|
| N18 Spiral PolyCut | ✅ Complete |
| CAM Settings Export/Import | ✅ Complete |
| Daily Auto-Backup | ✅ Complete |
| Simulation Metrics | ⚠️ Backend Ready |
| Job Intelligence | ⚠️ Backend Ready |
| Job-to-Preset Cloning | ⏳ Pending |

---

**Full Documentation:** [N18_FULL_INTEGRATION_COMPLETE.md](./N18_FULL_INTEGRATION_COMPLETE.md)
