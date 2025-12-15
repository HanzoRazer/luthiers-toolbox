# GitHub Issue Template System – Quick Start

## 🚀 Quick Start

### 1. View Available Bundle Templates

Navigate to your GitHub repository's Issues tab, click "New Issue", and you'll see:

```
Choose a template:
  📦 Bundle: N10.1 – Drill-down: subjobs, CAM events, heuristics
  📦 Bundle: MM-7 – Right-angle mosaic generator (pixel matrix → rod → tiles)
  📦 Bundle: N8.7.5 – Fix drift wizard
  ... (43 total bundle templates)
```

### 2. Create Bundle-Specific Issue

1. Click on desired bundle template
2. Title is pre-filled: `[N10.1] `
3. Labels auto-applied: `bundle`, `mainline`, `N10`, `live-monitor`, `active`
4. Fill in template sections:
   - Summary
   - Implementation checklist
   - Testing checklist
   - Artifacts
   - Documentation updates

### 3. Add New Bundle

**Step 1:** Edit `docs/rmos_bundles.json`
```json
{
  "id": "N11.0",
  "title": "Your new feature bundle",
  "labels": ["bundle", "mainline", "N11"]
}
```

**Step 2:** Regenerate templates
```powershell
python tools/generate_bundle_issue_templates.py
```

**Step 3:** Update master tree
Edit `docs/RMOS_MASTER_TREE.md`:
```markdown
- **[ ] N11.0** Your new feature bundle
```

**Step 4:** Commit changes
```powershell
git add .github/ISSUE_TEMPLATE/bundle_n11_0.md
git add docs/rmos_bundles.json
git add docs/RMOS_MASTER_TREE.md
git commit -m "Add N11.0 bundle"
git push
```

---

## 📋 Template Features

### Pre-filled Sections

**Every bundle template includes:**

✅ **Summary** – High-level description  
✅ **Acceptance Criteria** – Definition of done (6 items)  
✅ **Implementation Checklist** – Backend, frontend, integration (14 items)  
✅ **Testing Checklist** – Coverage requirements (5 items)  
✅ **Artifacts** – Files, screenshots, docs (4 items)  
✅ **Documentation** – Required docs updates (5 items)  
✅ **Notes** – Design decisions  
✅ **Related Bundles** – Dependencies/blockers  

### Auto-Applied Labels

Labels are automatically applied based on bundle configuration:

| Bundle Series | Labels |
|---------------|--------|
| N8.x | `bundle`, `mainline`, `N8`, `migration`/`database` |
| N9.x | `bundle`, `mainline`, `N9`, `analytics`/`artifacts` |
| N10.x | `bundle`, `mainline`, `N10`, `live-monitor`/`safety` |
| MM-x | `bundle`, `mosaic`, `MM`, `generator`/`materials` |

**Active bundle** (N10.1) also gets: `active` label

---

## 🔍 Finding Your Bundle

### Bundle ID → Template File Mapping

| Bundle ID | Template Filename |
|-----------|-------------------|
| N10.1 | `bundle_n10_1.md` |
| MM-7 | `bundle_mm-7.md` |
| N8.7.1 | `bundle_n8_7_1.md` |

**Normalization rules:**
- Lowercase conversion
- Dots (`.`) → Underscores (`_`)
- Hyphens (`-`) preserved

### All 43 Templates Generated

**N8-series (12 bundles):**
- N8.1, N8.2, N8.3, N8.4, N8.5, N8.6, N8.7
- N8.7.1, N8.7.2, N8.7.3, N8.7.4, N8.7.5

**N9-series (10 bundles):**
- N9.0, N9.1, N9.2, N9.3, N9.4, N9.5, N9.6, N9.7, N9.8, N9.9

**N10-series (6 bundles):**
- N10.0, N10.1 **(YOU ARE HERE)**, N10.2, N10.3, N10.4, N10.5

**MM-series (15 bundles):**
- MM-1, MM-2, MM-3, MM-4, MM-5, MM-6
- MM-7, MM-8, MM-9, MM-10, MM-11, MM-12, MM-13, MM-14, MM-15

---

## 🎯 Current Active Bundle

**N10.1 – Drill-down: subjobs, CAM events, heuristics**

To create an issue for the active bundle:
1. Go to GitHub Issues → New Issue
2. Select "Bundle: N10.1 – Drill-down..."
3. Fill in implementation details
4. Apply additional labels if needed (e.g., `high-priority`, `breaking-change`)
5. Assign to developer(s)
6. Submit

---

## 🔄 Moving "You Are Here" Marker

When switching to a new active bundle:

**Step 1:** Edit `docs/RMOS_MASTER_TREE.md`
```markdown
# Old location (remove marker)
- **[ ] N10.1** Drill-down: subjobs, CAM events, heuristics

# New location (add marker)
- **[ ] N10.2** Apprenticeship mode + safety overrides **(YOU ARE HERE)**
```

**Step 2:** Update `docs/rmos_bundles.json` labels
```json
// Remove "active" from N10.1
{
  "id": "N10.1",
  "labels": ["bundle", "mainline", "N10", "live-monitor"]
},

// Add "active" to N10.2
{
  "id": "N10.2",
  "labels": ["bundle", "mainline", "N10", "safety", "training", "active"]
}
```

**Step 3:** Regenerate templates
```powershell
python tools/generate_bundle_issue_templates.py
```

**Step 4:** Commit changes
```powershell
git add .github/ISSUE_TEMPLATE/bundle_n10_*.md
git add docs/rmos_bundles.json
git add docs/RMOS_MASTER_TREE.md
git commit -m "Move active bundle marker to N10.2"
```

---

## 📊 Bundle Progress Tracking

### Marking Bundles Complete

**Step 1:** Edit `docs/RMOS_MASTER_TREE.md`
```markdown
# Change checkbox from empty to filled
- **[x] N10.1** Drill-down: subjobs, CAM events, heuristics
```

**Step 2:** (Optional) Add completion labels to bundle config
```json
{
  "id": "N10.1",
  "labels": ["bundle", "mainline", "N10", "live-monitor", "completed"]
}
```

**Step 3:** Regenerate templates (if labels changed)
```powershell
python tools/generate_bundle_issue_templates.py
```

### Bundle Status Summary

View completion status in `docs/RMOS_MASTER_TREE.md`:

```
N8 – Migration & Storage: 12/12 complete ✅
N9 – Analytics & Artifacts: 10/10 complete ✅
N10 – Real-Time Operations: 1/6 complete (N10.0 done)
MM – Mixed-Material / Mosaic: 6/15 complete
```

---

## 🛠️ Troubleshooting

### Template not showing in GitHub

**Cause:** Template file not committed to `.github/ISSUE_TEMPLATE/`

**Solution:**
```powershell
git add .github/ISSUE_TEMPLATE/bundle_*.md
git commit -m "Add bundle issue templates"
git push
```

### Wrong labels applied

**Cause:** `docs/rmos_bundles.json` has incorrect labels

**Solution:**
1. Edit `docs/rmos_bundles.json` to fix labels
2. Run `python tools/generate_bundle_issue_templates.py`
3. Commit updated templates

### Bundle ID typo in template

**Cause:** Bundle ID in `docs/rmos_bundles.json` has typo

**Solution:**
1. Fix typo in `docs/rmos_bundles.json`
2. Delete old template file: `.github/ISSUE_TEMPLATE/bundle_<old_id>.md`
3. Run generator script to create corrected template
4. Update `docs/RMOS_MASTER_TREE.md` to match corrected ID

---

## 📚 Related Files

**Core system:**
- `docs/rmos_bundles.json` – Bundle definitions
- `tools/generate_bundle_issue_templates.py` – Generator script
- `.github/ISSUE_TEMPLATE/bundle_*.md` – Generated templates (43 files)

**Documentation:**
- `docs/RMOS_MASTER_TREE.md` – Development roadmap with "YOU ARE HERE"
- `tools/README.md` – Detailed tool documentation
- `docs/GITHUB_ISSUE_TEMPLATES_QUICKSTART.md` – This guide

---

**Need help?** See `tools/README.md` for detailed documentation.  
**Last Updated:** November 30, 2025
