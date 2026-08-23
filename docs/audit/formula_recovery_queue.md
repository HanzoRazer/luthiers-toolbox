# Formula / Calculator Recovery Queue

**Status:** FROZEN (2026-08-22) — derived from the frozen census; reconciliation passed. Advisory
prioritization. **Not authorized work; not a schedule; not a set of Dev Orders.** This document ranks
the findings from the [Formula / Calculator Authority Census](./formula_authority_census.md) into
**one comparable queue** so that consequence-and-evidence, not recency-of-discovery, decides order.
Execution of any item requires separate owner authorization.

**Relationship to the census.** The census is frozen (FROZEN 2026-08-22 — no remediation). It is the
*map*; this file is a *reading order over the map*. Row/§ references point back to the census; this
file introduces **no new findings** and **declares no authority** — it only orders what the census
already established. No code, `SPRINTS.md`, or Dev Order was created.

> **Post-freeze update rule.** New findings or priority changes must use the **existing
> six-criterion rubric** and reference the **frozen census or a dated census amendment**. Re-ordering
> the queue **does not rewrite census history** and **does not interrupt already-authorized work**
> unless separately authorized by the owner.

---

## Scoring rubric

Six criteria (from the owner brief), each scored **H / M / L**. Ordering is **qualitative and
transparent**, not a false-precision number — two items in the same tier are peers, and owner
weighting (e.g. valuing data-integrity over playability) can move items within a tier.

| Code | Criterion | H means |
|------|-----------|---------|
| **CC** | Consumer consequence | An authoritative consumer acts on it (gates output, sets scale, cuts material, drives a build decision) |
| **LR** | Live reachability | On a production/user-reachable path (front-end, router, CAM export) |
| **CS** | Correctness / safety impact | Currently produces a wrong, misleading, or unsafe result |
| **AA** | Authority ambiguity | Genuinely unclear which of several live implementations is authoritative |
| **EQ** | Evidence quality (readiness) | Census evidence is strong enough to act now (L = needs a trace first) |
| **RD** | Remediation dependency | Fixing it unblocks others, or its fix source already exists (keystone) |

**Tiering.** `P1` high-consequence + live + wrong-now + actionable · `P2` live defect or
consequential fragmentation, actionable · `P3` fragmentation / provenance / data-integrity, medium
or needs some verification · `P4` cleanup / lifecycle decisions / low urgency · `P0-investigate`
must be traced before it can be ranked at all.

---

## The queue

### P0 — investigate before ranking (evidence gate)
| Item | Census ref | CC | LR | CS | AA | EQ | RD | Rationale |
|------|-----------|----|----|----|----|----|----|-----------|
| Bridge acoustic calcs — deep trace | `bridge_calc.py` / `acoustic_bridge_calc.py` (INSUFFICIENT_EVIDENCE) | ? | ? | ? | ? | **L** | — | Census cannot responsibly adjudicate. A scoped consumer/liveness trace is the **precursor**; only then does it enter P1-P4. Cheap; unblocks a blind spot. |

### P1 — high consequence, live, wrong now, actionable
| # | Item | Census ref | CC | LR | CS | AA | EQ | RD | Rationale |
|---|------|-----------|----|----|----|----|----|----|-----------|
| 1 | **Nut-slot depth / "zero-fret" defect** | §2 / §17, rows 2, 3 (DATUM_CONFLICT + `+crown/2` + fragmentation) | H | H | **H** | **H** | H | H | Live calculator makes the GREEN action band **unreachable** — a luthier always reads non-GREEN. Four loci for one quantity (buggy live computer, dead-*better* twin, hard-coded `0.5`, input-only consumer). **Fix source already exists** (the dead "sounder" model, item 15) → keystone. |
| 2 | **Saw rim-speed units defect (safety-relevant)** | row 1 (`UNITS_DEFECT`, FUNDAMENTAL_PHYSICS, safety-relevant) | H | H | **H** | L | H | L | Units defect on a **live** saw rim-speed calc, flagged **safety-relevant** in the census — a wrong surface-speed↔RPM figure is a physical-safety exposure, not just a wrong number. Single implementation (AA=L), well-evidenced, self-contained. Remedy = **unit correction**, distinct from the validation work in items 1/3. |
| 3 | **Vectorizer authority without basis** | rows 21 (body scorers), 22 (export gate 0.60/0.30), 36 (coin scale weights) | H | H | M | M | H | M | Uncited weights/thresholds **rank body candidates, gate real production export, and set mm/px scale** on the live hostinger→Railway path. Not demonstrably "wrong" but authoritative-without-evidence on output that becomes CAM. `ValidationBasis=UNKNOWN_ORIGIN`. Remedy = **validation/authority evidence before any constant-tuning** (not a correction). Lifecycle note preserved: these are **live in-repo canonical** (§6 correction) — *not* migrated residue. |

### P2 — live defect or consequential fragmentation, actionable
| # | Item | Census ref | CC | LR | CS | AA | EQ | RD | Rationale |
|---|------|-----------|----|----|----|----|----|----|-----------|
| 4 | **`L_eff` units defect** | row 20 (MAINT-DEFER-004) | M | H | **H** | L | H | M | Dimensionally wrong length term on a live acoustic calc; bounded; stale second impl to retire alongside. Already tagged. |
| 5 | **rayleigh_ritz "fallback to scipy" unbacked** | row 19 (MAINT-DEFER-010) | M | H | M | M | H | L | Diagonal approximation behind a false fallback comment → silently wrong modal result + misleading claim. Already tagged. |
| 6 | **`api_v1/fret_math` nut_width latent units bug + two fret surfaces** | rows 29, 30 | M | H | M | H | H | M | `distance_from_nut − nut_width_mm` corrupts every fret if a real value is passed (default-safe today). Cheap to neutralize; also resolves which of two live fret endpoints is canonical. |
| 7 | **Blueprint contour classifier — uncited bands/confidences** | rows 35, 34 (dup rule ×3 loci) | M | H | M | M | H | M | Standard metrics → authoritative classification via magic bands + author-assigned confidences; the soundhole rule is duplicated byte-identical across 3 loci / 2 services. |
| 8 | **Compound-radius divergence** | row 11 | M | H | M | **H** | M | M | Two live interpolation conventions give **different radius at a given fret** (playability). Needs a small numeric verification before the fix decision (EQ=M). |

### P3 — fragmentation / provenance / data-integrity, medium
| # | Item | Census ref | CC | LR | CS | AA | EQ | RD | Rationale |
|---|------|-----------|----|----|----|----|----|----|-----------|
| 9 | **Soundhole Helmholtz stack fragmentation** | row 17 | M | H | L | H | M | M | `soundhole_calc` (canonical, router) vs `soundhole_physics` (parallel copy). Consolidate to one authority; values not shown wrong, so severity is ambiguity not defect. |
| 10 | **Material-property authority fragmentation (MOE / Sitka E_L)** | rows 15, 25 (*dispersion aspect*) | M | H | L | H | M | M | ≥4 MOE authorities + Sitka `E_L` 11.0 vs 9.5 composed into one EI. Individually plausible; the debt is dispersion, not a known wrong number. |
| 11 | **Wood dataset provenance** | row 25 (*attribution aspect*: ~450 unsourced), row 26 (severed generator) | M | H | L | M | M | L | Data-integrity: values live, generator deleted, ~450 unattributed. Large effort, low correctness-risk. **Owner weighting could raise this** if provenance is valued over playability. |
| 12 | **Acoustic calibration constants uncited** | rows 18 (`0.798` unknown), §2 row 10 (saddle-comp coeffs) | M | H | L | M | M | L | Uncited calibration on live acoustic/intonation constants; `ValidationBasis` gap, not a demonstrated error. |
| 13 | **Untested high-risk live impls** | rows 9 (neck/taper/bridge-height/string-spacing), 13-partial (Bézier ≥8 etc.), `validate_scale_before_export` | M | H | L | L | M | M | Consequential + live but no dedicated verification. Remedy = **add tests** (not code correction — these are `VALID_REUSE`/legitimate gates); urgency rises only if the code is touched. |

### P4 — cleanup / lifecycle decisions / low urgency
| # | Item | Census ref | CC | LR | CS | AA | EQ | RD | Rationale |
|---|------|-----------|----|----|----|----|----|----|-----------|
| 14 | Chipload / tool-deflection fragmentation | rows 4 (chipload), 5a/5b (tool deflection), §1/§4 | M | M | L | M | M | L | Rival CNC heuristics. **Scope note:** the chipload *relation* is `VALID_REUSE` — only invalid-input behavior (4) and the rival deflection *model* (5b, suspect `E` in 5a) diverge. Verify-or-consolidate; no known wrong output. |
| 15 | **Dead-but-relevant nut/saddle physics** | row 32 (`nut_compensation_physics`, `saddle_compensation_calc`) | — | — | — | — | H | **H** | Orphaned but the nut model is the **fix input for item 1** — preserve and harvest, do not delete. Sequenced *with* P1, **not** resurrected as an independent project (stays P4 on its own merits; RD-high only as item 1's evidence source). |
| 16 | Stale/superseded/migrated + no-action lifecycle | rows 16 (fan brace), 23 (Loop-3), 7/8 (deprecated shims `nut_comp_calc` / `headstock_break_angle`); **no-action:** row 38 (external DSP → `tap_tone_pi`), Tier A vectorizer relocation → `vectorizer-sandbox` | L | mixed | L | L | H | L | Lifecycle-explained. `16`/`23`/shims are *decisions* (delete? unwire?), not fixes. Row 38 and the Tier A relocation are **no-action** — external / cleanly relocated + precommit-guarded; listed here only to record that the §6 correction is preserved and nothing is owed. |

---

## Dependency edges (sequence, not severity)

- **Item 1 ⇐ Item 15.** The nut-slot fix consumes the dead-but-better "sounder" model. Harvest item 15
  first (or jointly); do not delete it. Item 15 stays P4 on its own merits — the dependency sequences
  it, it does **not** promote it to a standalone recovery project.
- **Item 6 resolves two rows at once** (fret-surface duplication 29 + the latent units bug 30) — a
  cheap P2 that removes a footgun and a fragmentation in one move.
- **Item 4 pairs with retiring the stale `L_eff` second impl** (same row 20).
- **Row 25 is split by aspect, not double-counted:** item 10 = authority *dispersion* (MOE), item 11 =
  *attribution* (~450 unsourced) — one census finding, two distinct remediation tracks.
- **P0 gates nothing else** but should run early — it is the only unresolved classification.

## How to read this queue

The point is a **finite, comparable order**, not a mandate. The historically loud items land where
consequence puts them: the **zero-fret / nut-slot defect**, the **safety-relevant saw rim-speed
units defect**, and the **vectorizer authority (P1)** rise because they are live, consequential, and
evidenced — but for *different* reasons demanding *different* remedies (correction/reconciliation for
1–2; validation-before-tuning for 3). **Wood provenance (P3)** and **soundhole fragmentation (P3)**
are real but lower-correctness-risk and can wait or be reweighted by the owner; the **orphaned
implementations (P4)** are mostly lifecycle decisions — except the one that is a fix *input*. Nothing
here is scheduled or authorized; it is the recovery **order** the census evidence supports, offered
for owner review before any code changes.

---

## Reconciliation audit (queue ⇄ census, 2026-08-22)

Audited the queue **against the census** (not the repository), per the owner's five checks. Result:
**PASS after 6 corrections** (applied above; the census was not touched).

| Check | Result |
|-------|--------|
| Every actionable census finding appears once, or has an explicit cross-ref/dependency disposition | **PASS (after fixes).** All actionable rows (1-5, 9-11, 15-23, 25, 26, 29, 30, 32, 34-36) and §-level findings (nut-slot §2, chipload/deflection §1/§4) now map to exactly one queue item, or an annotated aspect-split. Non-actionable lifecycle rows (38, Tier A relocation) carry an explicit **no-action** disposition (item 16). |
| No `VALID_REUSE` / `VALID_ALTERNATE_MODEL` finding became remediation | **PASS.** Rows 6, 13(full), 14, 22b, 24, 27, 28, 33, 39-43 and the `—` alternate-model rows are **absent** from the queue. The only VALID-adjacent entry (item 13) pulls the *test-coverage* aspect of rows 9/13 and `validate_scale_before_export` — explicitly "add tests," not correct-the-math. |
| Lifecycle corrections preserved (vectorizer relocation/conflation) | **PASS.** Item 3 labels the vectorizer stack **live in-repo canonical (§6 correction)**, not residue; item 16 records the Tier A relocation as cleanly-relocated / no-action. The 2026-08-21 over-broadening is not reintroduced. |
| Scores follow the six stated criteria | **PASS.** Spot-checked: item 1 (all-H → P1), item 2 (safety CS=H, AA=L single impl → P1 on safety+correctness), item 3 (CS=M honest — unvalidated ≠ wrong), items 9-12 (CS=L → P3, not P1). No score contradicts its tier. |
| Dependencies haven't distorted priority | **PASS.** Item 15 (dead-but-better nut model) stays **P4** and is sequenced as item 1's evidence input via a dependency edge — **not** elevated to a standalone P1 resurrection. Item 6's two-row efficiency is a sequencing note, not a severity boost. |

**Corrections applied to the queue during this audit** (census unchanged):
1. **Added row 1 (saw rim-speed units, safety-relevant) as P1 item 2** — it was missing entirely; a safety-relevant live defect cannot be omitted.
2. **Added row 21 (body scorers)** to the vectorizer item (now item 3) — previously only 22/36 were cited.
3. **Added row 9** (neck/taper/bridge-height/string-spacing UNTESTED_HIGH_RISK) to item 13 — previously only 13-partial.
4. **Dispositioned row 38 + Tier A relocation as no-action** (item 16) — previously silently omitted.
5. **Annotated the row-25 aspect split** (item 10 dispersion / item 11 attribution) as one finding / two tracks, not a double-count.
6. **Added scope notes** clarifying test-coverage-not-correction (item 13) and VALID_REUSE-relation-vs-divergent-input (item 14), so no valid math reads as remediation.

**Freeze recommendation:** with reconciliation passing, both artifacts are ready to **freeze** — the
census as the stable evidence base, this queue as the stable ordering mechanism. New findings can be
inserted into the queue by the same rubric **without** rewriting census history or auto-interrupting
authorized work. The next checkpoint (choosing the first authorized recovery increment) remains
owner-gated and is **out of scope here**.
