# CANONICAL GOVERNANCE INDEX

**Status:** Authoritative  
**Scope:** System-wide governance for Luthier’s ToolBox, RMOS, CNC Saw Lab, and AI subsystems  
**Audience:** Core developers, maintainers, safety reviewers, and future contributors

---

## Purpose

This document defines the **authoritative governance documents** for the project.

Governance documents listed here:
- describe **non-negotiable rules**
- reflect **behavior already enforced in code**
- override advisory, draft, or legacy documentation

If a rule is not enforced in code, it **does not belong** in the canonical set.

---

## Governance Model (At a Glance)

- **Authority is explicit**: RMOS executes; AI advises; UI requests
- **Safety is enforced**: not optional, not client-trusted
- **Execution is auditable**: every run produces immutable artifacts
- **Drift is managed**: contracts, invariants, and boundaries are locked

---

## Canonical Governance Documents

The following documents are **binding** and define how the system must behave.

### 1. `GOVERNANCE.md`
**Role:** Constitutional governance  
**Defines:**
- authority boundaries
- execution responsibility
- enforcement philosophy

This is the root document. All other governance policies derive from it.

---

### 2. `AI_SANDBOX_GOVERNANCE.md`
**Role:** AI authority containment  
**Defines:**
- advisory-only AI behavior
- sandbox boundaries (`_experimental/`)
- promotion rules for AI subsystems
- enforcement via CI and pre-commit hooks

AI may propose.  
RMOS decides.

---

### 3. `CNC_SAW_LAB_SAFETY_GOVERNANCE.md`
**Role:** Physical safety enforcement  
**Defines:**
- hard stop conditions
- unsafe execution prevention
- safety invariants for CNC operations

Safety violations block execution by design.

---

### 4. `RMOS_2.0_Specification.md`
**Role:** System execution specification  
**Defines:**
- workflow state machine
- sequencing rules
- feasibility → approval → execution order
- artifact generation requirements

This specification is normative and enforced.

---

### 5. `Tool_Library_Spec.md`
**Role:** Tooling authority  
**Defines:**
- tool identity
- dimensional correctness
- constraints that affect feasibility and CAM

Tool definitions are execution-critical.

---

### 6. `VALUE_ADDED_CODING_POLICY.md`
**Role:** Engineering discipline policy  
**Defines:**
- criteria for adding or retaining code
- prevention of feature sprawl
- consolidation-first engineering behavior

Code must increase system value to exist.

---

## Advisory Governance Documents (Not Binding)

The following documents are **intentionally not canonical**.
They provide guidance, direction, or future intent but are not yet enforced everywhere.

- `AI_SANDBOX_GOVERNANCE_v 2.0.md`
- `OpenAI_Provider_Contract.md`
- `GLOBAL_GRAPHICS_INGESTION_STANDARD.md`
- `ROSETTE_DESIGNER_REDESIGN_SPEC.md`
- `SPECIALTY_MODULES_QUICKSTART.md`

These documents may be promoted once:
- their rules are fully enforced in code
- overlap with canonical documents is resolved
- a single source of truth exists

---

## Archived Governance Documents

The following documents are retained for **historical context only**.
They must not be treated as current policy.

- `MM_5_ULTRA_FRAGILITY_POLICY_QUICKREF.md`
- `LEGACY_ARCHIVE_POLICY.md`

---

## Promotion Rule

A document may move from **Advisory → Canonical** only if:

1. The behavior it describes is enforced in code
2. There is no competing or overlapping canonical document
3. Enforcement mechanisms exist (tests, CI, runtime checks)
4. The document is reviewed for clarity and scope

Documentation follows implementation — not the other way around.

---

## Final Rule

> **If governance is optional, it is not governance.**

This index exists to ensure that governance is:
- visible
- enforceable
- unambiguous
- and durable

---

**Last Updated:** 2025-12-17
