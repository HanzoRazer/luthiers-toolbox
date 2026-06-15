# Sprint scope — CI-RED-015 three-way characterization

**Type:** thin execution-discipline note for one focused grounding pass. Not a handoff.
**Surface of record:** the `CI-RED-015` row in `SPRINTS.md`. **See that row for the
current count and cluster spread — do not restate the numbers here** (single source of
truth; they must not drift between the ledger and this note).

## What this pass is (and is not)

The `#120` workflow unmask made `API Tests` *report a current number* — it did **not**
reveal a hidden crisis. This is a **focused refresh of an already-open item (015)**, not
an emergency. But it **is core-path** (design → solve → persist → G-code), so it is worth
grounding properly: if any cluster is a **real regression** (not a stale test), it touches
the actual MVP claim — unlike the orthogonal api-verify surface (name, don't chase).

Energy: focused, not panicked, but real.

## Method — per cluster, classify three-way

For each cluster in the CI-RED-015 row, take a representative failing test, read the
**actual assertion vs. actual behavior** (run it, read the diff — don't infer), and put the
cluster in exactly one bucket:

- **stale-test** — kernel/behavior correct, test asserts old behavior → fix = update the
  assertion (like 015-E). 
- **real-regression** — the unmask revealed a genuine break → fix = the code.
- **another mask** — env/setup failure (DB, fixture, install) masquerading as a test fail,
  like CI-RED-019/020 → fix = the harness, then re-run to get the real verdict.

One PR per cluster (or per cause-class), smallest-first.

## The one discipline that decides this pass

**Do NOT assume stale-because-015-E-was.** 015-E is *one verified-stale 2-test sub-cluster*;
it is not evidence about the others. Each cluster gets grounded against reality on its own.
The whole reason this note exists separate from the row is to carry this forward so the next
session doesn't anchor on 015-E and wave the rest through as "probably stale."

## Core-path flag — ground these first

Clusters that touch persist/lifecycle are where a real regression would touch the MVP claim,
so they get grounded **before** the orthogonal ones:

- **RMOS-persistence** — e.g. `test_persist_true_returns_persisted_true`, `artifact_has_sha256`
  (these look like real behavior, not assertion drift — exactly the case to verify, not assume).
- **lifecycle-policy** — `test_lifecycle_policy_engine` (orchestrator/policy flow).
- **geometry-authority** — `test_geometry_authority_references` (canonical/derived reference rules).

Body-solver/IBG, body-geometry-repair, morphology-spine, and the singletons follow.

## Adjacent masks (separate turns, not this pass)

- **CI-RED-019** — routing-truth behind the setuptools editable-build flat-layout error
  (cause known: add `[tool.setuptools.packages.find]`; fixing *unmasks*, does not close).
- **CI-RED-020** — api-smoke server-unreachable (app starts, HTTP never ready; cause TBD).

Keep these distinct from the 015 characterization — they are harness/mask issues, not the
test-suite reconciliation.
