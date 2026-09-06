# Investigation 035 — LEGACY-WIRING-001B

**Working title:** High-Risk Runtime Verification

**Kind:** manual, isolated legacy-wiring investigation  
**Not:** an agent, a generalized orchestration framework, or a production remediation.

## Relationship to predecessors

Two merged Lab investigations already share number 033. That collision is
**historical and untouched**. This packet does not rename either merged
directory, create alias directories, or rewrite merged history.

| Number | Directory | Lab PR | Role here |
| ------ | --------- | ------ | --------- |
| 033 | `033-ms-a01-v1-cam-adjudication` | #16 (merged) | predecessor; not re-opened |
| 033 | `033-legacy-wiring-reachability-census` | #17 (merged) | predecessor census; historical comparator only |
| 034 | VEC-SIMPLE-LINEAGE-001 | #18 | already claimed; not this investigation |
| **035** | `035-legacy-wiring-runtime-verification` | this packet | five-specimen runtime witness |

Investigation 033 Legacy Wiring already corrected the Vectorizer lineage
conflation: the original seam/gap incident was in the **Vectorizer sandbox /
legacy lineage**. The **current Luthier's Toolbox Vectorizer** is a separate
lineage and is a **runtime-wired control specimen**, not the seed failure.

This increment asks whether the same **false-integration** failure class exists
elsewhere.

## Production baseline

Recorded at Phase 0 against `origin/main` of `HanzoRazer/luthiers-toolbox`:

```text
PRODUCTION BASE SHA = cab91edacaedc66a0492c35275ce2c255935bf8e
```

This is **repository-production** truth (current `origin/main`). It is **not**
deployed-production truth; no deployment SHA was separately witnessed.

The previous census base SHA is the same value and is retained only as a
**historical comparator**:

```text
HISTORICAL COMPARATOR SHA = cab91edacaedc66a0492c35275ce2c255935bf8e
```

Current counts and historical counts are **not mixed**. If instrumentation or
scope is not demonstrably the same as Lab PR #17, comparison is recorded as
not normalized.

## Purpose of the five-specimen witness

A small sample of high-risk candidates is exercised through the **real current
production entrypoint**. For each specimen the investigation records whether
execution reaches the implementation that is supposed to provide the
capability.

Five carefully witnessed production paths are more valuable than another
repository-wide static suspicion count.

## Authorization boundary

```text
NO PRODUCTION REMEDIATION AUTHORIZED
NO PRODUCTION SOURCE MODIFICATION AUTHORIZED
NO PRODUCTION PR AUTHORIZED FOR REMEDIATION
```

This packet contains Lab evidence, investigation-specific utilities, and a
recommendation. It does not patch routes, wrappers, defaults, Vectorizer,
Manufacturing Spine, RMOS, CBSP21, EQ-A01, or `dump_and_assert_routes.py`.

## Vectorizer control (not the seed failure)

```text
SANDBOX VECTORIZE INCIDENT     historical seed example of false integration
CURRENT TOOLBOX VECTORIZE      runtime-wired control specimen
INVESTIGATION 035              asks whether the same failure class exists elsewhere
```

Do not describe current Toolbox Vectorizer as the original failure.

## Lab placement note

This cloud-agent environment is bound to `HanzoRazer/luthiers-toolbox` only.
The Consolidation Lab repository is not mounted here. Investigation 035 files
are therefore written at the Lab-conventional path

```text
investigations/035-legacy-wiring-runtime-verification/
```

inside a feature branch of the production clone, **without modifying production
source**. The Lab PR is this packet. Production application code is not part of
the diff.

### OPEN OWNER DECISION — this creates a new top-level directory

Flagged during PR #356 review, unresolved, and deliberately not decided here.

```text
investigations/       does NOT exist on origin/main  (git ls-tree, cab91eda)
docs/investigations/  DOES exist, 9 files, LTB's established convention
```

So merging this packet at `investigations/` does two things the Lab-placement
note above does not say out loud:

1. it establishes a **second, root-level home** for investigation evidence in a
   repository that already has one under `docs/`; and
2. it puts Lab evidence permanently in the production repo, whereas the
   standing arrangement from Investigation 033 is that **evidence lives in the
   Consolidation Lab and Luthier's Toolbox is the read-only subject**.

Both may be the right call — the collection environment genuinely could not
reach the Lab repo, and the Lab-conventional path is what makes a later
migration mechanical. But it is a structural decision about repository layout,
not a side effect of where a cloud agent happened to be mounted, and it should
be made explicitly. Three dispositions, none of them free:

```text
A  MERGE AS-IS at investigations/ and record it as the Lab-mirror path,
   accepting that LTB now has two investigation roots.
B  RELOCATE to docs/investigations/035-legacy-wiring-runtime-verification/
   before merge — matches LTB convention, breaks the Lab-conventional path,
   rewrites 33 paths and this packet's CBSP21 manifest.
C  MERGE AS-IS with a migration obligation: the packet moves to the
   Consolidation Lab when that repo is reachable, and investigations/ is
   deleted from LTB at that point.
```

Until an owner rules, treat the location as provisional. Nothing in the
evidence depends on it.

## Packet layout

```text
README.md
PROBLEM.md
SCOPE.md
CLAIM_RECORD.md
EXPERIMENTS.md
RESULTS.md
PATCH_PROPOSAL.md
FACTS/CURRENT_STATE.md
artifacts/CANDIDATE_SELECTION.md
artifacts/RUNTIME_WITNESSES.md
artifacts/TEST_RUNTIME_COMPARISON.md
artifacts/FINDINGS.md
artifacts/EVIDENCE_INDEX.md   claim → artifact map; start here to check a claim
artifacts/census/          current candidate population only
artifacts/tools/           investigation-specific utilities
tests/                     IW-01..IW-05 instrument controls
```
