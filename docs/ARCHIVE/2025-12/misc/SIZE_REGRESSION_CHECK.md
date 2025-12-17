# Size Regression Check — Quick Reference

**Added:** November 6, 2025  
**Workflow:** `.github/workflows/api_health_and_smoke.yml`  
**Status:** ✅ Active

---

## 🎯 Purpose

Automatically detect when G-code output from post-processor presets:
- **Shrinks to zero** (indicates broken template/token expansion)
- **Grows by >X%** (indicates runaway loops or code bloat)

This prevents silent regressions from merging to main.

---

## 📊 How It Works

### **1. Baseline Establishment**
- First successful run uploads `smoke_posts.json` artifact
- Subsequent runs fetch the last green artifact as baseline
- Compares current run against baseline byte sizes

### **2. Enforcement Rules**

**Rule 1: Zero-byte check (always enforced)**
```
FAIL if current_bytes == 0
```

**Rule 2: Growth limit (default: 35%)**
```
FAIL if current_bytes > baseline_bytes × (1 + SIZE_GROWTH_THRESH)
```

**Rule 3: Shrink limit (optional, default: disabled)**
```
FAIL if current_bytes < baseline_bytes × (1 - SIZE_SHRINK_THRESH)
```

### **3. Workflow Steps**

1. **Run smoke test** → Generate `smoke_posts.json`
2. **Upload artifact** → Store for comparison
3. **Fetch baseline** → Download last green `smoke_posts.json`
4. **Compare sizes** → Enforce thresholds
5. **Notify on failure** → Slack/Email alerts

---

## ⚙️ Configuration

### **Setting Thresholds via Actions Variables**

Navigate to your repo/org settings:
```
Settings → Secrets and variables → Actions → Variables tab
```

Create these variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SIZE_GROWTH_THRESH` | `0.35` | Max allowed growth (35%) |
| `SIZE_SHRINK_THRESH` | `0.00` | Max allowed shrink (disabled by default) |

**Examples:**
- `0.20` → Allow 20% growth
- `0.50` → Allow 50% growth
- `0.35` → Allow 35% shrink (enable shrink detection)

### **Override via Workflow Dispatch**

When manually triggering the workflow, these values are read from repo/org variables. To test locally, set environment variables:

```powershell
$env:SIZE_GROWTH_THRESH = "0.20"
$env:SIZE_SHRINK_THRESH = "0.35"
# Run your local smoke test
```

---

## 🧪 Example Output

### **Passing Check**
```
Using SIZE_GROWTH_THRESH=0.35
Using SIZE_SHRINK_THRESH=0.00
No baseline found; skipping size compare (will establish on this run).
```

### **Failing Check (Growth)**
```
Size regression check FAILED:
 - grbl_pocket_adaptive: grew 1200 bytes (48.3% > 35.0% limit). base=2487, curr=3687
 - haas_drilling_g81: grew 850 bytes (41.2% > 35.0% limit). base=2062, curr=2912
```

### **Failing Check (Zero)**
```
Size regression check FAILED:
 - mach4_contour_finishing: current bytes=0 (shrank to zero)
```

### **Failing Check (Shrink, if enabled)**
```
Size regression check FAILED:
 - linuxcnc_roughing: shrank 895 bytes (42.1% > 35.0% shrink limit). base=2125, curr=1230
```

---

## 🔍 Troubleshooting

### **False Positive: Legitimate Growth**

**Scenario:** You intentionally added new features to a post-processor (e.g., new header comments, tool change macros).

**Solution:**
1. Review the actual G-code diff (download both artifacts)
2. If growth is intentional, temporarily increase `SIZE_GROWTH_THRESH`:
   ```
   Settings → Variables → SIZE_GROWTH_THRESH = 0.60  # Allow 60% for this merge
   ```
3. Re-run the workflow
4. After merge, reset to `0.35`

### **False Positive: New Preset Added**

**Behavior:** New presets skip growth check on first green run (no baseline yet).

**No action needed.** The preset will be compared on subsequent runs.

### **False Negative: Gradual Growth**

**Scenario:** G-code grows by 10% per week (cumulative 50% over 5 weeks), but never exceeds 35% in a single week.

**Solution:** Enable shrink detection to catch gradual regressions:
```
SIZE_GROWTH_THRESH = 0.15  # Tighter growth limit (15%)
SIZE_SHRINK_THRESH = 0.15  # Also catch 15% shrinks
```

### **Baseline Lost**

**Scenario:** Artifacts expire after 90 days (GitHub default).

**Behavior:** Next run will show:
```
No baseline found; skipping size compare (will establish on this run).
```

**No action needed.** The current run becomes the new baseline.

---

## 📈 Integration with Existing Workflow

### **Before Size Check:**
```yaml
- Run health (best-effort)
- Run smoke test
- Upload smoke_posts.json
- Notify on failure (Slack/Email)
```

### **After Size Check:**
```yaml
- Run health (best-effort)
- Run smoke test
- Upload smoke_posts.json
- Fetch last green artifact    # NEW
- Unzip baseline              # NEW
- Compare sizes               # NEW
- Notify on failure (Slack/Email)
```

**Key:** Size check fails the job, triggering notifications.

---

## 🎯 Benefits

### **1. Detect Broken Templates**
```
Before: Token {{TOOL_DIAMETER}} not expanded → G-code shrinks to 0 bytes
After:  Size regression check catches and fails CI
```

### **2. Catch Runaway Loops**
```
Before: Infinite loop in spiralizer → 50MB G-code file
After:  Size regression check catches 2000% growth
```

### **3. Prevent Silent Regressions**
```
Before: Post-processor refactor accidentally removes tool change macros
After:  Size regression check catches 30% shrink (if enabled)
```

### **4. Historical Tracking**
- Each artifact stores `smoke_posts.json` with byte counts
- Can download and compare across runs
- Audit trail for G-code size trends

---

## 🚀 Advanced Usage

### **Custom Thresholds Per Preset**

Modify the Python script to read per-preset thresholds:

```python
# Add to smoke_posts.json:
"results": {
  "grbl_pocket_adaptive": {
    "bytes": 2487,
    "growth_thresh": 0.50  # Allow 50% for this preset
  }
}

# Update size check script:
preset_thr = cinfo.get("growth_thresh", thr)  # Use preset-specific or default
limit = bb * (1.0 + preset_thr)
```

### **Slack/Email Per-Preset Alerts**

Modify notification to include which presets failed:

```yaml
SLACK_MESSAGE: |
  Failed presets:
  ${{ env.FAILED_PRESETS }}
```

Set `FAILED_PRESETS` in the Python script:
```python
os.environ["FAILED_PRESETS"] = "\n".join(errors)
```

---

## ✅ Verification

### **Manual Test**

1. **Trigger workflow manually:**
   ```
   Actions → API Health + Smoke → Run workflow
   ```

2. **Check logs for:**
   ```
   Using SIZE_GROWTH_THRESH=0.35
   No baseline found; skipping size compare (will establish on this run).
   ```

3. **Trigger again (should compare against first run):**
   ```
   Using SIZE_GROWTH_THRESH=0.35
   Size regression check OK.
   ```

4. **Force failure (edit a post config to break tokens):**
   ```
   Edit services/api/app/data/posts/grbl.json → Remove {{SAFE_Z}}
   Commit → Push → Workflow fails with:
   "grbl_pocket_adaptive: current bytes=0 (shrank to zero)"
   ```

---

## 📚 See Also

- [API Health + Smoke Workflow](../.github/workflows/api_health_and_smoke.yml)
- [Post-Processor System](./PATCH_N_SERIES_ROLLUP.md)
- [Smoke Test Implementation](./IMPLEMENTATION_CHECKLIST.md)

---

**Status:** ✅ Production-Ready  
**Maintenance:** Set `SIZE_GROWTH_THRESH` via Actions Variables  
**Cost:** ~30 seconds per workflow run (artifact fetch + compare)
