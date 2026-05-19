# Translator Security Model

**CAM Dev Order 7A — Execution Isolation and Safety**

**Status:** Planning Only — No Implementation  
**Date:** 2026-05-13

---

## Purpose

This document defines the future security model for translator and postprocessor execution. It specifies sandboxing, isolation, verification, and safety requirements.

**This is architecture planning, not implementation.**

---

## Security Principles

### Principle 1: Least Privilege

```
Execution components receive only the permissions required
for their specific task. No more.
```

### Principle 2: Defense in Depth

```
Multiple security layers. Failure of one layer does not
compromise the system.
```

### Principle 3: Fail Secure

```
On security boundary failure, default to blocking execution,
not permitting it.
```

### Principle 4: Auditability

```
All security-relevant actions are logged and auditable.
```

---

## Isolation Architecture

### Execution Sandbox Model

```
┌─────────────────────────────────────────────────────────────────────┐
│                         HOST SYSTEM                                  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    GOVERNANCE LAYER                             │ │
│  │                                                                 │ │
│  │  Full system access (governed)                                 │ │
│  │  Owns: registries, policy, audit, RMOS                        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                    [Isolation Boundary]                             │
│                              │                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    EXECUTION SANDBOX                            │ │
│  │                                                                 │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │              TRANSLATOR EXECUTION CONTEXT                 │  │ │
│  │  │                                                           │  │ │
│  │  │  Allowed:                                                 │  │ │
│  │  │  - Read Export Object (copy)                             │  │ │
│  │  │  - CPU for computation                                   │  │ │
│  │  │  - Memory (bounded)                                      │  │ │
│  │  │  - Write artifact (to staging)                          │  │ │
│  │  │                                                           │  │ │
│  │  │  Blocked:                                                 │  │ │
│  │  │  - Filesystem access                                     │  │ │
│  │  │  - Network access                                        │  │ │
│  │  │  - Governance state                                      │  │ │
│  │  │  - Other execution contexts                              │  │ │
│  │  │  - System calls (restricted)                             │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Resource Limits

### Memory Limits

| Component | Limit | Rationale |
|-----------|-------|-----------|
| Translator | 256 MB | Sufficient for large geometry |
| Postprocessor | 128 MB | G-code is text-based |
| Total sandbox | 512 MB | Prevents resource exhaustion |

### CPU Limits

| Component | Limit | Rationale |
|-----------|-------|-----------|
| Translator | 60 seconds | Complex geometry timeout |
| Postprocessor | 30 seconds | Postprocessing is simpler |
| Total execution | 120 seconds | Prevents runaway |

### Output Limits

| Artifact | Max Size | Rationale |
|----------|----------|-----------|
| DXF | 50 MB | Large geometry files |
| G-code | 100 MB | Long programs |
| Package | 200 MB | Complete bundle |

---

## Access Control

### What Execution Can Access

| Resource | Access | Notes |
|----------|--------|-------|
| Export Object | Read (copy) | Passed into sandbox |
| Execution context | Read | Authorization, metadata |
| Artifact staging | Write | For output only |
| Logging | Write | Audit trail |

### What Execution Cannot Access

| Resource | Reason |
|----------|--------|
| CAM_OPERATION_REGISTRY | Governance state |
| Policy engine | Governance state |
| Audit ledger | Governance state |
| RMOS directly | Bypass prevention |
| Filesystem | Isolation |
| Network | Isolation |
| Other sandboxes | Isolation |
| System clock (write) | Determinism |
| Random sources | Determinism |

---

## Determinism Requirements

### Why Determinism Matters

```
Same Export Object + Same Translator → Same Artifact

Determinism enables:
- Verification (re-run and compare)
- Caching (same input = cached output)
- Debugging (reproducible issues)
- Audit (recreate historical state)
```

### Determinism Rules

1. **No random values** — Random number generators prohibited
2. **No timestamps in output** — Use provided execution context time
3. **No environmental dependencies** — Cannot read environment variables
4. **Stable iteration order** — Collections must be sorted
5. **Fixed floating point** — Consistent precision handling

### Determinism Verification

```python
# PLANNING ONLY

def verify_determinism(
    translator_id: str,
    export_object: Any,
    iterations: int = 3,
) -> bool:
    """
    Verify translator produces deterministic output.
    
    Runs translator multiple times with same input.
    Compares output hashes.
    """
    pass
```

---

## Artifact Verification

### Pre-Persistence Verification

Before any artifact is persisted:

1. **Format validation** — Artifact is valid for declared format
2. **Size check** — Within limits
3. **Hash computation** — SHA256 computed
4. **Provenance check** — Required fields present
5. **Content scan** — No prohibited patterns

### Prohibited Content Patterns

| Pattern | Reason |
|---------|--------|
| Shell commands | Injection prevention |
| Network URLs | Exfiltration prevention |
| File paths (absolute) | Path traversal prevention |
| Binary blobs (unexpected) | Malware prevention |
| Embedded scripts | Injection prevention |

### Post-Persistence Verification

After persistence:

1. **Read-back hash** — Matches computed hash
2. **Provenance link** — Valid chain to Export Object
3. **Authorization link** — Valid approval token

---

## Authorization Verification

### Token Verification

```python
# PLANNING ONLY

def verify_authorization_token(
    token: AuthorizationToken,
    export_object_id: str,
    translator_id: str,
) -> VerificationResult:
    """
    Verify authorization token is valid for operation.
    
    Checks:
    - Token exists
    - Token not expired
    - Token not revoked
    - Token subject matches export_object_id
    - Token action matches translator_id
    - Token not already used (single-use)
    """
    pass
```

### Authorization Chain Verification

```python
# PLANNING ONLY

def verify_authorization_chain(artifact_id: str) -> bool:
    """
    Verify complete authorization chain for artifact.
    
    Traces from artifact back to lifecycle approval.
    Verifies each link has valid authorization.
    """
    pass
```

---

## Signature Model (Future)

### Digital Signatures

```python
# PLANNING ONLY

@dataclass
class SignedArtifact:
    """
    Cryptographically signed execution artifact.
    """
    
    artifact_content: bytes
    content_hash: str
    
    # Signature
    signature: bytes
    signature_algorithm: str  # e.g., "ed25519"
    
    # Signer
    signer_id: str            # Translator/postprocessor ID
    signer_public_key: str    # Public key (for verification)
    
    # Timestamp
    signed_at: datetime
    timestamp_signature: bytes  # Optional timestamp authority signature
```

### Verification Process

```
1. Verify signature against content hash
2. Verify signer public key is registered
3. Verify signer is authorized translator/postprocessor
4. Verify timestamp (optional)
```

---

## Security Boundaries

### Trust Boundaries

```
┌────────────────────────────────────────────────────────────────┐
│                    FULLY TRUSTED                                │
│                                                                 │
│  - Governance code                                             │
│  - Policy engine                                               │
│  - Audit system                                                │
│  - RMOS core                                                   │
└────────────────────────────────────────────────────────────────┘
                              │
                    [Trust Boundary]
                              │
┌────────────────────────────────────────────────────────────────┐
│                    PARTIALLY TRUSTED                            │
│                                                                 │
│  - Registered translators (sandboxed)                          │
│  - Registered postprocessors (sandboxed)                       │
│  - Built-in plugins                                            │
└────────────────────────────────────────────────────────────────┘
                              │
                    [Trust Boundary]
                              │
┌────────────────────────────────────────────────────────────────┐
│                      UNTRUSTED                                  │
│                                                                 │
│  - Third-party plugins (future, if allowed)                   │
│  - External services                                           │
│  - Network resources                                           │
└────────────────────────────────────────────────────────────────┘
```

### Boundary Enforcement

| Boundary Crossing | Enforcement |
|-------------------|-------------|
| Governance → Execution | Sandbox initialization |
| Execution → Governance | API validation + rejection |
| Execution → Filesystem | Blocked at sandbox level |
| Execution → Network | Blocked at sandbox level |

---

## Incident Response

### Security Events

| Event | Severity | Response |
|-------|----------|----------|
| Sandbox escape attempt | Critical | Terminate, alert, audit |
| Unauthorized state access | Critical | Reject, alert, audit |
| Resource limit exceeded | Medium | Terminate, retry allowed |
| Invalid artifact format | Low | Reject, log |
| Determinism failure | Medium | Alert, investigate |

### Audit Trail Requirements

All security events must capture:
- Timestamp
- Event type
- Translator/postprocessor ID
- Export Object ID
- Authorization token ID
- Outcome (success/failure)
- Error details (if any)

---

## Future Considerations

### Hardware Security Modules (HSM)

For high-assurance scenarios:
- Signing keys stored in HSM
- Signature operations performed in HSM
- Key extraction prevented

### Remote Attestation

For distributed execution:
- Verify execution environment integrity
- Verify translator code integrity
- Verify sandbox configuration

### Code Signing

For translator plugins:
- Translator code signed by author
- Signature verified before loading
- Revocation list checked

---

## Related Documents

- `TRANSLATOR_EXECUTION_ARCHITECTURE.md` — Runtime topology
- `EXECUTION_BOUNDARY_POLICY.md` — Governance vs execution isolation
- `MACHINE_OUTPUT_AUTHORIZATION_MODEL.md` — Approval semantics

---

*Translator Security Model — CAM 7A — 2026-05-13*
