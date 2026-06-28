# GAMS: Geometry Authority Mapping Specification

**Status:** Coordination Spec — operationalizes ratified C2-A distinctions; does NOT decide geometry-origin authority.
**Created:** 2026-06-27
**Scope:** Implementation-boundary classification for geometry-producing, geometry-consuming, and geometry-representing subsystems.
**Authority:** Coordinates with C2-A geometry authority decomposition (`C2A_GEOMETRY_AUTHORITY_PACKET.md`, RATIFIED). Does not supersede, reopen, or ratify C2 governance decisions.

---

## What GAMS Is — And What It Is Not (read first)

GAMS operationalizes the **already-ratified** C2-A geometry authority distinctions
([`../arbitration/C2_GEOMETRY_AUTHORITY_FRAMEWORK.md`](../arbitration/C2_GEOMETRY_AUTHORITY_FRAMEWORK.md))
into a shared vocabulary for implementation and code review. It is coordination, not decree.

GAMS does **not**:

- decide where authoritative body-geometry **originates** — that is the open C2 gate
  (see `C2_GEOMETRY_AUTHORITY_FRAMEWORK.md` §10, "Where does authoritative geometry
  originate?" and "Who owns body outline authority?", both **UNRESOLVED**);
- reopen, rewrite, or re-ratify the C2 arbitration sprint;
- ratify vectorizer output, IBG output, or template/user input as canonical geometry;
- make DXF, SVG, STEP, JSON, or any export format an authority namespace;
- create C3 enforcement, schemas, CI gates, or registry mutations.

If a reader comes away thinking GAMS *answered* the geometry-origin question, the document
has been misread. GAMS classifies; it does not adjudicate. Geometry-origin authority remains
governed by the C2/C3 process and explicit human ratification.

---

## Governing Sentence

GAMS does not decide what geometry is authoritative. It classifies the role a geometry
artifact is playing at an implementation boundary and requires that authority state be
**inherited from provenance**, not inferred from file format, route name, serializer name,
or storage location.

## Foundational Invariant — Two Independent Dimensions

> Operational role and authority state are independent dimensions. No implementation
> artifact acquires authority merely by changing operational role, serialization format,
> storage location, namespace, or routing path. Authority transitions require an explicitly
> governed promotion event.

**Why two axes (do not collapse this back to one).** A single-axis label such as
"Authority Geometry" silently fuses *what an artifact is doing* (its role) with *what
authority it carries* (its state). That fusion is precisely the failure GAMS exists to
prevent: it lets a **role** assertion smuggle in an **authority** claim. By keeping
`geometry_role` and `authority_state` orthogonal, the same DXF serializer can legitimately
carry evidence geometry, candidate geometry, or authority geometry — determined entirely by
the provenance of its source, never by the lane it travels through. A future editor who
"simplifies" the two axes back into one role-name would reintroduce the conflation. The two
axes are the enforcement of the principle in the vocabulary itself.

## Core Rule

**Export format never changes authority state.**

A DXF emitted from evidence geometry remains evidence geometry.
A DXF emitted from promoted authority geometry represents authority geometry.
A DXF emitted from CAM/runtime geometry remains operational geometry.
The serializer does not promote, certify, or canonize the geometry.

Short form:

```text
Geometry authority is inherited from provenance.
DXF is only a carrier.
```

## Purpose

This specification translates ratified C2 geometry authority distinctions into
implementation review language.

It prevents representation formats, export routes, serializer names, or storage locations
from being mistaken for geometry authority. The implementation question is not
"who owns DXF?" The implementation question is "what geometry source is being represented,
and what authority state did that source carry before serialization?"

## Required Implementation Labels

Every geometry handoff should carry two **required** labels:

```text
geometry_role
authority_state
```

and should **recommend** carrying:

```text
authority_source
promotion_mechanism
provenance_id
```

Suggested minimal shape:

```json
{
  "geometry_role": "representation",
  "authority_state": "derived",
  "authority_source": "vectorizer",
  "promotion_mechanism": "human_review",
  "provenance_id": "..."
}
```

The labels may live in request metadata, artifact metadata, provenance records, audit
payloads, or typed models depending on the boundary. The requirement is semantic: a reviewer
must be able to tell what role the geometry is playing and where its authority state came
from. `geometry_role` and `authority_state` are the two load-bearing labels; the
single-axis names below are a human-readable gloss, subordinate to these two.

## Role × Authority Matrix

Role answers "what is it doing?" Authority state answers "what authority does it possess?"
Source answers "where did that state come from?" Promotion answers "what event could change
that state?" These are four separate questions; the matrix keeps them separate.

| Artifact | Operational Role | Authority State | Authority Source | Promotion Mechanism | Implementation Meaning |
|---|---|---|---|---|---|
| Instrument Specification | `specification` | `authority_declared` — **only** for the specific dimensions an approved spec explicitly declares, **where an approved spec exists** | Approved spec record | Governance / spec approval | Canonical **only within the declared approved scope**. This row is **not** a general answer to where body-outline geometry originates — that is the open C2 gate. An undeclared dimension is not authoritative by table entry. |
| MRP Registry | `registry_metadata` | `governance_record` | Registry entry | Separate governance decision | Records ownership/status/governance metadata; does not automatically create geometry. |
| Vectorizer Output | `evidence` | `derived` | Scan/photo extraction | Human review / governed promotion | Evidence geometry; provenance-bearing and non-canonical by default. |
| IBG Output | `evidence` | `governed_evidence` | IBG intake/review package | Human review / promotion gate | Body evidence under intake/review gates; not authority unless promoted. |
| User Template | `candidate` | `proposed` | User declaration | Human review / governed promotion | Candidate authority geometry pending approval. |
| Human Review | `promotion` | `authority_transition` | Review record | Explicit human decision | May promote candidate/evidence into approved authority; the only artifact that legitimately changes authority state. |
| CAM Toolpath / Runtime Geometry | `operational` | `inherited` | Upstream selected geometry | _(none)_ | Manufacturing consumer; adapts representation, never defines geometry truth. |
| DXF Export | `representation` | `inherited` | Source geometry provenance | _(none)_ | Carrier only; serializer does not promote. |
| SVG Export | `representation` | `inherited` | Source geometry provenance | _(none)_ | Display/export carrier only. |
| STEP Export | `representation` | `inherited` | Source geometry provenance | _(none)_ | CAD exchange carrier only. |

### Single-axis gloss (subordinate shorthand)

The earlier prose vocabulary maps onto the two axes as follows. These names are convenient
shorthand for review discussion; the authoritative labels are always the `geometry_role` +
`authority_state` pair, never the fused name.

| Gloss name | `geometry_role` | `authority_state` |
|---|---|---|
| Authority Geometry | `specification` | `authority_declared` (scoped) |
| Authority Metadata | `registry_metadata` | `governance_record` |
| Evidence Geometry | `evidence` | `derived` or `governed_evidence` |
| Candidate Authority Geometry | `candidate` | `proposed` |
| Promotion Authority | `promotion` | `authority_transition` |
| Operational Geometry | `operational` | `inherited` |
| Representation Geometry | `representation` | `inherited` |

## Format-Lane Rule

DXF, SVG, STEP, JSON, and similar outputs are **representation lanes**.

They may carry geometry with different authority states, but the format lane itself does not
own those states.

| Source Geometry | Export Format | Output Role | Resulting Authority State |
|---|---|---|---|
| Vectorizer extraction | DXF | `representation` | `derived` |
| Human-promoted template | DXF | `representation` | `authority_transition` (promoted) |
| CAM runtime contour | DXF | `representation` | `inherited` (upstream operational) |
| IBG candidate package | SVG | `representation` | `governed_evidence` |
| Authority spec geometry | STEP | `representation` | `authority_declared` (scoped) |

## Review Questions

For any geometry handoff or export PR, reviewers should ask:

- What geometry source is being represented?
- What is the `geometry_role` at this boundary?
- What is the `authority_state` inherited from upstream provenance?
- Does the artifact preserve or reference provenance clearly?
- Is any route, serializer, filename, or storage location being used to imply authority?
- Does this change alter canonical geometry, or only representation/operational cleanup?

Reviewers should **not** ask:

- Is this the canonical DXF?
- Is this the authority DXF?
- Does DXF belong to vectorizer, CAM, IBG, or templates?

No component owns DXF as authority. DXF belongs to the representation layer.

## Current DXF Namespace Collision Guidance

Resolve DXF namespace conflicts by **source provenance**, not by assigning DXF ownership.

```text
Nobody owns DXF as authority.
DXF is a representation lane.
The owning question is upstream: what geometry source is being represented?
```

Implementation consequence:

- The same DXF serializer may export authority geometry, evidence geometry, candidate
  authority geometry, or operational geometry.
- Each export must preserve or reference the source authority state.
- The serializer must not promote, certify, or canonize geometry.
- Route names and file paths must not imply authority without provenance.

## Dedupe / Cleanup Classification

Blueprint DXF dedupe or cleanup work (e.g. the flag-gated geometry deduplication merged in
PR #159, default OFF) is classified as:

```text
Operational / representation cleanup
```

Suggested PR language:

```text
This PR modifies post-selection representation cleanup for blueprint DXF export. It does not
establish or modify authoritative body geometry. Its output remains a representation of the
upstream selected geometry and inherits that geometry's authority state.
```

This keeps representation hygiene out of the unresolved authoritative-geometry-origin
question.

## Artifact Consistency Chain

GAMS is one artifact in a chain, each answering a **different** question. None supersedes
another; they compose.

```text
C2
  -> defines authority semantics            (What is authoritative?)

GAMS
  -> maps authority semantics onto          (What role is this artifact playing,
     implementation roles                    and what authority state does it carry?)

Format Flow Matrix
  -> maps implementation interactions       (How does data move safely between formats?)

Canonical DXF Correctness
  -> validates serialization correctness    (Is this representation technically valid?)
```

| Artifact | Question it answers | Repo location |
|---|---|---|
| C2 Geometry Authority Framework | What is authoritative? | [`../arbitration/C2_GEOMETRY_AUTHORITY_FRAMEWORK.md`](../arbitration/C2_GEOMETRY_AUTHORITY_FRAMEWORK.md) |
| GAMS (this doc) | What role + authority state at the boundary? | this file |
| Format Flow Matrix | How does data move safely? | [`../../audit/DXF_FORMAT_FLOW_MATRIX.md`](../../audit/DXF_FORMAT_FLOW_MATRIX.md) |
| Canonical DXF Correctness | Is this representation technically valid? | _adjacent/future artifact — not yet a standalone doc_ |

**GAMS composes with the Format Flow Matrix; it does not conflict with it.** GAMS classifies
**authority state** at a seam (is this geometry derived, governed evidence, declared
authority?). The Format Flow Matrix classifies **format-compatibility risk** at the same seam
(is this R12/R2000 hand-off safe?). The two axes are orthogonal and complementary: a reader
encountering both documents at the same boundary should read GAMS for *authority semantics*
and the matrix for *format safety*. Neither supersedes the other.

The "Canonical DXF Correctness" artifact is described here as an adjacent/future concern
(renderer-independent file-property validity); no standalone document path is asserted for it
yet.

## Alignment With C2

GAMS operationalizes already-established C2 distinctions
(`C2_GEOMETRY_AUTHORITY_FRAMEWORK.md` §5 Propagation Constraints):

- derived geometry is not automatically canonical (RULE 2);
- serialization does not create authority (RULE 3);
- consumption does not imply ownership (RULE 4);
- sandbox/evidence geometry requires governed promotion before it can become authority
  (RULE 5);
- authority visibility is not authority centralization.

GAMS does not reopen the C2 governance sprint. It gives implementation and code review a
shared vocabulary for applying the ratified C2 framework at concrete boundaries.

## Current Maturity

GAMS is **normative guidance for implementation review. It is not yet a mechanically
enforced invariant.** Mechanical enforcement belongs to C3.

Until C3, "authority is inherited from provenance" holds by **reviewer discipline**, not by
gate. The `geometry_role` / `authority_state` labels are a review convention; nothing in the
runtime currently rejects an artifact for omitting or mislabeling them. GAMS should guide
implementation language, PR descriptions, test naming, artifact metadata, and review
checklists without claiming new governance authority.

## Future Enforcement

C3 may later enforce some or all of these requirements through schema, metadata validation,
CI checks, or artifact-contract tests. Until then, GAMS remains a coordination and review
specification.
