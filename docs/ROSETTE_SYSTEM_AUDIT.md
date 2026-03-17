# Rosette System Audit — Merge Gap Report

**Date:** 2026-03-17  
**Scope:** SYSTEM 1 (backend recipes) vs SYSTEM 2 (frontend prototypes). No changes made; audit only.

---

## 1. SYSTEM 1 — Backend

**File:** `services/api/app/art_studio/services/rosette/rosette_recipes.py`

| Metric | Value |
|--------|--------|
| **Total recipes** | **8** |
| **Model** | Named recipe presets (`RecipePreset`: id, name, desc, tags, num_segs, sym_mode, ring_active, grid) |
| **Grid** | Ring × segment → tile ID (e.g. `rosewood`, `maple`, `bwb`, `herringbone`, `checker`, `celtic`, `abalone`, `mop`, etc.) |

### All pattern/recipe IDs (System 1)

| # | Recipe ID | Name |
|---|-----------|------|
| 1 | `vintage-martin` | Vintage Martin |
| 2 | `shell-classic` | Shell Classic |
| 3 | `herringbone-band` | Herringbone Band |
| 4 | `celtic-ring` | Celtic Ring |
| 5 | `checkerboard-mosaic` | Checkerboard Mosaic |
| 6 | `minimalist` | Minimalist |
| 7 | `abalone-burst` | Abalone Burst |
| 8 | `rosewood-maple` | Rosewood & Maple |

### Tile/material IDs referenced in grids (System 1)

- Woods: `maple`, `rosewood`, `cream`, `ebony`, `walnut`, `mahogany`
- Purfling: `bwb`, `wbw`
- Motifs: `herringbone`, `checker`, `celtic`, `abalone`, `mop`

---

## 2. SYSTEM 2 — Frontend prototypes

### 2a. Rosette Designer HTML

**File:** `Rosette Designer/rosette-designer-v5.html`

| Metric | Value |
|--------|--------|
| **Total recipes** | **8** (inlined `RECIPES` array) |
| **Model** | Same structure as backend: id, name, desc, tags, numSegs, symMode, ringActive, grid |
| **Tile palette** | `TILE_CATS` / `TILE_MAP`: binding (maple, rosewood, cream, ebony, walnut, mahogany, abalone, mop), purfling (bwb, rbr, wbw), motifs (herringbone, checker, celtic, diagonal, dots, clear) |

### All recipe IDs in rosette-designer-v5.html

| # | Recipe ID | Name |
|---|-----------|------|
| 1 | `vintage-martin` | Vintage Martin |
| 2 | `shell-classic` | Shell Classic |
| 3 | `herringbone-band` | Herringbone Band |
| 4 | `celtic-ring` | Celtic Ring |
| 5 | `checkerboard-mosaic` | Checkerboard Mosaic |
| 6 | `minimalist` | Minimalist |
| 7 | `abalone-burst` | Abalone Burst |
| 8 | `rosewood-maple` | Rosewood & Maple |

**Conclusion:** HTML recipe set is **identical** to System 1 (same 8 IDs). No delta between backend and this file for recipe IDs.

---

### 2b. rosettePresets.ts (pattern families)

**File:** `packages/client/src/lib/rosettePresets.ts`

| Metric | Value |
|--------|--------|
| **Pattern families** | **6** |
| **Total named variations** | **19** (across families) |
| **Model** | Pattern families with parametric variations (`PatternFamily` → `PatternVariation` with `PatternParams`: segments, rings, ringWidths, stripFamilies, colorScheme, alternation). No recipe ID list; generates patterns from params. |

### All pattern family IDs (System 2 — TS only)

| # | Family ID | Name |
|---|-----------|------|
| 1 | `repeating_single` | Repeating Single Ring |
| 2 | `multi_ring_alternating` | Multi-Ring Alternating |
| 3 | `radial_star` | Radial Star |
| 4 | `bordered_field` | Bordered Field |
| 5 | `concentric_only` | Concentric Rings Only |
| 6 | `hybrid` | Hybrid Radial/Concentric |

### All variation names in rosettePresets.ts (by family)

- **repeating_single:** Herringbone (24 segments), Spanish Rope (16 segments), Wave Pattern (12 segments), German Rope (8 segments), Fine Herringbone (32 segments), Wide Rope (6 segments)
- **multi_ring_alternating:** Triple Ring Classic, Five Ring Delicate, Seven Ring Complex
- **radial_star:** 8-Point Star, 12-Point Star, 16-Point Star
- **bordered_field:** Simple Border, Double Border, Triple Border Complex
- **concentric_only:** Two-Tone Rings, Rainbow Gradient, Wide Band Minimalist
- **hybrid:** Segmented Core

### Strip/material family IDs in rosettePresets.ts

- `maple-light`, `walnut-dark`, `rosewood`, `ebony`, `padauk`, `cherry`, `mahogany`, `wenge`

---

## 3. Delta — Merge gap

### 3.1 Patterns in System 2 but NOT in System 1

| Source | Items |
|--------|--------|
| **rosettePresets.ts (family IDs)** | `repeating_single`, `multi_ring_alternating`, `radial_star`, `bordered_field`, `concentric_only`, `hybrid` |
| **rosettePresets.ts (variation names)** | Spanish Rope (16), Wave Pattern (12), German Rope (8), Fine Herringbone (32), Wide Rope (6), Triple Ring Classic, Five Ring Delicate, Seven Ring Complex, 8-Point Star, 12-Point Star, 16-Point Star, Simple Border, Double Border, Triple Border Complex, Two-Tone Rings, Rainbow Gradient, Wide Band Minimalist, Segmented Core |
| **rosette-designer-v5.html** | *None* — recipe set matches System 1. |

So: **all 6 pattern families and all 19 variation names** exist only in the TS frontend library; the backend has no equivalent recipe or pattern IDs for them.

### 3.2 Patterns in System 1 but NOT in System 2

| Source | Items |
|--------|--------|
| **rosettePresets.ts** | All **8 recipe IDs**: `vintage-martin`, `shell-classic`, `herringbone-band`, `celtic-ring`, `checkerboard-mosaic`, `minimalist`, `abalone-burst`, `rosewood-maple` — the TS file does not define these; it uses a family/variation taxonomy instead. |
| **rosette-designer-v5.html** | *None* — same 8 recipes as System 1. |

So: **all 8 backend recipe IDs** are absent from `rosettePresets.ts`; they exist only in the backend and in the HTML prototype.

---

## 4. Summary

| Comparison | In S2 only | In S1 only |
|------------|------------|------------|
| **Backend (S1) vs HTML (S2)** | 0 | 0 — **in sync** |
| **Backend (S1) vs rosettePresets.ts (S2)** | 6 family IDs + 19 variation names | 8 recipe IDs |

**Merge gap:** The backend and the HTML prototype share the same **8 named recipes**. The client library `rosettePresets.ts` is a **separate taxonomy** (6 pattern families, 19 parametric variations) and never merged with the backend recipe list: no mapping from family/variation to recipe IDs, and no backend representation of families/variations.

---

## 5. Auth / tier system — API feature gating

### 5.1 Where it lives

- **Edition (product) tier:** `app/middleware/edition_middleware.py`
- **Subscription (user) tier:** `app/auth/supabase_provider.py`, `app/middleware/tier_gate.py`
- **Persistence:** `app/db/models/user_profile.py`, `app/db/models/feature_flag.py`, migration `0001_supabase_auth_tables.py`

### 5.2 Tier levels

| System | Levels | Notes |
|--------|--------|--------|
| **Edition (middleware)** | `express`, `pro`, `enterprise`, plus standalone: `parametric`, `neck_designer`, `headstock_designer`, `bridge_designer`, `fingerboard_designer`, `cnc_blueprints` | Product/edition; not user subscription. Resolved via `X-Edition`, `?edition=`, env `LTB_DEFAULT_EDITION`; default `pro`. |
| **Subscription (Supabase/tier_gate)** | `free`, `pro` | User tier in `user_profiles.tier`. Hierarchy: pro > free (`TIER_LEVELS = {"free": 0, "pro": 1}`). |

### 5.3 Mechanism to gate API features by tier

- **Edition:**  
  - `get_edition` → `EditionContext` with `features` set.  
  - `ctx.can_access("feature_key")`, `ctx.require_feature("feature_key")`, `require_pro`, `require_enterprise`, `require_feature("adaptive_pocketing")` etc.  
  - Features are listed in `EDITION_FEATURES` and `FEATURE_REQUIREMENTS` (e.g. `gcode_export` → Pro; `fleet` → Enterprise).  
  - No DB lookup; edition comes from header/query/env.

- **Subscription (user tier):**  
  - `get_user_tier(user_id, db)` reads `user_profiles.tier` (returns `"free"` if missing).  
  - `check_feature_access(tier, feature_key, db)` reads `feature_flags` (`enabled`, `min_tier`); compares `TIER_LEVELS[tier] >= TIER_LEVELS[min_tier]`.  
  - **tier_gate.py:** `require_feature(feature_key)` and `require_tier("pro")` (or `require_pro`) enforce 401/403. Used with `get_current_principal` + DB.  
  - Seed feature flags in migration: `basic_dxf_export`, `gcode_generation`, `blueprint_import` (free); `ai_vision`, `batch_processing`, `advanced_cam`, `custom_posts` (pro).

So: **yes**, there is a mechanism to gate API features by tier: **edition** for product-level features (no DB), **subscription tier** for per-user gating via `user_profiles.tier` and `feature_flags` + `require_feature` / `require_tier` in `tier_gate.py`.
