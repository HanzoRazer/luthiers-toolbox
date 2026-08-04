# Annotated Engineering Lecture Notes  
## Guitar Analysis & Testing — Measurement Setup Course (PARTIAL)

**Presenter:** Trevor Gore (Gore Guitars, Sydney)  
**Location:** Robbie O’Brien’s workshop  
**Purpose:** Practical setup of measurement systems used with Gore’s Design & Build books — **not** full acoustic theory (deferred to books; “video years long” otherwise)  
**Ingest status:** Introduction only (~0:28–3:11). Detailed click-paths for Win7/Win10, Visual Analyzer, wood modes, bridge rotation, and monopole mobility **not yet in workspace transcript**.

---

## 0. Session architecture (from intro)

Gore addresses builders who emailed / asked how to set up the measurement chain. Scope is **how to measure**, not how to interpret every result (interpretation → books).

### Five modules announced

| # | Module | Stated content |
|---|--------|----------------|
| **A** | Microphone on Windows | Setup on **Windows 7** and **Windows 10** |
| **B** | Guitar frequency response curve | Using **Visual Analyzer** (spectrum analyzer); Win7 vs Win10 similar but different enough to cause problems |
| **C** | Wood elastic properties | Measure modes of vibration for thicknessing / material characterization (use of numbers → book) |
| **D** | Bridge rotation test | Soundboard stiffness under string torque |
| **E** | Monopole mobility | Responsiveness measure |

| Field | Value |
|-------|-------|
| Classification | **TG** curriculum / tooling pedagogy |
| Toolbox destination | **LAB** suite “Gore measurement setup”; Tap Tone may replace VA path for FRF while preserving stage semantics |
| Link | Luther Academy “Guitar Analysis and Testing” course referenced across Shop Talks |

**Point ID:** T01  

---

## 1. Teaching points from intro (ingested)

### 1.1 Books rely on measurement systems  
**Timestamps:** ~0:46–1:06  

Design/build acoustics in the books depend on measurement systems; this video shows how to set those systems up.

| Field | Value |
|-------|-------|
| Classification | **TG** |
| Toolbox destination | **KB** — empirical layer assumes measured inputs |

**Point ID:** T02  

---

### 1.2 Interpretation deferred to books  
**Timestamps:** ~1:06–1:18  

Detail on what measurements mean and how to use them is in the books; intentionally omitted here to keep the video practical.

| Field | Value |
|-------|-------|
| Classification | **TG** pedagogy |
| Toolbox destination | Guided labs should link “how to capture” vs “how to interpret” separately (analyzer boundary) |

**Point ID:** T03  

---

### 1.3 Motivation: setup friction  
**Timestamps:** ~1:34–1:43  

Many builders struggle with setup; video exists to cover those pain points.

| Field | Value |
|-------|-------|
| Classification | **EO**/**TG** |
| Toolbox destination | UX priority for measurement onboarding |

**Point ID:** T04  

---

### 1.4 Bridge rotation = torque response of soundboard  
**Timestamps:** ~2:29–2:39  

Bridge rotation test assesses how stiff the soundboard is and how it responds to string tension torque on the board.

| Field | Value |
|-------|-------|
| Classification | **TG** (definition only; procedure pending) |
| Link | ST#25 ~2° structural target; ST#20 “don’t obsess 1.5 vs 2°” for vanity vs structural test here |
| Gap | Full test SOP not in ingested transcript |

**Point ID:** T05  

---

### 1.5 Monopole mobility = responsiveness  
**Timestamps:** ~2:42–2:47  

Named as measure of guitar responsiveness (procedure pending; see Packs 3 & 5).

| Field | Value |
|-------|-------|
| Classification | **TG** |
| Gap | Course-specific click-path / recommended numbers may differ slightly from Shop Talk demos |

**Point ID:** T06  

---

### 1.6 Platform note: Win7 vs Win10  
**Timestamps:** ~2:52–3:04  

Mic and Visual Analyzer setup covered for both OS versions; “pretty similar but different enough to make it a problem.”

| Field | Value |
|-------|-------|
| Classification | **TG**/**EO** tooling caveat |
| Toolbox / Tap Tone | Prefer OS-agnostic modern path; archive Win7/10 VA steps as legacy appendix when transcript arrives |
| Gap | Actual setup steps not yet ingested |

**Point ID:** T07  

---

## 2. Module stubs (awaiting transcript)

### Module A — Microphone setup (Windows 7 / 10)
**Status:** Not ingested.  
**Expected:** Device selection, levels, exclusive mode, sample rate, troubleshooting.

### Module B — Visual Analyzer FRF
**Status:** Not ingested.  
**Expected:** Capture spectrum, buffers/averages, guitar tap procedure — compare Pack 1 P33 / Pack 2 W04 / Pack 5 R03.

### Module C — Wood elastic / modal measurements
**Status:** Not ingested.  
**Expected:** Free-plate or strip modes for E, etc.; thicknessing workflow hooks to book.

### Module D — Bridge rotation test
**Status:** Definition only (T05).  
**Expected:** Load/geometry, angle measurement, acceptance (~2°?).

### Module E — Monopole mobility
**Status:** Definition only (T06).  
**Expected:** Course-canonical jig/δ/f path — **reconcile with Pack 3 (27 mm) vs Pack 5 (0.15 mm)**.

---

## 3. Compact point catalog (ingested only)

| ID | Point | Class |
|----|-------|-------|
| T01 | Five-module measurement curriculum | TG |
| T02 | Books depend on measurement systems | TG |
| T03 | Interpretation → books; video = setup | TG |
| T04 | Setup friction motivated the video | EO/TG |
| T05 | Bridge rotation = torque/stiffness test (def only) | TG |
| T06 | Monopole mobility = responsiveness (def only) | TG |
| T07 | Win7 vs Win10 setup differs enough to break things | TG/EO |

---

*Append module sections as further transcript arrives. See `GAPS_NOT_RECORDED.md`.*
