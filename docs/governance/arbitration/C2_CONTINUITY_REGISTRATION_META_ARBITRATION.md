# C2 Continuity — Registration Meta-Arbitration

**Packet type:** Meta-arbitration (reconciles an internal contradiction between C2-B and C2-C/C2-D)
**Phase:** C2 (Semantic Reconciliation) — propose-not-decide
**State:** `RATIFIED` — **Option C (document-only) ratified 2026-06-23. The continuity decision dissolved.**
**Date:** 2026-06-23
**Depends on:** nothing upstream — this *precedes* the continuity A/B/C choice and, as ratified, dissolved it.

> **RESOLVED 2026-06-23 — Option C (document-only).** The C2-B↔C2-C/C2-D contradiction is resolved toward
> the document-only posture: "continuity" requires **no canonical registration**, C2-C/C2-D were **never
> truly blocked**, and the only continuity follow-up is lightweight warning comments (the namespace-conflation
> *guard* remains constitutionally deferred to C3). C2's remaining loose end reduces to **the single
> geometry-origin decision.**

> **Why this packet exists.** Before "ratify continuity Option A/B/C" can be a coherent ask, the corpus
> contradicts itself about whether a decision exists at all. This packet surfaces that meta-question,
> analyzes which posture is more constitutionally consistent, and tees it up for ratification. It
> deliberately does **not** decide (C2 prepares; the human assigns authority).

---

## 1. Semantic surface under arbitration

**Does the term "continuity" require canonical registration, or is documented operational separation
sufficient?** This is logically *prior* to the C2-B Option A/B/C choice: if documented separation
governs, the continuity decision **dissolves** (no ratification needed) and C2-C/C2-D are not actually
blocked.

The three distinct meanings (frozen from C2-B findings):

| Domain | Identifier | Meaning | Location |
|---|---|---|---|
| Manufacturing | `ContinuityLevel` G0/G1/G2 | surface tangency at shell junctions | `cam/topology_builder/contracts.py:16` |
| Governance | `continuity_graph` / `continuity_integrity` | review-chain ancestry/integrity | `cam/translator_governance_continuity_graph.py` |
| Vectorizer | `continuity_score` | vertex density per unit perimeter (jaggedness) | `services/contour_scoring.py:507` |

---

## 2. The contradiction (frozen evidence)

| Source | Posture | Quote |
|---|---|---|
| **C2-B** `C2-B_TOPOLOGY_NAMESPACE_ARBITRATION_FINDINGS.md` | **Register** | "Decision Required … Recommended: Option B — register manufacturing + governance continuity canonically, rename `continuity_score`→`smoothness_score`." |
| **C2-C / C2-D** `packets/C2_CONTINUITY_ARBITRATION_PACKET_003.md` §12, §16; `..._004.md` | **Document-only** | "This Packet Does NOT Require Ratification"; "No Tier 3 Escalations (Human Arbitration)." |

These disagree not on detail but on **whether a ratification decision exists.** That is the meta-question.

This is the *same class* of self-contradiction the sizing already found (`GOVERNANCE_STACK_INDEX_V1`
says "C2 — Not Started" while the approved corpus is decomposition-complete). **Reconciling C2's
internal contradictions is part of closing C2**; this is the load-bearing instance because it
determines whether a decision is owed.

---

## 3. The two postures (and how the A/B/C options map)

- **Posture R — Register** (C2-B). Add canonical ontology entries so the namespace is formally
  protected. Sub-options:
  - **Option A** — register all three (`manufacturing_continuity`, `governance_continuity`,
    `contour_continuity`) with `prohibited_reinterpretations`. **Zero code change** (registry entries +
    optional guard comments).
  - **Option B** — register the two with external surface (manufacturing, governance); **rename** the
    pure-internal vectorizer field `continuity_score`→`smoothness_score` so it stops colliding on the
    word at its source.
- **Posture D — Document-only** (C2-C/C2-D) = **Option C**. Add warning comments; rely on the existing
  operational separation; defer any enforcement to C3. **The continuity decision dissolves.**

---

## 4. Constitutional consistency analysis

**Argument that registration is framework-aligned (not premature convergence):**
Registering *three distinct* terms, each with `prohibited_reinterpretations`, is **decomposition-
codifying, not federating** — it nails down that the three are separate and must not be confused. That
is the framework's stated goal ("the greatest danger is premature semantic convergence caused by
superficially similar terminology"). Registration here *prevents* convergence; it does not cause it.

**The load-bearing argument for registration — the topology asymmetry:**
The canonical registry **already registers `topology`** (with `prohibited_reinterpretations`), and the
framework treats the registry as *its chosen mechanism* for namespace protection. Leaving `continuity`
unregistered while `topology` is registered is an **internal inconsistency in how the framework applies
its own mechanism.** Consistency argues for registering continuity the same way.

**The argument for document-only (Posture D):**
The three meanings are **already operationally separated** — C2-B itself records "NO DIRECT PATH" on
every confusion surface. The risk is **latent/future** ("nothing *prevents* future conflation"), not an
active defect. Constitutionally, guarding against future conflation is **C3 enforcement** (import
guards, CI), which is explicitly deferred. So "document the separation, defer the guard to C3" is
internally consistent with the C2/C3 split — at the cost of the topology asymmetry above.

**On the Option-B rename specifically (correcting an earlier assumption):**
`continuity_score` is **internal — 8 sites, 1 file (`services/contour_scoring.py`), zero external
readers.** It is therefore **not** the cross-repo coordinated-rename the convergence discipline
("additive fields only; no coordinated renames") guards against — that discipline targets cross-repo
vocabulary, and this is a local single-file refactor. So Option B's rename is **not disfavored** on
convergence grounds; it is a low-risk local change that removes the most-confusable collision at its
source.

---

## 5. Blast radius per option (grounded)

| Option | Code change | Blast radius |
|---|---|---|
| **A** register all three | none | 3 additive canonical-registry entries + optional guard comments. 0 code. |
| **B** register two + rename | rename `continuity_score`→`smoothness_score` | **8 sites, 1 file** (`services/contour_scoring.py`, 0 external readers) + 2 registry entries. |
| **C** document-only | none | warning comments only. 0 registry, 0 code. **Decision dissolves.** |

---

## 6. Recommendation (proposal — NOT a decision)

**Lean: Posture R (register).** The deciding constitutional argument is the **topology asymmetry** —
the framework's own protection mechanism is the registry, topology uses it, and continuity should be
handled consistently rather than left to prose. Between the register variants, **Option B is marginally
preferable**: it eliminates the most-confusable term (`continuity_score`) at its source for a genuinely
small, internal, zero-external-reader cost, and grounding showed the rename is *not* barred by the
convergence discipline. **Option A** is the conservative alternative (zero code, keeps the confusable
name but registers it).

**Posture D (Option C, document-only) is a legitimate lighter-touch** and dissolves the decision —
defensible if you judge the latent (non-active) risk not worth three registry entries, accepting the
topology asymmetry and leaving the guard to C3.

This is **your call** (Terminal 1 / sole authority). The recommendation prepares it; it does not make it.

---

## 7. Ratification

> **DECISION (ratified by the human authority):** **Option C — document-only.**
>
> - [ ] **A** — register all three, no rename
> - [ ] **B** — register manufacturing + governance; rename `continuity_score`→`smoothness_score`
> - [x] **C** — document-only (decision dissolves; no registration)
>
> Ratified by: Ross (Terminal 1 / sole authority)  Date: 2026-06-23
>
> **Rationale on record:** the three meanings are already operationally separated (NO DIRECT PATH); the
> risk is latent, not active; namespace-conflation enforcement is constitutionally C3's job. Warning
> comments are the enactment; the guard is deferred to C3. The continuity decision therefore **dissolves** —
> no canonical registration is owed, and C2-C/C2-D were never truly blocked.

---

## 8. What this unblocks

- If **A or B**: the continuity namespace is settled → C2-C provenance decomposition unblocks → C2-D
  unblocks. The continuity decision is **made** (small, per §5).
- If **C**: the continuity decision **dissolves** → C2-C/C2-D were never truly blocked → C2's remaining
  loose end reduces to **the single geometry-origin decision** (which still needs its own packet —
  separate work).
- Either way, this packet's ratification **clears the first gate** and resolves the C2-B↔C2-C/D
  contradiction, converting "governance positionally-on-hold" one concrete step toward "governance
  closed."

---

*C2 Continuity Registration Meta-Arbitration — DRAFT, ARBITRATION_READY, awaiting ratification.*
*Prepared under C2 propose-not-decide discipline: this artifact prepares a decision; it does not make one.*
