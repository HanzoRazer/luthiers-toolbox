# tap-tone-pi — Instrument Scope & Measurement Contract

## Instrument Class

**tap-tone-pi** is a **relative acoustic measurement instrument** designed to capture, preserve, and compare the vibrational response of physical specimens under controlled, repeatable excitation.

It is a **measurement instrument**, not an evaluation or decision system.

---

## What This Instrument Measures

tap-tone-pi measures and records:

* Time-domain audio response to impulsive excitation
* Frequency-domain magnitude spectra derived from FFT
* Resonant peak frequencies detected from measured spectra
* Session-level metadata describing capture conditions and parameters

All measurements are preserved as **raw artifacts** (audio, spectra, manifests) suitable for re-analysis.

---

## What This Instrument Does *Not* Claim

tap-tone-pi explicitly does **not**:

* Make judgments about "quality," "tone," or "goodness"
* Provide absolute, standards-traceable calibration (e.g., NIST)
* Measure absolute impedance, damping coefficients, or material constants
* Replace calibrated laboratory hardware (laser vibrometers, modal hammers)
* Perform psychoacoustic evaluation or subjective scoring

Any interpretation of measured data occurs **outside** the instrument.

---

## Valid Use Cases

The instrument is valid for:

* **Comparative measurements** under consistent conditions
* **Before / after analysis** (repair, modification, aging, humidity change)
* **Batch consistency checks** and drift detection
* **Educational and research demonstrations** of vibrational behavior
* **Exploratory structural acoustics** and modal analysis

Validity depends on **holding assumptions constant** between measurements.

---

## Measurement Assumptions (Held Constant)

For comparative validity, the following are assumed consistent within a study:

* Sensor type and placement
* Capture geometry
* Excitation method (impulse location and force)
* FFT parameters (windowing, bin size, overlap)
* Environmental conditions (to the degree practical)

These assumptions are **documented**, not enforced, and are preserved in exported artifacts.

---

## Data Integrity Guarantees

tap-tone-pi guarantees that:

* Raw measurements are preserved without modification
* Derived artifacts reference their source data
* Exported bundles are immutable and content-addressed
* Validation gates prevent emission of structurally invalid evidence
* Measurement and interpretation are strictly separated

This enables reproducibility, auditability, and long-term comparison.

---

## Interpretation Boundary

tap-tone-pi ends at **measurement and summarization**.

Any of the following are considered **downstream interpretation**:

* Assessing desirability or performance
* Ranking specimens
* Making design or repair decisions
* Applying domain-specific heuristics

These activities belong to external tools, human judgment, or future analytic systems.

---

## Summary Statement

> **tap-tone-pi is a laboratory-grade relative measurement instrument for acoustic and vibrational response.**
> It captures evidence, not conclusions.

---

### Version

Instrument Scope v1.0
