# Shields.io Badge System

**Status:** ✅ Implemented  
**Date:** November 6, 2025

---

## 🎯 Overview

The API Health + Smoke workflow now generates **Shields.io endpoint badges** and publishes them to GitHub Pages. This provides at-a-glance status of G-code output sizes for each post-processor preset.

### **What's New**
- ✅ **Per-preset badge JSON files** (grbl.json, mach3.json, etc.)
- ✅ **Aggregate index** (badges.json) with all presets + deltas
- ✅ **GitHub Pages deployment** - Automatic publishing to stable URLs
- ✅ **Color-coded badges** - Red/orange/yellow/green status indicators
- ✅ **Delta percentages** - Shows size changes vs baseline

---

## 📊 Badge Colors

Badges use color to indicate status at a glance:

| Color | Meaning | Example |
|-------|---------|---------|
| 🟥 **Red** | Empty output (0 bytes) | Failed generation |
| 🟧 **Orange** | Grew >35% vs baseline | Regression detected |
| 🟨 **Yellow** | No baseline yet | First run |
| 🟩 **Green** | Normal | All good |

---

## 🔗 Badge URLs

After the first workflow run, badges are available at:

```
https://<OWNER>.github.io/<REPO>/<preset>.json
```

**Examples:**
- `https://HanzoRazer.github.io/guitar_tap/grbl.json`
- `https://HanzoRazer.github.io/guitar_tap/mach3.json`
- `https://HanzoRazer.github.io/guitar_tap/haas.json`
- `https://HanzoRazer.github.io/guitar_tap/marlin.json`

**Aggregate index:**
- `https://HanzoRazer.github.io/guitar_tap/badges.json`

---

## 📋 badges.json Schema

The aggregate index includes all presets with delta calculations:

```json
{
  "schema": "toolbox-art-studio/badges-v1",
  "smoke_ok": true,
  "size_gate_ok": true,
  "growth_threshold": 0.35,
  "shrink_threshold": 0.0,
  "presets": {
    "GRBL": {
      "bytes": 1012,
      "baseline_bytes": 980,
      "delta_bytes": 32,
      "delta_pct": 0.0327,
      "badge_color": "green"
    },
    "Mach3": {
      "bytes": 1098,
      "baseline_bytes": 1105,
      "delta_bytes": -7,
      "delta_pct": -0.0063,
      "badge_color": "green"
    },
    "Haas": {
      "bytes": 1092,
      "baseline_bytes": 1092,
      "delta_bytes": 0,
      "delta_pct": 0.0,
      "badge_color": "green"
    },
    "Marlin": {
      "bytes": 962,
      "baseline_bytes": null,
      "delta_bytes": null,
      "delta_pct": null,
      "badge_color": "yellow"
    }
  }
}
```

**Fields:**
- `schema` - Version identifier for schema evolution
- `smoke_ok` - Overall smoke test status (boolean)
- `size_gate_ok` - Size regression gate status (boolean)
- `growth_threshold` - Maximum allowed growth (e.g., 0.35 = 35%)
- `shrink_threshold` - Maximum allowed shrink (e.g., 0.0 = 0%)
- `presets` - Per-preset data with bytes, deltas, and colors

**Per-preset fields:**
- `bytes` - Current output size in bytes
- `baseline_bytes` - Baseline size (null if no baseline yet)
- `delta_bytes` - Absolute change (current - baseline)
- `delta_pct` - Relative change as decimal (e.g., 0.0327 = 3.27%)
- `badge_color` - Computed color (red/orange/yellow/green)

---

## 🎨 Using Badges in README

### **Basic Shields.io Endpoint Badges**

Add these to your README.md:

```markdown
#### CAM Post Size (latest smoke)

![GRBL](https://img.shields.io/endpoint?url=https://HanzoRazer.github.io/guitar_tap/grbl.json)
![Mach3](https://img.shields.io/endpoint?url=https://HanzoRazer.github.io/guitar_tap/mach3.json)
![Haas](https://img.shields.io/endpoint?url=https://HanzoRazer.github.io/guitar_tap/haas.json)
![Marlin](https://img.shields.io/endpoint?url=https://HanzoRazer.github.io/guitar_tap/marlin.json)
```

**Result:**

![GRBL](https://img.shields.io/endpoint?url=https://HanzoRazer.github.io/guitar_tap/grbl.json)
![Mach3](https://img.shields.io/endpoint?url=https://HanzoRazer.github.io/guitar_tap/mach3.json)
![Haas](https://img.shields.io/endpoint?url=https://HanzoRazer.github.io/guitar_tap/haas.json)
![Marlin](https://img.shields.io/endpoint?url=https://HanzoRazer.github.io/guitar_tap/marlin.json)

### **Clickable Badges (Link to Workflow)**

Make badges clickable to see run details:

```markdown
[![GRBL](https://img.shields.io/endpoint?url=https://HanzoRazer.github.io/guitar_tap/grbl.json)](https://github.com/HanzoRazer/guitar_tap/actions/workflows/api_health_and_smoke.yml)
[![Mach3](https://img.shields.io/endpoint?url=https://HanzoRazer.github.io/guitar_tap/mach3.json)](https://github.com/HanzoRazer/guitar_tap/actions/workflows/api_health_and_smoke.yml)
```

### **Dashboard Link**

Add a link to the aggregate JSON for dashboards:

```markdown
**Dashboard feed (all presets):**  
`https://HanzoRazer.github.io/guitar_tap/badges.json`
```

---

## 🔧 Workflow Implementation

### **1. Permissions**

Added to workflow (top-level):

```yaml
permissions:
  contents: read
  pages: write
  id-token: write
```

### **2. Badge Generation Step**

Runs after delta report, generates:
- Per-preset JSON files (grbl.json, mach3.json, etc.)
- Aggregate index (badges.json)

```yaml
- name: Build badge JSONs from smoke_posts.json (+ index)
  if: always()
  shell: bash
  env:
    SIZE_GROWTH_THRESH: ${{ vars.SIZE_GROWTH_THRESH || '0.35' }}
    SIZE_SHRINK_THRESH: ${{ vars.SIZE_SHRINK_THRESH || '0.00' }}
    SIZE_GUARD_OUTCOME: ${{ steps.size_guard.outcome }}
  run: |
    mkdir -p public_badges
    python - <<'PY'
    # ... badge generation script ...
    PY
```

### **3. GitHub Pages Deployment**

Three-step deployment:

```yaml
- name: Configure Pages
  if: always()
  uses: actions/configure-pages@v5

- name: Upload Pages artifact (badges)
  if: always()
  uses: actions/upload-pages-artifact@v3
  with:
    path: public_badges

- name: Deploy to GitHub Pages
  if: always()
  id: deployment
  uses: actions/deploy-pages@v4
```

---

## 🚀 First-Time Setup

### **Step 1: Enable GitHub Pages**

1. Go to **Settings** → **Pages**
2. Set **Source** to "GitHub Actions"
3. Click **Save**

### **Step 2: Run Workflow**

Trigger manually or wait for nightly run:

```
Actions → API Health + Smoke → Run workflow
```

### **Step 3: Wait for Deployment**

First run creates the "GitHub Pages" environment. Accept the prompt if asked.

### **Step 4: Verify Badges**

Check that badge URLs work:
- `https://HanzoRazer.github.io/guitar_tap/grbl.json`
- `https://HanzoRazer.github.io/guitar_tap/badges.json`

### **Step 5: Update README**

Add badge markdown to your README.md (see examples above).

---

## 🎯 Dashboard Usage

The `badges.json` index is designed for dashboard consumption:

```javascript
// Fetch all badge data
const response = await fetch('https://HanzoRazer.github.io/guitar_tap/badges.json')
const data = await response.json()

// Check overall status
if (!data.smoke_ok) {
  console.log('❌ Smoke test failed!')
}
if (!data.size_gate_ok) {
  console.log('❌ Size gate failed!')
}

// Display per-preset status
for (const [preset, info] of Object.entries(data.presets)) {
  const status = info.badge_color === 'green' ? '✅' : '⚠️'
  const delta = info.delta_pct ? `(${(info.delta_pct * 100).toFixed(1)}%)` : ''
  console.log(`${status} ${preset}: ${info.bytes} bytes ${delta}`)
}
```

**Output:**
```
✅ GRBL: 1012 bytes (+3.3%)
✅ Mach3: 1098 bytes (-0.6%)
✅ Haas: 1092 bytes (0.0%)
⚠️ Marlin: 962 bytes (no baseline)
```

---

## 📊 Badge Message Format

### **With Baseline**
```
<preset>: <bytes> B (+<delta>%)
```
Example: `GRBL: 1012 B (+3.3%)`

### **Without Baseline (First Run)**
```
<preset>: <bytes> B
```
Example: `Marlin: 962 B`

### **Color Logic**

```python
def color_for(current_bytes, baseline_bytes):
    if current_bytes <= 0:
        return "red"        # Empty output
    if baseline_bytes == 0:
        return "yellow"     # No baseline
    growth = (current_bytes / baseline_bytes - 1.0)
    if growth > GROWTH_THRESHOLD:
        return "orange"     # Regression
    return "green"          # Normal
```

---

## 🔍 Troubleshooting

### **Issue:** Badges show 404
**Solution:**
- Verify GitHub Pages is enabled (Settings → Pages)
- Check workflow completed successfully
- Wait 1-2 minutes for Pages deployment to propagate

### **Issue:** Badges not updating
**Solution:**
- Shields.io caches responses (5 minutes default)
- Add `?v=<timestamp>` to badge URL to force refresh
- Or wait for cache to expire

### **Issue:** Wrong colors showing
**Solution:**
- Check `SIZE_GROWTH_THRESH` variable (Settings → Variables)
- Verify baseline artifact was fetched correctly
- Check workflow logs for badge generation step

### **Issue:** badges.json missing presets
**Solution:**
- Verify `smoke_posts.json` has all presets
- Check badge generation script for errors
- Ensure Python script completed successfully

---

## 🎨 Customization

### **Per-Preset Thresholds**

Create `badge_rules.json` with custom thresholds:

```json
{
  "GRBL": {"growth": 0.40, "color_override": null},
  "Haas": {"growth": 0.20, "color_override": null},
  "Marlin": {"growth": 0.50, "color_override": null}
}
```

Then load in badge script:

```python
rules = load("badge_rules.json") or {}
preset_thresh = rules.get(preset, {}).get("growth", grow_thr)
```

### **Include Absolute Delta**

Change message format:

```python
msg = f"{cb} B ({delta_pct:+.1%}, {delta_b:+d}B)"
```

Result: `GRBL: 1012 B (+3.3%, +32B)`

### **Schema Versioning**

Bump schema version when changing format:

```python
index = {
    "schema": "toolbox-art-studio/badges-v2",  # Bumped
    # ... rest of data
}
```

Dashboard code can check version and adapt.

---

## 📈 Benefits

### **1. Instant Status Visibility**
- Badges in README show current state at a glance
- No need to open workflow runs to check status
- Color-coded for quick assessment

### **2. Historical Tracking**
- Baseline comparisons show growth/shrink trends
- Delta percentages highlight gradual increases
- Orange badges flag regressions immediately

### **3. Dashboard Integration**
- Single JSON fetch gets all preset data
- No need to parse individual badge files
- Schema versioning enables evolution

### **4. PR Reviews**
- Reviewers see badge status in README
- Size impacts visible without running tests
- Easier to spot CAM output regressions

### **5. External Monitoring**
- Can be consumed by status dashboards
- Integration with monitoring tools
- Alerting on orange/red badges

---

## 🎉 Example README Section

```markdown
## 🛠️ CAM Post-Processor Status

### Latest Smoke Test Results

![GRBL](https://img.shields.io/endpoint?url=https://HanzoRazer.github.io/guitar_tap/grbl.json)
![Mach3](https://img.shields.io/endpoint?url=https://HanzoRazer.github.io/guitar_tap/mach3.json)
![Haas](https://img.shields.io/endpoint?url=https://HanzoRazer.github.io/guitar_tap/haas.json)
![Marlin](https://img.shields.io/endpoint?url=https://HanzoRazer.github.io/guitar_tap/marlin.json)

**Badge Colors:**
- 🟩 **Green** - Normal operation
- 🟨 **Yellow** - No baseline (first run)
- 🟧 **Orange** - Size regression detected (>35% growth)
- 🟥 **Red** - Empty output (0 bytes)

**Dashboard Feed:** `https://HanzoRazer.github.io/guitar_tap/badges.json`

Last updated: Daily at 03:30 AM Central (09:30 UTC)
```

---

## 📚 See Also

- [API_HEALTH_SMOKE_COMPLETE.md](./API_HEALTH_SMOKE_COMPLETE.md) - Workflow documentation
- [SIZE_REGRESSION_CHECK.md](./SIZE_REGRESSION_CHECK.md) - Size gate details
- [Shields.io Endpoint Schema](https://shields.io/endpoint) - Badge format docs

---

**Status:** ✅ Production Ready  
**Version:** 1.0  
**Date:** November 6, 2025
