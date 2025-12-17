# CompareLab Dev Checklist

> **Scope:** Any change that touches `client/src/components/compare/`, `client/src/composables/useCompareState.ts`, or related tests/docs.

This checklist exists to protect the CompareLab **state machine** and UI behavior from accidental regressions.

---

## 🎯 1. Files in Scope

## 🎯 1. Files in Scope

You **MUST** follow this checklist if you touch **any** of the following:

### Core State Machine
- `client/src/composables/useCompareState.ts`
- `client/src/composables/useCompareState.spec.ts`

### UI Components
- `client/src/components/compare/**/*.vue`
- `client/src/views/CompareLabView.vue`

### Documentation
- `docs/COMPARELAB_*.md`
- `docs/B22_*.md`
- `client/src/components/compare/README.md`

### Rule of Thumb

> If it can affect how CompareLab runs diffs, overlays, skeleton loading, or layer controls, this checklist applies.

---

## ✅ 2. Local Dev Steps (Before Commit)

### Step 1: Run CompareLab Unit Tests

From `client/` directory:

```bash
npm run test -- useCompareState
```

**Confirm:**
- ✅ All tests pass (40+ tests should run)
- ✅ No new warnings or noisy console logs
- ✅ Coverage remains ≥95% for state machine

**If tests fail:**
1. Review error messages for specific assertion failures
2. Check if you violated Protocol Rules 1-5 (see component README)
3. Verify state machine not bypassed
4. Run `npm run test:coverage` to see what's untested

---

### Step 2: Sanity-Check the UI

#### Start Services

```bash
# Terminal 1 - Backend
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd client
npm run dev
```

#### Manual Test Sequence

Open CompareLab in browser (`http://localhost:5173/compare-lab`):

1. **Load Geometry**
   - [ ] Import geometry JSON or load from Adaptive Lab
   - [ ] Geometry displays in UI

2. **Select Baseline**
   - [ ] Baseline picker shows available baselines
   - [ ] Select a baseline

3. **Trigger Diff Computation**
   - [ ] Click "Compare" or "Run Diff" button
   - [ ] **Skeleton loading stripes appear** (shimmer animation)
   - [ ] Controls disabled during computation

4. **Verify Success State**
   - [ ] Skeleton disappears when complete
   - [ ] Dual SVG display shows baseline vs. current
   - [ ] Overlay controls enabled
   - [ ] Stats displayed (added, removed, overlap)
   - [ ] Layer panel visible (if backend returns layers)

5. **Verify Error Handling**
   - [ ] Trigger error (e.g., disconnect backend, invalid baseline)
   - [ ] Warning banner appears with error message
   - [ ] Overlay controls disabled
   - [ ] Tooltips show disabled reason

6. **Test Layer Controls** (if applicable)
   - [ ] Layer checkboxes toggle
   - [ ] Diff badges visible on changed layers
   - [ ] Missing badges on incomplete layers

7. **Test Mode Switching**
   - [ ] Overlay mode works
   - [ ] Delta mode works
   - [ ] Blink mode works (if implemented)
   - [ ] X-ray mode works (if implemented)

---

### Step 3: Protocol Compliance Check

Review your changes against **B22.8 Protocol Rules** (see `client/src/components/compare/README.md`):

#### Protocol Rule 1: Single Source of Truth
- [ ] No manual mutations of `isComputingDiff`, `diffDisabledReason`, `overlayDisabled`
- [ ] All state changes go through composable actions

#### Protocol Rule 2: Wrapper Enforcement
- [ ] All async diff operations use `runWithCompareSkeleton()`
- [ ] No direct `fetch()` calls to `/api/compare/*` outside composable

#### Protocol Rule 3: Disabled State Binding
- [ ] All overlay controls bind `:disabled="overlayDisabled.value"`
- [ ] No local disabled logic in components

#### Protocol Rule 4: Props-Down / Events-Up
- [ ] State flows down via props
- [ ] Mutations flow up via events
- [ ] No direct composable calls from child components

#### Protocol Rule 5: Error Handling
- [ ] Errors captured in `diffDisabledReason`
- [ ] No silent error suppression
- [ ] User-visible error messages

**If any rule violated:** Refactor before committing

---

### Step 4: Update Documentation

If you changed state machine behavior:

- [ ] Update `client/src/components/compare/README.md`
  - Add new patterns to usage examples
  - Update state transition diagram
  - Document new actions/computed properties

- [ ] Update `docs/COMPARELAB_BRANCH_WORKFLOW.md`
  - Note protocol changes (if any)
  - Update status dashboard

- [ ] Update relevant `docs/B22_*.md` files
  - Implementation summaries
  - Test coverage changes

- [ ] Update this checklist (if process changed)

---

## 🔄 3. GitHub Workflow Guardrail

A dedicated CI workflow runs CompareLab tests whenever you touch CompareLab code or docs:

**Workflow:** `.github/workflows/comparelab-tests.yml`

**Status Badge:** [![CompareLab Tests](https://github.com/HanzoRazer/luthiers-toolbox/actions/workflows/comparelab-tests.yml/badge.svg)](https://github.com/HanzoRazer/luthiers-toolbox/actions/workflows/comparelab-tests.yml)

### Hard Rule

> **If you touch `components/compare/` or `useCompareState.ts`, the "CompareLab State Machine Tests" workflow MUST be ✅ green before merging.**

### How to Check

**Option 1: Badge Link**
- Click the badge in main README.md
- Verify your branch shows green checkmark

**Option 2: GitHub Actions Tab**
1. Go to repository → Actions
2. Click "CompareLab State Machine Tests" workflow
3. Find your branch/PR in the list
4. Confirm ✅ status

**Option 3: PR Checks**
- GitHub will show workflow status in PR
- Look for "CompareLab State Machine Tests / Run CompareLab unit tests"

### Confirm

- [ ] **CompareLab State Machine Tests** workflow is green for this PR
- [ ] No CompareLab-related test failures
- [ ] Coverage report shows ≥95% for state machine

**If workflow fails:**
1. Click "Details" on failed check
2. Review test output logs
3. Fix failing tests locally
4. Push fix and re-run workflow

---

## 📋 4. PR Checklist (Paste into PR Description)

Copy this block into PRs that affect CompareLab:

```markdown
### CompareLab Checklist (B22.8 Protocol Compliance)

#### Local Testing
- [ ] Ran `npm run test -- useCompareState` locally (from `client/`)
- [ ] All 40+ tests passed
- [ ] Coverage ≥95% for state machine core

#### UI Verification
- [ ] Sanity-checked CompareLab in browser
- [ ] Skeleton loading stripes display correctly
- [ ] Overlay controls disable during computation
- [ ] Error banner shows on failures
- [ ] Layer controls work (if applicable)

#### Protocol Compliance
- [ ] No manual state mutations (Rule 1)
- [ ] All async ops use `runWithCompareSkeleton()` (Rule 2)
- [ ] All controls bind to `overlayDisabled` (Rule 3)
- [ ] Props-down/events-up pattern maintained (Rule 4)
- [ ] Errors captured in `diffDisabledReason` (Rule 5)

#### CI/CD
- [ ] **CompareLab State Machine Tests** workflow is ✅ green
- [ ] Reviewed workflow logs (no warnings)

#### Documentation
- [ ] Updated `client/src/components/compare/README.md` (if behavior changed)
- [ ] Updated `docs/COMPARELAB_BRANCH_WORKFLOW.md` (if protocol changed)
- [ ] Updated relevant `docs/B22_*.md` files

#### Review Request
- [ ] Requested review from CompareLab maintainer (if available)
- [ ] Confirmed no CODEOWNERS violations
```

---

## ✅ Summary

**This checklist is the safety net that keeps B22.8's state machine patterns intact for future phases (B22.9, B23.x, etc.).**

---

**Status:** 🔒 Mandatory for all CompareLab changes  
**Version:** B22.8 (Current)  
**Next Review:** B22.9 protocol upload  
**Maintainer:** See CODEOWNERS file (if exists)

#### Controls not disabling
- Check `overlayDisabled` computed correctly in composable
- Verify `:disabled="overlayDisabled"` binding on controls

#### Banner not appearing
- Check `diffDisabledReason` prop flow from composable to component
- Verify `v-if="diffDisabledReason"` condition

#### State mutations outside composable
- Search codebase for direct `.value =` assignments to reactive refs
- Ensure all state changes go through composable actions

---

**Last Updated:** December 2, 2025  
**Commit:** B22.8 Guardrails & State Machine
