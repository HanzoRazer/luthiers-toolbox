# CAM Settings Backup & Restore

Unified backup and restore system for your **Machines**, **Posts**, and **Pipeline Presets** configurations.

---

## 📦 What Gets Backed Up

- **Machines**: Work envelopes, feed rates, acceleration, CAM defaults
- **Posts**: G-code dialects, headers/footers, canned cycles, line numbering
- **Pipeline Presets**: Reusable DXF → Plan → Post → Sim workflows

---

## 🔌 API Endpoints

### **GET `/api/cam/settings/summary`**
Returns counts for each category:
```json
{
  "machines_count": 5,
  "posts_count": 7,
  "pipeline_presets_count": 12
}
```

### **GET `/api/cam/settings/export`**
Exports full configuration as JSON:
```json
{
  "version": "A_N",
  "export_date": "2025-11-15T10:30:00Z",
  "machines": [...],
  "posts": [...],
  "pipeline_presets": [...]
}
```

### **POST `/api/cam/settings/import?overwrite=false|true`**
Imports configuration from exported JSON.

**Parameters:**
- `overwrite=false` (default): Skips items with existing IDs
- `overwrite=true`: Replaces existing items with matching IDs

**Response:**
```json
{
  "imported": {
    "machines": 5,
    "posts": 7,
    "pipeline_presets": 12
  },
  "skipped": {
    "machines": 0,
    "posts": 0,
    "pipeline_presets": 0
  },
  "errors": []
}
```

---

## 💻 Usage Examples

### **PowerShell/Windows**

**Export to file:**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/cam/settings/export" -UseBasicParsing |
  Select-Object -ExpandProperty Content |
  Out-File -FilePath "cam_settings_backup.json" -Encoding utf8
```

**Import without overwriting:**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/cam/settings/import?overwrite=false" `
  -Method POST `
  -ContentType "application/json" `
  -Body (Get-Content "cam_settings_backup.json" -Raw) `
  -UseBasicParsing
```

**Import with overwrite:**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/cam/settings/import?overwrite=true" `
  -Method POST `
  -ContentType "application/json" `
  -Body (Get-Content "cam_settings_backup.json" -Raw) `
  -UseBasicParsing
```

### **Bash/Linux/macOS**

**Export to file:**
```bash
curl -s http://localhost:8000/api/cam/settings/export > cam_settings_backup.json
```

**Import without overwriting:**
```bash
curl -X POST "http://localhost:8000/api/cam/settings/import?overwrite=false" \
  -H "Content-Type: application/json" \
  -d @cam_settings_backup.json
```

**Import with overwrite:**
```bash
curl -X POST "http://localhost:8000/api/cam/settings/import?overwrite=true" \
  -H "Content-Type: application/json" \
  -d @cam_settings_backup.json
```

---

## 🧪 Testing

Run the roundtrip smoke test:
```powershell
.\scripts\cam_settings_roundtrip_smoke.ps1 -BaseUrl "http://localhost:8000"
```

This test:
1. Exports current settings
2. Imports without overwrite (verifies skip logic)
3. Imports with overwrite (verifies replacement)
4. Validates summary counts

---

## 📋 UI Access

Visit **CAM Settings** dashboard in the web interface:
- **Path:** `/settings/cam`
- **Navigation:** Top menu → "CAM Settings"

**Features:**
- View summary counts for machines/posts/presets
- One-click **Export JSON** button
- **Import JSON** with file picker
- **Overwrite** checkbox for import behavior
- Quick links to Machine Manager, Post Manager, Pipeline Lab

---

## ⚠️ Important Notes

### **Overwrite Behavior**
- `overwrite=false`: Safe for merging configs (skips duplicates by ID)
- `overwrite=true`: Replaces existing items (use for full restore)

### **ID Handling**
- Machines and Posts use `id` field for matching
- Pipeline Presets without `id` auto-generate from `name`
- Duplicate IDs with `overwrite=false` → skipped
- Duplicate IDs with `overwrite=true` → replaced

### **Error Handling**
- Import returns partial success with error details
- Failed items listed in `errors` array with `kind`, `id`, and `error` message
- Successfully imported items counted in `imported` object

---

## 🔐 Backup Best Practices

1. **Regular Backups**: Export settings after major configuration changes
2. **Version Control**: Store backup JSON in Git for change tracking
3. **Pre-Migration**: Export before upgrading Luthier's Tool Box
4. **Machine-Specific**: Keep separate backups per machine/shop
5. **Dated Files**: Name exports with timestamps: `cam_settings_2025-11-15.json`

---

## 📁 File Structure

**Exported JSON:**
```json
{
  "version": "A_N",
  "export_date": "2025-11-15T10:30:00Z",
  "machines": [
    {
      "id": "grbl_router_1",
      "name": "GRBL Router 1",
      "controller": "GRBL",
      "units": "mm",
      "limits": {"min_x": 0, "max_x": 800, ...},
      "feed_xy": 3000,
      "rapid": 5000,
      "accel": 1200
    }
  ],
  "posts": [
    {
      "id": "GRBL",
      "name": "GRBL 1.1",
      "dialect": "grbl",
      "header": ["G21", "G90", "G17"],
      "footer": ["M30"]
    }
  ],
  "pipeline_presets": [
    {
      "id": "relief_safe_6mm",
      "name": "Relief Safe 6mm",
      "spec": {...}
    }
  ]
}
```

---

## 🚀 Related Documentation

- [Machine Profiles Module M](../MACHINE_PROFILES_MODULE_M.md) - Machine configuration system
- [Multi-Post Export System](../PATCH_K_EXPORT_COMPLETE.md) - Post-processor integration
- [Pipeline Lab Bundle](../COMPLETE_BUNDLE_EXTRACTION_PLAN.md) - Preset management workflow

---

**Status:** ✅ Production Ready (Item 15 - Phase A_N)  
**Updated:** November 15, 2025
