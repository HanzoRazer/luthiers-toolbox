# Translator Artifact Lifecycle

**CAM Dev Order 7A — Execution Artifact Flow**

**Status:** Planning Only — No Implementation  
**Date:** 2026-05-13

---

## Purpose

This document defines the lifecycle of artifacts produced by translators and postprocessors. It specifies provenance requirements, immutability expectations, and audit lineage for execution artifacts.

**This is architecture planning, not implementation.**

---

## Artifact Chain

```
┌─────────────────────────────────────────────────────────────────────┐
│                      EXPORT OBJECT                                   │
│                                                                      │
│  Canonical manufacturing representation                              │
│  Owned by: Governance                                                │
│  Lifecycle: Governed by 6A-6M architecture                         │
│  Persistence: RMOS artifact (export_object_json)                    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    [Translation Approval]
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   TRANSLATION ARTIFACT                               │
│                                                                      │
│  Format-specific serialization of Export Object                     │
│  Examples: DXF file, SVG file, neutral toolpath package            │
│  Owned by: Execution layer                                          │
│  Persistence: RMOS artifact (translation_artifact_*)               │
└─────────────────────────────────────────────────────────────────────┘
                              │
                  [Postprocessing Approval]
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  POSTPROCESSED ARTIFACT                              │
│                                                                      │
│  Controller-specific machine output                                  │
│  Examples: GRBL G-code, FANUC G-code, ShopBot file                 │
│  Owned by: Execution layer                                          │
│  Persistence: RMOS artifact (postprocessed_artifact_*)             │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    [Execution Approval]
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  MACHINE OUTPUT PACKAGE                              │
│                                                                      │
│  Complete execution bundle with provenance                          │
│  Contains: Machine output + authorization chain + metadata          │
│  Owned by: Execution layer                                          │
│  Persistence: RMOS artifact (machine_output_package_json)          │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    [Machine Execution]
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  EXECUTION RECORD                                    │
│                                                                      │
│  Audit trail of physical execution                                  │
│  Contains: What ran, when, outcome, operator                        │
│  Owned by: Execution audit                                          │
│  Persistence: RMOS artifact (execution_record_json)                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Artifact Types

### Translation Artifacts

| Type | Format | Extension | Content |
|------|--------|-----------|---------|
| DXF Geometry | DXF R12/R2000 | `.dxf` | 2D geometry |
| SVG Geometry | SVG 1.1 | `.svg` | Scalable vectors |
| Neutral Toolpath | JSON | `.toolpath.json` | Machine-neutral paths |
| STEP Geometry | STEP AP214 | `.step` | 3D geometry |

### Postprocessed Artifacts

| Type | Controller | Extension | Content |
|------|------------|-----------|---------|
| GRBL G-code | GRBL 1.1 | `.nc` | G-code dialect |
| FANUC G-code | FANUC | `.nc` | G-code dialect |
| ShopBot | ShopBot | `.sbp` | Vendor format |
| Carbide3D | Carbide Motion | `.nc` | Vendor dialect |

### Package Artifacts

| Type | Purpose | Format |
|------|---------|--------|
| Machine Output Package | Complete execution bundle | JSON wrapper |
| Execution Record | Audit of machine run | JSON |

---

## Provenance Model

### Provenance Requirements

Every execution artifact MUST include:

```python
# PLANNING ONLY

@dataclass
class ArtifactProvenance:
    """
    Required provenance for all execution artifacts.
    """
    
    # Identity
    artifact_id: str              # Unique identifier
    artifact_type: str            # "translation", "postprocessed", etc.
    
    # Content integrity
    content_hash: str             # SHA256 of artifact content
    content_bytes: int            # Size in bytes
    
    # Source chain
    source_artifact_id: str       # Parent artifact ID
    source_artifact_hash: str     # Parent content hash
    
    # For translation artifacts
    export_object_id: str         # Source Export Object
    export_object_hash: str       # Export Object hash at translation time
    
    # Authorization
    authorization_token_id: str   # Approval token that permitted this
    
    # Creation context
    created_by: str               # Translator/postprocessor ID
    created_at: datetime          # UTC timestamp
    
    # Additional metadata
    format_version: str           # Output format version
    deterministic: bool           # Whether output is deterministic
```

### Provenance Chain Integrity

```
Export Object (hash: abc123)
    │
    └── Translation Artifact (source_hash: abc123, hash: def456)
            │
            └── Postprocessed Artifact (source_hash: def456, hash: ghi789)
                    │
                    └── Machine Output Package (source_hash: ghi789)
```

Each artifact's `source_hash` must match the `content_hash` of its parent.

---

## RMOS Integration

### Artifact Kind Mapping

| Artifact | RMOS Kind |
|----------|-----------|
| Export Object | `export_object_json` |
| Translation (DXF) | `translation_artifact_dxf` |
| Translation (SVG) | `translation_artifact_svg` |
| Translation (Toolpath) | `translation_artifact_toolpath` |
| Postprocessed (GRBL) | `postprocessed_artifact_grbl` |
| Postprocessed (FANUC) | `postprocessed_artifact_fanuc` |
| Machine Output Package | `machine_output_package_json` |
| Execution Record | `execution_record_json` |

### Persistence Flow

```
Translator produces artifact
    │
    ▼
Content hash computed
    │
    ▼
Provenance assembled
    │
    ▼
RMOS artifact persisted (content-addressed)
    │
    ▼
Artifact reference returned
```

---

## Immutability Expectations

### Immutable Once Persisted

```
Execution artifacts are WRITE-ONCE.
Once persisted to RMOS, content cannot change.
```

If a correction is needed:
1. Create new artifact with corrected content
2. New artifact gets new hash
3. Original artifact remains (with deprecation flag)
4. Audit trail shows both artifacts

### Hash Guarantees

```
Content hash serves as:
- Integrity verification
- Content-addressable storage key
- Provenance chain link
- Audit reference
```

Same content → same hash (deterministic).

---

## Artifact Lifecycle States

```
┌──────────────┐
│   CREATED    │ ← Artifact produced by translator/postprocessor
└──────────────┘
       │
       ▼
┌──────────────┐
│  PERSISTED   │ ← Stored in RMOS with provenance
└──────────────┘
       │
       ▼
┌──────────────┐
│   APPROVED   │ ← Human approved for next stage
└──────────────┘
       │
       ▼
┌──────────────┐
│    USED      │ ← Consumed by next stage or machine
└──────────────┘
       │
       ├──────────────────────┐
       ▼                      ▼
┌──────────────┐      ┌──────────────┐
│  COMPLETED   │      │   REVOKED    │
│  (normal)    │      │  (exception) │
└──────────────┘      └──────────────┘
```

---

## Audit Lineage

### Forward Lineage (What did this artifact produce?)

```python
# PLANNING ONLY

def get_forward_lineage(artifact_id: str) -> List[str]:
    """Find all artifacts derived from this artifact."""
    pass
```

### Backward Lineage (What is this artifact's origin?)

```python
# PLANNING ONLY

def get_backward_lineage(artifact_id: str) -> List[str]:
    """Trace artifact back to source Export Object."""
    pass
```

### Full Provenance Query

```python
# PLANNING ONLY

def get_full_provenance_chain(artifact_id: str) -> ProvenanceChain:
    """
    Return complete provenance from Export Object to artifact.
    
    Includes:
    - All intermediate artifacts
    - All authorization tokens
    - All timestamps
    - All content hashes
    """
    pass
```

---

## Artifact Verification

### Hash Verification

```python
# PLANNING ONLY

def verify_artifact_integrity(artifact_id: str) -> bool:
    """
    Verify artifact content matches stored hash.
    
    Returns True if:
    - Content hash matches stored hash
    - Provenance chain is valid
    - Source artifact hashes match
    """
    pass
```

### Provenance Verification

```python
# PLANNING ONLY

def verify_provenance_chain(artifact_id: str) -> VerificationResult:
    """
    Verify complete provenance chain integrity.
    
    Checks:
    - Each artifact's source_hash matches parent's content_hash
    - All authorization tokens valid
    - No gaps in chain
    - Root is valid Export Object
    """
    pass
```

---

## Artifact Retention

### Retention Policy (Conceptual)

| Artifact Type | Retention |
|---------------|-----------|
| Export Object | Permanent |
| Translation Artifact | Until superseded |
| Postprocessed Artifact | Project lifetime |
| Machine Output Package | Project lifetime |
| Execution Record | Permanent (audit) |

### Cleanup Rules

- Artifacts with dependent artifacts cannot be deleted
- Audit records never deleted
- Export Objects never deleted
- Orphaned artifacts may be archived

---

## DXF Artifact Specifics

### DXF as Translation Artifact

```
Export Object
    │
    ▼
DXF Translator (future)
    │
    └── Calls dxf_compat internally
    │
    ▼
DXF Translation Artifact
    │
    ├── Content: DXF file bytes
    ├── Format: R12 or R2000
    ├── Provenance: Links to Export Object
    └── Kind: translation_artifact_dxf
```

### DXF Is Not Canonical

The DXF artifact is a serialization, not the truth:

| Aspect | Export Object | DXF Artifact |
|--------|---------------|--------------|
| Role | Canonical | Derived |
| Authority | Source of truth | Interchange format |
| Mutability | Governed | Immutable |
| Geometry | Abstract | Serialized |

---

## G-code Artifact Specifics

### G-code as Postprocessed Artifact

```
Neutral Toolpath (translation artifact)
    │
    ▼
GRBL Postprocessor
    │
    ▼
GRBL G-code Artifact
    │
    ├── Content: G-code text
    ├── Dialect: grbl_1.1
    ├── Provenance: Links to toolpath + Export Object
    └── Kind: postprocessed_artifact_grbl
```

---

## Related Documents

- `TRANSLATOR_EXECUTION_ARCHITECTURE.md` — Runtime topology
- `MACHINE_OUTPUT_AUTHORIZATION_MODEL.md` — Approval semantics
- `EXECUTION_CAPABILITY_REGISTRY_MODEL.md` — Capability declarations

---

*Translator Artifact Lifecycle — CAM 7A — 2026-05-13*
