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

Focused colocated tests (37 total, all green):

| Spec | Count | Covers |
| --- | --- | --- |
| `router/index.spec.ts` | 11 | canonical route + name, explicit `projectId` prop, named build, required-param rejection, bare redirect w/ query+hash, `project_id`≠identity, unchanged legacy route |
| `shared-state/useInstrumentProject.spec.ts` | 14 | both A→B response orders, repeated same-id determinism, failed-B isolation, superseded-error suppression, single-flight refusal, stuck-saving regression, cross-Project save success + failure isolation, commit request shape, interface stability, `clearProject` determinism |
| `hub/InstrumentHubShell.spec.ts` | 6 | explicit-id load, prop A→B reload, controlled error w/ no stale content, retry binds to current prop, no auto-commit, explicit Apply delegates to the composable |
| `views/AppDashboardView.spec.ts` | 6 | named route from explicit query, legacy fallback for absent/empty/array query, no singleton fallback, truthful labels |

Suite / gate results at implementation:

- **Full frontend suite:** 752 passed, 17 todo, 1 file skipped, **0 failed** (42 files).
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
