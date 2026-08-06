# BR-044A — Frontend radiation-ratio proof packet

> **INCOMPLETE — WORK IN PROGRESS.** Consumer inventory and repair-authority analysis are complete.
> The baseline, reproduction, fixture, component-witness, remediation-sync, and validation sections
> still require final assembly before this packet becomes the authoritative BR-044A closeout.
> **BR-044 remains `CONFIRMED_DEFECT`, unresolved, and production repair remains unauthorized.**

**Branch:** `br-044a` · **Baseline:** `main` `0179a032` · **Evidence commits:** `668ca20e` (unit
reproduction), `8e01b95c` (component witness), `5a38b304` (TC-12 adapter finding), `6e88b7a6`
(consumer inventory)
**Production files changed:** none.

---

## TC-12 — Does the backend canonical value reach this component?

**Verified code fact. No.**

> **Canonical evidence record:**
> [`BR-044A_TC-12_API_ADAPTER_FINDING.md`](BR-044A_TC-12_API_ADAPTER_FINDING.md) (`5a38b304`).
> That document owns the per-boundary evidence and the data-flow trace. It is not reproduced
> here — this packet cites it.

**Summary for this packet.** The backend's canonical `radiation_ratio` is structurally unavailable
to `StiffnessIndexPanel` on **both** the hardcoded and the API-backed path: `ApiTonewoodRecord`
does not declare the field, `apiRecordToEntry` does not map it, and the local `TonewoodEntry` has
no field to receive it. The panel therefore recomputes locally for API-backed records exactly as it
does for hardcoded ones — it is **not** preferring a local value over an available backend value.
`/api/registry/tonewoods` does publish `radiation_ratio` (BR-043 repaired it there), but this
component's request type does not model it.

### Why this matters to the authority decision

*(This section is this packet's contribution; it is analysis on top of the cited evidence record,
not a restatement of it.)*

1. **Decision 5 is not an adapter tweak.** "Consume the backend value where present; compute
   locally only where absent" currently has **no present case**. Implementing it requires three
   type-level additions before any parity assertion can exist: the field on `ApiTonewoodRecord`,
   the field on the local `TonewoodEntry`, and the mapping in `apiRecordToEntry`. BR-044B must
   scope those explicitly rather than assuming a one-line change.
2. **Decision 4's conclusion holds, but its justification changes.** The recommended
   "shared contract, local pure implementation" is right — not merely because fallback operation
   is desirable, but because a corrected local implementation is the **only** thing that works
   today for *either* path.
3. **The compatibility risk is discharged, and it was real.** The order anticipated that the
   proof "may assume API records include fields not exposed through the current endpoint or
   adapter." They are not exposed. Recorded here as verified code fact, not inference.

### Evidence classification

- **Verified code fact:** the per-boundary findings, owned by the cited TC-12 record.
- **Architectural inference:** consequences 1–3 above.
- **Not established here:** whether any other frontend surface consumes the backend value;
  `useTonewoods.ts` declares `radiation_ratio` on its own separate type, but it is not on this panel's
  data path.

---

## TC-14 — Consumer inventory

Search terms: `calcRadiationRatio`, `radiationRatio`, `radiation_ratio`, `rrColor`,
`soundboardRating`. Scope: `packages/client/src`, excluding `node_modules`. Every live hit is
classified below; none is unexplained.

| Site | Role | Classification |
|---|---|---|
| `useStiffnessIndex.ts:69` `calcRadiationRatio` | `(c/ρ) × 1000` | **PRODUCER** — the single producer |
| `useStiffnessIndex.ts:149` | calls producer inside `computeIndices` | producer call site |
| `useStiffnessIndex.ts:127,132` | `radiationRatio`, `soundboardRating` on `TonewoodIndices` | type surface |
| `useStiffnessIndex.ts:140,144` | null branch when `moeGpa` absent | null path (TC-06) |
| `useStiffnessIndex.ts:155–160` | thresholds `12.0 / 10.5 / 9.0` → Excellent/Good/Acceptable/Below average | **QUALITATIVE CONSUMER** |
| `useStiffnessIndex.ts:166` | `radiationRatio: +rr.toFixed(3)` | **ROUNDING** — see finding 1 |
| `useStiffnessIndex.ts:217` | `sortBy` default `'radiation_ratio'` | **SORTER (default order)** |
| `useStiffnessIndex.ts:236–237` | `(b.radiationRatio ?? 0) - (a.radiationRatio ?? 0)` | **SORTER** — see finding 2 |
| `StiffnessIndexPanel.vue:49` | sort `<option value="radiation_ratio">` | sorter control |
| `StiffnessIndexPanel.vue:105–108` | table cell, `rrColor(...)`, `.toFixed(2)` | **DISPLAY + COLOUR** |
| `StiffnessIndexPanel.vue:146–147` | detail card, `rrColor(...)`, `.toFixed(3)` | **DISPLAY + COLOUR** |
| `StiffnessIndexPanel.vue:168–172` | soundboard-quality badge + CSS class from rating text | **QUALITATIVE DISPLAY** |
| `StiffnessIndexPanel.vue:255–258` | comparison table: two values, `deltaClass`, `formatDelta` | **COMPARISON** |
| `StiffnessIndexPanel.vue:312` `rrColor` | thresholds `12.0 / 10.5 / 9.0` | **COLOUR CONSUMER** |
| `tonewoodData.ts:21` | docstring `radiation_ratio = speed_of_sound / density` | stale prose — see finding 3 |
| `useTonewoods.ts:66` | `radiation_ratio?: number | null` | **NOT THIS PANEL** — separate composable/type; no path into `StiffnessIndexPanel` |
| `__tests__/*.spec.ts` | BR-044A characterisation suites | test (evidence only) |

### Finding 1 — rounding is applied to the scaled value *(VERIFIED CODE FACT)*

`useStiffnessIndex.ts:166` stores `+rr.toFixed(3)` — three decimals of the **×1000** value. On the
corrected canonical scale, 3dp of ~11.87 retains fewer significant figures than 3dp of ~11870.
BR-044B must state the rounding authority explicitly rather than inherit `toFixed(3)` unexamined;
the panel separately re-rounds to 2dp (`:105`, `:255`) and 3dp (`:146`) at display time.

### Finding 2 — sorting is **not** affected by the defect *(ARCHITECTURAL INFERENCE)*

`×1000` is a positive monotonic transform, so the descending comparator at `:236–237` produces the
same ordering before and after the repair. This bounds the blast radius: the defect corrupts
**rating, colour, and displayed magnitude**, but not sort order. BR-044B still needs a sort
regression test to prove invariance, not to fix it.

### Finding 3 — a third stale prose instance *(VERIFIED CODE FACT)*

`tonewoodData.ts:21` documents `radiation_ratio = speed_of_sound / density` — the **canonical**
formula — in the same package whose implementation multiplies by 1000. The prose was right and the
code diverged from it. This is the same prose-vs-arithmetic drift already corrected in
`InstrumentMaterialSelector.vue` (BR-043) and `useStiffnessIndex.ts` `calcSpecificMoe` (BR-045).
BR-044B must align this line with whatever profile it publishes.

### Consumer-count summary

One producer; two threshold consumers (rating, colour) both on `12.0 / 10.5 / 9.0`; three display
sites; one comparison surface; one sorter (default ordering). All within
`design-utilities/wood-intelligence/stiffness/`. **No consumer outside that directory** — the
`useTonewoods.ts` hit is a different composable with its own type and is not evidence about this
panel.

---

## Authority analysis

### Recommended authority model *(IMPLEMENTATION RECOMMENDATION)*

BR-044B should make the frontend's pure local producer conform to the canonical BR-043 contract:

```text
radiation_ratio = speed_of_sound_m_s / density_kg_m3
```

The local producer remains necessary because both built-in and API-adapted records currently arrive
without a transported derived value. Correcting this producer therefore repairs both live paths in
one bounded change while preserving offline/fallback behavior.

The authority boundary should be:

```text
canonical quantity definition and scale  -> backend / shared engineering authority
pure local fallback implementation       -> frontend stiffness subsystem
qualitative thresholds                   -> existing advisory UI policy
rounding and display precision            -> explicit frontend presentation policy
```

This does **not** make the frontend a competing scientific authority. It is a deterministic local
implementation of the same contract, required by the current product's fallback design.

### Backend transport disposition *(IMPLEMENTATION RECOMMENDATION)*

Backend-value transport should be deferred from the minimum BR-044B repair unless owner review
explicitly authorizes the larger contract change. Today there is no field to consume, so adding
transport requires coordinated changes to:

1. `ApiTonewoodRecord`;
2. `TonewoodEntry` or a separate adapted-record type;
3. `apiRecordToEntry`;
4. precedence rules when both transported and locally computable values exist;
5. mismatch handling and parity tests.

Those changes are useful for future authority enforcement, but they are not necessary to stop the
live rating and display collapse. Mixing them into the minimum repair would turn a one-producer
scale correction into an API/type migration.

### Rounding authority *(IMPLEMENTATION RECOMMENDATION)*

BR-044B must not silently inherit `+rr.toFixed(3)` as a scientific rule. The recommended split is:

- keep the internal calculated value unrounded through classification and sorting;
- apply explicit rounding only at the presentation boundary;
- use one documented display precision consistently for table, detail, and comparison surfaces;
- pin the chosen display precision with tests;
- compare parity using an unrounded value or a declared tolerance, never display-rounded strings.

If the existing `TonewoodIndices` contract requires a stored rounded number for compatibility,
BR-044B must document that as a deliberate compatibility constraint and add a precision regression.

### Threshold authority *(ARCHITECTURAL INFERENCE)*

The current `12.0 / 10.5 / 9.0` thresholds are numerically on the canonical unscaled profile and
will regain discriminating power once the producer is corrected. BR-044B should not change them as
part of the scale repair.

That conclusion is limited: this proof establishes scale compatibility, not empirical validity of
the labels `Excellent`, `Good`, `Acceptable`, or `Below average`.

### Sort behavior *(VERIFIED CONSEQUENCE)*

Sorting requires no production repair because multiplying every non-null value by a positive
constant preserves order. BR-044B still needs a regression proving that the corrected producer does
not reorder the current fixture set unexpectedly through rounding or null handling.

---

## Rejected alternatives

### Alternative A — backend-only calculation

Rejected for BR-044B. The component intentionally falls back to built-in records when the API is
unavailable, and the current adapter does not transport `radiation_ratio`. Requiring backend
availability would be a product-behavior change larger than the defect repair.

### Alternative B — change thresholds to the ×1000 scale

Rejected. That would preserve the frontend's isolated profile, perpetuate divergence from BR-043,
and leave the visible and documented quantity inconsistent across surfaces.

### Alternative C — divide values only at display time

Rejected. Rating and colour consume the stored scaled value before display. Presentation-only
conversion would leave the behavioral defect live and create multiple representations of the same
quantity inside one component.

### Alternative D — add backend transport and remove local calculation in the same repair

Rejected as the minimum repair. It expands scope into API typing, adaptation, precedence, and
migration while still failing the offline path unless another local fallback is retained.

### Alternative E — postpone BR-044 until a generalized unit-profile platform exists

Rejected. The defect is live, bounded, and repairable under the already-settled BR-043 scale. The
future authority layer should prevent recurrence, not block a known correction.

---

## BR-044B bounded patch plan

### Required production modifications

#### `packages/client/src/design-utilities/wood-intelligence/stiffness/useStiffnessIndex.ts`

- change `calcRadiationRatio` from `(speedMs / densityKgM3) * 1000` to
  `speedMs / densityKgM3`;
- correct the function and module comments to the canonical unscaled profile;
- preserve null handling and soundboard-role gating;
- make rounding authority explicit;
- retain the existing thresholds unless separately authorized;
- preserve sort semantics.

#### `packages/client/src/design-utilities/wood-intelligence/stiffness/StiffnessIndexPanel.vue`

- replace stale `c/ρ ×10³` labels with the approved canonical label;
- align table, detail, and comparison display precision;
- do not change rating text, threshold values, or colour palette in the scale repair.

#### `packages/client/src/design-utilities/wood-intelligence/stiffness/tonewoodData.ts`

- reconcile the top-level formula prose with the final published label and scale;
- no material data changes.

### Required test modifications

#### `__tests__/useStiffnessIndex.spec.ts`

- invert TC-01 from ~11,870 to ~11.87;
- replace TC-02 with the canonical `c/ρ` identity;
- replace TC-03 with boundary tests at `9.0`, `10.5`, and `12.0`;
- invert TC-04 so controlled fixtures occupy distinct intended bands;
- replace TC-05 ratio `1000` with frontend/backend parity `1` within tolerance;
- retain TC-06 missing-data behavior;
- add unrounded or tolerance-based parity tests;
- add a sort-invariance regression.

#### `__tests__/StiffnessIndexPanel.spec.ts`

- invert TC-07 to the canonical displayed magnitude;
- invert TC-08 so controlled rows do not all render `Excellent`;
- invert TC-09 so colour bands discriminate where fixture values cross thresholds;
- invert TC-10 to the approved canonical label;
- retain the fallback-path witness.

### Deferred optional contract work

The following are **not** part of the minimum BR-044B repair unless separately authorized:

- add `radiation_ratio` to `ApiTonewoodRecord`;
- add transported-value storage to `TonewoodEntry`;
- map the field in `apiRecordToEntry`;
- define transported-versus-computed precedence;
- add runtime mismatch reporting.

Track these as a follow-on authority/parity improvement rather than silently including them.

---

## Test inversion and migration strategy

1. Preserve the current BR-044A commits as historical evidence.
2. In BR-044B, rewrite characterization assertions into normative corrected-behavior assertions.
3. Keep one explicit regression test proving the historical ×1000 path is absent.
4. Verify hardcoded and API-adapted primitive-input records produce the same canonical result.
5. Test exact threshold inclusivity:
   - `12.0` -> `Excellent`;
   - `10.5` -> `Good`;
   - `9.0` -> `Acceptable`;
   - immediately below `9.0` -> `Below average`.
6. Verify non-soundboard entries still receive `null` rating.
7. Verify missing-MOE behavior remains unchanged.
8. Verify sorting order is invariant for the existing fixture set.
9. Verify all three display surfaces use the same approved label and precision.
10. Run adjacent frontend and TypeScript regressions before queue closeout.

No persisted user-data migration is identified in this subsystem. The visible numeric magnitude and
rating/colour results will change immediately after deployment; that is the intended defect repair.

---

## Residual scientific limitations

- The proof validates the numerical scale contract, not the empirical quality of the thresholds.
- Species-level reference values do not establish specimen-level acoustic quality.
- The words `Excellent`, `Good`, `Acceptable`, and `Below average` remain advisory UI interpretation.
- No uncertainty, moisture, grain orientation, damping, or measurement provenance is incorporated.
- Backend transport and parity enforcement remain absent from this panel.
- A generalized derived-index unit/profile authority remains future work.

---

## Remaining — NOT YET WRITTEN OR FINALIZED

Required before BR-044A closeout:

1. Executive finding.
2. Scope and non-goals.
3. Baseline and branch evidence.
4. Reproduction commit summary.
5. Formula comparison.
6. Controlled fixture table.
7. Component witness summary.
8. Built-in fallback data-flow section.
9. API-backed data-flow section.
10. Explicit non-findings.
11. TC-11 fallback verification.
12. TC-13 API-adapted recomputation verification.
13. TC-15 exact threshold-boundary characterization.
14. TC-16 non-soundboard characterization.
15. Remediation-record synchronization.
16. CBSP21 manifest and final validation.

The consumer inventory, authority analysis, rejected alternatives, BR-044B patch plan, and test
inversion strategy are complete. **No PR may be opened until the remaining sections exist, the WIP
header is removed, and all remediation records agree.**
