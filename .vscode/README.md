# VSCode Workspace Guard – CompareLab

This workspace is configured to highlight **direct mutations** of CompareLab core state:

- `isComputingDiff`
- `diffDisabledReason`
- `overlayDisabled`

ESLint runs **on type**, and the custom rule `no-direct-state-mutation` marks these mutations as errors.

## Multi-Layer Protection System

This workspace enforces CompareLab protocol (B22.8) through **4 defensive layers**:

### Layer 1: Inline Comments
**File:** `client/src/composables/useCompareState.ts`

30-line guardrail header at the top of the state machine explains:
- Which state is protected
- Violation examples (❌ WRONG)
- Correct patterns (✅ RIGHT)
- All 5 protocol rules
- References to checklist and README

### Layer 2: ESLint Rules (Real-Time)
**File:** `.eslint-rules/no-direct-state-mutation.js`

Custom ESLint rule that flags direct mutations as you type:
- Runs on every keystroke (`eslint.run: "onType"`)
- Shows red squiggles immediately
- Blocks 3 forbidden mutations:
  - `isComputingDiff.value = ...`
  - `overlayDisabled.value = ...`
  - `diffDisabledReason.value = ...`

### Layer 3: Unit Tests
**File:** `client/src/composables/useCompareState.spec.ts`

40+ unit tests with 95%+ coverage:
- Test skeleton wrapper behavior
- Validate overlay disable logic
- Verify error recovery patterns
- Check double-click protection

Run with: `cd client && npm run test -- useCompareState`

### Layer 4: Pre-Commit Hooks
**Files:** `.husky/pre-commit`, `package.json` (lint-staged)

Husky + lint-staged prevent commits with violations:
- ESLint runs on all staged CompareLab files
- Unit tests run automatically
- Commit aborted if either fails
- Works even outside VSCode (CLI, CI)

## How It Works Together

If you see a **red squiggle** when touching these refs:

> ❌ **Direct mutation detected**
> 
> Use `runWithCompareSkeleton()` and `useCompareState()` actions instead.

**Correct Pattern:**
```typescript
// ✅ RIGHT - Use the wrapper
await compareState.runWithCompareSkeleton(() => {
  return api.compareSvg(baselineId, geom)
})

// ✅ RIGHT - Use composable actions
await compareState.computeDiff(baselineId, geom)

// ❌ WRONG - Direct mutation (ESLint error)
isComputingDiff.value = true
```

## Local Development Workflow

1. **Write code** → ESLint shows red squiggle immediately (Layer 2)
2. **Save file** → VSCode auto-formats, ESLint re-validates
3. **Run tests** → `npm run test -- useCompareState` (Layer 3)
4. **Stage & commit** → Husky runs lint + tests (Layer 4)
5. **Push to GitHub** → CI workflow runs full suite

## Troubleshooting

### ESLint Not Running
- Install extension: `dbaeumer.vscode-eslint`
- Check output: "ESLint" tab in VSCode Output panel
- Verify `eslint.run: "onType"` in workspace settings

### Rule Not Firing
- Check file path: Rule only applies outside `useCompareState.ts`
- Restart ESLint server: Ctrl+Shift+P → "ESLint: Restart ESLint Server"
- Verify `.eslint-rules/` folder exists with rule file

### Pre-Commit Hook Failing
- Run manually: `cd client && npm run lint`
- Check staged files: `git status`
- Fix violations, re-add files, commit again

## References

- **Component API:** `client/src/components/compare/README.md`
- **Protocol Workflow:** `docs/COMPARELAB_BRANCH_WORKFLOW.md`
- **Dev Checklist:** `docs/COMPARELAB_DEV_CHECKLIST.md`
- **CI Workflow:** `.github/workflows/comparelab-tests.yml`

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│  Developer writes code                  │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  Layer 1: Inline Comments               │
│  (Education - Read the header)          │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  Layer 2: ESLint (onType)               │
│  (Prevention - Red squiggle)            │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  Layer 3: Unit Tests (npm test)         │
│  (Validation - 40+ tests)               │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  Layer 4: Pre-Commit Hook (Husky)       │
│  (Enforcement - Block bad commits)      │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  Commit lands in repo (protected)       │
└─────────────────────────────────────────┘
```

## Status

- ✅ Custom ESLint rule active
- ✅ VSCode onType linting enabled
- ✅ Red error highlighting configured
- ✅ Pre-commit hooks installed
- ✅ Unit tests passing (40+ tests)
- ✅ CI workflow active (GitHub Actions)

**All 4 layers operational** ✓
