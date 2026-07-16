# SPINE-005 — Project-Scoped Instrument Hub Route Adoption (Audit)

**Status:** Implemented on a held draft PR for owner review.
**Evidence authority:** LAB-023, revalidated against production `origin/main`; PATCH_023 @ `ea05c68` (lab) as the governing implementation order.
**Scope class:** Frontend routing + Project-singleton concurrency hardening. No backend, schema, or persistence change.

This audit records what was delivered. It is written against the implemented diff, not the plan.

---

## 1. Objective delivered

The existing, already-built `InstrumentHubShell` is now reachable as a live, explicitly
Project-scoped route. A user can open the Instrument Hub through a canonical Project
identity, edit locally, and commit through the existing explicit **Apply to Project** path,
while the standalone Instrument Geometry workflow is preserved unchanged. No new Project
authority, store, loader, write path, backend API, or schema was introduced.

---

## 2. Evidence and revalidation

LAB-023 pinned its evidence at production `58ffadeb`. At implementation time `origin/main`
was `3d23c667`; the single intervening commit (`feat(ibg)`, PR #222) is backend Python only
(`git diff --name-only 58ffadeb..3d23c667 -- packages/client/` is empty). Every LAB-023
observation was reconfirmed on current `main`:

- the `/instrument-hub` alias still sat on the `InstrumentGeometry` route;
- `InstrumentHubShell.vue` still imported `./shared-state/...` while the directory is a
  sibling (`../shared-state/`), and a pristine type-check reproduced the two `TS2307`
  module-resolution errors;
- `useInstrumentProject.loadProject` still early-returned while a load was pending and still
  retained prior state on load failure.

The premise held; no material drift returned the work to investigation.

---

## 3. Route topology

### Before

| Path | Route name | Target |
| --- | --- | --- |
| `/instrument-geometry` | `InstrumentGeometry` | `InstrumentGeometryView.vue` |
| `/instrument-hub` (alias of the above) | `InstrumentGeometry` | `InstrumentGeometryView.vue` |

No live route rendered `InstrumentHubShell` or called `loadProject`.

### After

| Path | Route name | Target | Notes |
| --- | --- | --- | --- |
| `/instrument-geometry` | `InstrumentGeometry` | `InstrumentGeometryView.vue` | Unchanged |
| `/instrument-hub` | — | redirect → `/instrument-geometry` | Forwards query + hash verbatim; never infers a Project |
| `/instrument-hub/:projectId` | `InstrumentHub` | `InstrumentHubShell.vue` (`props: true`) | Canonical Project-scoped entry |

The alias was removed so the bare path could carry the redirect; the two surfaces are no
longer conflated under one route name.

---

## 4. Project identity flow

```
route /instrument-hub/:projectId
        │  props: true
        ▼
InstrumentHubShell  props.projectId  (sole identity source)
        │  onMounted + watch(props.projectId)
        ▼
useInstrumentProject.loadProject(projectId)   ← canonical existing load
        │
        ▼
local edit buffers  ──user clicks Apply──►  existing commit* methods (explicit write)
```

Identity comes only from the route parameter. It is never inferred from recent projects,
global current-project state, filenames, cached history, or browser storage. The Dashboard's
Project-aware Hub link derives its Project **only** from an explicit `route.query.project_id`
and never falls back to the `useInstrumentProject` singleton.

---

## 5. Mutation boundary (preserved)

Existing explicit user-initiated **Apply to Project** commits remain authorized through
`useInstrumentProject`. Route entry, Project loading, local editing, and navigation perform no
writes. No automatic write, implicit commit, new write method, or additional mutation path was
added. This was proven by tests asserting `putDesignState` is not called on mount, load, input,
or route change, and is called only on an explicit Apply click.

---

## 6. Concurrency hardening of the shared singleton

`useInstrumentProject` is a module singleton also observed by `CadSidebar`,
`AppDashboardView`, and `AssistantView`. Making it route-driven required response isolation.
Delivered, with no new abstraction and the public interface unchanged:

- **Latest-request-wins loading.** Each `loadProject` captures a monotonic generation; every
  post-`await` mutation and the `finally` are gated on that generation still being current, so
  a superseded load is a silent no-op and cannot publish another Project's data, error, or
  loading flag.
- **Quarantine on Project switch.** Loading a different Project clears the prior visible state
  up front, so a failed load never leaves the previous Project renderable under the new URL.
- **Single-flight explicit commits.** A second commit while one is pending issues no request
  and returns `false`; the caller's draft and the active save's metadata are untouched.
- **Cross-Project save isolation.** Each commit captures its target Project and generation; the
  server write always stands, but its response is applied to client state only while that
  Project is still active, so an A-save resolving after navigation to B cannot replace B's
  state, dirty, saving, error, or last-saved metadata.
- **`clearProject`** bumps the generation so an in-flight load cannot repopulate after clear.

The single-flight guard (`_saveInFlight`) is a private non-reactive module variable and is not
part of the public return; `_loadGen` likewise. No public export or method signature changed.

---

## 7. Compatibility behavior

- `/instrument-geometry` retains its component, route name, and behavior (directly tested).
- `/instrument-hub` and `/instrument-hub?x=1#y` redirect to `/instrument-geometry`, preserving
  query and hash; a `project_id` query on the bare path is **not** promoted to the Hub route.
- The one known bare-route caller, `SmartGuitarShell.vue`, keeps its `to="/instrument-hub"`
  link (routing through the redirect) and now truthfully labels the destination *Instrument
  Geometry*.

---

## 8. Tests and verification

Focused colocated tests (41 total, all green — 4 added by the §12 risk-closure pass):

| Spec | Count | Covers |
| --- | --- | --- |
| `router/index.spec.ts` | 11 | canonical route + name, explicit `projectId` prop, named build, required-param rejection, bare redirect w/ query+hash, `project_id`≠identity, unchanged legacy route |
| `shared-state/useInstrumentProject.spec.ts` | 16 | both A→B response orders, repeated same-id determinism, failed-B isolation, superseded-error suppression, single-flight refusal, stuck-saving regression, cross-Project save success + failure isolation, commit request shape, interface stability, `clearProject` determinism; **+ A1→A2→B→A3 mixed-order latest-wins (§4.4); + clearProject-during-save discard & guard release (§5.4)** |
| `hub/InstrumentHubShell.spec.ts` | 8 | explicit-id load, prop A→B reload, controlled error w/ no stale content, retry binds to current prop, no auto-commit, explicit Apply delegates to the composable; **+ no spec-draft leak into a spec-less destination Project (§5.1); + Apply disabled while a commit is in flight (§4.1)** |
| `views/AppDashboardView.spec.ts` | 6 | named route from explicit query, legacy fallback for absent/empty/array query, no singleton fallback, truthful labels |

Suite / gate results (after the §12 risk-closure pass):

- **Full frontend suite:** 756 passed, 17 todo, 1 file skipped, **0 failed** (42 files).
- **Type-check (`vue-tsc --noEmit`):** 150 pre-existing errors, **0 introduced**. Baseline on
  pristine `origin/main` was 154; the 4 resolved are the Hub's own import/type errors closed by
  the import correction.
- **Build (`vite build`):** succeeded (the >500 kB chunk-size note is a pre-existing advisory
  warning, not an error).
- **CBSP21 patch-input and gate checks:** pass against the `origin/main...HEAD` file set.

### Independent review correction

Independent review of the held draft PR (three fresh reviewers across the eight review
dimensions) returned READY / READY-WITH-REQUIRED-CORRECTIONS. One confirmed required
correction was applied: `_commit` set the reactive `_isSaving` display flag unconditionally
but cleared it only inside the identity/generation-gated apply branches, so a same-id
`loadProject` that superseded an in-flight save left a stuck "Saving…" indicator (display
only; no data-safety or single-flight-guard impact). The reset moved into the `finally`,
where single-flight guarantees exactly one save owns the flag. Four §9-named test cases that
lacked a standalone witness were added (stuck-saving regression, cross-Project save-failure
isolation, repeated same-id determinism, array-form query fallback).

---

## 9. Known limitations (recorded, not repaired)

Activation makes previously unmounted Hub behavior reachable. SPINE-005 records these existing
behaviors without broadening its scope to repair them:

- Bracing and Setup stages contain explicit future-phase placeholder panels.
- The Body **Apply to Project** flow calls two existing commit methods sequentially, so the
  existing API can persist the first change before a later call fails. This is characterized by
  tests, not redesigned.
- `dismissSaveError` is an existing no-op.
- Stage-completion heuristics and fallback links are existing behavior, not SPINE-005 claims.
- The Dashboard's AI Assistant link references route name `AiAssistantProject`, which the
  production router does not define — a pre-existing LAB-023-noted mismatch left untouched.
  It is supplied in the `AppDashboardView` test fixture router only, so the component mounts;
  production routing and that link's behavior are unchanged.

---

## 10. Deferred migrations

Out of scope and not begun: any Project-selection UI; store retirement or Pinia consolidation;
neck, nut, body, bridge, materials, CAM, Analyzer, or RMOS adoption; Hub feature or redesign
work; and any backend, schema, persistence, or authorization change. No successor (SPINE-006 /
LAB-024) is implied by this work.

---

## 11. Reviewer question

> Can a user now enter the existing Instrument Hub through an explicit canonical Project
> identity, preserve the existing Instrument Geometry workflow, and retain the Hub's established
> user-controlled Project commit behavior — without introducing automatic writes, a new
> frontend authority, or a broader migration?

**Yes**, as delivered and tested above.

---

## 12. Risk-closure review (SPINE-005R)

**Method.** A commit-by-commit and line-by-line re-review of all six PR commits and the eleven
changed files against the PR head, plus a repository-wide sweep of every `useInstrumentProject`
consumer, `commit*` caller, and `/instrument-hub` reference. Each cited risk was reproduced
against current code, not accepted from prior prose. Fixes were limited to reproduced,
in-scope defects — no Project authority, backend contract, or implicit-write path was added.

**Commit-by-commit result.** No commit introduced a correctness defect. Commit 1 (route + Hub
compile activation) fixes the Hub's previously broken relative imports; the bare `/instrument-hub`
redirect forwards query/hash verbatim and never infers a Project. Commit 2 rewrites `loadProject`
to latest-request-wins and sets the requested identity immediately while quarantining prior state
— a net-safer transition than the prior "old project fully rendered until the new one resolves".
Commit 3's navigation is Project-addressed only on an explicit URL `project_id`. Commits 4–6 are
governance evidence and the stuck-saving-flag correction, all sound.

**Confirmed fix (§5.1 — the one reproduced defect).** `InstrumentHubShell.vue` synced its local
edit buffers (`localSpec` / `localType` / `localMaterials`) forward-on-truthy only and never reset
them on absent state. Because `isLoaded` is true whenever `design_state` is non-null even if `spec`
is null, switching from a Project with a committed spec to one that has an instrument type but no
committed spec yet left the prior Project's uncommitted draft rendered — and committable via
**Apply** — under the new Project's identity. The buffer sync now resets each section to its empty
baseline when the loaded Project lacks it. Regression witness: `InstrumentHubShell.spec.ts` "does
not carry an edited spec draft into a Project that has no committed spec (§5.1)".

**Refuted by evidence.**

- **§4.1 busy-save ambiguity** — the Hub's **Apply to Project** buttons are already
  `:disabled="isSaving || !isDirty"`, so a second commit can never be issued from the UI while one
  is in flight. Witnessed by a new disabled-during-commit test; the discriminated-result API
  remains a follow-up, not an in-PR refactor.
- **§5.8 non-Hub singleton consumers** — every consumer (`CadSidebar`, `AppDashboardView`,
  `AssistantView`, `BridgeLabPanel`, `useBridgeWorkspace`, `BlueprintSavePanel`,
  `InstrumentMaterialSelector`) either gates on `isLoaded` / null-safe computeds or uses
  `projectId` purely as an identifier string. None assumes `projectId` implies loaded state, so the
  new `projectId=new, state=null` transition window breaks no consumer.
- **§5.3 same-id reload during save** — already covered: the save's captured generation vs
  `_loadGen` discards a superseded response and the `finally` always releases the display flag.

**Higher-order witnesses added (§4.4, §5.4).** `useInstrumentProject.spec.ts` now proves an
A1→A2→B→A3 chain publishes only the latest generation under scrambled resolution order, and that a
save in flight when `clearProject()` runs is discarded (no cleared state repopulated, no stale
metadata) while the single-flight guard is released so a later Project can still load and commit.

**Deferred as follow-ups (out of scope per §9 stop conditions).**

- **§4.2 stale-operation diagnostics** — discarded late load/save failures are silently dropped.
  No canonical non-user-facing client logger exists; introducing one is telemetry infrastructure
  and is deferred rather than built here.
- **§4.3 `AiAssistantProject` unregistered route** — pre-existing; this PR does not touch
  `assistantTo`. Resolving the AI Assistant route architecture is an explicit stop condition. Noted
  additionally: the PR's `AppDashboardView` test fixture registers a mock route of that name, which
  masks the production gap — the follow-up should reconcile the two.
- **§5.2 full-state overwrite / two-commit partial persist** — `_commit` sends the full merged
  design state (last-write-wins) and the Body **Apply** flow issues two sequential commits. Both
  are pre-existing backend-contract properties, not PR-induced; characterized, not redesigned.
- **§5.6 bare-route caller** — `SmartGuitarShell.vue` intentionally keeps `to="/instrument-hub"`
  as the compatibility redirect; retained by design.

**Verdict: READY WITH REQUIRED CORRECTIONS** — the §5.1 leak fix is required and applied; the
remaining items are refuted or deferred with evidence. Full focused + full-suite verification green
(41 focused, 756 total, 0 failed). The PR remains open for owner decision.
