# B22.16 Quick Reference - Golden + Report Fusion

**One-page guide to automatic HTML report generation for golden checks**

---

## 🎯 What It Does

Every golden check (pass or drift) automatically generates an HTML visual diff report.

```
Golden Check → HTML Report in reports/
CI Workflow → Reports uploaded as artifacts
```

---

## 🚀 Quick Commands

### Local Golden Check with Report

```bash
# Single check
python tools/compare_golden_cli.py check \
  --baseline .golden/body_v1_vs_v2.json \
  --left body_v1.svg \
  --right body_v2.svg

# Output:
# ✅ [PASS] body_v1_vs_v2.json
#    Report: reports/body_v1__vs__body_v2__PASS.html

# Batch check
python tools/compare_golden_cli.py check-all --dir .golden

# Custom report directory
python tools/compare_golden_cli.py check-all \
  --dir .golden \
  --report-dir custom_reports
```

### Open Reports

```bash
# Windows
start reports/*.html

# macOS
open reports/*.html

# Linux
xdg-open reports/*.html
```

---

## 📁 Report Naming

```
reports/<left>__vs__<right>__PASS.html   # Matching golden
reports/<left>__vs__<right>__DRIFT.html  # Drift detected
```

**Example:**
```
reports/body_v1__vs__body_v2__PASS.html
reports/neck_old__vs__neck_new__DRIFT.html
```

---

## 🎨 Report Contents

Each HTML report includes:

1. **Status header** - PASS/DRIFT indicator
2. **PNG preview** - Visual comparison snapshot
3. **Summary cards** - Full bbox, diff bbox, layer count
4. **Layer table** - Presence in left/right
5. **JSON payload** - Full API response (collapsible)

**Styling:**
- Dark theme (#05070b background)
- Standalone HTML (no external deps)
- Mobile responsive

---

## 🔄 CI Integration

### Workflow Behavior

```yaml
# .github/workflows/comparelab-golden.yml

1. Run golden checks with reports
2. Upload reports/*.html as artifacts (always)
3. Upload golden baselines (on failure only)
```

### Accessing Reports in GitHub

1. **Go to Actions tab** in GitHub
2. **Open workflow run**
3. **Download `comparelab-reports` artifact**
4. **Unzip and open HTML files**

**Artifact retention:** 30 days

---

## 🧪 Quick Test

```bash
# 1. Create test SVGs
echo '<svg width="100" height="100"><rect x="10" y="10" width="80" height="80"/></svg>' > test_left.svg
echo '<svg width="100" height="100"><rect x="15" y="10" width="80" height="80"/></svg>' > test_right.svg

# 2. Create golden
python tools/compare_golden_cli.py create \
  --left test_left.svg \
  --right test_right.svg \
  --mode overlay \
  --out .golden/test.json

# 3. Check (should PASS + generate report)
python tools/compare_golden_cli.py check \
  --baseline .golden/test.json \
  --left test_left.svg \
  --right test_right.svg

# 4. Open report
start reports/test_left__vs__test_right__PASS.html

# 5. Modify SVG to trigger drift
echo '<svg width="100" height="100"><rect x="20" y="10" width="80" height="80"/></svg>' > test_right.svg

# 6. Check again (should DRIFT + generate report)
python tools/compare_golden_cli.py check \
  --baseline .golden/test.json \
  --left test_left.svg \
  --right test_right.svg

# 7. Compare PASS vs DRIFT reports
start reports/test_left__vs__test_right__*.html
```

---

## 🔍 Common Use Cases

### CAM Toolpath Change

```bash
# Scenario: Algorithm update changes toolpath

# 1. Golden exists
.golden/body_pocket_v1.json

# 2. Code changes toolpath
git commit -m "feat: optimize adaptive stepover"

# 3. CI runs golden check
# → Drift detected
# → reports/body_pocket__DRIFT.html uploaded

# 4. Download artifact
gh run download <run-id> -n comparelab-reports

# 5. Review visual diff
open comparelab-reports/body_pocket__DRIFT.html

# 6. Decision
# - Intentional improvement? → Update golden
# - Regression? → Revert code
```

### DXF Export Validation

```bash
# Scenario: Export format change

# Before merge
python tools/compare_golden_cli.py check-all --dir .golden

# If drift
# 1. Open reports/part_export__DRIFT.html
# 2. Review geometry differences
# 3. Validate precision/format
# 4. Update golden if correct
```

---

## 🐛 Troubleshooting

### Reports Not Generated

**Check:**
```bash
# Verify report directory exists
ls -la reports/

# Test with explicit path
python tools/compare_golden_cli.py check \
  --baseline .golden/test.json \
  --left test.svg \
  --right test.svg \
  --report-dir /tmp/reports
```

### CI Artifacts Missing

**Debug workflow:**
```yaml
# Add before upload step
- name: List reports
  run: |
    ls -la reports/
    find . -name "*.html"
```

### Wrong Data in Report

**Verify API response:**
```python
# In compare_golden_cli.py
compare_root = await _post_compare(...)
print(f"Keys: {compare_root.keys()}")
print(f"PNG present: {bool(compare_root.get('png_data_base64'))}")
```

---

## 📊 CLI Arguments

### `check` Command

```bash
python tools/compare_golden_cli.py check \
  [--base-url http://localhost:8000] \
  --left <path> \
  --right <path> \
  --baseline <golden.json> \
  [--report-dir reports]
```

### `check-all` Command

```bash
python tools/compare_golden_cli.py check-all \
  [--base-url http://localhost:8000] \
  [--dir .golden] \
  [--report-dir reports]
```

---

## 🎯 Key Features

- ✅ **Automatic** - No manual steps
- ✅ **Visual** - PNG preview in every report
- ✅ **Contextual** - Full metadata included
- ✅ **Persistent** - 30-day CI retention
- ✅ **Standalone** - Reports work offline
- ✅ **Searchable** - Clear filename pattern

---

## 📚 Related Docs

- [B22.16 Full Spec](./B22_16_GOLDEN_REPORT_FUSION.md)
- [B22.15 Golden System](./COMPARELAB_GOLDEN_SYSTEM.md)
- [B22.14 Report Format](./COMPARELAB_REPORTS.md)
- [B22.13 Automation API](./B22_13_COMPARE_AUTOMATION_API.md)

---

## ✅ Checklist

Local setup:
- [ ] `tools/compare_golden_cli.py` updated
- [ ] `reports/` directory created
- [ ] Test golden baseline created
- [ ] Test check run successful
- [ ] Report opened in browser

CI setup:
- [ ] `.github/workflows/comparelab-golden.yml` updated
- [ ] Workflow triggered
- [ ] Artifacts uploaded
- [ ] Reports downloaded from CI
- [ ] Reports viewable

---

**Status:** ✅ B22.16 Complete  
**Quick Start:** Run `python tools/compare_golden_cli.py check-all` → Open `reports/*.html`
