# CAM Post Size Dashboard

**Live Monitoring:** Zero-dependency HTML dashboard for tracking G-code post-processor output sizes and smoke test results.

---

## 🎯 Overview

A lightweight, real-time dashboard that visualizes:
- ✅ **Smoke Test Status** (PASS/FAIL)
- ✅ **Size Gate Status** (growth threshold monitoring)
- ✅ **Per-Preset Metrics** (bytes, baseline, delta %)
- ✅ **Visual Indicators** (red/orange/yellow/green chips)
- ✅ **Delta Bars** (±% change visualization)

---

## 📁 Files

| File | Purpose | Size |
|------|---------|------|
| `public_badges/index.html` | Dashboard UI | ~8 KB |
| `public_badges/badges.json` | Data source (CI-generated) | ~1 KB |

---

## 🌐 Deployment

### **Automatic GitHub Pages Deployment**

The dashboard is automatically deployed with your existing GitHub Pages workflow:

1. **CI generates** `badges.json` during smoke tests
2. **Pages workflow** publishes `public_badges/` folder
3. **Dashboard fetches** `badges.json` client-side (no server needed)

**Live URL:**
```
https://<OWNER>.github.io/<REPO>/
```

Or if you have other Pages content:
```
https://<OWNER>.github.io/<REPO>/public_badges/
```

### **Local Testing**

```powershell
# Serve locally
cd public_badges
python -m http.server 8080

# Open browser
start http://localhost:8080
```

---

## 📊 Dashboard Features

### **1. Status Pills**
- **Smoke:** Green (OK) / Red (FAILED) based on `smoke_ok`
- **SizeGate:** Green (OK) / Red (FAILED) based on `size_gate_ok`
- **badges.json:** Direct link to raw JSON data

### **2. Color-Coded Chips**
| Color | Condition | Meaning |
|-------|-----------|---------|
| 🟢 **Green** | Normal | Within thresholds |
| 🟠 **Orange** | Growth | Exceeded growth threshold |
| 🟡 **Yellow** | No baseline | First run or missing baseline |
| 🔴 **Red** | Empty | Zero-byte output (critical) |

### **3. Sortable Table**
Click any column header to sort:
- **Preset** (alphabetical)
- **Bytes** (current size)
- **Baseline** (reference size)
- **Δ bytes** (absolute change)
- **Δ %** (percentage change)

### **4. Delta Bars**
Visual representation of percentage change:
- **Green bar** (right): Growth
- **Red bar** (left): Shrinkage
- **Scale:** ±50% visual clamp (adjustable)

### **5. Filter & Export**
- **Filter:** Live search by preset name
- **Refresh:** Reload data (↻ button)
- **Export CSV:** Download table as CSV file

---

## 📋 Data Format (`badges.json`)

### **Structure**
```json
{
  "smoke_ok": true,
  "size_gate_ok": true,
  "growth_threshold": 0.10,
  "shrink_threshold": -0.05,
  "presets": {
    "GRBL": {
      "bytes": 547,
      "baseline_bytes": 523,
      "delta_bytes": 24,
      "delta_pct": 0.046,
      "badge_color": "green"
    }
  }
}
```

### **Field Descriptions**
| Field | Type | Description |
|-------|------|-------------|
| `smoke_ok` | boolean | Overall smoke test pass/fail |
| `size_gate_ok` | boolean | Size threshold gate pass/fail |
| `growth_threshold` | float | Max allowed growth (e.g., 0.10 = 10%) |
| `shrink_threshold` | float | Max allowed shrinkage (e.g., -0.05 = -5%) |
| `presets.<name>.bytes` | int | Current output size |
| `presets.<name>.baseline_bytes` | int | Reference size |
| `presets.<name>.delta_bytes` | int | Size change (bytes) |
| `presets.<name>.delta_pct` | float | Size change (fractional, e.g., 0.05 = 5%) |
| `presets.<name>.badge_color` | string | Chip color (green/orange/yellow/red) |

---

## 🎨 Customization

### **1. Adjust Visual Scale**

Edit `barHTML()` function in `index.html`:

```javascript
// Default: ±50% visual scale
const maxAbs = 0.50;

// More sensitive: ±20%
const maxAbs = 0.20;

// Less sensitive: ±100%
const maxAbs = 1.00;
```

### **2. Change Color Scheme**

Edit CSS `:root` variables:

```css
:root{
  --bg:#0b0f14;           /* Background */
  --panel:#111823;        /* Card background */
  --text:#e5e7eb;         /* Text color */
  --chip-green:#16a34a;   /* Green chip */
  --chip-orange:#f59e0b;  /* Orange chip */
  /* ... */
}
```

### **3. Add Custom Columns**

Extend the table in HTML and JavaScript:

```html
<!-- Add to <thead> -->
<th data-key="custom_field" data-num>Custom <span class="sort">↕</span></th>

<!-- Add to row generation -->
<td>${fmtInt(info.custom_field)}</td>
```

### **4. Threshold Display**

Thresholds are shown in the footer:
```
Thresholds: growth=10%, shrink=5%
```

These are read from `badges.json` dynamically.

---

## 🔧 Maintenance

### **Update Thresholds**

Thresholds are defined in your CI workflow:

```yaml
# In .github/workflows/cam_smoke_size.yml
env:
  GROWTH_THRESHOLD: "0.10"   # 10%
  SHRINK_THRESHOLD: "-0.05"  # -5%
```

Dashboard reads these from `badges.json` (no HTML changes needed).

### **Add New Presets**

New presets automatically appear when added to `badges.json`:

```json
{
  "presets": {
    "NewPreset": {
      "bytes": 450,
      "baseline_bytes": null,
      "delta_bytes": null,
      "delta_pct": null,
      "badge_color": "yellow"
    }
  }
}
```

Dashboard will render:
- ✅ Row with "NewPreset" name
- 🟡 Yellow chip (no baseline)
- ✅ Current size (450 bytes)

---

## 📖 Usage Examples

### **Example 1: Check Smoke Status**

```
1. Open dashboard
2. Look at "Smoke" pill (top right)
   - Green "OK" = All tests passed
   - Red "FAILED" = See CI logs
```

### **Example 2: Investigate Size Growth**

```
1. Sort by "Δ %" column (click header)
2. Look for orange/red chips
3. Check Δ Bar for visual magnitude
4. Click "badges.json" link for raw data
```

### **Example 3: Export for Analysis**

```
1. Filter to specific presets (if needed)
2. Click "⬇ Export CSV" button
3. Open in Excel/Google Sheets
4. Generate charts or reports
```

### **Example 4: Monitor Trends**

```
1. Bookmark dashboard URL
2. Check after each CI run
3. Compare Δ% over time
4. Alert if consistently growing
```

---

## 🚀 Integration with CI

### **GitHub Actions Workflow**

Your existing workflow generates `badges.json`:

```yaml
- name: Generate Size Badges
  run: |
    python scripts/generate_badges.py \
      --output public_badges/badges.json \
      --growth-threshold 0.10 \
      --shrink-threshold -0.05
      
- name: Deploy to GitHub Pages
  uses: actions/upload-pages-artifact@v2
  with:
    path: public_badges/
```

### **Badge Generation Script**

Example `scripts/generate_badges.py`:

```python
import json

badges = {
    "smoke_ok": all_tests_passed,
    "size_gate_ok": within_thresholds,
    "growth_threshold": 0.10,
    "shrink_threshold": -0.05,
    "presets": {}
}

for preset in ["GRBL", "Mach3", "Haas", "Marlin"]:
    current = get_current_size(preset)
    baseline = get_baseline_size(preset)
    
    badges["presets"][preset] = {
        "bytes": current,
        "baseline_bytes": baseline,
        "delta_bytes": current - baseline if baseline else None,
        "delta_pct": (current - baseline) / baseline if baseline else None,
        "badge_color": determine_color(current, baseline)
    }

with open("public_badges/badges.json", "w") as f:
    json.dump(badges, f, indent=2)
```

---

## 🐛 Troubleshooting

### **Dashboard shows "Failed to load badges.json"**

**Causes:**
- File not deployed to Pages
- Wrong URL path
- CORS issues (local testing)

**Solutions:**
```powershell
# Check file exists
curl https://<OWNER>.github.io/<REPO>/badges.json

# Local testing: use http.server
python -m http.server 8080

# Check Pages deployment status
# GitHub → Settings → Pages
```

### **Data appears outdated**

**Solution:** Hard refresh (Ctrl+F5) or click "↻ Refresh" button.

The dashboard uses `cache:'no-cache'` but browsers may still cache.

### **Colors don't match expectations**

**Check badge logic:**
```json
{
  "badge_color": "orange"  // Should be: green, orange, yellow, or red
}
```

Dashboard renders whatever color is in JSON. Update badge generation script if incorrect.

---

## 📚 Related Documentation

- [CAM Smoke Tests](../SMOKE_TESTS.md) - Test execution details
- [Size Gate Policy](../SIZE_GATE_POLICY.md) - Threshold definitions
- [CI Workflows](../.github/workflows/) - Badge generation automation

---

## 🎓 Advanced Features

### **Real-time Updates**

Add auto-refresh every 60 seconds:

```javascript
// Add to init() function
setInterval(() => {
  init(); // Reload data
}, 60000); // 60 seconds
```

### **Preset Grouping**

Group by controller type:

```javascript
const groups = {
  'Hobby': ['GRBL', 'Marlin'],
  'Industrial': ['Mach3', 'Haas']
};
```

### **Historical Trends**

Fetch multiple badge files:

```javascript
const history = await Promise.all([
  fetch('./badges-2025-11-01.json'),
  fetch('./badges-2025-11-02.json'),
  // ...
]);
```

---

**Live Dashboard:** `https://<OWNER>.github.io/<REPO>/`  
**Raw Data:** `https://<OWNER>.github.io/<REPO>/badges.json`  
**Last Updated:** November 6, 2025
