# Agent Session Bookmark — 2026-02-05 (Updated)

**Purpose:** Resume point for AI agent — ALL QUESTIONS RESOLVED
**Last Active:** 2026-02-05
**Session Goal:** ~~Answer 15 critical questions~~ ✅ COMPLETE — Ready for WP execution
**Ship Date:** March 02, 2026 (to testers)
**Target Score:** 7.0/10

---

## Status: ALL 15 QUESTIONS RESOLVED ✅

The product owner provided answers to all open questions. The project is **pre-production** (no live CNC tests, no external users). This enables aggressive cleanup.

---

## Final Q&A Resolution (Owner Answers 2026-02-05)

| # | Question | Final Answer | Status |
|---|----------|--------------|--------|
| Q1 | Shipped product boundary | **Tiered by marketing.** Owner's version: Smart Guitar + Audio Analyzer. Other tiers: feature-gated by marketing. | ✅ RESOLVED |
| Q2 | Second frontend consumer | **None.** `streamlit_demo/` is unused prototype (Vue is superset). `client/` is stale duplicate. Delete both. | ✅ RESOLVED |
| Q3 | `client/` vs `packages/client/` | `client/` is stale. Safe to delete. | ✅ RESOLVED |
| Q4 | Unsafe G-code incidents | **No** — system has never been live tested on real CNC machines. | ✅ RESOLVED |
| Q5 | Simulation mandatory | **By marketing tier** (feature flag, not universal). | ✅ RESOLVED |
| Q6 | Feeds/speeds validated | **Awaiting live test** — pre-production, no real-world validation yet. | ✅ RESOLVED |
| Q7 | Actual test coverage | **36%** (measured via `pytest --cov`). README claims "100%" are false. | ✅ RESOLVED |
| Q8 | Production deployment | Railway + Docker local. | ✅ RESOLVED |
| Q9 | Active users | **Zero** — pre-production. Aggressive remediation OK. | ✅ RESOLVED |
| Q10 | Staging environment | **N/A** — pre-production. Main branch IS staging until first release. | ✅ RESOLVED |
| Q11 | Domain knowledge | **Owner is domain expert** (single developer, builds guitars). | ✅ RESOLVED |
| Q12 | Rollback strategy | Git-based. | ✅ RESOLVED |
| Q13 | Cross-repo consumers | **Low risk** — ToolBox consumes FROM `sg-spec` and `tap_tone_pi`, not reverse. | ✅ RESOLVED |
| Q14 | Ship date | **March 02, 2026** (to testers) — ~25 days from today. | ✅ RESOLVED |
| Q15 | Target score | **7.0/10** (revised from 6.3). | ✅ RESOLVED |

---

## Key Decisions Made

### Product Strategy
- **Marketing tiers** will be established AFTER monorepo cleanup
- Tier repos already exist with some code: `ltb-express`, `ltb-pro`, `ltb-enterprise`, etc.
- Standalone products: `ltb-parametric-guitar`, `ltb-neck-designer`, `blueprint-reader`, etc.
- Goal: **7.0/10 clean monorepo** before splitting

### streamlit_demo/ Evaluation
- **Verdict:** Vue frontend is complete superset
- All features (Guitar Designer, Rosette Builder, Blueprint Reader, etc.) exist in Vue with more functionality
- **Action:** Safe to delete — no unique code to preserve

### __REFERENCE__/ Decision (Rule 5 Conflict)
- **Option C selected:** Archive externally, then delete
- **Timing:** AFTER other WP fixes complete (WP-0, WP-1, WP-4)
- Contains 5,324 files of historical reference material
- Will be moved to external repo/backup before deletion

---

## Verified Metrics

| Metric | Count | Source |
|--------|-------|--------|
| Test coverage | **36%** | `pytest --cov` (measured) |
| Tests passed | 1,363 | pytest run |
| Tests failed | 4 | Integration tests (need live server) |
| Bare `except:` blocks | 97 | grep |
| `except Exception` blocks | 1,622 | grep |

---

## WP-0 Deletion List — Confirmed vs. Pending Verification

| Item | Status | Action |
|------|--------|--------|
| `streamlit_demo/` | ✅ CONFIRMED DELETE | Vue is superset, no unique code |
| `client/` | ✅ CONFIRMED DELETE | Stale duplicate of `packages/client/` |
| `__ARCHIVE__/` | ⏳ VERIFY FIRST | Check contents before deletion |
| `__REFERENCE__/` | ⏳ DEFERRED | Archive externally AFTER other WP fixes |
| `server/` | ⏳ VERIFY FIRST | Check contents before deletion |
| Backup `.vue` files | ⏳ VERIFY FIRST | Confirm no imports reference them |
| Backup `.py` files | ⏳ VERIFY FIRST | Confirm no imports reference them |

---

## Execution Order (Updated)

| Phase | Work | Blocked By |
|-------|------|------------|
| **1** | WP-0: Delete `streamlit_demo/`, `client/` (confirmed) | Nothing |
| **2** | WP-0: Verify & delete `__ARCHIVE__/`, `server/`, backups | Phase 1 |
| **3** | WP-1 Tier 1A: Fix 97 bare `except:` blocks | Nothing |
| **4** | WP-1 Tier 1B: Fix safety-critical `except Exception` | Phase 3 |
| **5** | WP-4: Documentation triage + README fix (36% not 100%) | Nothing |
| **6** | Update Rule 5 in copilot-instructions.md | Phases 1-5 |
| **7** | Archive `__REFERENCE__/` to external repo | Phase 6 |
| **8** | Delete `__REFERENCE__/` from monorepo | Phase 7 |

---

## Timeline to Ship (March 02, 2026)

| Week | Dates | Focus |
|------|-------|-------|
| Week 1 | Feb 5-12 | WP-0 (dead code) + WP-1 Tier 1A (bare except) |
| Week 2 | Feb 12-19 | WP-4 (docs/README) + WP-1 Tier 1B |
| Week 3 | Feb 19-26 | WP-5 (Quick Cut onboarding) + polish |
| Week 4 | Feb 26-Mar 2 | Buffer + `__REFERENCE__/` archive + ship |

---

## Documents Reviewed

| Document | Status | Key Findings |
|----------|--------|--------------|
| `.github/copilot-instructions.md` | ✅ Read | Existing AI instructions (comprehensive) |
| `CHIEF_ENGINEER_HANDOFF.md` | ✅ Read + Updated | 6-phase remediation plan, 15 questions NOW RESOLVED |
| `REMEDIATION_PLAN.md` | ✅ Read + Updated | Timeline updated for March 02, 2026 ship date |
| `luthiers-toolbox-design-review.md` | ✅ Read | Original review scored 5.15/10 |
| `luthiers-toolbox-design-review-factcheck.md` | ✅ Read | Corrected score ~4.7/10, systematic undercount |

---

## Commands for Quick Resume

```powershell
# Run tests with coverage
cd "C:\Users\thepr\Downloads\luthiers-toolbox\services\api"
.venv/Scripts/python.exe -m pytest --cov=app --cov-report=term

# Delete confirmed dead code
cd "C:\Users\thepr\Downloads\luthiers-toolbox"
git rm -r streamlit_demo/
git rm -r client/

# Check what's in directories before deleting
ls -la __ARCHIVE__/
ls -la server/
```

---

*Updated 2026-02-05: All 15 questions resolved. Ready for WP execution.*
