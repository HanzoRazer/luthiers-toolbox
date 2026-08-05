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
