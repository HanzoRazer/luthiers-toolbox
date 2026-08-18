# PR #280 — `typescript` 5.9.3 → 7.0.2: incompatibility witness and disposition

**Subject:** `dependabot/npm_and_yarn/packages/client/typescript-7.0.2` (PR #280)
**Substrate:** `origin/main` @ `3e925c50`; PR head CI run `32015909465`; local probe worktree
on `packages/client` with `npm ci` + `npm install --no-save typescript@<v>`
**Disposition:** **CLOSE #280.** Replace with a manual `typescript@6.0.3` upgrade.
**Related:** DEP-SEC-001A (`docs/ci/DEPENDABOT_TRIAGE_AND_DECISION_2026-08-09.md` §5), BR-021

---

## 1. Verdict

TypeScript 7 is not adoptable by this package today, and the reason is structural rather than
a matter of stricter diagnostics. **No application source needs to change.** Three separate
tools in the client toolchain break, all from one cause.

`typescript@7.0.2` ships an `exports` map whose package root is a version stub:

```
7.0.2:  "." : "./lib/version.cjs"   + ./unstable/{fs,ast,sync,async,proto,...}
        bin: { tsc }                       # tsserver bin REMOVED
        engines: node >= 16.20.0
6.0.3:  (no exports field at all)
        bin: { tsc, tsserver }
        engines: node >= 14.17
5.9.3:  (no exports field at all)
        bin: { tsc, tsserver }
        engines: node >= 14.17
```

Every consumer that does `require('typescript')` or deep-imports `typescript/lib/*` therefore
loses the compiler API. Three of ours do.

| Tool | Version here | Failure under TS 7.0.2 | Exit |
|---|---|---|---|
| `vue-tsc` (type-check) | `^2.1.0` | `ERR_PACKAGE_PATH_NOT_EXPORTED: './lib/tsc' is not defined by "exports"` | 1 |
| `@typescript-eslint/*` (lint) | `^6.21.0` | `TypeError: Cannot read properties of undefined (reading 'Intrinsic')` in `type-utils/dist/containsAllTypesByName.js:27` | 2 |
| `@vue/compiler-sfc` (vitest **and** `vite build`) | via `@vitejs/plugin-vue@^5` | `[@vue/compiler-sfc] No fs option provided to compileScript in non-Node environment` — it sources its filesystem from `ts.sys`, which the stub does not expose | 1 |

The third one is the deploy-breaker: it fires while compiling
`src/tools/audio_analyzer/renderers/AudioRenderer.vue`, whose `defineProps<RendererProps>()`
uses an **imported** type, which forces SFC-level type resolution.

**The "Node version" concern raised in review is refuted.** TS 7 raises the engine floor to
`>=16.20.0`; CI (`client_lint_build.yml`) and both client Dockerfiles pin Node 20. Node was
never the blocker.

---

## 2. Evidence

### 2.1 CI witness (PR #280 head, run `32015909465`, job `lint-build`)

```
> vue-tsc --noEmit
Error [ERR_PACKAGE_PATH_NOT_EXPORTED]: Package subpath './lib/tsc' is not defined by
  "exports" in .../packages/client/node_modules/typescript/package.json
  at Object.run (.../node_modules/vue-tsc/index.js:7:32)
##[error]Process completed with exit code 1

TypeError: Failed to load plugin '@typescript-eslint' declared in '.eslintrc.cjs':
  Cannot read properties of undefined (reading 'Intrinsic')
  at Object.<anonymous> (.../@typescript-eslint/type-utils/dist/containsAllTypesByName.js:27:30)
##[error]Process completed with exit code 2

FAIL src/tools/audio_analyzer/renderers/__tests__/pickRenderer.spec.ts
Error: [@vue/compiler-sfc] No fs option provided to `compileScript` in non-Node environment.
 Test Files  1 failed | 40 passed | 1 skipped (42)
```

**The first two were reported as green steps.** See §4.

### 2.2 Local probe — `vite build`, i.e. the Railway failure

Reproduced against the same source:

```
typescript@7.0.2 -> npx vite build
  error during build:
  [vite:vue] [@vue/compiler-sfc] No fs option provided to `compileScript` ...
  EXIT=1 ; dist/index.html NOT produced
```

`packages/client/Dockerfile` runs `npm run build` then
`test -f /app/dist/index.html || (echo "Build failed" && exit 1)`. That is precisely the
`reliable-elegance - @luthiers-toolbox/client` deployment failure reported on the PR. The
Railway failure and the vitest failure are **one bug**, not two.

### 2.3 Local probe — `typescript@6.0.3` is clean

Same worktree, same source, only the compiler swapped:

| Check | TS 5.9.3 (current lock) | TS 6.0.3 |
|---|---|---|
| `vue-tsc --noEmit` | exit 2, **150** `error TS` diagnostics | exit 2, **150** — output **byte-identical** (`diff` empty) |
| `eslint . --ext .ts,.vue` | exit 1, 34 errors / 7683 warnings | exit 1, **34 errors / 7683 warnings** — identical |
| `vitest run` | — | **exit 0, 41 files, 756 passed** |
| `vite build` | — | **exit 0, `dist/index.html` produced** |

One caveat, and it is the step the review did not identify: on TS 6.0.3 the *unmodified*
tsconfig fails fast with a single diagnostic before type-checking anything —

```
tsconfig.json(26,5): error TS5101: Option 'baseUrl' is deprecated and will stop
functioning in TypeScript 7.0. Specify compilerOption '"ignoreDeprecations": "6.0"'.
```

Deleting `"baseUrl": "."` is the correct fix rather than silencing it: the single `paths`
entry is already tsconfig-relative (`"@/*": ["./src/*"]`), so mapping is unaffected. That is
the configuration the identical-150 result above was measured under, including the 33
pre-existing `Cannot find module '@/…'` diagnostics, which are unchanged in both directions.

---

## 3. Disposition

1. **Close PR #280.** Merging it red-lines the client build and the Railway deploy.
2. **`.github/dependabot.yml`** — `typescript`, `vue-tsc`, `eslint`, `@typescript-eslint/*`
   majors added to `ignore`, joining `vite`/`vitest` as DEP-SEC Tier-2. These four move as one
   unit; a lone major of any of them is unmergeable by construction. Dependabot will close
   #280 itself once this lands.
3. **Replacement upgrade — `typescript@6.0.3`** (branch `deps/client-typescript-6`), which is
   validated above and is also the compiler TS 7 expects you to migrate *from*.
4. **TypeScript 7 is not scheduled.** Re-open it only when `vue-tsc`/Volar and
   `@typescript-eslint` both declare TS 7 support; that is a coordinated multi-package
   migration, not a Dependabot bump.

---

## 4. The durable finding — the gate could not have caught this

`client_lint_build.yml` carried `continue-on-error: true` on **both** the type-check and the
lint step. So on PR #280:

- `Type check (vue-tsc)` — vue-tsc crashed, exit 1, **zero files checked** → step reported green
- `Lint (ESLint)` — plugin failed to load, exit 2, **zero files linted** → step reported green
- `Run tests (Vitest)` — no tolerance flag → red, the only thing that noticed

This is DEP-SEC-001A §5 and BR-021 landing exactly as predicted: *"a major bump performed
against that configuration would produce no automated signal if it broke the build."* The
tolerance was written for **150 known type errors**; what it actually tolerated was the
compiler not running at all.

The fix in this change keeps the debt tolerance but separates the two cases:

- **vue-tsc** — tolerated only when it emits at least one `error TS…` diagnostic. Exit non-zero
  with no diagnostic is a toolchain failure and fails the job.
- **ESLint** — exit 1 (findings) tolerated; exit 2 or higher (fatal config/plugin error) fails
  the job.

Verified against both states in the probe worktree:

| Toolchain | Type-check step | Lint step |
|---|---|---|
| `typescript@7.0.2` | **exit 1** — "vue-tsc exited 1 without emitting a single TS diagnostic" | **exit 1** — "ESLint exited 2 - fatal configuration/plugin error" |
| `typescript@5.9.3` (main today) | exit 0 — "150 pre-existing type diagnostics (non-blocking, BR-021)" | exit 0 — findings tolerated |

BR-021 itself is untouched: the 150 diagnostics remain deferred debt.

---

## 5. Secondary observations

- **The stale TODO undercounted its own debt in the wrong direction.** The comment said
  *"Fix 400+ pre-existing type errors"*; the measured count on `3e925c50` is **150**. BR-021 is
  smaller than its record claims.
- **`--max-warnings=1200` is inert.** The client reports **7683** warnings, so `npm run lint`
  can never exit 0 on this budget — the flag reads like a ratchet but binds nothing. Setting a
  real, ratcheting budget is an owner decision and is *not* changed here.
- **The Dependabot "missing labels" bot comment is not a config defect.** `.github/dependabot.yml`
  correctly requests `dependencies` and `javascript`; those two labels **do not exist in the
  repository**, so Dependabot cannot apply them. The fix is to create the labels, which is a
  repo-settings change and is deliberately left to the owner:
  ```
  gh label create dependencies --color 0366d6 --description "Dependency updates"
  gh label create javascript   --color f1e05a --description "JavaScript/TypeScript ecosystem"
  ```
  Removing them from the config, as review suggested, would discard working intent.
- **`.eslint-rules/package.json` is an unmonitored npm manifest.** `.github/dependabot.yml`
  watches only `/packages/client`. Low-value (local rule package, no runtime reach) but it is a
  real gap in the "active dependency-security intake boundary" the config header claims.
