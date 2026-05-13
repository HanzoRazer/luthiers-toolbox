# Machine Output Authorization Model

**CAM Dev Order 7A — Future Execution Approval Semantics**

**Status:** Planning Only — No Implementation  
**Date:** 2026-05-13

---

## Purpose

This document defines the future authorization model for machine output generation. It specifies how approvals flow from governance through execution, and how authorization remains isolated from automation.

**This is architecture planning, not implementation.**

---

## Authorization Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LIFECYCLE APPROVAL (6M)                           │
│                                                                      │
│  Authority: Promotion decisions                                      │
│  Scope: Operation maturity, registry state                          │
│  Grantor: Human via promotion evidence review                       │
│  Effect: Operation advances maturity level                          │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   TRANSLATION APPROVAL (Future)                      │
│                                                                      │
│  Authority: Export Object → Translation Artifact                    │
│  Scope: Single Export Object, single translator                     │
│  Grantor: Human via translation request review                      │
│  Effect: Translation artifact may be produced                       │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  POSTPROCESSING APPROVAL (Future)                    │
│                                                                      │
│  Authority: Translation Artifact → Machine Output                   │
│  Scope: Single artifact, single postprocessor, single machine       │
│  Grantor: Human via postprocessing request review                   │
│  Effect: Machine output may be produced                             │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   EXECUTION APPROVAL (Future)                        │
│                                                                      │
│  Authority: Machine Output → Physical Execution                     │
│  Scope: Single output package, single machine, single run           │
│  Grantor: Human via execution request review                        │
│  Effect: Machine may execute the output                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Approval Types

### Lifecycle Approval (Current)

```
Established in 6L/6M.
Concerns operation maturity, not execution.
```

| Aspect | Value |
|--------|-------|
| Subject | CAM operation |
| Action | Maturity promotion |
| Evidence | Promotion evidence bundle |
| Grantor | Human |
| Duration | Permanent (registry change) |

### Translation Approval (Future)

```
Approval to convert Export Object to translation artifact.
```

| Aspect | Value |
|--------|-------|
| Subject | Specific Export Object |
| Action | Translation to specific format |
| Evidence | Validated Export Object + compatibility report |
| Grantor | Human |
| Duration | Single use |

### Postprocessing Approval (Future)

```
Approval to convert translation artifact to machine output.
```

| Aspect | Value |
|--------|-------|
| Subject | Specific translation artifact |
| Action | Postprocessing to specific controller |
| Evidence | Translation artifact + machine profile |
| Grantor | Human |
| Duration | Single use |

### Execution Approval (Future)

```
Approval to run machine output on physical machine.
```

| Aspect | Value |
|--------|-------|
| Subject | Specific machine output package |
| Action | Physical machine execution |
| Evidence | Machine output + safety checklist |
| Grantor | Human (machine operator) |
| Duration | Single run |

---

## Authorization Token Concept

### Token Structure (Conceptual)

```python
# PLANNING ONLY — Not implemented

@dataclass
class AuthorizationToken:
    """
    Authorization token for execution actions.
    
    Tokens are:
    - Immutable once created
    - Single-use
    - Scoped to specific action
    - Human-granted
    - Auditable
    """
    
    token_id: str              # Unique identifier
    token_type: str            # "translation", "postprocessing", "execution"
    
    # Subject
    subject_id: str            # Export Object ID, artifact ID, etc.
    subject_hash: str          # Content hash of subject
    
    # Action scope
    action: str                # Specific action authorized
    target: str                # Target translator/postprocessor/machine
    
    # Authorization chain
    grantor: str               # Human identifier
    granted_at: datetime       # UTC timestamp
    expires_at: datetime       # Expiration (optional)
    
    # Provenance
    prerequisite_token: str    # Previous token in chain (if any)
    evidence_hash: str         # Hash of evidence used for decision
    
    # State
    used: bool = False         # Token has been consumed
    used_at: datetime = None   # When consumed
```

### Token Chain

```
Lifecycle Approval (6M)
         │
         ▼
Translation Token ←── [Human grants]
         │
         ▼
Postprocessing Token ←── [Human grants]
         │
         ▼
Execution Token ←── [Human grants]
```

Each token requires the prior token in the chain to exist and be valid.

---

## Authorization Constraints

### What Tokens Can Authorize

| Token Type | Authorizes |
|------------|------------|
| Translation | Producing translation artifact from Export Object |
| Postprocessing | Producing machine output from translation artifact |
| Execution | Running machine output on physical machine |

### What Tokens Cannot Authorize

| Action | Reason |
|--------|--------|
| Registry modification | Governance domain, not execution |
| Policy exception | Governance domain |
| Future executions | Single-use constraint |
| Different subjects | Scope constraint |
| Self-extension | Automation prohibition |

---

## Human Approval Requirements

### Translation Approval Prerequisites

Before human can approve translation:

1. Export Object exists and is validated (green gate)
2. Translator compatibility validated (green/yellow gate)
3. Lifecycle policy allows translation
4. Promotion evidence shows operation is mature enough

### Postprocessing Approval Prerequisites

Before human can approve postprocessing:

1. Translation artifact exists
2. Translation artifact has valid provenance
3. Machine profile validated
4. Postprocessor compatibility validated

### Execution Approval Prerequisites

Before human can approve execution:

1. Machine output package exists
2. Machine output has valid provenance chain
3. Machine safety requirements met
4. Operator qualified for machine

---

## Non-Automatable Actions

The following actions MUST remain human-initiated:

| Action | Reason |
|--------|--------|
| Granting translation approval | Safety-critical decision |
| Granting postprocessing approval | Machine-specific decision |
| Granting execution approval | Physical safety decision |
| Extending token scope | Prevents scope creep |
| Creating approval policies | Meta-governance |
| Bypassing validation | Never permitted |

---

## Revocation Model

### Token Revocation (Future)

Tokens may be revoked:
- By original grantor
- By admin override
- By system on expiration
- By system on security event

Revocation effects:
- Token marked invalid
- Dependent tokens invalidated
- Artifacts remain (with revocation audit)
- Re-approval required for new execution

### Artifact Revocation

Artifacts themselves are NOT revoked. Instead:
- Artifact marked with revocation notice
- Provenance updated to show revocation
- Further use requires new approval chain

---

## Signing Concept (Future)

### Digital Signature Model

```python
# PLANNING ONLY

@dataclass
class SignedApproval:
    """
    Cryptographically signed approval.
    
    Future implementation may require:
    - PKI infrastructure
    - Hardware security modules
    - Certificate chain validation
    """
    
    approval_content: bytes     # Canonical approval data
    signature: bytes            # Digital signature
    signer_certificate: str     # Certificate reference
    signing_time: datetime      # Timestamp
    signature_algorithm: str    # Algorithm identifier
```

Signing provides:
- Non-repudiation (signer cannot deny approval)
- Integrity (approval cannot be modified)
- Authentication (signer identity verified)

---

## Authorization Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                      GOVERNANCE PHASE                             │
│                                                                   │
│  Export Object ──→ Validation ──→ Policy Check ──→ Lifecycle     │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                   TRANSLATION APPROVAL                            │
│                                                                   │
│  Human reviews:                                                   │
│  - Export Object validation report                                │
│  - Translator compatibility report                                │
│  - Operation maturity status                                      │
│                                                                   │
│  Human decides: [APPROVE] or [REJECT]                            │
│                                                                   │
│  If approved: Translation token issued                           │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                   TRANSLATOR EXECUTION                            │
│                                                                   │
│  Translator consumes token                                        │
│  Translator produces artifact                                     │
│  Artifact includes provenance                                     │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                 POSTPROCESSING APPROVAL                           │
│                                                                   │
│  Human reviews:                                                   │
│  - Translation artifact                                           │
│  - Machine profile                                                │
│  - Postprocessor compatibility                                    │
│                                                                   │
│  Human decides: [APPROVE] or [REJECT]                            │
│                                                                   │
│  If approved: Postprocessing token issued                        │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                  POSTPROCESSOR EXECUTION                          │
│                                                                   │
│  Postprocessor consumes token                                     │
│  Postprocessor produces machine output                            │
│  Output includes full provenance chain                           │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    EXECUTION APPROVAL                             │
│                                                                   │
│  Machine operator reviews:                                        │
│  - Machine output package                                         │
│  - Provenance chain                                               │
│  - Safety checklist                                               │
│                                                                   │
│  Operator decides: [RUN] or [ABORT]                              │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Security Considerations

### Token Security

- Tokens must be unforgeable
- Tokens must be tamper-evident
- Token storage must be secure
- Token transmission must be encrypted

### Approval Audit

- All approvals logged
- All rejections logged
- Approval evidence preserved
- Audit trail immutable

---

## Related Documents

- `TRANSLATOR_EXECUTION_ARCHITECTURE.md` — Runtime topology
- `EXECUTION_BOUNDARY_POLICY.md` — Governance vs execution isolation
- `TRANSLATOR_SECURITY_MODEL.md` — Security requirements

---

*Machine Output Authorization Model — CAM 7A — 2026-05-13*
