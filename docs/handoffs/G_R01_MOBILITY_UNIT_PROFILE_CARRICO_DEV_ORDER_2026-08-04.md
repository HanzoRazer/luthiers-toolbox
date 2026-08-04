# G-R01 Mobility Unit Profile — Carrico Evidence Dev Order

**Date:** 2026-08-04  
**Status:** DEV-READY — for system-developer review before implementation  
**Lane:** Acoustics / LUTHERIE_MATH FoM · Stack D mobility blocker  
**Canonical IDs:** **G-R01** (primary) · **G-M09** (Pack 3 alias) · related **G-M13**, **G-M15**, **G-R02**, **G-HM04**  
**Canonical conflict record:** [`docs/calculators/acoustics/CANONICAL_BLOCKER_MOBILITY_UNIT_PROFILE.md`](../calculators/acoustics/CANONICAL_BLOCKER_MOBILITY_UNIT_PROFILE.md)  
**Parent orientation:** [`LUTHERIE_MATH_UNFINISHED_SECTIONS_DEV_HANDOFF_2026-08-04.md`](./LUTHERIE_MATH_UNFINISHED_SECTIONS_DEV_HANDOFF_2026-08-04.md) (Stack D)  
**Posture after PR #243:** Knowledge cohort is closed; this order closes the **productization blocker**, not more lecture harvest.

---

## 1. Purpose

Give system developers a **reviewable, separately PR’d work order** to close **G-R01** using **Carrico / Gore primary evidence** — spreadsheet arithmetic, units, and deflection-scale adjudication — then freeze a Toolbox **unit profile** before any mobility badge ships.

```text
Carrico sheet + jig provenance
  → reproduce spoken score arithmetic (inputs + units documented)
  → freeze unit_profile (carrico_gore_v1 + si_raw)
  → adjudicate Pack 3 ~27 mm vs Pack 5 / Nicoletti ~0.01–0.15 mm
  → mark CANONICAL_BLOCKER Closed (IDs stay stable)
  → only then consider score/threshold UI
```

**Success for this order:** G-R01 closure criteria met with linked evidence.  
**Not success:** A calculator that guesses units, or shipping “exceptional / responsive” badges on tip-spoken numbers.

---

## 2. Audience & review intent

| Role | Use this doc to… |
|------|------------------|
| **System developers** | Approve PR splits, evidence bar, and “done” before coding |
| **Implementers** | Execute one PR at a time; do not collapse the sequence |
| **PR reviewers** | Check acceptance criteria + review questions per PR |

Reviewers should answer:

```text
Can we reproduce Carrico arithmetic with pinned inputs/units?
Is the Toolbox unit profile frozen and SI-mapped?
Is 27 mm adjudicated with primary-source evidence (not inference alone)?
Is the canonical blocker Closed with stable IDs and pack cross-refs updated?
Are mobility badges still forbidden until that close lands?
```

---

## 3. Scope

### In scope

1. Obtain / pin Carrico spreadsheet (and jig doc pointers) with provenance + SHA-256.  
2. Reproduce tip example arithmetic; document constants (\(g\), force, δ units, score scale).  
3. Publish Toolbox **unit profiles** (`si_raw`, `carrico_gore_v1`) as normative docs (+ optional schema).  
4. Adjudicate Pack 3 spoken **~27 mm** / score **~31.3** vs Pack 5 **~0.15 mm** and Nicoletti small-δ class.  
5. Close `CANONICAL_BLOCKER_MOBILITY_UNIT_PROFILE.md`; update pack GAPS status rows (do not fork narrative).  
6. Optional gated follow-on: SI-only mobility compute labeled `unit_profile: si_raw` — **no threshold badges**.

### Out of scope (explicit non-goals)

| Non-goal | Why |
|----------|-----|
| Ship “exceptional / responsive / Y>…” UI badges in any PR below | Closure criteria 1–4 must land first |
| Invent jig geometry (G-M01–G-M02) from “typical practice” | Gap policy: primary sources only |
| Re-host Carrico sheet / Luther Academy app as product runtime | Appendix B — no independent engines |
| Merge Gore score bands into SI without mapping | G-R02 / G-M15 |
| Close full Pack 3 SOP (G-M17 peak rules, etc.) | Separate from unit-profile close |
| Import Holmberg “exceptional Y” as product thresholds | **G-HM04** inherits G-R01; closes with it |
| Calendar estimates | Sequence by dependency only |

---

## 4. Locked decisions

1. **Single conflict record.** All packs cross-reference `CANONICAL_BLOCKER_MOBILITY_UNIT_PROFILE.md`. Do not redefine G-R01 / G-M09 elsewhere.  
2. **Evidence closes the gate — wording does not.** Provisional inference (~0.01–0.15 mm class) is not Closed.  
3. **IDs stay stable.** Closing updates status + evidence links; never renumber G-R01 / G-M09.  
4. **Two profiles, not one muddy number.** Prefer SI for science (`k` in N/m, \(\delta\) in m, \(Y_{\mathrm{SI}}\)); Gore shop score only under `carrico_gore_v1` with explicit mapping.  
5. **Tip-spoken 27 mm is not a lab default** until adjudicated (ASR error **or** alternate definition with evidence).  
6. **Separate PRs.** Do not bundle evidence intake, unit-profile freeze, δ adjudication, and badge UI.  
7. **LUTHERIE_MATH ownership.** Any new formula/§ text lives in `docs/LUTHERIE_MATH.md`; packs remain dialect / measurement inputs.  
8. **License before port.** Spreadsheet logic may be documented and tested against; redistribution/port requires G-M33 clearance before code copies cell formulas wholesale.

---

## 5. Evidence eligibility matrix

What counts toward closing G-R01:

| Evidence class | Eligible to close? | Notes |
|----------------|-------------------|--------|
| Carrico spreadsheet (versioned file + SHA-256 + source URL/path) | **Required** | Arithmetic + units (G-M13) |
| Carrico / Gore jig written SOP or published measurement chapter | **Strong** | Load point, support, load mass (supports δ adjudication) |
| Controlled re-measure on finished top under documented 1 kg protocol | **Strong** | Independent of ASR tip |
| Nicoletti EGB / MB kit numeric δ already in packs | **Supporting** | Small-δ regime; cannot alone freeze Carrico score |
| Pack 5 spoken ~0.15 mm | **Supporting** | Plausible finished-top class; not Carrico arithmetic |
| Tip ASR alone (~27 mm, ~31.3) | **Not sufficient** | Hypothesis generator only |
| “Typical luthier practice” without citation | **Forbidden** | Same as Pack 3 gap policy |
| Holmberg sheet Y bands | **Not sufficient for close** | May consume profile after freeze (G-HM04) |

**Minimum bar to mark Closed:**

1. Pinned Carrico sheet + reproduced example(s) with documented inputs/units.  
2. Published Toolbox unit profile (SI preferred + score mapping).  
3. Written adjudication of 27 mm (ASR **or** alternate definition) with primary-source link.  
4. Canonical blocker status → **Closed** + date + evidence links; pack GAPS rows updated.

---

## 6. Current repo grounding

| Artifact | Role today |
|----------|------------|
| `CANONICAL_BLOCKER_MOBILITY_UNIT_PROFILE.md` | **OPEN** — conflict + closure criteria |
| Pack 3 `gore_monopole_mobility_measurement/` | Tip SOP outline; G-M09 alias; G-M13 arithmetic blocker |
| Pack 5 `gore_shop_talk_responsive_objectives/` | G-R01 primary gap row; G-R02 K units |
| Nicoletti EGB / MB packs | Independent small-δ evidence; cannot freeze Carrico |
| Holmberg G-HM04 | Inherits this blocker — no exceptional-Y badges |
| `LUTHERIE_MATH.md` Appendix B | Points at canonical blocker; no mobility § solver yet |
| Product code | **No** first-class Gore mobility feature / badges |

Spoken tip example (Pack 3, **not** canonical truth): \(\delta=27\,\mathrm{mm}\), \(f=180.7\,\mathrm{Hz}\), score \(31.3\); SI path for same inputs ≈ \(Y\sim 3.13\) class — unit-profile hazard.

---

## 7. Separate PR sequence (review & merge in order)

Do not open PR-E until PR-D is merged (or explicitly waive with system-dev sign-off).  
PR-A → PR-B → PR-C may be prepared in parallel as **drafts**, but merge order is A then B then C then D.

### PR-A — Carrico evidence intake & arithmetic reproduction

**Branch pattern:** `cursor/g-r01-pr-a-carrico-evidence-<suffix>`  
**Type:** Docs / evidence artifacts only (no product UI)

| Deliverable | Detail |
|-------------|--------|
| Evidence package | Spreadsheet binary **or** export tables under agreed path; SHA-256; version/date; source attribution; license note (G-M33 status: allowed to document / blocked to port) |
| Arithmetic worksheet | Markdown (or notebook-as-md) reproducing tip example **and** at least one alternate input row from the sheet |
| Constants table | \(F\) or \(g\), δ unit, \(k\) unit, \(m\) formula, \(Y\)/score formula, rounding |
| Gap touch | Pack 3 G-M13 → “Evidence landed — pending profile freeze” (not Closed yet) |

**Acceptance**

- [ ] Third party can recompute score from documented cells without watching the video.  
- [ ] Tip 31.3 either matches sheet under stated units **or** mismatch is explained (ASR / different cells / different build).  
- [ ] No product thresholds enabled.  
- [ ] Binaries: follow Holmberg workbook policy (inventory + hash if binary not committed).

**Reviewer questions**

```text
Are inputs/units unambiguous enough to freeze carrico_gore_v1 next?
Is license status clear for documentation vs code port?
```

---

### PR-B — Freeze Toolbox unit profiles + LUTHERIE_MATH binding

**Depends on:** PR-A merged  
**Type:** Normative docs (+ optional thin schema / constants module — no badges)

| Deliverable | Detail |
|-------------|--------|
| Unit profile spec | New doc e.g. `docs/calculators/acoustics/MOBILITY_UNIT_PROFILES.md` (or § under LUTHERIE_MATH) defining `si_raw` and `carrico_gore_v1` |
| Mapping | Score ↔ SI \(Y\) (and \(k\) N/m vs N/mm if G-R02 applies) with worked example from PR-A |
| Math hub | Appendix B / new FoM § pointer: profiles owned here; packs are dialect |
| Optional code | Pure functions + tests for SI path only, labeled `unit_profile: si_raw` — **display thresholds off** |

**Acceptance**

- [ ] Preferred SI: \(k\) in N/m, \(\delta\) in m (or mm with explicit conversion), \(Y_{\mathrm{SI}}\) defined.  
- [ ] `carrico_gore_v1` constants frozen with version id + sheet SHA from PR-A.  
- [ ] G-R02 addressed or explicitly deferred with reason tied to profile (not left silent).  
- [ ] Crosswalk Pack 3 §C calibration steps 1–3 marked satisfied for arithmetic/profile; thresholds still blocked.

**Reviewer questions**

```text
Could a UI engineer ship badges from this doc alone? (Must be No until PR-D.)
Is si_raw safe to expose as scientific output without implying Gore bands?
```

---

### PR-C — Adjudicate Pack 3 ~27 mm (δ conflict)

**Depends on:** PR-A (PR-B parallel-OK as draft)  
**Type:** Evidence + narrative close of deflection-scale fork

| Deliverable | Detail |
|-------------|--------|
| Adjudication note | Section in canonical blocker **or** sibling `EVIDENCE_G_R01_DELTA_ADJUDICATION.md` |
| Verdict | One of: (1) ASR / transcription error; (2) alternate definition (load path, scale, unfinished plate, indicator units); (3) sheet uses different δ than spoken tip — with proof |
| Cross-check | Pack 5 ~0.15 mm + Nicoletti ~0.01–0.15 mm class cited as supporting regime, not as Carrico substitute |
| Metadata | Recommended lab schema enums remain; default example δ must not be 27 mm unless verdict (2) proves it |

**Acceptance**

- [ ] Closure criterion 3 language satisfied with primary-source links.  
- [ ] Pack 3 tip numbers marked **source-spoken / non-default** unless alternate definition proven.  
- [ ] No silent “use 0.15 mm everywhere” without protocol match.

**Reviewer questions**

```text
Is the 27 mm story closed by evidence, or still best-guess?
Would shipping Pack 3 tip as lab default still be wrong after this PR?
```

---

### PR-D — Close canonical blocker + pack register sync

**Depends on:** PR-A + PR-B + PR-C merged  
**Type:** Status flip + cross-reference hygiene (small, reviewable)

| Deliverable | Detail |
|-------------|--------|
| Canonical blocker | Status → **Closed**; date; evidence links to PR-A/B/C artifacts |
| Pack GAPS | G-R01, G-M09, G-M13, G-M15 (if closed), G-R02 (if closed), G-HM04, G-A07, Nicoletti notes — status vocabulary only; no forked narrative |
| Orientation / HOW_TO_REVIEW | Standing hold text: badges allowed **only if** blocker Closed **and** explicit product PR enables them |
| Cohort | Regenerate catalog/index if point status fields change; `check_cohort_coverage.py` PASS |

**Acceptance**

- [ ] All four closure criteria in canonical file checked off.  
- [ ] IDs G-R01 / G-M09 unchanged.  
- [ ] No badge UI in this PR.  
- [ ] Unfinished-§§ handoff Stack D row updated: mobility unit profile **Closed** (pointer to evidence).

**Reviewer questions**

```text
Is Closed earned, or are we renaming Open?
Do all packs defer to the single closed record?
```

---

### PR-E — Gated product follow-on (optional; after D)

**Depends on:** PR-D Closed  
**Split further if large**

| Option | Content | Still forbidden until explicit OK |
|--------|---------|-----------------------------------|
| **E1** | Guided lab schema + SI compute API (`si_raw`) | Threshold badges / Gore bands |
| **E2** | Score display under `carrico_gore_v1` | Auto “responsive/exceptional” badges |
| **E3** | Threshold badges (11–12 / 20 or book Y bands) | Requires G-M15 + product sign-off; separate PR from E1 |

**Default recommendation:** Land **E1** only in the first product PR after D. Treat E2/E3 as a later product decision.

---

## 8. Closure criteria ↔ PR map

| # | Criterion (canonical blocker) | PR |
|---|------------------------------|-----|
| 1 | Reproduce Carrico spreadsheet arithmetic with documented inputs/units | **A** (+ freeze in **B**) |
| 2 | Publish Toolbox unit profile (SI + score mapping) | **B** |
| 3 | Reconcile Pack 3 27 mm (ASR or alternate definition) with evidence | **C** |
| 4 | Status Closed + date + evidence links; IDs stable | **D** |

Related gaps closed or narrowed by this sequence:

| ID | Expected outcome after D |
|----|---------------------------|
| G-M13 | Closed with sheet arithmetic |
| G-M09 | Closed as alias when G-R01 Closed |
| G-R02 | Closed in B or explicitly deferred with ticket |
| G-M15 | May remain Open until E3 — **do not** enable badges |
| G-HM04 | Unblocked for *future* threshold work; still no ship in D |

---

## 9. Implementation rules (until D merges)

From Pack 3 gap policy — still binding:

1. Docs/KB teaching the outline is OK.  
2. **No threshold badges** in product UI.  
3. SI scientific output OK only if labeled `unit_profile: si_raw` and not compared to 11/12/20.  
4. Guided lab drafts may require metadata enums including `unknown`.  
5. Never invent G-M01–G-M02 jig geometry to force a close.

---

## 10. System-developer review checklist

Use before approving the first implementation PR:

- [ ] Agree PR-A → D merge order and that badges are not in A–D.  
- [ ] Agree evidence eligibility matrix (Carrico sheet required).  
- [ ] Agree binary/hash policy for spreadsheet artifacts.  
- [ ] Agree `si_raw` vs `carrico_gore_v1` naming and SI preferred units.  
- [ ] Agree 27 mm cannot be lab default without PR-C verdict.  
- [ ] Agree G-M33 license gate before formula port into `services/api`.  
- [ ] Agree Holmberg / badge work waits on Closed blocker.  
- [ ] Confirm owner for evidence acquisition (who obtains Carrico sheet if not in-repo).

**Sign-off block (fill when reviewing):**

```text
Reviewed by: ____________
Date: ____________
Verdict: Approve sequence as written / Approve with amendments (list below)
Amendments:
-
```

---

## 11. Suggested file touch map (by PR)

| PR | Likely paths |
|----|----------------|
| A | `docs/calculators/acoustics/gore_monopole_mobility_measurement/` (evidence + GAPS); optional `docs/reference/` or pack `artifacts/` inventory; canonical blocker “Evidence in progress” note |
| B | `MOBILITY_UNIT_PROFILES.md` (new) or `LUTHERIE_MATH.md` FoM §; Pack 3 CROSSWALK; optional `services/api/app/calculators/*mobility*` SI-only + tests |
| C | Canonical blocker adjudication section; Pack 3/5 GAPS; Nicoletti cross-note if needed |
| D | Canonical blocker **Closed**; GAPS across packs; unfinished handoff Stack D; `HOW_TO_REVIEW_THIS_CORPUS.md` hold text; cohort regen |
| E | Lab schema / router / Vue guided lab — separate product PR |

---

## 12. Pointers

| Resource | Path |
|----------|------|
| Canonical blocker | [`docs/calculators/acoustics/CANONICAL_BLOCKER_MOBILITY_UNIT_PROFILE.md`](../calculators/acoustics/CANONICAL_BLOCKER_MOBILITY_UNIT_PROFILE.md) |
| Pack 3 gaps / crosswalk | [`gore_monopole_mobility_measurement/`](../calculators/acoustics/gore_monopole_mobility_measurement/) |
| Pack 5 gaps | [`gore_shop_talk_responsive_objectives/GAPS_NOT_RECORDED.md`](../calculators/acoustics/gore_shop_talk_responsive_objectives/GAPS_NOT_RECORDED.md) |
| Review guide | [`HOW_TO_REVIEW_THIS_CORPUS.md`](../calculators/acoustics/HOW_TO_REVIEW_THIS_CORPUS.md) |
| Math hub Appendix B | [`docs/LUTHERIE_MATH.md`](../LUTHERIE_MATH.md) |
| Unfinished §§ | [`LUTHERIE_MATH_UNFINISHED_SECTIONS_DEV_HANDOFF_2026-08-04.md`](./LUTHERIE_MATH_UNFINISHED_SECTIONS_DEV_HANDOFF_2026-08-04.md) |
| Coverage | `python3 scripts/knowledge_packs/check_cohort_coverage.py` |

---

## 13. One-page scoreboard

| PR | Intent | Unblocks | Badge UI? |
|----|--------|----------|-----------|
| **A** | Carrico sheet pinned + arithmetic | Profile freeze | No |
| **B** | `si_raw` + `carrico_gore_v1` | SI lab compute | No |
| **C** | 27 mm adjudicated | Honest defaults | No |
| **D** | G-R01 **Closed** | E1+ product work | No |
| **E1** | SI guided lab | Shop measurement UX | No |
| **E2/E3** | Score / badges | Marketing thresholds | Only after explicit OK |

---

## 14. Immediate next action

1. System developers review §10 checklist and sign off (or amend).  
2. Assign owner to obtain Carrico spreadsheet (PR-A blocker if absent).  
3. Open **PR-A** only after sign-off — do not start badge UI or parallel “close G-R01” wording PRs.
