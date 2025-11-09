# Unified Pipeline Quick Reference

**Quick start guide for the integrated CAM pipeline system**

---

## 🚀 Quick Start

### 1. Start the API Server
```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

### 2. Access AdaptiveKernelLab
```
http://localhost:5173/lab/adaptive
```

### 3. Test Adaptive Kernel
```typescript
// Load demo loops
Click "Load Demo Rectangle"

// Adjust parameters
tool_d: 6.0 mm
stepover: 0.45
strategy: "Spiral"

// Run
Click "Run Adaptive Kernel"

// View results
✓ Length: 1460mm
✓ Time: 80s
✓ Moves: 43
```

### 4. Export to Pipeline
```typescript
// Enable snippet
☑ Show pipeline snippet

// Send to PipelineLab
Click "Send to PipelineLab"
// ✓ Preset saved to localStorage
```

---

## 📡 API Endpoints

### Adaptive Pocket
```http
POST /api/cam/pocket/adaptive/plan
Content-Type: application/json

{
  "loops": [{"pts": [[0,0], [100,0], [100,60], [0,60]]}],
  "units": "mm",
  "tool_d": 6.0,
  "stepover": 0.45,
  "strategy": "Spiral"
}
```

**Response:**
```json
{
  "moves": [
    {"code": "G0", "z": 5.0},
    {"code": "G1", "x": 97, "y": 3, "f": 1200}
  ],
  "stats": {
    "length_mm": 1460.47,
    "time_s": 80.5,
    "move_count": 43
  }
}
```

---

### Unified Pipeline
```http
POST /cam/pipeline/run
Content-Type: multipart/form-data

file: body.dxf (binary)
pipeline: {
  "ops": [
    {"kind": "dxf_preflight"},
    {"kind": "adaptive_plan"},
    {"kind": "adaptive_plan_run"},
    {"kind": "export_post", "params": {"post_id": "GRBL"}},
    {"kind": "simulate_gcode"}
  ],
  "tool_d": 6.0,
  "units": "mm"
}
```

**Response:**
```json
{
  "ops": [
    {"kind": "dxf_preflight", "ok": true, "payload": {...}},
    {"kind": "adaptive_plan_run", "ok": true, "payload": {...}},
    {"kind": "simulate_gcode", "ok": true, "payload": {...}}
  ],
  "summary": {
    "time_s": 80.5,
    "length_mm": 1460.47
  }
}
```

---

## 🔑 Key Files

| File | Purpose |
|------|---------|
| `services/api/app/routers/pipeline_router.py` | Unified pipeline orchestration |
| `packages/client/src/api/adaptive.ts` | TypeScript API client |
| `packages/client/src/views/AdaptiveKernelLab.vue` | Adaptive dev playground |
| `services/api/app/services/adaptive_kernel.py` | Reusable adaptive bridge |
| `services/api/app/routers/blueprint_cam_bridge.py` | DXF → Adaptive integration |

---

## 🎛️ Pipeline Operations

| Operation | Purpose | Input | Output |
|-----------|---------|-------|--------|
| `dxf_preflight` | Validate DXF | DXF bytes | Validation report |
| `adaptive_plan` | Extract loops | DXF bytes | Loop list |
| `adaptive_plan_run` | Generate toolpath | Loops + params | Moves + stats |
| `export_post` | Add post headers | G-code | Formatted G-code |
| `simulate_gcode` | Run simulation | G-code | Sim stats |

---

## 🧪 Testing Commands

### Python (Direct API)
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Test adaptive endpoint
resp = client.post("/api/cam/pocket/adaptive/plan", json={
    "loops": [{"pts": [[0,0], [100,0], [100,60], [0,60]]}],
    "units": "mm",
    "tool_d": 6.0
})
assert resp.status_code == 200
```

### PowerShell (cURL)
```powershell
# Test pipeline
$body = @{
    "ops" = @(
        @{"kind" = "adaptive_plan"},
        @{"kind" = "adaptive_plan_run"}
    )
    "tool_d" = 6.0
    "units" = "mm"
} | ConvertTo-Json -Depth 10

curl -X POST "http://localhost:8000/cam/pipeline/run" `
  -F "file=@body.dxf" `
  -F "pipeline=$body"
```

---

## 📝 Common Patterns

### Pattern 1: Adaptive Only
```typescript
const result = await planAdaptive({
  loops: [{pts: [[0,0], [100,0], [100,60], [0,60]]}],
  units: "mm",
  tool_d: 6.0,
  strategy: "Spiral"
});
```

### Pattern 2: Adaptive + Post
```json
{
  "ops": [
    {"kind": "adaptive_plan_run"},
    {"kind": "export_post", "params": {"post_id": "GRBL"}}
  ]
}
```

### Pattern 3: Full Pipeline
```json
{
  "ops": [
    {"kind": "dxf_preflight"},
    {"kind": "adaptive_plan"},
    {"kind": "adaptive_plan_run"},
    {"kind": "export_post"},
    {"kind": "simulate_gcode"}
  ]
}
```

---

## 🚨 Troubleshooting

### Error: "Invalid loops JSON"
**Fix:** Ensure JSON array format:
```json
[
  {"pts": [[0,0], [100,0], [100,60], [0,60]]}
]
```

### Error: "Post not found"
**Fix:** Check post exists:
```bash
ls services/api/app/data/posts/grbl.json
```

### Error: "No gcode available"
**Fix:** Add `adaptive_plan_run` before `simulate_gcode`:
```json
{
  "ops": [
    {"kind": "adaptive_plan_run"},  // Generates gcode
    {"kind": "simulate_gcode"}      // Consumes it
  ]
}
```

---

## 🎯 Parameter Cheat Sheet

| Parameter | Default | Range | Purpose |
|-----------|---------|-------|---------|
| `tool_d` | 6.0 | 3-12 mm | End mill diameter |
| `stepover` | 0.45 | 0.3-0.7 | Fraction of tool_d |
| `stepdown` | 2.0 | 0.5-3 mm | Depth per pass |
| `margin` | 0.5 | 0.2-2 mm | Boundary clearance |
| `strategy` | "Spiral" | Spiral/Lanes | Toolpath pattern |
| `feed_xy` | 1200 | 800-2500 | Cutting feed (mm/min) |
| `safe_z` | 5.0 | 3-10 mm | Retract height |

---

## 📚 See Also

- [UNIFIED_PIPELINE_INTEGRATION_COMPLETE.md](./UNIFIED_PIPELINE_INTEGRATION_COMPLETE.md) - Full integration docs
- [ADAPTIVE_POCKETING_MODULE_L.md](./ADAPTIVE_POCKETING_MODULE_L.md) - Adaptive engine details
- [BLUEPRINT_PHASE2_CAM_INTEGRATION.md](./BLUEPRINT_PHASE2_CAM_INTEGRATION.md) - Blueprint bridge docs

---

**Status:** ✅ Ready for Development  
**Last Updated:** November 8, 2025
