# Knowledge packs — developer orientation

**Purpose of this exercise:** Harvest *remnants of measurable shop workflows* from lecture / webinar transcripts into a knowledge layer **before** calculator or lab UI work.  
**PR:** [#243](https://github.com/HanzoRazer/luthiers-toolbox/pull/243) · branch `cursor/gore-shop-talk-20-lecture-notes-83c1`  
**Living index (theme summaries):** [`GORE_LECTURE_SERIES_SUMMARY.md`](./GORE_LECTURE_SERIES_SUMMARY.md)  
**Policy:** Documentation only. Cross-link schools; **do not merge** dialects into one calculator. Prefer empirical knowledge / guided labs over inventing thresholds.

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
| **OH** | Open hypothesis / taste |

### Processing pipeline used

```text
transcript paste
  → SOURCE_TRANSCRIPT (clean ASR)
  → ANNOTATED_* (point IDs + class + destination)
  → CROSSWALK (Toolbox mapping + NO-CALC)
  → GAPS (blockers)
  → GORE_LECTURE_SERIES_SUMMARY (index)
  → .cbsp21/patches/gore-lecture-series-packs-1-5.json (manifest)
```

**Point ID namespaces (do not renumber casually):**

| Prefix | School / pack family |
|--------|----------------------|
| P | Gore Shop Talk #20 |
| W | Gore wolf mailbag |
| M | Gore monopole mobility tip |
| S | Gore Shop Talk #25 |
| R | Gore responsive objectives |
| U | Gore Shop Talk #44 |
| A | Gore Shop Talk #51 / Academy apps |
| Y | Somogyi apprentice workflow |
| ES | Somogyi primary (01–02) |
| N | Nicoletti family (continues across his packs) |
| PM | Howman *Physics Mind* steel-string seminar |
| G-* | Gap IDs (`G-R01`, `G-M09`, `G-ES##`, `G-N##`, `G-PM##`, `G-T##`, …) |

---

## 2. Catalog — all packs

### A. Gore / O’Brien (priority-stack school)

| Pack | Path | Primary notes |
|------|------|----------------|
| 1 Shop Talk #20 | [`gore_shop_talk_20/`](./gore_shop_talk_20/) | P01–P38 |
| 2 Wolf mailbag | [`gore_wolf_notes_mailbag/`](./gore_wolf_notes_mailbag/) | W01–W09 |
| 3 Monopole mobility tip | [`gore_monopole_mobility_measurement/`](./gore_monopole_mobility_measurement/) | M01–M12 |
| 4 Shop Talk #25 | [`gore_shop_talk_25/`](./gore_shop_talk_25/) | S01–S21 |
| 5 Responsive objectives | [`gore_shop_talk_responsive_objectives/`](./gore_shop_talk_responsive_objectives/) | R-points + **G-R01** |
| 6 Guitar Analysis & Testing | [`gore_guitar_analysis_testing/`](./gore_guitar_analysis_testing/) | **PARTIAL** intro only |
| 7 Shop Talk #44 | [`gore_shop_talk_44/`](./gore_shop_talk_44/) | U01–U23 |
| 8 Shop Talk #51 Academy apps | [`gore_shop_talk_51_luther_academy_apps/`](./gore_shop_talk_51_luther_academy_apps/) | A01–A29 |

### B. Somogyi (related non-Gore)

| Pack | Path | Notes |
|------|------|-------|
| 01 Air pump / bracing / tap | [`somogyi_01_air_pump_bracing_tap_tone/`](./somogyi_01_air_pump_bracing_tap_tone/) | ES01–ES15 |
| 02 Top & Back | [`somogyi_02_top_and_back/`](./somogyi_02_top_and_back/) | ES16–ES28 |
| Apprentice first build | [`somogyi_apprentice_build_workflow/`](./somogyi_apprentice_build_workflow/) | Y01–Y20 |

### C. Nicoletti / MB / Iulius (related non-Gore)

| Pack | Path | Notes |
|------|------|-------|
| MB Acoustic Study Set how-to | [`nicoletti_mb_sound_acoustic_study_set/`](./nicoletti_mb_sound_acoustic_study_set/) | N01–N16 |
| MB kit interview | [`nicoletti_mb_kit_interview/`](./nicoletti_mb_kit_interview/) | N17–N42 |
| Science / Luthier Stories | [`nicoletti_science_luthier_stories/`](./nicoletti_science_luthier_stories/) | N43–N68 |
| Tonewood parameters webinar | [`nicoletti_tonewood_parameters_webinar/`](./nicoletti_tonewood_parameters_webinar/) | N69–N99 |
| EGB measuring/tuning Jul 2022 | [`nicoletti_egb_measuring_tuning_2022/`](./nicoletti_egb_measuring_tuning_2022/) | N100–N130 |

### D. Howman (related non-Gore)

| Pack | Path | Notes |
|------|------|-------|
| Physics Mind (Curtin 2011) | [`physics_mind_steel_string_lecture/`](./physics_mind_steel_string_lecture/) | PM01–PM36 |

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

**Standing NO-CALC rules (from packs):** no invented Win7 paths; no falcate geometry from talk alone; no hardcoded 236/275 Hz or 190 Hz mold coincidence as globals; no mobility “responsive” badges until unit profile locked.

---

## 5. Suggested reading order for developers

1. This file  
2. [`GORE_LECTURE_SERIES_SUMMARY.md`](./GORE_LECTURE_SERIES_SUMMARY.md) — theme map  
3. Crosswalks only (skim): Pack 5, Pack 3, Nicoletti EGB 2022, Nicoletti tonewood webinar  
4. Gap registers for anything you plan to implement  
5. Annotated notes only when a crosswalk row points at a specific ID  

---

## 6. What “done” looked like for intake

- Transcripts ingested → packs on branch / PR #243  
- CBSP21 manifest: `.cbsp21/patches/gore-lecture-series-packs-1-5.json`  
- Independent of MB Sound empirical corpus PR #244 (kit SOP ≠ panel workbooks)

**Not done / not claimed:** runtime calculators, merged “universal” acoustic workflow, closed mobility thresholds, Pack 6 full SOPs.
