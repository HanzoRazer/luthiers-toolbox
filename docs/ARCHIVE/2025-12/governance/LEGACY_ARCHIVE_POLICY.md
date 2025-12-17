✅ Document 2: LEGACY_ARCHIVE_POLICY.md

(Place at repo root)

# Legacy Archive Policy
This document defines when and how legacy or obsolete directories are moved into the `__ARCHIVE__/` hierarchy.

This protects the repo from clutter and accidental loss of important historical code while ensuring active development stays clean and aligned with RMOS 2.0.

---

## 1. Archive Philosophy

We *archive*, not delete.

Goals:
- Keep the active repo small, modern, and readable.
- Preserve previous subsystems for reference and data recovery.
- Prevent regressions where half-integrated legacy modules reappear in the live code.

The slogan:
**“If it isn’t part of RMOS 2.0, Saw Lab 2.0, Art Studio 2.0, or the Calculator Service Layer — it belongs in the archive.”**

---

## 2. Archive Directory Structure



ARCHIVE/
build_bundles/
patch_bundles/
server_legacy/
legacy_subsystems/
sandbox_history/


Descriptions:

- **build_bundles**  
  All patch/bundle directories originally used to update the repo.

- **patch_bundles**  
  Patch materials that have been superseded, merged, or replaced.

- **server_legacy**  
  Old FastAPI server attempts or backend experiments no longer in use.

- **legacy_subsystems**  
  Retired modules such as:
  - Old CNC Saw Lab
  - Old ToolBox Art Studio versions
  - Old calculators not used by RMOS 2.0
  - Prototype geometry engines

- **sandbox_history**  
  Retired experimental sandboxes that were promoted or merged.

---

## 3. When to Archive Something

A directory should be moved into `__ARCHIVE__/` if:

1. The functionality has been migrated into:
   - `services/api/app/rmos`
   - `services/api/app/saw_lab`
   - `services/api/app/toolpath`
   - `services/api/app/calculators`
   - `services/api/app/art_studio`

**OR**

2. The functionality has been intentionally retired and documented in `DEPRECATED_SUBSYSTEMS.md`.

**OR**

3. The directory exists only as unpacked build bundles, patches, or abandoned experiments.

**OR**

4. The directory duplicates logic now in RMOS 2.0 or Saw Lab 2.0.

---

## 4. How to Archive a Directory (Procedure)

### Step 1 — Confirm migration status  
Create a small checklist:



Subsystem: <name>
Location: <path>

□ Fully migrated to RMOS/SawLab/ArtStudio
□ Partially migrated (list missing items)
□ Explicitly deprecated
□ Unknown (requires review)


### Step 2 — Move directory into archive  
Example:



git mv ToolBox_OldArtStudio ARCHIVE/legacy_subsystems/


### Step 3 — Add to DEPRECATED_SUBSYSTEMS.md  
Record the rationale:


Old Art Studio (2024)

Replaced by ArtStudio 2.0 in services/api/app/art_studio/.
Archived on: YYYY-MM-DD.


### Step 4 — Verify imports  
Run:



pytest services/api/app/tests


Confirm nothing in the live codebase tries to import the archived module.

---

## 5. Adding New Sandboxes

All new experimental work must be created under:



sandbox/<feature_or_date>/


NOT at repo root.

Rules:
- No imports from sandbox into production code.
- Sandboxes must contain a `README.md` explaining their purpose.
- Once promoted, the code must be moved into the official subsystem and the sandbox moved to `sandbox_history/`.

---

## 6. What Must Never Be Archived

The following are **always active**:

- `services/api/app/`
- `docs/`
- `tests/` inside `services/api/app/tests`
- CI configuration
- `REPO_LAYOUT.md` and this `LEGACY_ARCHIVE_POLICY.md`

---

## 7. Governance

Any structural change to the repo requires updating both documents:
- `REPO_LAYOUT.md`
- `LEGACY_ARCHIVE_POLICY.md`

This preserves a stable development map and prevents structural drift.


If you'd like next steps