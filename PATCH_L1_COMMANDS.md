# Patch L.1 - Command Reference Card

**Quick commands for testing and using Adaptive Pocketing L.1**

---

## 🚀 Installation

```powershell
# Install L.1 dependency
pip install pyclipper==1.3.0.post5

# Or install all dependencies
cd services/api
pip install -r requirements.txt
```

---

## 🧪 Testing

```powershell
# Start API server
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Run L.1 tests (new terminal)
cd ..\..
.\test_adaptive_l1.ps1

# Run basic tests (original)
.\test_adaptive_pocket.ps1
```

---

## 📡 API Calls

### **Plan with Island**
```powershell
curl -X POST http://127.0.0.1:8000/cam/pocket/adaptive/plan `
  -H 'Content-Type: application/json' `
  -d '{
    "loops": [
      {"pts": [[0,0],[120,0],[120,80],[0,80]]},
      {"pts": [[40,20],[80,20],[80,60],[40,60]]}
    ],
    "tool_d": 6.0,
    "stepover": 0.45,
    "margin": 0.8,
    "strategy": "Spiral",
    "smoothing": 0.3,
    "feed_xy": 1200,
    "safe_z": 5,
    "z_rough": -1.5
  }'
```

### **G-code Export (GRBL)**
```powershell
curl -X POST http://127.0.0.1:8000/cam/pocket/adaptive/gcode `
  -H 'Content-Type: application/json' `
  -d '{
    "loops": [{"pts": [[0,0],[100,0],[100,60],[0,60]]}],
    "tool_d": 6.0,
    "stepover": 0.45,
    "strategy": "Spiral",
    "smoothing": 0.3,
    "post_id": "GRBL"
  }' `
  -o pocket.nc
```

### **Simulation**
```powershell
curl -X POST http://127.0.0.1:8000/cam/pocket/adaptive/sim `
  -H 'Content-Type: application/json' `
  -d '{
    "loops": [{"pts": [[0,0],[80,0],[80,50],[0,50]]}],
    "tool_d": 6.0,
    "stepover": 0.50,
    "strategy": "Lanes"
  }'
```

---

## 📊 Common Scenarios

### **Precision Work (Tight Tolerance)**
```json
{
  "smoothing": 0.1,    // 0.1mm arc tolerance
  "stepover": 0.40,    // 40% stepover
  "margin": 0.5        // Standard margin
}
```

### **Standard Pocketing (Default)**
```json
{
  "smoothing": 0.3,    // 0.3mm arc tolerance
  "stepover": 0.45,    // 45% stepover
  "margin": 0.8        // Conservative margin
}
```

### **Fast Roughing**
```json
{
  "smoothing": 0.8,    // 0.8mm arc tolerance
  "stepover": 0.60,    // 60% stepover
  "margin": 1.0        // Safe margin
}
```

---

## 🐛 Troubleshooting

```powershell
# Check if pyclipper is installed
pip show pyclipper

# Reinstall if needed
pip uninstall pyclipper
pip install pyclipper==1.3.0.post5

# Check API health
curl http://127.0.0.1:8000/health

# View API logs
cd services/api
uvicorn app.main:app --reload --log-level debug
```

---

## 📖 Documentation

```powershell
# Open documentation
start PATCH_L1_ROBUST_OFFSETTING.md       # Full documentation
start PATCH_L1_QUICKREF.md                # Quick reference
start ADAPTIVE_POCKETING_MODULE_L.md      # Module overview
start PATCH_L1_IMPLEMENTATION_SUMMARY.md  # Implementation summary
```

---

## 🔗 Quick Links

- **API Endpoints:** http://127.0.0.1:8000/docs
- **Vue UI:** http://localhost:5173
- **GitHub Repo:** https://github.com/HanzoRazer/guitar_tap

---

## ✅ Quick Validation

```powershell
# 1. Install dependency
pip install pyclipper==1.3.0.post5

# 2. Start API
cd services/api
uvicorn app.main:app --reload &

# 3. Test endpoint
curl http://127.0.0.1:8000/cam/pocket/adaptive/plan `
  -X POST -H 'Content-Type: application/json' `
  -d '{"loops":[{"pts":[[0,0],[60,0],[60,40],[0,40]]}],"tool_d":6.0}'

# 4. Run full tests
.\test_adaptive_l1.ps1
```

---

**Status:** Ready for production use 🚀  
**Version:** L.1.0  
**Last Updated:** November 5, 2025
