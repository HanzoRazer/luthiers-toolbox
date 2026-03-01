# Code Quality Handoff - Luthiers Toolbox Client
**Generated**: 2026-02-25 | **Analyzer**: v2 (improved)
**Scope**: `packages/client/src/` | **Total Issues**: 4,783

---

## Executive Summary

| Severity | Count | Action |
|----------|-------|--------|
| Critical | 0 | None (v2 eliminated false positives) |
| Warning | 1,469 | Review duplicates, dead CSS |
| Info | 3,314 | Magic numbers, TODOs (low priority) |

**Key Win**: v2 analyzer reduced noise 65% (13,800 → 4,783) by fixing Vue `<script setup>` false positives.

---

## Priority 1: Duplicate Code Blocks (Warning)

**Pattern**: 5+ identical/similar lines across files
**Impact**: Maintenance burden, inconsistent bug fixes

### Hotspots (by issue count)

| Directory | Duplicates | Action |
|-----------|------------|--------|
| `components/adaptive/composables/` | ~120 | Extract shared composables |
| `components/compare/` | ~100 | Create CompareUtils.ts |
| `components/rosette/composables/` | ~90 | Consolidate pattern helpers |
| `components/rmos/composables/` | ~50 | Unify RMOS utilities |
| `views/` | ~80 | Extract view-level hooks |

### Common Duplicate Patterns

1. **Error handling boilerplate** (50+ occurrences)
   ```typescript
   // Repeated pattern - extract to useAsyncAction()
   loading.value = true
   try { ... } catch (e) { error.value = e } finally { loading.value = false }
   ```

2. **Fetch + transform** (40+ occurrences)
   ```typescript
   // Repeated pattern - extract to useFetchTransform()
   const data = await fetch(url)
   const json = await data.json()
   return transform(json)
   ```

3. **Ref initialization** (30+ occurrences)
   ```typescript
   // Repeated pattern - extract to useFormState()
   const form = ref({ field1: '', field2: '', ... })
   const errors = ref({})
   const touched = ref({})
   ```

---

## Priority 2: Dead CSS Selectors (Warning)

**Pattern**: CSS selectors with no matching template elements
**Impact**: Bundle bloat, confusion

### Hotspots

| Component | Dead Selectors | Likely Cause |
|-----------|---------------|--------------|
| `ScientificCalculator.vue` | 15+ | Refactored template |
| `PipelineLabView.vue` | 12+ | Removed features |
| `BlueprintLabView.vue` | 10+ | Template changes |
| `ManufacturingCandidateList.vue` | 8+ | Dynamic classes |

**Fix Strategy**: Run `npm run build` with CSS purge, or manually audit `.btn-*`, `.card-*` classes.

---

## Priority 3: Magic Numbers (Info)

**Pattern**: Numeric literals without named constants
**Impact**: Unclear intent, harder maintenance

### Already Allowlisted (safe to ignore)
- 0, 1, 2, -1, 100, 50, 25, 75
- Powers of 2: 8, 16, 32, 64, 128, 256, 512, 1024
- HTTP codes: 200, 201, 400, 401, 403, 404, 500
- Angles: 90, 180, 270, 360

### Candidates for Named Constants

| Value | Occurrences | Suggested Name |
|-------|-------------|----------------|
| 300 | 40+ | `ANIMATION_DURATION_MS` |
| 500 | 35+ | `DEBOUNCE_DELAY_MS` |
| 1000 | 30+ | `SECOND_MS` |
| 12 | 25+ | `FRET_COUNT` or `GRID_COLUMNS` |
| 22 | 20+ | `MAX_FRETS` |
| 650 | 15+ | `SCALE_LENGTH_MM` |

**Fix**: Create `constants/dimensions.ts`, `constants/timing.ts`

---

## Priority 4: TODO/FIXME Comments (Info)

**Pattern**: Unresolved work markers
**Impact**: Technical debt tracking

### Distribution

| Tag | Count | Action |
|-----|-------|--------|
| TODO | ~200 | Triage into issues |
| FIXME | ~50 | Higher priority bugs |
| HACK | ~20 | Refactor candidates |
| XXX | ~10 | Review immediately |

**Fix**: Run `grep -rn "TODO\|FIXME\|HACK\|XXX" src/` and create GitHub issues.

---

## Files Requiring Most Attention

| File | Warnings | Info | Primary Issue |
|------|----------|------|---------------|
| `components/toolbox/ScientificCalculator.vue` | 45 | 30 | Duplicates + dead CSS |
| `views/PipelineLabView.vue` | 40 | 25 | Duplicates + magic numbers |
| `views/BlueprintLabView.vue` | 35 | 20 | Duplicates + dead CSS |
| `components/rosette/DesignFirstWorkflowPanel.vue` | 30 | 25 | Duplicates |
| `components/rmos/ManufacturingCandidateList.vue` | 25 | 20 | Dead CSS |

---

## NOT Included in v2 (Manual Check Needed)

The v2 analyzer doesn't check these (old analyzer did, but with many false positives):

1. **Memory leaks** - `setTimeout`/`setInterval` without cleanup
   - Search: `grep -rn "setTimeout\|setInterval" src/ | grep -v clearTimeout`

2. **Event listeners** - `addEventListener` without `removeEventListener`
   - Search: `grep -rn "addEventListener" src/ | grep -v removeEventListener`

3. **eval() usage** - Known in `ScientificCalculator.vue`
   - Risk: XSS if user input reaches eval
   - Fix: Use `math.js` library or safe expression parser

---

## Quick Wins (< 1 hour each)

1. **Create `composables/useAsyncAction.ts`** - Eliminates 50+ duplicates
2. **Create `constants/timing.ts`** - Names 100+ magic numbers
3. **Audit `ScientificCalculator.vue`** - Highest issue density
4. **Run CSS purge** - Removes dead selectors automatically

---

## Running the Analyzer

```bash
cd C:/Users/thepr/Downloads/code-analysis-tool

# Full scan
PYTHONPATH=scripts python -m code_quality C:/Users/thepr/Downloads/luthiers-toolbox/packages/client/src

# Warnings only
PYTHONPATH=scripts python -m code_quality --severity warning C:/Users/thepr/Downloads/luthiers-toolbox/packages/client/src

# Summary only
PYTHONPATH=scripts python -m code_quality --summary C:/Users/thepr/Downloads/luthiers-toolbox/packages/client/src

# Specific directory
PYTHONPATH=scripts python -m code_quality C:/Users/thepr/Downloads/luthiers-toolbox/packages/client/src/components/toolbox
```

---

## Config Location

`C:/Users/thepr/Downloads/code-analysis-tool/scripts/code_quality/.codequalityrc.json`

Adjust `rules.magic_numbers.allowlist` to suppress domain-specific values.

---

*End of handoff*
