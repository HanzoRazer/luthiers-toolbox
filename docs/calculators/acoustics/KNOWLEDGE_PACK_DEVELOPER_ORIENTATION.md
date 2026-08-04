# Knowledge packs — developer orientation

**Purpose of this exercise:** Harvest transcript remnants into a knowledge layer **before** calculator or lab UI work.  
**PR:** [#243](https://github.com/HanzoRazer/luthiers-toolbox/pull/243) · branch `cursor/gore-shop-talk-20-lecture-notes-83c1`  
**Policy:** Documentation only. Cross-link schools; **do not merge** dialects into one calculator. Prefer empirical knowledge / guided labs over inventing thresholds.

---

## 0. Two lanes (sort first)

Delineate **instrument-building physics** from **shop / building knowledge**. Same spine sentence (“light stiff top, finite energy”) may appear in both; tag by **deliverable**, not by vocabulary overlap.

| Lane | Index | Deliverable for Toolbox |
|------|-------|-------------------------|
| **Physics** | [`PHYSICS_KNOWLEDGE_INDEX.md`](./PHYSICS_KNOWLEDGE_INDEX.md) | Meters, models, lab SOPs, unit profiles |
| **Shop / building** | [`SHOP_BUILDING_KNOWLEDGE_INDEX.md`](./SHOP_BUILDING_KNOWLEDGE_INDEX.md) | Dialect cards, stage-gate UX, intake questionnaires, anti-patterns |

**Gore-centric theme summary** (physics subset): [`GORE_LECTURE_SERIES_SUMMARY.md`](./GORE_LECTURE_SERIES_SUMMARY.md) — do not use it as the only catalog for non-Gore or shop packs.

**Filing rule:** New transcript → choose lane → pack folder → update **that** lane index (and Gore summary only if Gore/O’Brien physics). Dual-file only when README says so.

**Nothing drops to the sandbox floor:** [`COHORT_GOVERNANCE.md`](./COHORT_GOVERNANCE.md) — intake checklist, annotation bar, search contract, coverage gate.

| Artifact | Role |
|----------|------|
| [`cohort_catalog.json`](./cohort_catalog.json) | Machine catalog of every pack + point ID |
| [`POINT_SEARCH_INDEX.md`](./POINT_SEARCH_INDEX.md) | Human/grep search by prefix, pack, keyword |
| `python3 scripts/knowledge_packs/build_cohort_catalog.py` | Rebuild catalog + search index |
| `python3 scripts/knowledge_packs/check_cohort_coverage.py` | **Must PASS** before commit/PR (unfiled / incomplete / zero points / CBSP21 gaps fail) |

---

## 1. Pack template (what each folder is)

Every pack is a folder under `docs/calculators/acoustics/<pack_id>/` with the same five files (workflow packs may rename the notes file):

| File | Role |
|------|------|
| `README.md` | Source identity, status (partial/complete), school, links to related packs, classification tags |
| `SOURCE_TRANSCRIPT.md` | Cleaned working extract (ASR fixes noted; not a legal transcript archive) |
| `ANNOTATED_LECTURE_NOTES.md` *(or `ANNOTATED_WORKFLOW_NOTES.md`)* | Classified teaching points with stable IDs (`P##`, `W##`, `M##`, `ES##`, `N##`, …), timestamps, Toolbox destination, gaps |
| `CROSSWALK_TOOLBOX.md` | Map points → Toolbox / Tap Tone Pi / other packs; **NO-CALC** rules |
| `GAPS_NOT_RECORDED.md` | Explicit absences + severity + closure log (do not invent) |

### Classification tags (shared)

| Tag | Meaning |
|-----|---------|
| **EP** | Established principle |
| **EO** | Empirical / on-camera observation |
| **TG** | Trevor Gore |
| **RO** | Robbie O’Brien shop practice |
| **IS** | Irvin/Ervin Somogyi |
| **AP** | Apprentice / builder deviation |
| **GN** | Giuliano Nicoletti |
| **MB** | Maderas Barber kit / presentation |
| **MW** | Michael Watts framing |
| **DH** | Dominic Howman method |
| **JK** | Jacob / Kanaka method |
| **GL** | Garrett Lee method |
| **SH** | Shop / builder practice (non-school-specific shop lane) |
| **BK** | Michael Bashkin shop practice |
| **ESF** | Eric Schaefer shop practice |
| **GH** | Gregory Holmberg spreadsheet implementation |
| **OH** | Open hypothesis / taste |

### Processing pipeline used

```text
transcript paste
  → choose lane (physics vs shop)
  → SOURCE_TRANSCRIPT (clean ASR)
  → ANNOTATED_* (point IDs + class + destination)
  → CROSSWALK (Toolbox mapping + NO-CALC)
  → GAPS (blockers; G-* IDs for missing numbers)
  → lane index (PHYSICS_* or SHOP_*)
  → GORE_LECTURE_SERIES_SUMMARY only if Gore physics subset
  → rebuild cohort_catalog.json + POINT_SEARCH_INDEX.md
  → python3 scripts/knowledge_packs/check_cohort_coverage.py  # must PASS
  → .cbsp21/patches/gore-lecture-series-packs-1-5.json (manifest)
  → commit / push / update PR
```

**Point ID namespaces (do not renumber casually):**

| Prefix | School / pack family | Default lane |
|--------|----------------------|--------------|
| P | Gore Shop Talk #20 | Physics |
| H | Gore Shop Talk #20 heuristics (H01–H10) | Physics |
| W | Gore wolf mailbag | Physics |
| M | Gore monopole mobility tip | Physics |
| S | Gore Shop Talk #25 | Physics |
| R | Gore responsive objectives | Physics |
| U | Gore Shop Talk #44 | Physics |
| A | Gore Shop Talk #51 / Academy apps | Physics |
| T | Gore Guitar Analysis & Testing (Pack 6 partial); also theory cross-refs | Physics |
| Y | Somogyi apprentice workflow | Shop |
| ES | Somogyi primary (01–02) | Physics (doctrine) |
| N | Nicoletti family (continues across his packs) | Mixed — see pack README |
| PM | Howman *Physics Mind* steel-string seminar | Physics |
| IB | Jacob/Kanaka I-beam bracing physics | Physics (shop dual) |
| GL | Garrett Lee soundboard deflection Ep. 13 | Physics (shop dual) |
| SB | Shop soundboard species & voicing | Shop |
| TB | Shop top bracing history / H-brace journal | Shop |
| BK | Bashkin JM full acoustic build workflow | Shop |
| SC | Schaefer straight → fully compensated saddle | Shop |
| HM | Holmberg Gore/Gilet modeling spreadsheets | Physics |
| MB | MB Sound / Nicoletti TPC panel laboratory records | Physics |
| G-* | Gap IDs (`G-R01`, `G-M09`, `G-ES##`, `G-N##`, `G-PM##`, `G-SB##`, `G-TB##`, `G-GL01`, `G-SC##`, `G-HM##`, `G-MB##`, …) | — |

**Search tip:** prefixes may collide across packs (e.g. `T##`); always disambiguate with `pack_id` in [`cohort_catalog.json`](./cohort_catalog.json) / [`POINT_SEARCH_INDEX.md`](./POINT_SEARCH_INDEX.md).

---

## 2. Catalog — all packs

Canonical catalogs live in the **lane indexes** (§0). Short map:

| Lane | Where to look |
|------|----------------|
| Physics | [`PHYSICS_KNOWLEDGE_INDEX.md`](./PHYSICS_KNOWLEDGE_INDEX.md) — Gore, Nicoletti metrology, Howman, I-beam (IB), Garrett Lee deflection (GL), Holmberg Gore sheets (HM), MB Sound TPC panel labs (MB), Somogyi doctrine |
| Shop | [`SHOP_BUILDING_KNOWLEDGE_INDEX.md`](./SHOP_BUILDING_KNOWLEDGE_INDEX.md) — soundboard (SB), top bracing (TB), Bashkin JM workflow (BK), Schaefer compensated saddle (SC), Somogyi apprentice, MB kit how-to/interview |
| Gore themes only | [`GORE_LECTURE_SERIES_SUMMARY.md`](./GORE_LECTURE_SERIES_SUMMARY.md) |

---

## 3. Harvested workflow remnants (what developers should stare at)

These are **dialect cards**, not a single merged pipeline. Where schools agree, note the agreement; where they diverge, keep both.

### 3.1 Shared “measure then place” spine

```text
Select wood (optional metrology)
  → Build stages with FRF checkpoints
  → Place resonances off (between) scale tones
  → Set monopole mobility / responsiveness intentionally
  → Troubleshoot wolves / hot modes (mass, hole, braces, pins)
  → Optional: Chladni to map peak ↔ shape
  → Optional: customer/spec sheet of modes + Y
```

| Stage | Gore remnant | Nicoletti remnant | Somogyi remnant | Howman remnant |
|-------|--------------|-------------------|-----------------|----------------|
| Wood pick | SRC by intent; Q often secondary | \(\rho\), \(E\), SRC (Schelleng), orthotropy, Q/damping; REW plate FFT; Gore *vibrational stiffness* sheet | Stiffness/weight + Q by genre; tap “ringing potential” | QS/split billets; fist-tap S/W + crack screen; spruce vs WRC by tension |
| Free / early top | Free-top pitch tuning discouraged as finished proxy | Half-plate FFT @ ~4 mm; RH ~45% | Deflection **stiffness** target (not mm); braces oversized → carve while listening | Free-edge tap toward target; cube-rule caution; Chladni optional/declined |
| Boxed stages | Closed-box FRF; spectrogram stages | Top-on-sides in **fixed mold**; pretune monopole; then close box / bridge | Shell tap; top↔air↔back “ping-pong” | Basswood linings isolate; voice back for long dipole / posture intent |
| Finished QC | Mid-scale triad; ½-semitone clearance; mobility thresholds (unit-blocked) | FRF + mobility every guitar; Chladni for R&D; ETS / putty / pins | Qualitative live vs thud; tandem frequency relationship | Body-damped vs free back; strobe intonation; bridge near body center |
| Tools | Visual Analyzer (Pack 6 partial); Carrico; Luther Academy apps | miniDSP + **Room EQ Wizard**; 25 cm; ~32 averages; 1 kg dial | Ear + deflection feel | Ear/tap; go-bar dome dishes; strobe tuner |

### 3.2 Concrete lab SOPs already sketched (candidate Toolbox labs)

1. **Impact FRF** — mic distance, averages, saddle taps, string damping (Nicoletti EGB N104; MB kit Phase 1; Gore Pack 2 taps).  
2. **Monopole mobility** — 1 kg deflection + plugged-hole \(f\) → \(k,m,Y\) (Gore Pack 3/5/8; Nicoletti N109; MB kit Phase 3).  
3. **Chladni** — BT amp + small speaker + powder at FRF peaks (MB kit Phase 2; Nicoletti N110).  
4. **Wolf clearance** — map peaks to pitch classes; resonances *between* notes (Gore Pack 2; Nicoletti N106).  
5. **Plate tonewood intake** — density + long/cross/twist modes → spreadsheet targets (Nicoletti tonewood webinar N78–N81).  
6. **Build-stage gates** — free top ≠ finished; top-on-rim / mold checkpoints (Gore Pack 1/5; Nicoletti N89/N123; Somogyi ES13/ES22).

### 3.3 Priority / philosophy remnants (UX copy, not solvers)

- Gore stack: modes off scale tones → right mobility → intonation (don’t max-\(Y\) alone).  
- Nicoletti: QC + standards + customer vocabulary; measure finished guitars before changing your method.  
- Somogyi: efficient **air pump**; don’t ignore the back; top–back resonance relationship.  
- Howman: physics as post-hoc language; X-brace mode control; Hoover basswood isolation; bridge-center monopole.

---

## 4. Blockers before code (fresh-eyes checklist)

| ID | Issue | Why it blocks UI |
|----|-------|------------------|
| **G-R01 / G-M09** | Pack 3 spoken **27 mm** vs Pack 5 ~**0.15 mm** vs Nicoletti typical **~0.01–0.02 mm** | Wrong \(k\) by ~1000× if 27 mm treated as real. Prefer **0.01–0.15 mm class**; still need Carrico sheet for full close. |
| Pack 6 | Guitar Analysis course SOPs incomplete | Win mic / Visual Analyzer click-paths missing |
| G-N10 / G-N21 | Nicoletti spreadsheet / Schelleng formula cells | Can’t port EMP plate calculator faithfully |
| G-ES09–11 | Somogyi top–back ratio, δ targets, brace-stop | No Somogyi numeric lab |
| G-N08 | Mode-label map Nicoletti ↔ Gore T11x | Labeling bugs in FRF UI |
| Unit profiles | Carrico score vs SI \(Y\) | Threshold badges unsafe |
| **G-GL01** | Garrett Lee on-screen δ targets not in ASR | Can’t ship his deflection band as lab defaults |
| **G-HM03 / G-HM04** | Holmberg presets unverified as builds; Y&gt;14 citations share mobility unit block | No cut lists / no exceptional-Y badges from sheets alone |

**Standing NO-CALC rules (from packs):** no invented Win7 paths; no falcate geometry from talk alone; no hardcoded 236/275 Hz or 190 Hz mold coincidence as globals; no mobility “responsive” badges until unit profile locked; Holmberg sheets = starting points + measure-your-wood (HM02).

---

## 5. Suggested reading order for developers

1. This file (§0 lanes)  
2. [`PHYSICS_KNOWLEDGE_INDEX.md`](./PHYSICS_KNOWLEDGE_INDEX.md) and/or [`SHOP_BUILDING_KNOWLEDGE_INDEX.md`](./SHOP_BUILDING_KNOWLEDGE_INDEX.md) for your task  
3. Gore theme map only if working Gore physics: [`GORE_LECTURE_SERIES_SUMMARY.md`](./GORE_LECTURE_SERIES_SUMMARY.md)  
4. Crosswalks only (skim): Pack 5, Pack 3, Nicoletti EGB 2022, Nicoletti tonewood webinar; shop: SB soundboard; BK Bashkin full workflow  
5. Gap registers for anything you plan to implement  
6. Annotated notes only when a crosswalk row points at a specific ID  

---

## 6. What “done” looked like for intake

- Transcripts ingested → packs on branch / PR #243  
- CBSP21 manifest: `.cbsp21/patches/gore-lecture-series-packs-1-5.json`  
- Cohort floor held: `check_cohort_coverage.py` → PASS; catalog + search index current  
- MB Sound / TPC **panel laboratory records** ingested as [`mb_sound_panel_laboratory_records/`](./mb_sound_panel_laboratory_records/) (MB01–MB28; tab-by-tab). Still distinct from kit SOP pack (`nicoletti_mb_sound_acoustic_study_set`) and from any future raw-array data track

**Not done / not claimed:** runtime calculators, merged “universal” acoustic workflow, closed mobility thresholds, Pack 6 full SOPs.
