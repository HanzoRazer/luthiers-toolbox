# ADR-0006: RMOS RunArtifact Mapping

**Status:** Accepted  
**Date:** 2025-12-25  
**Context:** Tap-Tone Measurement Node → ToolBox/RMOS (Future Integration)  
**Decision Drivers:** Forward compatibility, minimal coupling, clean ingestion path

---

## Decision

### 1) Integration is deferred, contract is not

Direct RMOS integration code is deferred, but artifacts SHALL be produced in a shape that can be ingested as RMOS RunArtifacts / attachments with minimal transformation.

---

### 2) Mapping strategy

Each tap-tone capture SHALL map to:

* **One RMOS RunArtifact** of type `tap_tone_capture`
* With attachments:

  * `audio.wav`
  * `analysis.json`
  * `spectrum.csv`
  * optional: `channels.json`, `geometry.json` (Phase 2+)
  * optional: plots/images (future)

A multi-take session MAY map to:

* a "parent" `tap_tone_session` artifact containing summary + pointers to child capture artifacts.

---

### 3) Required provenance fields (artifact metadata)

For RMOS ingestion, the capture SHALL include metadata fields equivalent to:

* `tool_id`: `"tap_tone_node"` (or finalized tool name)
* `tool_version`: semantic version
* `mode`: `"acoustics"`
* `event_type`: `"measurement"`
* `ts_utc`
* `label` / `tap_point`
* capture parameters (sample_rate, seconds, channels)
* protocol identifiers (fixture, mic_distance, tap tool) when known

---

### 4) Hashing / dedup

Artifacts SHOULD include:

* SHA256 hashes of attachments (computed at export time)
* Stable naming:

  * `audio_<sha>.wav`, etc., if RMOS expects content-addressed storage later

Dedup behavior is RMOS-side; tap-tone node remains artifact-first.

---

### 5) Export adapter (future)

When integration begins, it SHALL be implemented as a separate "export adapter" module that:

* reads the artifact bundle
* constructs RMOS RunArtifact payload
* uploads attachments through the chosen RMOS intake path

The measurement node SHALL NOT import RMOS as a dependency in Phase 1–2.

---

## Rationale

* RMOS evolves; measurement artifacts should not depend on RMOS internals.
* A stable artifact contract makes ingestion trivial later.
* The adapter pattern prevents coupling and preserves offline usability.

---

## Consequences

* You can develop/testing the node independently.
* RMOS integration becomes a bounded future task, not a creeping dependency.
* Artifacts remain useful even without RMOS.

---

## Non-Goals

* No RMOS database writes from the tap-tone node
* No requirement for network connectivity during capture
* No attempt to "synchronize" captures to RMOS runs in Phase 1
