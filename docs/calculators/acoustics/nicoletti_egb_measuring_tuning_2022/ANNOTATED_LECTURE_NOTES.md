# Annotated Lecture Notes  
## Measuring & Tuning Acoustic Guitar Performance — EGB July 2022

**Presenter:** Giuliano Nicoletti  
**Event:** EGB / PLG webinar, July 2022  
**Companions:** Tonewood webinar; MB kit how-to/interview; Gore Packs 2/3/5/6  
**Critical cross-school evidence:** Spoken 1 kg deflection **~0.01–0.02 mm** (plus Taylor examples ~0.13–0.15 mm) — same order as Gore Pack 5 (~0.15 mm); **contradicts Pack 3 “27 mm”** as typical finished-top δ.

---

## 1. Role of measurement

### 1.1 QC even when you already like your guitars  
**Timestamps:** ~1:20–2:51  

Not only R&D. Photograph builds; ensure outgoing instruments perform — without forcing a method change.

| Field | Value |
|-------|-------|
| Classification | **GN** |
| Link | Kit interview N17; tonewood N69 |
| Toolbox destination | QC checklist / build archive |

**Point ID:** N100  

---

### 1.2 Priority trio: FRF → mobility → Chladni  
**Timestamps:** ~2:57–4:07  

FRF + monopole mobility for nearly every guitar; Chladni mainly R&D/troubleshoot. Bridge rotation often subsumed in mobility. Wood params = other webinar.

**Point ID:** N101 · **GN**

---

## 2. Frequency response

### 2.1 Peaked musical FRF vs flat monitor  
**Timestamps:** ~4:37–7:32  

Evaluate differently from hi-fi flatness; peaks sit in fretted range.

| Field | Value |
|-------|-------|
| Classification | **GN** |
| Link | Science pack N49 |

**Point ID:** N102  

---

### 2.2 Mode map: A0 ~100; monopole; optional back; dipoles  
**Timestamps:** ~8:12–14:19  

Air ~100 Hz; pistonic monopole; active back if light/near; long then cross dipole on X-brace Martins. Display often to 1 kHz (~50 dB down). No maker-association upper-limit standard yet.

**Point ID:** N103 · **GN**/EP

---

### 2.3 REW + miniDSP; 25 cm; ~32 averages; saddle taps  
**Timestamps:** ~14:30–24:15  

miniDSP USB mic + cal file; Room EQ Wizard; hold by neck; mic ~**25 cm** close field; average ~**32** taps; damp strings; saddle zone for full FRF. Overlay notes live for wolf clearance check.

| Field | Value |
|-------|-------|
| Classification | **GN** |
| Closes (partial) | G-N01 — REW + miniDSP confirmed for **guitar** FRF (not only plates) |
| Link | MB study-set Phase 1; Pack 6 VA path |
| Toolbox destination | LAB FRF protocol card |

**Point ID:** N104  

---

## 3. Mastering / checklist

### 3.1 PLG basic checklist  
**Timestamps:** ~24:46–25:11  

Modes match project; wolf risk; harmonic stacking of peaks; higher-order radiating modes.

**Point ID:** N105 · **GN**

---

### 3.2 Place resonances between notes; example 106 / 180  
**Timestamps:** ~26:23–28:42  

Avoid fundamental+harmonic pile-up (e.g. 110/220). Example air 106, monopole 180 — clearance from open A / 220. Light tops more wolf-sensitive. Play **between** resonances.

| Field | Value |
|-------|-------|
| Classification | **GN** |
| Link | Gore Pack 2; interview N23 |
| Toolbox destination | Wolf clearance RULE |

**Point ID:** N106  

---

### 3.3 Higher modes: present vs radiating  
**Timestamps:** ~28:50–30:08  

Always exist; heavy board / bracing can suppress radiated SPL — large timbre effect; dialect not ranking.

**Point ID:** N107 · **GN**

---

### 3.4 A0 / monopole levers; 4DOF coupling  
**Timestamps:** ~32:46–36:50  

A0 via hole size (purfling ring → 106). Monopole via thickness, braces, side mass, pin mass (~5 g). Gore **4DOF** simulator: modes coupled. Easier to lower \(f\) than raise.

**Point ID:** N108 · **GN**/TG

---

## 4. Monopole mobility (numeric δ)

### 4.1 Jig: 1 kg, plug hole, compute \(m\), compliance, \(Y\)  
**Timestamps:** ~40:26–42:27, ~58:31–1:00:19  

Micrometer platform; ~**1 kg** at center; measure δ; plug soundhole; measure uncoupled \(f\); Excel → equivalent mass + monopole mobility. String tension little effect. Typical δ spoken **0.01–0.02 mm**.

| Field | Value |
|-------|-------|
| Classification | **GN**/EO |
| Link | Gore Packs 3/5; study-set N14; interview N31–N34 |
| **G-R01 / G-M09** | **Strong corroboration** of 0.01–0.15 mm class; Pack 3 **27 mm** remains ASR-risk |
| Toolbox destination | MEAS mobility — unit profile; do not adopt 27 mm |
| Gap | Exact Excel formulas still G-N10 |

**Point ID:** N109  

---

## 5. Chladni practice

### 5.1 Small speaker + BT amp + powder; brace relation  
**Timestamps:** ~42:33–45:11  

Small driver to focus; oregano/basil; LED inside. Plate usually dominates pattern vs bracing unless bracing very heavy; shows where to tweak.

**Point ID:** N110 · **GN**

---

### 5.2 Selective putty on tripole (~5 g)  
**Timestamps:** ~56:01–57:58  

Hot long tripole ~606 Hz; mass far from monopole — surgical FRF change.

**Point ID:** N111 · **GN**/EO

---

## 6. Characterization library (spoken)

| ID | Comparison | Teaching use | Class |
|----|------------|--------------|-------|
| N112 | D28 vs LX1E | Size/SPL/A0/high-mode presence; travel/feedback design | EO/GN |
| N113 | D28 (~79 g) vs Larrivée (~103 g) | Same catalog woods/shape ≠ same \(Y\)/spectrum | EO/GN |
| N114 | OM-28 vs D28 | Mass/SPL/mobility similar order; scallop δ; high-mode count | EO/GN |
| N115 | Benedetto-style archtop | Higher A0/monopole; mid focus; thick graduated top | EO/GN |
| N116 | Responsive X (~68 g) vs ES-335-like vs Les Paul | Acoustic FRF nearly vanishes on heavy solid bodies | EO/GN |

Do not hardcode these as Toolbox defaults without book/table verification (G-N17).

---

## 7. Process / community

| ID | Point | Class |
|----|-------|-------|
| N117 | Seasonal humidity/dome small \(f\) shifts; FRF aging modest in his sample | GN/EO |
| N118 | Customer spec: FRF + modes + mobility parameters; push for standards | GN |
| N119 | Start: measure finished guitars, don’t change the method yet | GN |
| N120 | Prefer miniDSP+REW (~€100) over ad-hoc condenser/phone | GN |
| N121 | Taylor edge channel: δ ~0.13–0.15 mm samples; not magic mobility | GN/EO |
| N122 | Thinning: ↑compliance and ↓mass oppose | GN |
| N123 | Stage: top on rims (fixed edges) before back/bridge | GN |
| N124 | Troughs between peaks → cleaner sustain (high impedance) | GN |
| N125 | Linear mode superposition OK for Chladni practice | GN/EP |
| N126 | Semi/solid electric: prefer electrical/pickup measurements | GN |
| N127 | Repair/amp feedback use-case for FRF storytelling | GN/OH |
| N128 | Article + Appendix A software setup on website | GN |
| N129 | Tonewood/damping webinar foreshadowed | GN |
| N130 | Organizers / community common-language goal (APLG etc.) | GN/EO |

---

## 8. School contrast + δ conflict

| Topic | This webinar | Gore Pack 3 tip | Gore Pack 5 |
|-------|--------------|-----------------|-------------|
| 1 kg δ | **~0.01–0.02 mm** typical; Taylor ~0.13–0.15 | Spoken **27 mm** | ~**0.15 mm** |
| Toolchain | REW + miniDSP + averages | Carrico jig + tip video | Lead-shot / dial culture |
| FRF | Impact + 32 avg, 25 cm | Visual Analyzer (Pack 6) | Spectrogram stages |

**Disposition:** Treat Pack 3 27 mm as **ASR-risk / non-typical**. Prefer 0.01–0.15 mm class for finished tops pending Carrico sheet stills. Do **not** close G-R01 fully until Carrico arithmetic verified — but Nicoletti is independent corroboration of the small-δ regime.

---

*See `CROSSWALK_TOOLBOX.md` and `GAPS_NOT_RECORDED.md`.*
