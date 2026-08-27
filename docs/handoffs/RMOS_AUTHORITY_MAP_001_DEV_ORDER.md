# RMOS-AUTHORITY-MAP-001 — Manufacturing Authority & Reachability Census

**Status:** STAGE 1 IN PROGRESS (this PR) — stop at the Step-7 checkpoint  
**Date:** 2026-08-27  
**Repository:** HanzoRazer/luthiers-toolbox  
**Base:** `origin/main` at execution time  
**Active lane:** Luthier's Toolbox → Repository Consolidation → RMOS Production Workflow  
**Nature:** one-off read-only RMOS audit / consolidation increment. Production behavior changes are prohibited.

This is **not an agent build**. Grounding Agent v0.1 remains the only agent under trial.

```text
Allowed in this increment:
  one bounded RMOS audit
  one script
  one registry artifact
  one report
  one PR

Not allowed:
  new agent identity or role
  new agent lifecycle or orchestration
  new GitHub workflow for a mapper
  standing autonomous registry service
  production import of the registry
```

---

## Why this increment exists

The RMOS production audit found routes. That is not the same as a trustworthy
capability-level map of design intent, feasibility authority, artifact
generation, persistence, and actual production reachability.

Source-level similarity of “sibling bypasses” was insufficient:

| Initially looked like | Runtime truth |
| --- | --- |
| Adaptive sibling bypass | Authority was consumed; persisted provenance lied |
| Drilling sibling bypass | Emission-stage contract cannot truthfully feed a design-level evaluator |
| Profiling bypass | Route was runtime-dead from a decorator/annotation defect |
| V-carve production bypass | Also runtime-dead before #324; becomes an authority exposure if reachability is restored |
| Retract governed routes | Self-minted GREEN after output generation (now blocked-by-design) |
| Retract plain routes | Completely bypassed RMOS (now blocked-by-design) |

Those are different architectural conditions. Incorrect convergence follows from
an incorrect model of the manufacturing system. This increment records the
model as a reviewed audit artifact. It does not remediate it.

---

## What this is / is not

**This is** a GEN-5-style census: a deterministic inventory script, an inert
JSON registry, a JSON Schema, a human checkpoint report, and tests that the
inventory and registry stay consistent.

**This is not** a second agent, a standing authority-mapping service, or a
runtime consumer. Presence in the registry grants **no** execution authority.

This registry describes manufacturing execution reachability for audit use. It
does **not** replace:

- `docs/governance/CANONICAL_AUTHORITY_MAP.md` (semantic ownership)
- `services/api/app/cam/geometry_authority_registry.py` (7T geometry refs; no machine-output authority)
- `services/api/app/cam/ontology_authority_map.py` (7M vocabulary; `execution_authorized = false`)

---

## Grounding (prerequisite, existing agent only)

Run Grounding Agent v0.1 against the material premises of this order **before**
mutation. Do not change Grounding Agent code to accommodate this increment.

Verified 2026-08-27 against `origin/main` (`GA-TRIAL-0002`, MATCH / PROCEED):

| Premise | Claim | Result |
| --- | --- | --- |
| Grounding v0.1 exists | `tools/grounding_agent/cli.py` at `origin/main` | MATCH |
| Trial ledger exists | `docs/governance/agents/GROUNDING_AGENT_v0.1_TRIAL_LEDGER.md` | MATCH |
| PR #324 merged | GitHub `merged: true` | MATCH |
| `@safety_critical` fix on main | `services/api/app/core/safety.py` | MATCH |
| RMOS feasibility-authority boundary | `feasibility/engine.py`, `feasibility_authority.py` | MATCH |
| Retract convergence exists | `tests/rmos/test_rmos_output_route_convergence.py` | MATCH |
| Adaptive convergence (#322) | GitHub `merged: true` | MATCH |
| Existing RMOS audit | `docs/audit/rmos_prod_audit_001.md` | MATCH |

If Grounding returns STALE / BLOCKED / INSUFFICIENT_EVIDENCE → STOP. Do not
reinterpret STOP as permission to update the handoff while working.

---

## Locked decisions (Stage 1)

**D1 — Ground before acting.** Record the real use in the existing trial ledger.
Do not create a separate ledger PR.

**D2 — Capability, not route, is the primary unit.** Example: retract owns
`/gcode`, `/gcode/download`, `/gcode_governed`, `/gcode/download_governed`.
Grouping is deterministic (seeded path prefixes, then derived path-family).
If grouping cannot be established without a subjective guess, STOP and report
the taxonomy problem.

**D3 — Reachability is empirical.** Source presence is not LIVE. Stage 1 records
`MOUNTED` from the FastAPI route table (recursing `_IncludedRouter`; naive
`app.routes` under-counts). Runtime POST witnesses are withheld until Stage 2
review. Where runtime reachability cannot be established safely:
`reachability = MOUNTED`, `runtime_evidence = NOT_OBTAINED_STAGE_1`.

**D4–D6 — Authority, contract, persistence.** Named in the schema. **Not
populated with conclusions in Stage 1.** All dispositions are `UNKNOWN` /
`INSUFFICIENT_EVIDENCE` until Stage 2 is authorized.

**D7 — Client reachability is evidence, not authority.** Empty in-repo consumers
do not classify a route dead.

**D8 — No production remediation.** This increment may add the registry, schema,
one audit script, tests, audit documentation, and CBSP21 metadata. It may not
modify CAM behavior, feasibility, RMOS decisions, route availability, clients,
persistence, or G-code generation. Nothing production-facing imports the
registry.

**D9 — V-carve post-#324** is a Stage 2 classification. Stage 1 only records
that the production route is mounted.

**D10 — Existing audits are leads, not truth.** Reproduce against current main.

---

## Stage 1 deliverables (this PR)

1. Rewritten Dev Order (this file) — plain audit, not an agent.
2. One script: `scripts/audit/rmos_authority_map.py`  
   Report / validate only. Does not edit the registry. No agent CLI.
3. One schema: `services/api/app/rmos/schemas/manufacturing_authority_registry.schema.json`
4. One inert registry: `services/api/app/rmos/manufacturing_authority_registry.json`  
   Seeded `UNKNOWN` / `INSUFFICIENT_EVIDENCE`.
5. Tests: MAR-001–008 and MAR-021–024 (integrity, discovery completeness, negatives).
6. Checkpoint report: `docs/audit/rmos_manufacturing_authority_map_001.md`
7. `GA-TRIAL-0002` row in the existing Grounding trial ledger.
8. CBSP21 per-PR manifest.
9. Draft PR. Stop.

MAR-009–020 (authority semantics and known-system witnesses) are **Stage 2**,
after owner review of the taxonomy.

---

## Stage 1 stop / checkpoint questions

Report, then wait for review:

- mounted route count (top-level vs walked vs OpenAPI)
- machine-output candidates
- capability count (seeded vs derived)
- registered capabilities
- unexplained emitters
- route aliases
- excluded surfaces
- taxonomy additions requested
- evidence limitations
- runtime witnesses attempted
- runtime witnesses withheld for safety

Stage 2 begins only after review of grouping, vocabularies, and the evidence model.

---

## Stop conditions

STOP rather than improvise if:

1. Grounding returns STOP.
2. Current main materially changes the authority architecture described here.
3. Discovery finds an existing canonical **manufacturing-capability** registry serving this purpose.
4. Capability grouping cannot be established without subjective guesses.
5. A supposedly live route requires stateful/machine-affecting execution to establish reachability (record `NOT_OBTAINED_SAFELY`; do not invent).
6. An evaluator mapping requires fabricated manufacturing inputs (Stage 2).
7. The audit discovers a safety condition requiring immediate remediation — report it; do not patch here.
8. Registry validation would require changing production code.
9. The proposed registry duplicates semantic / geometry / ontology authority (it does not; those maps are a different concern).
10. The tranche begins turning into an RMOS redesign **or a new agent**.

A stop produces evidence and a ruling request — not a workaround.

---

## Definition of Done (full order; Stage 1 is the checkpoint slice)

We can ask “which manufacturing capabilities can actually produce machine
artifacts today, and what authority governs each one?” and get one
evidence-backed answer.

Stage 1 is done when the capability model itself is reviewable: inventory,
grouping, seeded UNKNOWN registry, completeness tests, checkpoint report,
Grounding trial row, no production behavior changed, no new agent created,
no remediation authorized.
