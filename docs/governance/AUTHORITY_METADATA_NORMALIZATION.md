# Authority Metadata Normalization

**Date:** 2026-05-24  
**Status:** Active — Compatibility Layer  
**Sprint:** Cross-Repo Governance Normalization 1A  
**Authority:** Interoperability contract (non-ratifying)

---

## Purpose

AuthorityMetadata is a **compatibility layer, not a replacement** for existing authority models.

It provides additive metadata structure for cross-repo normalization with:

- All fields optional or default-safe
- No authority granting
- Safe cross-repo serialization
- Gradual adoption path

---

## Package Location

Contract-like governance models currently live flat under `app/governance` pending package normalization:

```text
services/api/app/governance/authority_metadata.py
```

---

## Design Principles

### Compatibility Layer

```text
does not replace AuthorityState
does not replace AuthorityStateContainer
does not grant authority
describes authority state only
```

### Safe Defaults

All fields are optional or have safe defaults:

```python
authority_state: Optional[str] = None
epistemic_status: Optional[str] = None
review_state: Optional[ReviewState] = None
lifecycle_state: Optional[LifecycleState] = None
source_repo: SourceRepo = SourceRepo.UNKNOWN
non_authoritative_reason: Optional[str] = None
```

### Built-in Exclusions

Every metadata instance carries explicit authority exclusions:

```python
authority_exclusions: List[str] = [
    "execution authorization",
    "production deployment",
    "governance bypass",
    "review bypass",
    "lifecycle promotion",
    "cross-repo authority propagation",
]
```

---

## Schema

```python
@dataclass
class AuthorityMetadata:
    authority_state: Optional[str]           # from AuthorityState enum
    epistemic_status: Optional[str]          # from EpistemicStatus enum
    review_state: Optional[ReviewState]      # review queue state
    lifecycle_state: Optional[LifecycleState]  # export lifecycle
    source_repo: SourceRepo                  # originating repository
    source_subsystem: Optional[str]          # originating subsystem
    non_authoritative_reason: Optional[str]  # why not authoritative
    authority_exclusions: List[str]          # what this does NOT authorize
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]                 # use metadata["notes"] for notes
```

---

## Enums

### ReviewState

Aligned with luthiers 8E review queue:

```python
class ReviewState(str, Enum):
    NOT_SUBMITTED = "not_submitted"
    PENDING_REVIEW = "pending_review"
    IN_REVIEW = "in_review"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"
    DEFERRED = "deferred"
    REVIEWED = "reviewed"
    REJECTED = "rejected"
```

### LifecycleState

Aligned with luthiers DXF lifecycle:

```python
class LifecycleState(str, Enum):
    R_AND_D_EXCLUDED = "r_and_d_excluded"
    BLOCKED_PROVENANCE = "blocked_provenance"
    DIRECT_SAVE_GAP = "direct_save_gap"
    COMPAT_ONLY = "compat_only"
    LIFECYCLE_GOVERNED = "lifecycle_governed"
```

### SourceRepo

Cross-repo tracking:

```python
class SourceRepo(str, Enum):
    LUTHIERS_TOOLBOX = "luthiers_toolbox"
    TAP_TONE_PI = "tap_tone_pi"
    CAM_ASSIST_BLUEPRINT = "cam_assist_blueprint"
    VECTORIZER_SANDBOX = "vectorizer_sandbox"
    EXTERNAL = "external"
    UNKNOWN = "unknown"
```

---

## Factory Functions

### General luthiers metadata

```python
metadata = create_luthiers_authority_metadata(
    authority_state="advisory_candidate",
    epistemic_status="predicted",
    review_state=ReviewState.PENDING_REVIEW,
    lifecycle_state=LifecycleState.COMPAT_ONLY,
    subsystem="ibg",
)
```

### Vectorizer metadata (always non-authoritative)

```python
metadata = create_vectorizer_authority_metadata(
    subsystem="research",
)
# Returns metadata with:
#   lifecycle_state=R_AND_D_EXCLUDED
#   non_authoritative_reason="R&D excluded — research output only"
```

### IBG metadata (blocked provenance)

```python
metadata = create_ibg_authority_metadata()
# Returns metadata with:
#   lifecycle_state=BLOCKED_PROVENANCE
#   non_authoritative_reason="IBG provenance blocked pending R1 ratification"
```

---

## Key Methods

### Check if authoritative

```python
if metadata.is_authoritative():
    # Proceed with elevated trust
else:
    # Handle non-authoritative case
```

Returns False if:
- `non_authoritative_reason` is set
- `authority_state` is sandbox/advisory/rejected
- `lifecycle_state` is excluded/blocked

### Check if production ready

```python
if metadata.is_production_ready():
    # Safe for production use
```

Returns True only if:
- `lifecycle_state` is `LIFECYCLE_GOVERNED`
- `authority_state` is approved
- `review_state` is `REVIEWED`

### Check if review required

```python
if metadata.requires_review():
    # Route to review queue
```

Returns True if:
- `review_state` indicates pending review
- `authority_state` is sandbox/advisory

---

## Non-Authoritative States

### R&D Excluded (vectorizer-sandbox)

```text
lifecycle_state: R_AND_D_EXCLUDED
non_authoritative_reason: "R&D excluded — research output only"
authority_exclusions: [..., "spine integration", "IBG memory population"]
```

### Blocked Provenance (IBG)

```text
lifecycle_state: BLOCKED_PROVENANCE
non_authoritative_reason: "IBG provenance blocked pending R1 ratification"
authority_exclusions: [..., "DXF export", "IBG memory population"]
```

---

## What This Does NOT Do

| Action | Reason |
|--------|--------|
| Replace AuthorityState | Compatibility layer |
| Replace AuthorityStateContainer | Compatibility layer |
| Grant authority | Describes only |
| Unblock IBG provenance | Requires R1 ratification |
| Promote lifecycle state | Requires governance action |
| Bypass review | Constitutional invariant |

---

## Cross-Repo Exchange

The metadata enables safe cross-repo exchange:

```text
source_repo tracks origin
lifecycle_state preserves constraints
authority_exclusions travel with artifact
non_authoritative_reason explains limitations
```

---

## Tests

```bash
pytest tests/governance/test_authority_metadata.py -v
```

---

## Related Documents

- [CROSS_REPO_CONFIDENCE_ENVELOPE_V1.md](CROSS_REPO_CONFIDENCE_ENVELOPE_V1.md)
- [IBG_PROVENANCE_ATTACHMENT_SPEC.md](IBG_PROVENANCE_ATTACHMENT_SPEC.md)
- [CROSS_REPO_AUTHORITY_CROSSWALK.md](CROSS_REPO_AUTHORITY_CROSSWALK.md)

---

*Authority Metadata Normalization — 2026-05-24*
