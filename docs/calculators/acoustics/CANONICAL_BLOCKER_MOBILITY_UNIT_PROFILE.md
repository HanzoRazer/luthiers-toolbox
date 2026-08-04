# Canonical blocker — mobility unit / deflection profile

**Status:** **OPEN — productization blocked**  
**Canonical IDs:** **G-R01** (primary) · **G-M09** (alias / Pack 3 tip)  
**Authority:** This file is the **single repo-wide record** for the conflict. Other packs must **cross-reference** here, not redefine the resolution.

---

## Conflict (source-level)

| Source | Spoken / recorded δ under ~1 kg | Notes |
|--------|----------------------------------|-------|
| Pack 3 tip (O’Brien / Carrico jig ASR) | **~27 mm** + score **~31.3** | Physically extreme for a finished top; treat as **source-spoken / ASR-risk**, not a canonical benchmark |
| Pack 5 Responsive Objectives | **~0.15 mm** | Much more plausible for finished steel-string tops |
| Nicoletti EGB 2022 (N109) | **~0.01–0.02 mm** typical; Taylor samples ~0.13–0.15 mm | Independent small-δ regime |

**Current best inference (provisional):** physical δ for finished tops is in the **~0.01–0.15 mm class**, not 27 mm.  
**Not closed:** Carrico / Gore spreadsheet arithmetic + Toolbox **unit profile** (N/mm vs N/m, score vs SI \(Y\)).

---

## What stays blocked until closed

- Mobility / “exceptional” / “responsive” **UI badges** and threshold bands  
- Shipping Pack 3 tip numbers as lab defaults  
- Treating Pack 5 δ demo as universal acceptance criteria without unit-profile lock  
- Holmberg “exceptional Y” citations as product thresholds (**G-HM04** inherits this blocker)

---

## Pack cross-references (do not fork the story)

| Pack / doc | Local ID | Role |
|------------|----------|------|
| [`gore_shop_talk_responsive_objectives/GAPS_NOT_RECORDED.md`](./gore_shop_talk_responsive_objectives/GAPS_NOT_RECORDED.md) | G-R01 | Original Pack 5 gap row — defers here |
| [`gore_monopole_mobility_measurement/GAPS_NOT_RECORDED.md`](./gore_monopole_mobility_measurement/GAPS_NOT_RECORDED.md) | G-M09 | Pack 3 tip gap — alias of G-R01 |
| Orientation blocker table | G-R01 / G-M09 | Points here |
| `LUTHERIE_MATH.md` Appendix B.3 | G-R01 / G-M09 | Points here |

---

## Closure criteria

1. Reproduce Carrico spreadsheet arithmetic with documented inputs and units.  
2. Publish a Toolbox **unit profile** (preferred SI: \(k\) in N/m, \(\delta\) in m; score/display mapping explicit).  
3. Reconcile Pack 3 spoken 27 mm as ASR error **or** alternate definition (e.g. different load path / scale) with primary-source evidence.  
4. Update this file’s status to **Closed** with date + evidence links; leave G-R01/G-M09 IDs stable.
