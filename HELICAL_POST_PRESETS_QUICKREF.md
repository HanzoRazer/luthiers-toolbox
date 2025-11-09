# Helical Post Presets - Quick Reference

**Version:** v16.1.1 | **Date:** November 7, 2025

---

## 🎯 Quick Start

### **1. Frontend Usage (Vue)**
```vue
<select v-model="form.post_preset">
  <option value="GRBL">GRBL</option>
  <option value="Mach3">Mach3</option>
  <option value="Haas">Haas (R-mode, G4 S)</option>
  <option value="Marlin">Marlin</option>
</select>
```

### **2. API Request**
```json
POST /api/cam/toolpath/helical_entry
{
  "cx": 0, "cy": 0, "radius_mm": 6.0,
  "z_target_mm": -3.0, "pitch_mm_per_rev": 1.5,
  "post_preset": "Haas"  // ← Add this field
}
```

### **3. Response**
```json
{
  "stats": {
    "post_preset": "Haas",
    "arc_mode": "R"  // or "IJ"
  }
}
```

---

## 📋 Preset Comparison

| Preset | Arc Mode | Dwell | Use Case |
|--------|----------|-------|----------|
| **GRBL** | I,J | G4 P (ms) | Hobbyist CNC (default) |
| **Mach3** | I,J | G4 P (ms) | Windows CNC |
| **Haas** | R | G4 S (sec) | Industrial VMC ⚠️ |
| **Marlin** | I,J | G4 P (ms) | 3D printer CNC |

**⚠️ CRITICAL:** Haas uses **seconds** for G4 S, not milliseconds!

---

## 🧪 Testing

### **PowerShell (Windows)**
```powershell
cd tools
.\smoke_helix_posts.ps1
```

### **Make (Unix/WSL)**
```bash
make smoke-helix-posts
```

---

## 🔑 Key Files

- `services/api/app/utils/post_presets.py` - Backend presets
- `packages/client/src/views/HelicalRampLab.vue` - UI dropdown
- `tools/smoke_helix_posts.ps1` - Smoke test

---

## 📚 Full Documentation

See [HELICAL_POST_PRESETS.md](./HELICAL_POST_PRESETS.md) for complete details.
