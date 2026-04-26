# Blueprint Pipeline Regression Investigation

**Date:** 2026-04-26
**Status:** Investigation complete, fix deferred to dedicated sprint
**Terminal:** 1

---

## Summary

The blueprint extraction pipeline has multiple layers of regression. The documented recovery mode (`restored_baseline`) has itself degraded since its creation. A focused sprint is required to restore working behavior.

---

## Baseline Document Reference

**Document:** `docs/RECOVERY_BASELINE.md`
**Baseline commit:** `86c49526` (2026-04-11 01:41:33)
**Regression commit:** `f49ead1d` (2026-04-12 15:42:22)

### Document's Claimed Performance (Melody Maker)

| Metric | REFINED | restored_baseline |
|--------|---------|-------------------|
| Entity count | 24,097 | 343,399 |
| Confidence | 0.086 | **0.690** |
| Action | REJECT | REVIEW |

---

## Current State (2026-04-26 Testing)

### Melody Maker PDF

| Metric | REFINED | restored_baseline | Document claimed |
|--------|---------|-------------------|------------------|
| Dimensions | 559 × 432 mm | 559 × 432 mm | 647 × 500 mm |
| Entity count | 44,475 | 344,872 | 343,399 |
| Closed contours | 1 | 166 | — |
| Confidence | 0.332 | **0.384** | **0.690** |
| Action | review | review | review |

### Cuatro Puertorriqueño PDF

| Metric | Vectorizer (phase3) | restored_baseline |
|--------|---------------------|-------------------|
| Dimensions | 272 × 500 mm | 251 × 450 mm |
| Entity count | 22,794 | 232,501 |
| Closed contours | — | 145 |
| Confidence | N/A | 0.356 |
| Action | N/A | review |

---

## Key Findings

### 1. restored_baseline mode has degraded

- Document claimed 0.690 confidence
- Current testing shows 0.384 confidence
- **45% confidence drop** since document was written

### 2. "Ship as fallback" was never resolved

From `docs/RECOVERY_BASELINE.md` status table:
```
| Ship as fallback | PENDING | — |
```

The fix was documented but never deployed to production.

### 3. 11 commits have modified blueprint files since recovery

```
git log --oneline 46c3cec4..HEAD -- services/api/app/services/blueprint_clean.py services/api/app/services/blueprint_orchestrator.py
```

Commits include:
- `3db07c62` fix(vectorizer): restore morphological gap closing in enhanced mode
- `ab6f7632` feat(orchestrator): add mode=enhanced for multi-scale extraction
- `d9435834` feat(orchestrator): wire spec_name parameter for scale correction
- `814be53b` Revert "feat(vectorizer): implement phase 6b confidence-gated body polyline output"
- `ec56946a` feat(vectorizer): implement phase 6b confidence-gated body polyline output
- `db713cc7` fix(vectorizer): raise gap join thresholds for thin-stroke PDFs
- `3b18e852` feat(vectorizer): add conservative BODY-layer gap joining
- `0bcddcb4` feat(vectorizer): add acceptance grading for layered extraction
- `6284078d` feat(blueprint): integrate layer building and controlled export (Phase 4)
- `ffd07421` feat(blueprint): wire real annotation pass into dual-pass extraction
- `e6950d25` feat(vectorizer): add LAYERED_DUAL_PASS mode stub to orchestrator

### 4. Code inserted into wrong function

From `SPRINTS.md`:
```
OutlineReconstructor inserted into dead code path 
(_clean_blueprint_restored_baseline) instead of production 
path (_clean_blueprint_refined) — never executed
```

This explicitly documents that code meant for the production path was accidentally put in the dead code path.

---

## Test Artifacts Preserved

```
services/api/test_temp/baseline_comparison/
├── melody_maker_restored_baseline.dxf  (54.3 MB, 344,872 entities)
└── cuatro_restored_baseline.dxf        (29.0 MB, 232,501 entities)
```

---

## Architectural Context

Three independent extraction systems exist (confirmed by Diagnostic 3):

| System | Location | Purpose |
|--------|----------|---------|
| vectorizer_phase3.py | services/blueprint-import/ | CLI PDF extraction with ML classification |
| blueprint_extract.py | services/api/app/services/ | API extraction (simple edge detection) |
| photo_vectorizer_v2.py | services/photo-vectorizer/ | Photo/image extraction |

The orchestrator uses `blueprint_extract.py`, not `vectorizer_phase3.py`. They produce different outputs by design (57x entity count difference).

---

## Recommended Next Step

**Test commit `86c49526` directly via git checkout** to verify the document's claimed behavior.

```bash
git worktree add ../luthiers-toolbox-baseline 86c49526
cd ../luthiers-toolbox-baseline/services/api
# Run same Melody Maker test
# Compare confidence score to document's claimed 0.690
```

If `86c49526` produces the claimed 0.690 confidence:
- Bisect between `86c49526` and current HEAD to find regression points
- Consider reverting to baseline and reapplying changes selectively

If `86c49526` does NOT produce claimed behavior:
- Document was inaccurate
- Investigation must start from scratch

---

## Related Findings (Same Session)

1. **Sprint 3B PR 1 committed:** `9397c055` — migrated 3 critical path files to DxfWriter
2. **EXTMIN/EXTMAX hotfix:** `3b7e0a99` — removed inverted sentinel values (ezdxf still writes its own)
3. **Sprint 3 migration claims false:** 10/12 files never actually migrated (Terminal 2 finding)
4. **Scale issues:** Both extraction systems report wrong scale (separate from DXF migration)

---

## Status

| Item | Status |
|------|--------|
| Regression characterized | COMPLETE |
| Baseline document found | COMPLETE |
| restored_baseline tested | COMPLETE (degraded) |
| Root cause isolated | PENDING (requires 86c49526 checkout) |
| Fix implemented | BLOCKED |
| Production fallback shipped | BLOCKED |

**Next action:** Fresh sprint to test `86c49526` directly and trace regression path.

---

## Author

Terminal 1 (Claude Code)
Date: 2026-04-26
