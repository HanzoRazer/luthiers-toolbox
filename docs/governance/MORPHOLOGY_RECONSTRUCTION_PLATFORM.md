# Morphology Reconstruction Platform (MRP)

**Status:** ACTIVE GOVERNANCE FRAMEWORK  
**Effective:** 2026-05-11 — **amended 2026-08-29**

---

> ## AMENDMENT — 2026-08-29 (descriptive-capture correction)
>
> **APPROVED BY:** Ross (repository owner), 2026-08-29, by direct instruction in session.
>
> **Defect corrected:** *descriptive capture*. Statements of what the system did on
> 2026-05-11 were written into canonical documents in the imperative register, which
> converted present-tense observations into permanent prohibitions on future work. No
> decision was ever recorded barring the capability; the prohibition arose from document
> formatting, not from an argument.
>
> **Diagnostic signature:** a prohibition whose reason column restates the prohibition.
> Compare the Math Authority section of `IBG_ROLE_DEFINITION.md`, which cites Sevy
> (*American Lutherie* #58), Mottola (#78), and a plus/minus 0.01 inch tolerance. The
> corrected rows cited nothing.
>
> **Rule applied:** permanent prohibition -> present-tense description.
>
> **What did NOT change:** every sourced authority row. IBG math remains `LOCKED` under
> Sevy/Mottola. Image processing and photo input remain out of scope. The Blueprint Reader
> MVP protections stand. Human oversight is preserved: its authority is relocated from a
> tool to a role, not removed.
>
> **This amendment authorizes nothing.** It removes a governance bar that was never
> deliberately raised. Any implementation requires its own Dev Order.
>
> **Lines changed in this file:** 46 and 111 of the 2026-05-11 text, the only two lines in
> this document carrying the defect.
>
> | Was | Now |
> |---|---|
> | `\| BOE \| Human correction/editor \| AUTHORITATIVE \|` | `HUMAN-IN-THE-LOOP` |
> | `- Bypass BOE authority` | `- Bypass required human review` |
>
> **Contradiction resolved:** line 45 assigns the IBG Morphology Layer *Shape intelligence /
> EVOLUTIONARY*, while `IBG_ROLE_DEFINITION.md` barred IBG from learning. Both were effective
> 2026-05-11. **Resolved in favour of line 45**, which stands unchanged; the companion
> document is corrected to match.

---

## Purpose

Govern the evolution of the Blueprint Reader + IBG ecosystem from rendered/vectorized DXF generation into instrument-aware CAD reconstruction and manufacturing intelligence.

---

## Core Principle

```
Protect the production MVP while evolving morphology intelligence in isolated, governed layers.

The MVP must never be destabilized by experimental learning systems.
```

---

## Platform Topology

```
Image/PDF
  → Blueprint Reader MVP
  → partial DXF geometry
  → IBG Morphology Reconstruction
  → Solved Body Model
  → Export Object
  → Translators
  → STEP / DXF / SVG / CAM
```

---

## Canonical Layer Definitions

| Layer | Responsibility | Governance |
|-------|----------------|------------|
| Blueprint Reader MVP | Deterministic extraction | PROTECTED |
| DXF Translator Layer | Serialization compatibility | STABILIZED |
| IBG Morphology Layer | Shape intelligence | EVOLUTIONARY |
| BOE | Human correction/editor | HUMAN-IN-THE-LOOP |
| Export Object | Canonical manufacturing representation | DXF-AGNOSTIC |
| Translators | Serialization targets | ISOLATED |
| CAM/Postprocessors | Machine execution | DOWNSTREAM |

**On the BOE row (amended 2026-08-29).** BOE is the surface through which a human exercises
correction authority. The authority belongs to the human review step, not to the tool. Any
approval surface satisfying the same requirement — an alternative editor, an API
confirmation, a customer review step, a threshold-based auto-accept where one has been
explicitly approved — satisfies this row. Nothing in this framework requires that human
review occur in a particular application.

---

## Protected Systems

See: `BLUEPRINT_READER_PROTECTION_RULES.md`

| System | Protection Level |
|--------|------------------|
| Blueprint Reader MVP | LOCKED |
| restored_baseline mode | LOCKED |
| DXF compliance layer | LOCKED |
| IBG math engine | LOCKED |
| Sevy/Mottola calculations | LOCKED |

---

## Canonical Objective

**Current:**
```
Rendered DXF → morphology reconstruction → Solved Body Model → DXF/JSON export
```

**Future:**
```
Rendered DXF → morphology reconstruction → CAD-grade parametric body model → STEP/CAD export
```

**NOT:**
```
Photo → AI → STEP (bypassing reconstruction)
```

The DXF/rendered geometry remains intermediate reconstruction material.

---

## Export Governance

The Export Object layer remains DXF-agnostic:
- No DXF field names
- No DXF entity assumptions
- No translator semantics
- No machine-controller assumptions

DXF becomes: `Export Object → DXF Translator`

---

## AI Governance Rules

### Forbidden Behaviors

Agents may NOT:
- Redefine "done"
- Replace MVP modes
- Silently alter extraction behavior
- Remove restored_baseline
- Collapse representation into DXF
- Inject AI mutation into production path
- Bypass required human review
- Optimize without regression verification

### Mandatory Requirements

All morphology-intelligence work must:
- Preserve deterministic MVP
- Operate behind feature flags
- Maintain regression corpus
- Produce audit logs
- Preserve rollback paths
- Document confidence levels

---

## Framing Rule

**Correct:**
```
Instrument-aware morphology reconstruction and CAD preparation.
```

**Incorrect:**
```
AI-generated CAD.
```

---

## Related Governance Documents

- `IBG_ROLE_DEFINITION.md`
- `BLUEPRINT_READER_PROTECTION_RULES.md`
- `MORPHOLOGY_CORPUS_STANDARD.md`
- `THREE_LOOP_ARCHITECTURE_REFRAMED.md`
- `SPRINT_NAMESPACE_STANDARD.md`

---

*Canonical governance framework for the Morphology Reconstruction Platform.*
