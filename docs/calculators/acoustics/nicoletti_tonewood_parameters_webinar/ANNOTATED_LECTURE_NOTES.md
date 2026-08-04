# Annotated Lecture Notes  
## Tonewood Parameters Measurement & Selection (Nicoletti webinar)

**Presenter:** Giuliano Nicoletti  
**Audience:** European Guitar Builders / French Guitar Luthiers (PLG) — 2nd technical webinar  
**Companions:** TPC/Luthier Stories; MB kit packs; Gore vibrational-stiffness & mobility packs  
**Processing rule:** Knowledge layer only. Do not invent spreadsheet cells, Schelleng formula coefficients, or universal stage Hz from this model’s 190 Hz coincidence.

---

## 1. Motivation

### 1.1 Not required for excellence; four reasons to adopt  
**Timestamps:** ~0:15–2:48  

Consistency; learning; wood stewardship; enjoyment.

| Field | Value |
|-------|-------|
| Classification | **GN** |
| Link | Kit interview N17 |
| Toolbox destination | DOC adoption narrative |

**Point ID:** N69  

---

### 1.2 Structure vs acoustics (~70 kg load)  
**Timestamps:** ~2:48–4:15  

Tonewood must carry ~70 kg static string load **and** radiate efficiently — opposing demands. Today’s scope = acoustic parameters.

| Field | Value |
|-------|-------|
| Classification | **GN** |
| Toolbox destination | Separate structural vs acoustic workflows |

**Point ID:** N70  

---

## 2. Core tonewood parameters

### 2.1 Density — impedance + bridge EQ  
**Timestamps:** ~4:15–5:33  

\(\rho\) sets soundboard↔rim impedance match and radiating roles; bridge/bridge-plate mass acts as small EQ / low-pass.

| Field | Value |
|-------|-------|
| Classification | **GN**/EP |
| Toolbox destination | Tonewood + bridge-mass fields |

**Point ID:** N71  

---

### 2.2 \(E\) + Schelleng radiation coefficient (~1963)  
**Timestamps:** ~5:33–6:55  

\(E\) with \(\rho\) → SRC; density inverse **and cubed** → density dominates board radiating quality.

| Field | Value |
|-------|-------|
| Classification | **EP**/GN |
| Link | Gore Pack 5 SRC; interview N26 |
| Gap | Exact SRC formula text as shown on slide |

**Point ID:** N72  

---

### 2.3 Density not compensated by higher \(E\) (PRT scatter)  
**Timestamps:** ~7:02–10:13  

Pacific Rim Tonewoods \(E\)–\(\rho\) cloud: large dispersion. Simulations: 12 GPa/360 → ~136 g, SRC~16; denser 460 kg/m³ case → higher mass, SRC~14; ~24 GPa needed to compensate at 2.2 mm — nonexistent. For spruce, density paramount.

| Field | Value |
|-------|-------|
| Classification | **GN**/EO |
| Caveat | Second \(E\) spoken as “50 GPa” — treat as **ASR-risk** (likely 15) |
| Toolbox destination | Warn against “thinner denser = same” without calc |

**Point ID:** N73  

---

### 2.4 Orthotropy — measure cross-grain or dipoles drift  
**Timestamps:** ~10:13–12:57  

\(E_\parallel \gtrsim 10\,E_\perp\). Cross-bending dipole order shifts (5th isotropic vs 3rd orthotropic); Chladni confirms. Matching monopole without cross-grain data ≠ matching character.

| Field | Value |
|-------|-------|
| Classification | **GN** |
| Toolbox destination | Require \(E_L\), \(E_T\), (twist) in plate intake |

**Point ID:** N74  

---

### 2.5 Damping / Q — vibration-only property  
**Timestamps:** ~12:57–16:15  

Viscoelastic damping under oscillation; spruce Q~80 vs mahogany Q~30 (demo impulses). Low damping for efficient radiation of scarce string energy.

| Field | Value |
|-------|-------|
| Classification | **GN**/EP |
| Link | Somogyi Q; Gore Q-null tension — document |
| Toolbox destination | Optional Q/damping field |

**Point ID:** N75  

---

## 3. Guitar modes (context for wood choice)

### 3.1 Dipoles/tripoles can rival monopole SPL  
**Timestamps:** ~17:18–19:07  

Example Orchestra/Martin-like: air; live-back monopoles; dipoles ~350/450; long tripole; ~83–84 dB peaks shape timbre.

| Field | Value |
|-------|-------|
| Classification | **GN**/EO |
| Link | Gore T11x naming — map carefully (G-N08) |
| Toolbox destination | FRF annotation dialect |

**Point ID:** N76  

---

### 3.2 Bracing moves dipole spacing; style tradeoffs  
**Timestamps:** ~19:07–21:30  

X-brace: dipoles often ~350–400 Hz close. Fan classical: long dipole nearer monopole ~250 Hz. Archtop: emphasize monopole. Fingerstyle: more higher modes. No universal best.

| Field | Value |
|-------|-------|
| Classification | **GN** |
| Toolbox destination | Bracing dialect × mode-map cards |

**Point ID:** N77  

---

## 4. Measurement methods

### 4.1 Density hygiene  
**Timestamps:** ~23:20–23:40  

Dimensions + mass; uniform thickness.

**Point ID:** N78 · **GN**

---

### 4.2 Prefer dynamic FFT over static deflection  
**Timestamps:** ~23:40–24:37  

Deflection: simple but static + incomplete orthotropic/shear. Prefer vibrating conditions near instrument frequencies.

| Field | Value |
|-------|-------|
| Classification | **GN** |
| Link | Somogyi ES27 deflection culture — different stage/purpose |
| Toolbox destination | Prefer modal plate \(E\) path |

**Point ID:** N79  

---

### 4.3 REW + UMIK/miniDSP; Caldersmith nodal/antinode protocol  
**Timestamps:** ~24:46–26:50  

Room EQ Wizard; miniDSP USB mic; Caldersmith procedure; hold nodes, tap antinodes; long/cross/twist; Chladni if doubtful. Manual/articles on site.

| Field | Value |
|-------|-------|
| Classification | **GN** |
| Link | MB kit Phase 1 mic; TPC marble system (related) |
| Closes (partial) | G-N01 — names **Room EQ Wizard** as suggested software |

**Point ID:** N80  

---

### 4.4 Vibrational stiffness (Gore) → thickness / mass / SRC  
**Timestamps:** ~26:58–30:02  

Gore (2011/13) vibrational stiffness: braced-off board on infinite chassis as anticipation target. Side/back mass shifts final board \(f\) via impedance. Calibrate from own builds; spreadsheet outputs target thickness, panel mass, SRC.

| Field | Value |
|-------|-------|
| Classification | **TG**/GN |
| Link | Gore plate/mobility toolchain; Pack 8 apps |
| Toolbox destination | **EMP** plate target calculator — cite Gore+Nicoletti sheet, don’t invent cells |
| Gap | **G-N10** spreadsheet field map |

**Point ID:** N81  

---

### 4.5 Spectra as tap library (cedar/spruce/ebony/mahogany)  
**Timestamps:** ~30:10–34:28  

FRF = visual tap. Species differ in overtone density and Q — store/compare, not only scalar inputs.

**Point ID:** N82 · **GN**/EO

---

### 4.6 Damping: Lucchi limits; half-power vs log decrement  
**Timestamps:** ~34:35–40:42  

Lucchi ultrasonic = wrong band / system damping. Half-power needs dense FFT points (no phone apps). Log-decrement software in progress. Damping rises with frequency.

| Field | Value |
|-------|-------|
| Classification | **GN** |
| Link | TPC (Luthier Stories N55–N57) |
| Toolbox destination | LAB damping methods card |

**Point ID:** N83  

---

### 4.7 Damping × intent; headroom defined  
**Timestamps:** ~41:04–43:50  

More damping → strumming headroom; high Q → fingerstyle detail. Headroom = how hard before saturation/distortion on light high-mobility tops.

| Field | Value |
|-------|-------|
| Classification | **GN** |
| Link | Science pack N46–N47; interview N35 |

**Point ID:** N84  

---

### 4.8 Simple marble setup can match laser if careful  
**Timestamps:** ~44:09–45:12  

**Point ID:** N85 · **GN**/EO

---

## 5. Shop process constraints

### 5.1 Half-plates ~4 mm; RH ~45%; aging ≠ main \(E/\rho\)  
**Timestamps:** ~45:35–1:02:18  

Don’t measure full thin joined tops (too low \(f\)). Clean to ~4 mm; batch sessions. Aging: mainly HF structure; humidity swamps comparisons (~45% RH). Tap-feel at suppliers needs consistent worked thickness.

**Point ID:** N86 · **GN**

---

### 5.2 Spreadsheet \(c=\sqrt{E/\rho}\) not a damping proxy  
**Timestamps:** ~1:02:30–1:03:48  

**Point ID:** N87 · **GN**

---

## 6. Build-stage use of data

### 6.1 Three adoption levels  
**Timestamps:** ~1:04:11–1:06:29  

(1) Buy high-SRC wood; (2) plan monopole → thickness/mass by density intent; (3) measure through build.

**Point ID:** N88 · **GN**

---

### 6.2 Top-on-sides in fixed mold — pretune monopole  
**Timestamps:** ~1:06:45–1:12:21  

Glue top before back; block sides in **same mold**. Example: central-bar shave 220→**190** Hz without moving dipoles/tripoles. Finished return to 190 after box/bridge/finish path is **model+mold coincidence**. Always same jig mass. Shoot slightly high — hard to recover stiffness.

| Field | Value |
|-------|-------|
| Classification | **GN**/EO |
| Link | Interview N24/N27 |
| Toolbox destination | Stage gates + maker-specific ballparks |
| Gap | Do not globalize 190 Hz |

**Point ID:** N89  

---

### 6.3 Closed box + finished ETS example  
**Timestamps:** ~1:12:31–1:16:10  

Coupled A0/top/back; optional opening tune; Chladni; bridge changes shapes. Finished wolves hard; ETS **200 g → ~5 Hz**, monopole ~**170 Hz** clear.

| Field | Value |
|-------|-------|
| Classification | **GN**/EO |
| Link | Science pack N53; Gore wolves |
| Gap | G-N15 mass kit still incomplete |

**Point ID:** N90  

---

### 6.4 Customer spec sheet + standards plea  
**Timestamps:** ~1:16:18–1:18:13  

Ship FRF, monopole mobility, equivalent mass, three main mode frequencies — relationship, lifetime baseline, differentiation vs industry.

**Point ID:** N91 · **GN**

---

## 7. Late practical Q&A (compressed)

| ID | Point | Class |
|----|-------|-------|
| N92 | Tap completed guitar near saddle for full FRF; antinode for mode hunt; monopole near bridge locus | GN |
| N93 | Unknown peaks → Chladni at that Hz | GN |
| N94 | Brace carve = fine (couple mm); don’t gut structure | GN |
| N95 | Spoken search bands: air ~90–120 Hz; monopole ~170–220 Hz | GN/EO |
| N96 | Wolves spoil sustain/clarity/partials/intonation; treat mass/pins/putty (~3 g); can’t erase resonance without killing voice | GN |
| N97 | Overbuilt factory tops hide wolves but sound boring | GN |
| N98 | Audience magnet tuning (Pagelli) — interesting, not Nicoletti SOP | OH/EO |
| N99 | Hot-spot / “anti-wolf” excess: FRF+Chladni+putty; new strings/humidity can create transient issues | GN |

---

## 8. Point index (core)

| ID | Theme |
|----|-------|
| N69–N70 | Why measure; structure vs acoustics |
| N71–N75 | \(\rho\), \(E\), SRC, orthotropy, Q |
| N76–N77 | Mode balance / bracing dialects |
| N78–N85 | Metrology stack |
| N86–N87 | Process / \(c\) |
| N88–N91 | Build + customer use |
| N92–N99 | Shop Q&A practice |

---

## 9. School contrast snapshot

| Topic | This webinar | Gore packs | Prior Nicoletti packs |
|-------|--------------|------------|------------------------|
| Plate target | Gore **vibrational stiffness** + Nicoletti sheet | Same Gore books / apps | Kit deflection = finished \(k\) |
| SRC | Schelleng; density cubed emphasis | Pack 5 SRC by intent | Interview N26 |
| Orthotropy | Must measure \(E_T\) for dipole map | Often implicit | Less explicit before |
| Damping | Half-power / log-dec; Lucchi critique | Q often secondary | TPC system |
| Stage Hz | Maker-calibrated mold ballparks | Mid-scale triad absolutes | Kit/interview qualitative |

---

*See `CROSSWALK_TOOLBOX.md` and `GAPS_NOT_RECORDED.md`.*
