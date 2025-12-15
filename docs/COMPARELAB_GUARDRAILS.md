# COMPARELAB GUARDRAILS

**One Page. Everything. No madness.**

CompareLab (B22.8+) relies on a strict state machine. These guardrails prevent UI drift, broken overlays, and bad merges.

---

## 1. Canonical State Machine

**Implemented in:**  
`client/src/composables/useCompareState.ts`

**It owns:**
- `isComputingDiff`
- `diffDisabledReason`
- `overlayDisabled`
- `runWithCompareSkeleton(fn)`

**RULE:** Nothing else in the codebase may mutate these directly.

**All diff operations must call:**
```typescript
await runWithCompareSkeleton(() => api.compareSvg(...));
```

---

## 2. ESLint Protection

**Custom rule:** `.eslint-rules/no-direct-state-mutation.js`

**Flags direct mutations like:**
```typescript
isComputingDiff.value = false;    // ❌ forbidden
overlayDisabled.value = true;     // ❌ forbidden
diffDisabledReason.value = null;  // ❌ forbidden
```

**Enabled in** `client/.eslintrc.cjs`:
```javascript
plugins: ["comparelab"],
rules: {
  "no-direct-state-mutation": "error"
},
rulePaths: ["../.eslint-rules"]
```

---

## 3. VSCode Real-Time Red Squiggles

**`.vscode/settings.json`:**
```json
{
  "eslint.run": "onType",
  "eslint.options": {
    "rulePaths": [".eslint-rules"]
  },
  "eslint.validate": ["vue","typescript","javascript","typescriptreact"],
  "editor.renderValidationDecorations": "on"
}
```

This makes violations appear **as you type**, not when you commit.

---

## 4. Husky + lint-staged (Pre-Commit Enforcement)

**Install:**
```bash
cd client
npm install -D husky lint-staged
```

**`.husky/pre-commit`:**
```bash
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

cd client && npx lint-staged
```

**`client/package.json`:**
```json
{
  "lint-staged": {
    "src/components/compare/**/*.{ts,vue}": [
      "eslint --fix",
      "vitest run --coverage -- useCompareState"
    ],
    "src/composables/useCompareState.{ts,spec.ts}": [
      "eslint --fix",
      "vitest run --coverage -- useCompareState"
    ]
  }
}
```

**Result:** No commit allowed unless ESLint and CompareLab tests pass.

---

## 5. GitHub Action — CompareLab CI

**`.github/workflows/comparelab-tests.yml`:**
```yaml
name: CompareLab State Machine Tests
on:
  push:
    paths:
      - "client/src/components/compare/**"
      - "client/src/composables/useCompareState.ts"
  pull_request:
    paths:
      - "client/src/components/compare/**"
      - "client/src/composables/useCompareState.ts"
jobs:
  comparelab-tests:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: client
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: npm ci
      - run: npm run test -- useCompareState
```

Only runs when CompareLab code changes. Prevents unreviewed CompareLab regressions.

---

## 6. README Badge

**Add to root `README.md`:**
```markdown
[![CompareLab Tests](https://github.com/HanzoRazer/luthiers-toolbox/actions/workflows/comparelab-tests.yml/badge.svg)](https://github.com/HanzoRazer/luthiers-toolbox/actions/workflows/comparelab-tests.yml)
```

Shows CompareLab CI health at a glance.

---

## 7. Developer Checklist (Tape this to your monitor)

**If you touch `/components/compare/`, you MUST:**

- ✅ Run `npm run test -- useCompareState`
- ✅ Verify CompareLab UI still loads/skeletons correctly
- ✅ Fix any ESLint violations (including state-machine rule)
- ✅ Ensure CompareLab GitHub Action is green
- ✅ **Do not directly mutate core state refs**

---

## 8. Golden Rule

**All CompareLab diff logic flows through `useCompareState`.**

**No exceptions. No shortcuts. No direct state mutation.**

---

## Quick Reference

| Layer | File | Purpose |
|-------|------|---------|
| **State Machine** | `client/src/composables/useCompareState.ts` | Single source of truth |
| **ESLint Rule** | `.eslint-rules/no-direct-state-mutation.js` | Detect violations |
| **VSCode Config** | `.vscode/settings.json` | Real-time red squiggles |
| **Pre-Commit** | `.husky/pre-commit` | Block bad commits |
| **CI** | `.github/workflows/comparelab-tests.yml` | Prevent bad merges |

---

**Done. Short. Unified. Everything in one place. No more madness.**
