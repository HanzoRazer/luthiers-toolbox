# Annotated Lecture Notes  
## Giuliano Nicoletti / Maderas Barber — Acoustic Guitar Study Set

**Presenter:** Maderas Barber (kit walkthrough)  
**Method origin:** Giuliano Nicoletti — *Master in the Sound of the Acoustic Guitar*; kit collaboration with Maderas Barber  
**Scope:** Three-phase kit: (1) FRF / spectrum capture, (2) Chladni visualization, (3) 1 kg bridge deflection  
**Excluded:** Marketing close as teaching content; music beds  
**Processing rule:** Connectivity demo only — do not invent δ readings, mobility formulas, or mode-label maps beyond what is spoken. Defer deep SOP to Nicoletti book/videos (as the presenter does).

---

## 0. Architecture of the kit

Three phases:

1. **Acoustic response** of the guitar (measurement mic + impact) → spectrum / monopole–dipole–tripole IDs  
2. **Chladni patterns** on the top at selected frequencies (BT amp + precision speaker + powder)  
3. **Bridge deflection** under **1 kg** (dial indicator) → top “movilidad” / stiffness proxy  

Presenter repeatedly: this video = **connectivity / kit use**; full theory and detailed technique → Nicoletti book + his videos + MB Sound playlist.

---

## 1. Provenance

### 1.1 Collaboration + book basis  
**Timestamps:** ~0:00–0:31  

Kit from Nicoletti × Maderas Barber collaboration; pieces built from research in *Master in the Sound of the Acoustic Guitar* to measure acoustic response of guitars.

| Field | Value |
|-------|-------|
| Classification | **GN** / **MB** |
| Toolbox destination | **DOC** method provenance; cite book before shipping a “Nicoletti lab” |
| Gap | ISBN / edition / English vs Spanish title variants |

**Point ID:** N01  

---

## 2. Phase 1 — Acoustic response (FRF-like capture)

### 2.1 Hardware: miniDSP USB measurement mic + tripod  
**Timestamps:** ~0:47–1:22  

miniDSP measurement microphone; USB to computer; small desk tripod included. Normally used for sound-system calibration; here for guitar acoustic response.

| Field | Value |
|-------|-------|
| Classification | **MB** kit SKU; measurement practice **GN**/industry |
| Link to Gore | Pack 6 Visual Analyzer path — different toolchain, same *capture FRF* job |
| Toolbox destination | **LAB** mic profile metadata (make/model/serial) |

**Point ID:** N02  

---

### 2.2 Per-mic calibration file via serial  
**Timestamps:** ~1:25–1:47  

Mic has serial/ID; download that unit’s calibration file from miniDSP manufacturer site to optimize performance.

| Field | Value |
|-------|-------|
| Classification | **MB** / good metrology practice |
| Toolbox destination | **MEAS** — require or warn on calibration file presence |

**Point ID:** N03  

---

### 2.3 Software via book QR; RTA view; select miniDSP  
**Timestamps:** ~1:49–2:22  

Book QR → measurement software. On launch: confirm miniDSP mic. Upper menu: **RTA** (spectrum analyzer). Detailed use → Giuliano’s videos.

| Field | Value |
|-------|-------|
| Classification | **GN** / **MB** |
| Gap | **G-N01** — software product name / version / OS not spoken |
| Toolbox destination | DOC link-out; do not reverse-engineer UI from this clip |

**Point ID:** N04  

---

### 2.4 Mic ~few cm; kit hammer; multiple taps while recording  
**Timestamps:** ~2:29–3:12  

Place mic a couple of centimetres from the guitar; included hammer; several taps; software record.

| Field | Value |
|-------|-------|
| Classification | **GN**/MB demo SOP (sketch) |
| Link to Gore | Pack 2 “10-tap FRF”; Pack 6 FRF protocol gaps |
| Gap | Exact tap location(s), force, string state, support conditions |

**Point ID:** N05  

---

### 2.5 Read curve → monopole / dipole / tripole frequencies  
**Timestamps:** ~3:12–3:40  

From the response curve, identify frequencies for **monopole, dipole, and tripole** parameters (first interest); more info exists.

| Field | Value |
|-------|-------|
| Classification | **GN** mode vocabulary |
| Link to Gore | Pack 1/5/7 modal naming (T111/T112… / air–top) — **map carefully**; do not assume 1:1 labels |
| Toolbox destination | **KB** mode-label dialect card: Nicoletti monopole/dipole/tripole |

**Point ID:** N06  

---

## 3. Phase 2 — Chladni visualization

### 3.1 Bluetooth amp + precision speaker  
**Timestamps:** ~4:05–5:04  

BT amplifier/power amp + precision loudspeaker (kit). Speaker cables → amp; mains **220 V** via included transformer.

| Field | Value |
|-------|-------|
| Classification | **MB** kit |
| Toolbox destination | LAB hardware checklist |

**Point ID:** N07  

---

### 3.2 Pair phone to NS-01G; frequency-generator app  
**Timestamps:** ~5:07–6:12  

Power on → blue LED scanning → phone joins **NS-01G**. App: frequency generator. Test **440 Hz**; raise level **very gently** (high power).

| Field | Value |
|-------|-------|
| Classification | **MB** |
| Gap | Exact app name/store listing; amp power rating |
| Toolbox destination | LAB safety note: start quiet |

**Point ID:** N08  

---

### 3.3 Drive at Phase-1 key frequencies; powder tracer  
**Timestamps:** ~6:12–6:39  

Emit key frequencies from Phase 1 analysis. Tracer: light/volatile — **oregano**, pepper, or wood sawdust — distributed on the top. Stabilize guitar so powder doesn’t slide downhill.

| Field | Value |
|-------|-------|
| Classification | **GN**/MB |
| Toolbox destination | LAB Chladni procedure card |

**Point ID:** N09  

---

### 3.4 Demo: monopole ~236–238 Hz; dipole trial ~275 Hz  
**Timestamps:** ~6:39–8:40  

From Phase-1 analysis: monopolar ~**236–238 Hz** (refine in analysis); at 236 Hz monopole motion drawn. Higher mode trial ~**275 Hz** → two-pole (dipole) motion.

| Field | Value |
|-------|-------|
| Classification | **EO** (this guitar, this analysis) |
| Caveat | Not universal targets — identification outputs, not design specs |
| Toolbox destination | Example only in docs; never hardcode 236/275 |

**Point ID:** N10  

---

### 3.5 Phase-2 purpose restated  
**Timestamps:** ~8:40–8:58  

BT amp + phone frequency emission → draw Chladni patterns on the top = second measurement/analysis phase.

| Field | Value |
|-------|-------|
| Classification | **GN**/MB |
| Toolbox destination | Workflow stage 2 of 3 |

**Point ID:** N11  

---

## 4. Phase 3 — Bridge deflection under 1 kg

### 4.1 Dial-indicator fixture, bridge-centered, adjustable feet  
**Timestamps:** ~9:00–9:38  

Accessory with **dial indicator** and adjustable feet for guitar size/height. Indicator pin centered on the **bridge**.

| Field | Value |
|-------|-------|
| Classification | **GN**/MB |
| Link to Gore | Pack 3 monopole-mobility **stiffness** jig (1 kg deflection) — same *family* |
| Link to Somogyi | Pack 02 ES27 deflection stiffness culture |
| Toolbox destination | **LAB**/MEAS deflection fixture profile |

**Point ID:** N12  

---

### 4.2 Bone saddle strip protects bridge from pin  
**Timestamps:** ~9:38–10:06  

Included bone strip (saddle bone) so pin does not scratch/damage bridge.

| Field | Value |
|-------|-------|
| Classification | **MB** shop hygiene |
| Toolbox destination | LAB checklist |

**Point ID:** N13  

---

### 4.3 Quantity: height change with vs without calibrated 1 kg  
**Timestamps:** ~10:06–10:48  

Measure how much bridge height changes when applying **perfectly calibrated 1 kg**. Weight has a cavity for the upper pin to seat/balance. Interest = **difference** unloaded vs loaded. Spoken as measuring tapa **deflexión** / **movilidad**.

| Field | Value |
|-------|-------|
| Classification | **GN**/MB |
| Link to Gore | Pack 3: \(k = F/\delta\) with 1 kg; Pack 5 δ conflict (**G-R01**) |
| Critical | **No dial reading spoken** — does **not** close 27 mm vs ~0.15 mm |
| Gap | **G-N02** — δ value, units on dial, string state, whether full \(Y=1/\sqrt{km}\) is computed in Nicoletti workflow |
| Toolbox destination | MEAS: capture δ mm + F + metadata; unit profile mandatory |

**Point ID:** N14  

---

## 5. Closure / learning path

### 5.1 Three phases summarized  
**Timestamps:** ~10:48–11:06  

(1) Mic + taps acoustic capture; (2) speaker frequencies → Chladni; (3) bridge deflection.

| Field | Value |
|-------|-------|
| Classification | **MB** |
| Toolbox destination | Guided lab checklist (3 stages) |

**Point ID:** N15  

---

### 5.2 Book + YouTube playlist as deep SOP  
**Timestamps:** ~11:06–11:51  

Full explanation/foundation in Nicoletti book (in kit or catalog alone). Channel playlist: measurement kit + **MB Sound**. Goal: improve sound of next guitar.

| Field | Value |
|-------|-------|
| Classification | **GN**/MB |
| Gap | Playlist URL; which MB Sound videos are canonical SOP vs marketing |
| Toolbox destination | External curriculum links |

**Point ID:** N16  

---

## 6. Point index

| ID | Point | Class |
|----|-------|-------|
| N01 | Nicoletti × MB kit from book research | GN/MB |
| N02 | miniDSP USB measurement mic + tripod | MB |
| N03 | Serial → manufacturer calibration file | MB |
| N04 | Book QR software; RTA; select miniDSP | GN/MB |
| N05 | Mic ~cm; kit hammer; multi-tap record | GN/MB |
| N06 | Curve → monopole / dipole / tripole freqs | GN |
| N07 | BT amp + precision speaker (220 V) | MB |
| N08 | Pair NS-01G; freq-gen app; gentle level | MB |
| N09 | Drive Phase-1 keys; oregano/pepper/sawdust | GN/MB |
| N10 | Demo ~236–238 Hz mono; ~275 Hz dipole | EO |
| N11 | Phase 2 = Chladni via BT drive | GN/MB |
| N12 | Dial indicator centered on bridge | GN/MB |
| N13 | Bone strip protects bridge | MB |
| N14 | Δheight with calibrated 1 kg = movilidad | GN/MB |
| N15 | Three-phase summary | MB |
| N16 | Book + MB Sound playlist for depth | GN/MB |

---

## 7. School contrast snapshot

| Topic | Nicoletti / MB kit (this pack) | Gore packs | Somogyi 01–02 |
|-------|--------------------------------|------------|---------------|
| FRF tool | miniDSP + book software RTA | Visual Analyzer (Pack 6) | Ear / tap qualitative |
| Mode viz | Chladni at identified Hz | FRF peak reading; less powder demo | Ping-pong / live box |
| Stiffness | 1 kg + dial at **bridge** | 1 kg mobility jig → \(k\) then \(Y\) | Deflection target before bracing |
| Spoken “movilidad” | Bridge δ under 1 kg (this video) | Full \(Y=1/\sqrt{km}\) + thresholds | Efficiency / air-pump language |
| Design targets | Not in this connectivity video | Mid-scale triad, clearance, \(Y\) bands | Top–back frequency relationship |

Dialect / vendor-kit card — do not merge into Gore calculator defaults.

---

*See `CROSSWALK_TOOLBOX.md` and `GAPS_NOT_RECORDED.md`.*
