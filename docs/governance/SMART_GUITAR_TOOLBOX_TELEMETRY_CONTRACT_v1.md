# SMART_GUITAR ↔ TOOLBOX_TELEMETRY_CONTRACT_v1

**Status:** Normative (Enforced)
**Effective Date:** 2026-01-10
**Owner:** Architecture Board
**Review Cycle:** Semi-Annual

---

## Executive Summary

This contract defines the **only permitted telemetry exchange** from **Smart Guitar systems** back into **ToolBox** after manufacturing and delivery.

The purpose of telemetry ingestion is **manufacturing intelligence and lifecycle optimization** — **not pedagogy, coaching, or player evaluation**.

> **ToolBox builds guitars and learns how to build them better.**
> **Smart Guitar teaches people to play them better.**
> **Telemetry may inform manufacturing — it must never inform teaching.**

---

## Core Principle (Non-Negotiable)

> **Smart Guitar may emit operational telemetry.
> ToolBox may ingest telemetry for manufacturing insight only.
> No pedagogical, instructional, or player-evaluative data may cross this boundary.**

Violation of this principle constitutes **authority inversion** and is grounds for rejection.

---

## System Roles & Authority

### Smart Guitar (Source System)

Smart Guitar is the **runtime authority** for:

* Player interaction
* Pedagogical feedback
* Coaching logic
* Lesson progression
* Practice evaluation
* Musical interpretation

Smart Guitar **owns all teaching semantics**.

---

### ToolBox (Sink System)

ToolBox is the **manufacturing authority** for:

* Physical design
* Process planning
* Cost modeling
* Manufacturing analytics
* Lifecycle optimization

ToolBox **must not interpret player skill, behavior, or intent**.

---

## Telemetry Scope (Allowed)

Only the following telemetry categories may be transmitted from Smart Guitar to ToolBox.

### 1. Instrument Utilization Metrics

Aggregated, non-player-specific usage data:

* Power-on hours
* Session count
* Idle vs active time
* Feature enablement rates
* Mode usage frequency

**Constraints:**

* Aggregated only
* No per-lesson breakdown
* No per-player correlation

---

### 2. Hardware Performance Metrics

Metrics related to the physical instrument and electronics:

* Pickup noise floor
* ADC clipping rates
* Latency jitter
* Sensor error counts
* Firmware fault codes
* Thermal excursions

**Purpose:** improve hardware design and component selection.

---

### 3. Environmental & Operating Conditions

* Temperature ranges
* Humidity exposure (bucketed)
* Shock / vibration events
* Transport vs stationary usage ratios

**No GPS, location, or identity allowed.**

---

### 4. Manufacturing Outcome Feedback

Telemetry explicitly tied to **manufacturing decisions**, not players:

* Fret wear rate buckets
* Nut/saddle wear indicators
* String break frequency (bucketed)
* Electronics failure MTBF
* Structural adjustment frequency

These metrics may be correlated **only** with:

* Build spec
* Material choice
* Manufacturing batch
* Design revision

---

### 5. Cost Attribution Signals

Telemetry that enables lifecycle cost modeling:

* Warranty-relevant events (non-user-fault)
* Component replacement intervals
* Maintenance frequency bands

---

## Explicitly Prohibited Telemetry

The following **must never** cross the boundary:

### Player / Pedagogy Data (Hard Prohibition)

* Player identity
* Player skill level
* Practice duration per lesson
* Accuracy, timing, or musical correctness
* Lesson completion status
* Coaching feedback
* Musical interpretation metrics
* Audio recordings for evaluation

> **ToolBox must never know how well someone plays.**

---

### Teaching System Internals

* Lesson graphs
* Curriculum sequencing
* Coaching heuristics
* AI prompt traces
* Teaching model parameters

---

### Raw Audio or Musical Content

* Raw performance audio
* MIDI note streams
* Timing traces
* Expressive dynamics

Even anonymized — **not allowed**.

---

## Telemetry Structure (Abstract Schema)

All telemetry payloads MUST conform to the following structure:

```json
{
  "schema_version": "v1",
  "emitted_at_utc": "2026-01-10T17:32:00Z",
  "instrument_id": "sg-physical-unit-id",
  "manufacturing_batch_id": "tb-batch-xxxx",
  "telemetry_category": "hardware_performance | utilization | environment | lifecycle",
  "metrics": {
    "metric_name": {
      "value": 123,
      "unit": "count | hours | celsius | ratio",
      "aggregation": "sum | avg | max | bucket"
    }
  }
}
```

### Required Properties

* No free-form text fields
* No nested arbitrary objects
* All metrics must be numerically aggregatable

---

## Identity & Correlation Rules

### Allowed Correlation Keys

* Manufacturing batch ID
* Design revision ID
* Hardware SKU
* Component lot

### Forbidden Correlation Keys

* Player ID
* Account ID
* Lesson ID
* Session ID
* Musical content ID

---

## Data Flow Direction (One-Way)

```
Smart Guitar  ──►  ToolBox
```

There is **no reverse telemetry**.

ToolBox **must not** push:

* Coaching adjustments
* Teaching suggestions
* Player feedback
* Lesson changes

---

## Enforcement

### Mandatory Gates

1. **Schema validation gate** (blocking)
2. **Forbidden-field scan** (blocking)
3. **Aggregation verification** (blocking)
4. **Correlation key whitelist** (blocking)

### Auditability

All telemetry ingested by ToolBox must be:

* Logged with schema hash
* Traceable to a contract version
* Replayable for audit

---

## Architectural Rationale (Why This Exists)

This boundary ensures:

* ToolBox remains a **manufacturing intelligence system**
* Smart Guitar remains a **teaching system**
* AI coaching IP is protected
* Manufacturing insights compound without privacy risk
* No future refactor can "accidentally" blend domains

---

## One-Sentence Summary

> **Smart Guitar teaches musicians.
> ToolBox builds instruments.
> Telemetry may improve the build — never the lesson.**

---

## Related Contracts

* `TOOLBOX_SMART_GUITAR_BOUNDARY_CONTRACT_v1.md`
* `ART_STUDIO_SCOPE_GOVERNANCE_v1.md`
* `SECURITY_TRUST_BOUNDARY_CONTRACT_v1.md`
* `RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md`

---

## Revision History

| Version | Date       | Notes                     |
| ------: | ---------- | ------------------------- |
|    v1.0 | 2026-01-10 | Initial normative release |
