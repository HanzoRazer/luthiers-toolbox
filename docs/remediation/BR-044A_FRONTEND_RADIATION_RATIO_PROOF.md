# BR-044A — Frontend radiation-ratio proof packet

> **INCOMPLETE — WORK IN PROGRESS.** This document currently contains **one** completed
> section: the API data-path finding (TC-12). Every other required section is listed in
> §Remaining and is **not yet written**. Do not treat this packet as the BR-044A proof
> until those sections exist. **BR-044 remains `CONFIRMED_DEFECT`, unresolved, and
> production repair remains unauthorized.**

**Branch:** `br-044a` · **Baseline:** `main` `0179a032` · **Evidence commits:** `668ca20e` (unit
reproduction), `8e01b95c` (component witness)
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
3. **The §11 compatibility risk is discharged, and it was real.** The order anticipated that the
   proof "may assume API records include fields not exposed through the current endpoint or
   adapter." They are not exposed. Recorded here as verified code fact, not inference.

### Evidence classification

- **Verified code fact:** the per-boundary findings, owned by the cited TC-12 record.
- **Architectural inference:** consequences 1–3 above.
- **Not established here:** whether the endpoint response would deserialize the field if added;
  whether any *other* frontend surface consumes the backend value (`useTonewoods.ts` declares
  `radiation_ratio` on its own separate type — that is a different composable and is **not**
  evidence about this panel). Both belong to the consumer inventory.

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
| `useTonewoods.ts:66` | `radiation_ratio?: number \| null` | **NOT THIS PANEL** — separate composable/type; no path into `StiffnessIndexPanel` |
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
regression test to *prove* invariance, not to fix it.

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

## Remaining — NOT YET WRITTEN

Required by the BR-044A2 order and absent from this document:

1. Executive finding · 2. Baseline and branch evidence · 3. Reproduction commits ·
4. Formula comparison · 5. Controlled fixture table · 6. Component witness ·
7. Consumer inventory · 8. Built-in fallback data flow · 9. API-backed data flow ·
10. Backend/frontend authority comparison · 11. Recommended authority model ·
12. Rejected alternatives · 13. BR-044B patch plan · 14. Test inversion and migration plan ·
15. Residual scientific limitations · 16. Explicit non-findings

Also outstanding: consumer inventory (TC-14), remediation-record synchronization, the CBSP21
manifest, targeted validation, and the single BR-044A PR. **No PR may be opened until every
section above exists and all records agree.**
