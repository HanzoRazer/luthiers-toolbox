# API Tests

## 🔒 MVP Golden Path Tests (DXF → GRBL G-code)

### Purpose

The ToolBox MVP is defined by a **single locked manufacturing path**:

```
DXF → plan_from_dxf → GRBL G-code
```

This path is enforced by a **golden snapshot test** that ensures:

* CAM output is **deterministic**
* Manufacturing changes are **intentional and reviewable**
* Regressions cannot silently alter G-code

The authoritative test is:

```
test_mvp_dxf_to_gcode_grbl_golden.py
```

It uses a fixed DXF fixture and compares the generated GRBL G-code against a committed golden `.nc` file.

---

### Golden Snapshot Policy (READ CAREFULLY)

⚠️ **Do NOT update golden files casually.**

Golden G-code snapshots represent **manufacturing intent**.

You may only regenerate and commit a golden snapshot when **all** of the following are true:

1. You intentionally changed CAM logic, feeds/speeds, geometry handling, or post-processing
2. You understand and accept the resulting G-code differences
3. The change has been reviewed as a **manufacturing behavior change**, not just a code refactor

---

### How the Test Works

* If the golden file exists:

  * The test **must match exactly** (after normalization)
  * Any difference fails CI
* If the golden file does NOT exist:

  * The test will generate it
  * The test will fail with instructions to commit the file

This behavior is intentional and protects the MVP path.

---

### Regenerating the Golden Snapshot (Intentional Changes Only)

If you have made a **deliberate CAM change**:

```bash
cd services/api
python scripts/regenerate_mvp_golden_gcode.py
git add tests/golden/mvp_rect_with_island__grbl.nc
git commit -m "Update MVP GRBL golden gcode (intentional CAM change)"
```

Never regenerate golden files as part of "cleanup," "formatting," or unrelated refactors.

---

### What This Test Guarantees

By enforcing this snapshot, we guarantee that:

* ToolBox can always convert a valid DXF into **viable GRBL G-code**
* Changes to CAM output are visible, reviewable, and intentional
* The manufacturing MVP cannot silently degrade

This test is the **manufacturing spine** of ToolBox.

Treat it accordingly.
