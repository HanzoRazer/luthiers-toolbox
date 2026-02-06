# ADR-0004: Acoustic vs Structural Interpretation Boundary

**Status:** Accepted  
**Date:** 2025-12-25  
**Context:** Tap-Tone Measurement Node / Multi-Channel Acoustic Testing  
**Decision Drivers:** Scientific defensibility, correct claims, scope control, future extensibility

---

## Decision

### 1) Separate "what we measure" from "what we infer"

The system SHALL explicitly distinguish between:

* **Acoustic (pressure) measurements**: what microphones measure in air
* **Structural (vibration) measurements**: what the instrument body (wood) is doing

This boundary SHALL be enforced in:

* UI labels
* artifact metadata
* documentation
* any downstream report generation

---

### 2) Allowed claims by sensor type

#### Microphones (Pressure Field)

Mic data MAY support claims about:

* radiated sound pressure distribution (near-field / far-field)
* frequency content (peaks, bands)
* time delays / phase relationships between mic positions
* coherence (band-limited reliability)
* radiation "hot zones" (beamforming/NAH results) **as inferred acoustic fields**

Mic data SHALL NOT be used to claim:

* plate deflection shapes
* structural eigenmodes as measured truth
* "wave flow in the wood"
* brace stiffness changes as direct structural parameters
  unless corroborated with structural sensors or strong experimental protocol.

#### Structural Sensors (Accelerometers / LDV)

Structural data MAY support claims about:

* local acceleration / velocity responses
* structural mode shapes (if spatial grid is adequate)
* plate motion and modal participation
* "wave flow" and deflection patterns (within sensor resolution)

Structural sensing is REQUIRED for any claim phrased as:

* "mode shape"
* "plate deflection"
* "structural wave propagation"
* "wood vibration map"

---

### 3) Output labeling requirements

Any derived map/image/field SHALL be labeled as one of:

* **Acoustic radiation map (inferred)** — mic array based
* **Structural vibration map (measured)** — LDV/accelerometer based
* **Structural vibration estimate (inferred)** — only if model + validation exist (research-only)

---

## Rationale

* Mic arrays measure air pressure, not wood motion. Mixing these leads to invalid conclusions.
* The "different beast" vision demands credible testing; credibility comes from strict claims discipline.
* This boundary allows multi-mic expansion without overstating what it proves.

---

## Consequences

* Multi-mic features target acoustic radiation inference, not structural vibration truth.
* Structural mapping becomes an explicit future milestone (LDV/accelerometer integration).
* Documentation/UI must reflect interpretation class to avoid misunderstanding.

---

## Non-Goals

* No structural mode truth from mic-only data
* No brace/thickness recommendations derived solely from mic arrays in early phases
