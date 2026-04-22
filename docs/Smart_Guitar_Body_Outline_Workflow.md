# Smart Guitar — Body Outline Workflow
## Internal Use Only

**Owner:** Design Engineering  
**Last Updated:** 2026-04-22  
**Target Editor Version:** v3.5.0

---

## Spec Reference

| Dimension | Value | Axis |
|-----------|-------|------|
| **Length** | 444.5 mm | Y (positive toward neck) |
| **Width** | 368.3 mm | X (positive bass, negative treble) |
| **Depth** | 44.45 mm | Z (not represented in 2D outline) |
| **Origin** | Body center | (0,0) |
| **Butt center** | (0, -222.25) | Half of length |
| **Neck center** | (0, +222.25) | Half of length |

---

## Corrected Dimension Truth Table

| Feature | X (mm) | Y (mm) | Notes |
|---------|--------|--------|-------|
| Butt center | 0 | -222.25 | Centerline (half of 444.5 length) |
| Neck center | 0 | +222.25 | Centerline |
| Lower bout max | ±184.15 | -92 | Half of 368.3 width |
| Waist min | ±110 | 0 | Approximate — verify with spec |
| Upper bout max | ±160 | +120 | Approximate — Explorer-Klein shape |
| Cutaway apex | -180 | +140 | Treble side only (mirror mode OFF) |
| Pickup 1 (neck) | 0 | +60 | Centered |
| Pickup 2 (bridge) | 0 | -20 | Centered |

**Important:** 444.5 is LENGTH (Y-axis). 368.3 is WIDTH (X-axis). Do not swap.

---

## Recommended Workflow

### Phase 1: Setup

1. Open Body Outline Editor → **Empty Mode**
2. Set snap to **1mm**
3. Turn **Mirror mode ON**
4. Import Smart Guitar concept render (orthographic, no perspective)
5. Calibrate against body length (444.5mm)

### Phase 2: Core Outline

1. Place centerline nodes using numeric entry (double-click):
   - Butt center: (0, -222.25)
   - Neck center: (0, +222.25)

2. Place bout extremes:
   - Lower bout: (±184.15, -92)
   - Waist: (±110, 0)
   - Upper bout: (±160, +120)

3. Run **Smooth All**

4. Adjust handles for Explorer-Klein shape:
   - Lower bout: medium handles (~35-40% of segment length)
   - Waist: shorter handles (~20-25%) for tighter curve
   - Upper bout: medium handles, asymmetric at transitions

### Phase 3: Cutaway

1. Turn **Mirror mode OFF**

2. On treble side upper bout, select nodes in cutaway region

3. Move nodes to form cutaway:
   - Apex at approximately (-180, +140)
   - Transition from upper bout to cutaway should be smooth (asymmetric handles)

4. Add extra nodes for cutaway curve detail (click on curve to insert)

5. Shape with `Alt+drag` on handles for asymmetric transitions

### Phase 4: Ergonomic Voids

Create each void using **+ Add Void** with role "other":

| Void | Approximate Position | Shape |
|------|---------------------|-------|
| Upper bass | (-120, +100) | Curved oval |
| Upper treble | (+120, +100) | Curved oval |
| Lower bass | (-100, -80) | Curved oval |

**For each void:**
- Use numeric entry for exact positions (refer to spec document)
- 10-14 nodes with smooth symmetric handles
- Verify bounding box matches spec

### Phase 5: Electronics Voids

| Void | Role | Position | Notes |
|------|------|----------|-------|
| Neck pickup | pickup | (0, +60) | Centered |
| Bridge pickup | pickup | (0, -20) | Centered |
| Control cavity | control_cavity | (-80, -140) | Per spec |
| Jack hole | jack | (+100, -200) | Per spec |
| Pi 5 cavity | other | (0, -100) | If modeling top plate |

### Phase 6: Verification

Before export, verify:

1. **Symmetry** (mirror mode ON):
   - Left/right node counts match
   - Centerline nodes at X=0
   - Run `testWeightedMirror()` in console

2. **Dimensions**:
   - Bounding box: W=368.3mm, H=444.5mm
   - Measure key distances with M tool

3. **Self-intersection**:
   - Run `testSelfIntersection()` in console
   - Export DXF validates automatically

### Phase 7: Export

1. **Save session:** `smart_guitar_body_vX.sgession`
2. **Export DXF:** R12 format, tessellation 30
3. **Export JSON:** For backend validation

---

## Troubleshooting

### Outline not symmetric?

- Check mirror mode is ON
- Run `testWeightedMirror()` in console
- Look for warnings about unpaired nodes

### Void positions off?

- Use numeric entry (double-click node)
- Verify coordinates against spec table above
- Check that void is active (Mode shows void ID)

### Export to Fusion 360 looks wrong?

- Use DXF R12 format
- Tessellation at 30-40 points per curve
- Check winding direction (auto-enforced)

### Bounding box wrong size?

- Check centerline nodes at X=0 exactly
- Verify bout extremes with numeric entry
- Remember: 444.5 is LENGTH (Y), 368.3 is WIDTH (X)

---

## Session Checkpoints

Save sessions at these milestones:

| Checkpoint | Filename Example |
|------------|------------------|
| After core outline | `smart_guitar_body_v1_outline.sgession` |
| After cutaway | `smart_guitar_body_v2_cutaway.sgession` |
| After ergonomic voids | `smart_guitar_body_v3_voids.sgession` |
| After electronics | `smart_guitar_body_v4_electronics.sgession` |
| Final verified | `smart_guitar_body_FINAL.sgession` |

---

## Reference Documents

- Smart Guitar Spec: `services/api/app/instrument_geometry/body/specs/smart_guitar_v1.json`
- Body Outline Editor Manual: `docs/Body_Outline_Editor_User_Manual.md`
- Body Solver API: `docs/api/body_solver_openapi.yaml`
