# IBG role-definition inheritance review (2026-08-29)

**Status:** REVIEW INVENTORY — not a rewrite  
**Trigger:** `IBG_ROLE_DEFINITION.md` §8 item 3  
**Scan:** `luthiers-toolbox` at `2646992fc294a904438042d529b939ec6db80662` plus this amendment  
**Method:** grep of `*.md` for the removed 2026-05-11 constraints (`one-way consumer`, `No feedback loop`, `not a learning system`, `Strategy caching (Loop 2)`, `Loop 2 learning`, `IBG is deterministic` as a Loop 2 bar)

This list is for review. It does not amend the cited files. The reading rule in `IBG_ROLE_DEFINITION.md` still applies to "Image Body Generator" titles: same system, no image-processing inference, do not propagate that expansion.

---

## Direct inheritance of "no upstream feedback"

These state the superseded sentence, or the same constraint, as a standing fact about IBG.

| File | Line / locus | Text | How it inherits |
|------|----------------|------|-----------------|
| `docs/handoffs/VECTOR_1B_LOOP2_PROVENANCE_AUDIT.md` | Q5, ~77 | `IBG is a one-way consumer of vectorizer output. No feedback loop exists.` | Closest copy of the removed role-definition sentence. Used to answer "does IBG feed anything back into Blueprint Reader/vectorizer?" A future reader can treat this as a 2026-05-11 *code* finding (no selector existed) and must not treat it as a current IBG *governance* bar. |
| `docs/architecture/IBG_BOE_BOUNDARY_MODEL.md` | Non-Goals, ~219 | `Loop 2 learning (cross-image caching) — IBG is deterministic` | Places Loop 2 outside IBG's boundary because IBG is deterministic. After the amendment, determinism still binds the **solver**; evaluation/selection is in-scope as advisory. This non-goal needs a later edit if the boundary model is used to decline selector work. |

No other `docs/governance/` file besides the amended role definition still contains `one-way consumer` or `feedback loop exists upstream`.

---

## Same bar, weaker wording (Loop 2 / learning out of IBG)

These do not copy the feedback-loop sentence. They still treat Loop 2 / learning as IBG-forbidden.

| File | Locus | Text | Note |
|------|-------|------|------|
| `docs/handoffs/IBG_FUNCTIONAL_CAPABILITY_ASSESSMENT_2026-05-11.md` | §7 table, ~198 | `Strategy caching \| NOT IMPLEMENTED \| No Loop 2 cross-image learning` | Capability snapshot. "NOT IMPLEMENTED" remains factually true. "No Loop 2" as a reason not to implement is the old bar. |
| `docs/handoffs/IBG_2A_BOE_INTEGRATION_BOUNDARY_AUDIT.md` | ~329 | `Learning system: Out of scope (IBG is deterministic math, not ML)` | Closer to the old ML row than to the feedback-loop sentence. Solver determinism still holds; "learning system out of scope" for an **evaluator** does not. |

---

## Cite `IBG_ROLE_DEFINITION.md` without repeating the removed rows

These name the role file as authority. They do not restate "no upstream feedback." After this amendment they inherit the new text automatically.

- `docs/governance/MORPHOLOGY_RECONSTRUCTION_PLATFORM.md`
- `docs/governance/IBG_CONSTITUTIONAL_RUNTIME_FOUNDATION.md`
- `docs/governance/GOVERNANCE_TOPOLOGY_MAP.md`
- `docs/governance/BODY_ISOLATION_ADAPTER_REDESIGN_NOTES.md`
- `docs/handoffs/IBG_2A_BOE_INTEGRATION_BOUNDARY_AUDIT.md` (references list)

---

## Not inheritance of the IBG bar

Loop 2 language that is about the **vectorizer** three-loop sketch, not IBG's one-way-consumer rule:

- `CLAUDE.md` (experimental / sandbox Loop 2)
- `docs/governance/THREE_LOOP_ARCHITECTURE_REFRAMED.md`
- `docs/handoffs/VECTORIZER_GEOMETRY_AUDIT_HANDOFF_2026-05-11.md`
- `docs/handoffs/BLUEPRINT_READER_MVP_BASELINE_2026-05-11.md`
- `docs/AI_CONTINUITY_FRAMEWORK.md`

Those remain under the 2026-05-30 three-loop conflation correction. This amendment does not authorize building `VectorizerAGE` / `AdaptiveExtractor` / `strategy_cache` (role definition §8 item 1).

---

## Namespace table that will keep propagating "Image Body Generator"

Not a feedback-loop inheritor. Left unedited on purpose (not a cleanup sweep). Active tables that still expand IBG as "Image Body Generator":

- `docs/governance/SPRINT_NAMESPACE_STANDARD.md` (IBG row)
- `docs/governance/CAD_SEMANTIC_AUTHORITY_RULES.md`
- `docs/governance/audits/SYSTEM_CONFLATION_AUDIT_2026-06-21.md`
- `docs/handoffs/GOVERNANCE_REMEDIATION_IMPLEMENTATION_GUIDE.md`

Reading rule in the role definition covers these until someone edits them on purpose.

---

*Review only. No selector authorized. Solver math unchanged.*
