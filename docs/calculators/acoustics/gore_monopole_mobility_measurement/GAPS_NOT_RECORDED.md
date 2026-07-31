# Gaps Not Recorded — Monopole Mobility SOP

**Status:** Knowledge of absence — essential even when shop-floor granularity is not obtainable from the source video.  
**Policy:** Do **not** invent missing detail. Track gaps here; close only from primary sources (Gore books, Carrico spreadsheet/jig docs, controlled re-measure, or explicit instructor clarification).  
**Related recorded SOP:** [`ANNOTATED_LECTURE_NOTES.md`](./ANNOTATED_LECTURE_NOTES.md) §7 (procedure-complete, tooling-light).

---

## Why this document exists

The tip gives a usable outline (load → \(\delta\) → plug → \(f\) → \(Y\)). It does **not** specify the mechanical boundary conditions, peak-picking rules, or spreadsheet arithmetic that make numbers **reproducible across shops**. Without naming those gaps, a Toolbox lab risks:

- shipping thresholds against the wrong unit profile  
- measuring a different “monopole” than Gore’s  
- comparing builds that were never measured the same way  

---

## Gap register

IDs use `G-M##` (mobility gaps). Severity: **Blocker** (must resolve before calculator/thresholds), **High** (reproducibility), **Medium** (quality), **Low** (nice-to-have).

### A. Jig geometry & boundary conditions

| ID | Not recorded | Why it matters | Severity | How to close later |
|----|--------------|----------------|----------|--------------------|
| G-M01 | Exact **load application point** (bridge center, saddle line, between pins, top at bridge footprint, etc.) | \(k\) is path-dependent; wrong point ≠ Gore mobility | **Blocker** | Carrico jig docs / stills from video / Gore Vol. measurement chapter |
| G-M02 | Guitar **support / clamping** in the jig (rim support, neck cradle, back free vs constrained) | Changes apparent stiffness and mode shape | **Blocker** | Same |
| G-M03 | Whether strings are at **pitch, slack, or removed** during deflection | String tension and bridge torque alter \(\delta\) | **High** | Re-watch frames + instructor note; encode as required metadata |
| G-M04 | Bridge **installed vs not**, saddle in/out, string-through vs pin | ST#20: bridge adds mass **and** stiffness — stage must match claim | **High** | Stage taxonomy (already flagged M12) |
| G-M05 | Indicator resolution, brand, mounting compliance, cup alignment | Systematic \(\delta\) error → \(k\) and \(Y\) error | **Medium** | Jig BOM / calibration procedure |
| G-M06 | Settling time, creep, number of load cycles before reading | Soft tops creep under 1 kg | **Medium** | Shop protocol from Gore/Carrico |
| G-M07 | Temperature / humidity at measurement | Wood compliance drifts | **Medium** | Standard shop climate note |
| G-M08 | Left-hand / right-hand / body-size jig variants | Transferability across OM vs dread vs classical | **High** | Geometry drawings per body class |

### B. Deflection reading protocol

| ID | Not recorded | Why it matters | Severity | How to close later |
|----|--------------|----------------|----------|--------------------|
| G-M09 | Whether 27 mm is typical, exceptional, or ASR-risk (vs 2.7 mm) | Order-of-magnitude \(k\) error | **Blocker** | Visual confirmation from video frame + spreadsheet example |
| G-M10 | Official rule for **load-on vs unload** averaging | Robbie mentions both; no rule for disagreement | **Medium** | Written Carrico SOP |
| G-M11 | Rejection criteria (tilt, binding, uneven rim contact) | Bad \(\delta\) silently accepted | **Medium** | Lab checklist |
| G-M12 | Sign / direction of deflection (into cup convention) | Spreadsheet sign assumptions | **Low** | Spreadsheet cell docs |

### C. Force & unit profile

| ID | Not recorded | Why it matters | Severity | How to close later |
|----|--------------|----------------|----------|--------------------|
| G-M13 | Exact Carrico spreadsheet **arithmetic and units** (N/m vs kgf/m vs scaled score) | Spoken **31.3** ≠ pure SI ~**3.13** for stated inputs | **Blocker** | Obtain sheet; freeze `unit_profile: carrico_gore_v1` |
| G-M14 | Whether \(g\) is 9.81, 9.80665, or “1 kgf” shorthand | Threshold drift | **High** | Spreadsheet constants |
| G-M15 | Published definition of threshold bands (11–12 / 20): score vs SI | Mis-badge “responsive” | **Blocker** | Gore book + Luther Academy app spec |
| G-M16 | Precision / rounding rules displayed to user | Comparison noise across builds | **Low** | App/sheet defaults |

### D. Uncoupled frequency capture

| ID | Not recorded | Why it matters | Severity | How to close later |
|----|--------------|----------------|----------|--------------------|
| G-M17 | Which spectral peak is “the” uncoupled monopole if several appear | Wrong \(f\) → wrong \(m\) and \(Y\) | **Blocker** | Gore peak-ID rules; Guitar Tap docs; Tap Tone labeling |
| G-M18 | Tap location(s) for \(f\) (bridge, lower bout, etc.) | Mode selectivity | **High** | Same |
| G-M19 | Number of taps / averaging / rejection of double-hits | Same class of “grass” issues as ST#20 FRF | **Medium** | Align with FRF lab pack |
| G-M20 | Mic distance, axis, gain, app FFT settings | Peak frequency bias | **Medium** | Guitar Tap recommended settings |
| G-M21 | Plug seal quality metric (leak vs airtight) | Residual air coupling | **High** | Acceptance: no audible cavity contribution / expected \(f\) band |
| G-M22 | Yogurt-cup vs machined plug equivalence | Systematic \(f\) offset between methods | **Medium** | A/B measure on one guitar |
| G-M23 | Strings: must be loose for cup method; plug method leaves strings — tension state for \(f\) vs for \(\delta\) | Inconsistent stage between \(k\) and \(f\) legs | **High** | Single stage matrix table |

### E. Effective mass & model assumptions

| ID | Not recorded | Why it matters | Severity | How to close later |
|----|--------------|----------------|----------|--------------------|
| G-M24 | Validity limits of single DOF \(m=k/(2\pi f)^2\) on real tops | When multi-mode / non-monopole pollutes \(f\) | **High** | Gore theory bounds; when to abort |
| G-M25 | Relation of this \(m\) to physical top mass or radiation mass | Pedagogy / KB; avoid false equivalence | **Medium** | Book cross-reference |
| G-M26 | Whether mobility is “average admittance” over a band or a single-mode proxy | Interpretation of \(Y\) | **High** | Gore definition paragraph |

### F. Interpretation & build integration

| ID | Not recorded | Why it matters | Severity | How to close later |
|----|--------------|----------------|----------|--------------------|
| G-M27 | Body-style / string-tension specific threshold tables | One 11–12 / 20 table may be too coarse | **High** | Empirical corpus |
| G-M28 | Interaction protocol: high \(Y\) but wolf on scale tone — pass/fail order | Priority stack needs UX rules | **High** | Encode Pack 1 stack + Pack 2 clearance |
| G-M29 | How brace edits map quantitatively to \(\Delta Y\) (not only direction) | Guided “lower brace → mobility up” lacks magnitudes | **Medium** | Shop corpus (EMP) |
| G-M30 | Classical vs steel jig / load differences beyond threshold numbers | Wrong fixture transfer | **High** | Separate SOPs if required |
| G-M31 | Finished-guitar vs in-progress box: when mobility claim is allowed in UI | Premature “responsive” badges | **High** | Stage gates |

### G. Provenance / tooling (non-blocking but track)

| ID | Not recorded | Why it matters | Severity | How to close later |
|----|--------------|----------------|----------|--------------------|
| G-M32 | Stable URLs / versions for Carrico jig, spreadsheet, Guitar Tap, Luther Academy apps | Bitrot | **Medium** | Pin versions when obtained |
| G-M33 | License / redistribution rights for spreadsheet logic in Toolbox | Legal | **High** before porting sheet |
| G-M34 | Video title, publish date, URL | Citation completeness | **Low** | Add when known |
| G-M35 | Frame stills of jig contact and caliper reading | Resolve G-M01/G-M09 | **High** | Capture from source video under fair-use notes |

---

## What *was* recorded (scope boundary)

Do not treat gaps as “SOP missing entirely.” The following **are** recorded at outline fidelity:

- Definition of \(Y\) as responsiveness / average-admittance proxy (Gore term)  
- \(Y=1/\sqrt{km}\), \(F=9.81\,\mathrm{N}\) for 1 kg, \(k=F/\delta\), \(m=k/(2\pi f)^2\)  
- Jig + 1 kg + mm deflection + optional average  
- Soundhole plugged for uncoupled \(f\)  
- Example numbers as spoken: \(\delta=27\,\mathrm{mm}\), \(f=180.7\,\mathrm{Hz}\), score \(31.3\)  
- Threshold chatter: ~11–12 steel, ~20 classical / Gore “very responsive”  
- Unit-profile hazard (31.3 vs SI ~3.13)  
- Bridge stage caveat via Shop Talk cross-link  

---

## Implementation rules until gaps close

1. **Docs/KB OK** — teach the outline and show this gap register.  
2. **No threshold badges in product UI** until G-M13 + G-M15 closed.  
3. **SI path OK as scientific output** if labeled `unit_profile: si_raw` and not compared to 11/12/20.  
4. **Guided lab drafts** must require metadata fields even when values are unknown enums (`load_point: unknown`, `support: unknown`).  
5. **Never invent** jig geometry from “typical lutherie practice” to fill G-M01–G-M02.

---

## Cross-pack gaps (mobility-adjacent, not unique to this video)

Tracked here so mobility work does not pretend the rest of the stack is complete:

| Gap | Pack | Note |
|-----|------|------|
| Mode-selective voicing recipes (which brace moves which mode) | Shop Talk P02 | EMP corpus, not this video |
| Exact 100/180/226 applicability by body size | Shop Talk P04 | Taste + body-style variants |
| Live-back peak-density metric definition | Shop Talk P14–P16 | Needs FRF feature definition |
| Wolf tuner-flutter detection algorithm | Wolf W02 | UX/signal detail absent |
| Carrico sheet vs Tap Tone Pi handoff | This pack + analyzer boundary | Ownership clear; schema not |

---

## Closure log

| Gap ID | Closed? | Date | Evidence |
|--------|---------|------|----------|
| *(none yet)* | — | — | — |

When a gap closes, move a one-line entry here and patch the SOP section in `ANNOTATED_LECTURE_NOTES.md` — do not silently delete the gap row; mark **Closed** and leave the history.
