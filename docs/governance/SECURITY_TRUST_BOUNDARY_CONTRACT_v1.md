# Security Trust Boundary Contract

**Document Type:** Canonical Governance Specification
**Version:** 1.0
**Effective Date:** December 16, 2025
**Status:** AUTHORITATIVE
**Classification:** SECURITY-CRITICAL
**Source:** Vision Engine Bundle - SECURITY.md

---

## Governance Statement

This document establishes the **canonical security trust boundaries** for the Luthier's ToolBox platform. These boundaries are **non-negotiable security requirements** that protect manufacturing integrity, audit trails, and system safety.

### Core Security Principle

> **RMOS is the execution authority. AI is advisory only.**

Any code that can produce manufacturing outputs (toolpaths, G-code, run artifacts) MUST be:
- **Deterministic** — Same inputs produce same outputs
- **Server-side authoritative** — Client cannot override
- **Governed** — Feasibility + Approval + Audit trails required

---

## Trust Boundary Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                        TRUST BOUNDARY DIAGRAM                               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    AUTHORITATIVE ZONE                                 │  │
│  │                    (Production / Execution)                           │  │
│  │                                                                       │  │
│  │   services/api/app/rmos/                                              │  │
│  │   ├── feasibility/    → Safety scoring (CRITICAL)                     │  │
│  │   ├── workflow/       → State machine control (CRITICAL)              │  │
│  │   ├── toolpaths/      → G-code generation (CRITICAL)                  │  │
│  │   ├── runs/           → Immutable artifact storage (CRITICAL)         │  │
│  │   ├── engines/        → Version registry                              │  │
│  │   └── gates/          → Policy enforcement                            │  │
│  │                                                                       │  │
│  │   SECURITY LEVEL: CRITICAL                                            │  │
│  │   AUTHORITY: Full execution rights                                    │  │
│  │   AUDIT: All actions logged immutably                                 │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                   │                                         │
│                                   │ PUBLIC API ONLY                         │
│                                   │ (No direct imports)                     │
│                                   │ (No internal access)                    │
│                                   ▼                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                      ADVISORY ZONE                                    │  │
│  │                      (AI Sandbox / Experimental)                      │  │
│  │                                                                       │  │
│  │   services/api/app/_experimental/ai/                                  │  │
│  │   services/api/app/_experimental/ai_graphics/                         │  │
│  │                                                                       │  │
│  │   SECURITY LEVEL: RESTRICTED                                          │  │
│  │   AUTHORITY: Propose only, no execution                               │  │
│  │   AUDIT: Suggestions logged, not authoritative                        │  │
│  │                                                                       │  │
│  │   FORBIDDEN:                                                          │  │
│  │   ✗ Import RMOS internals                                             │  │
│  │   ✗ Call authority functions                                          │  │
│  │   ✗ Write to authoritative paths                                      │  │
│  │   ✗ Bypass feasibility checks                                         │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Trust Zones Specification

### Authoritative Zone (Production)

**Path:** `services/api/app/rmos/**`

| Capability | Security Requirement |
|------------|---------------------|
| Feasibility computation | Server-side only, client input stripped |
| Safety policy enforcement | Non-bypassable, deterministic |
| Workflow approvals | Requires GREEN feasibility |
| Toolpath generation | Requires APPROVED workflow state |
| Run artifact persistence | Immutable, content-addressed |

**Access Control:**
- Full read/write to RMOS data stores
- Full execution authority
- Audit logging mandatory

### Advisory Zone (AI Sandbox)

**Path:** `services/api/app/_experimental/ai/**`
**Path:** `services/api/app/_experimental/ai_graphics/**`

| Capability | Security Requirement |
|------------|---------------------|
| Parameter proposals | Data only, no execution |
| Feasibility requests | Via public API only |
| Artifact analysis | Read-only access |
| Image generation | Sandbox storage only |

**Access Control:**
- Read-only to public APIs
- Write to sandbox paths only
- No direct RMOS access
- No authority function calls

---

## Non-Negotiable Security Invariants

### Invariant 1: Server-Side Feasibility Enforcement

```
┌─────────────────────────────────────────────────────────────┐
│                    INVARIANT 1                               │
│           Server-Side Feasibility Enforcement                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Client-provided feasibility is ALWAYS:                     │
│  • Stripped from requests                                   │
│  • Ignored in processing                                    │
│  • Replaced with server-computed values                     │
│                                                             │
│  Feasibility MUST be recomputed server-side for ANY:        │
│  • Workflow approval request                                │
│  • Toolpath generation request                              │
│  • Manufacturing action                                     │
│                                                             │
│  VIOLATION = SECURITY INCIDENT                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Invariant 2: Explicit Approval Requirement

```
┌─────────────────────────────────────────────────────────────┐
│                    INVARIANT 2                               │
│              Explicit Approval Requirement                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Toolpath generation REQUIRES:                              │
│                                                             │
│  1. Valid workflow session                                  │
│  2. Server-computed feasibility = GREEN                     │
│  3. Explicit call to /api/workflow/approve                  │
│  4. Workflow state = APPROVED                               │
│                                                             │
│  Direct toolpath generation is FORBIDDEN.                   │
│  Shortcuts are FORBIDDEN.                                   │
│  State machine bypasses are FORBIDDEN.                      │
│                                                             │
│  VIOLATION = SECURITY INCIDENT                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Invariant 3: Immutable Audit Trail

```
┌─────────────────────────────────────────────────────────────┐
│                    INVARIANT 3                               │
│                 Immutable Audit Trail                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Every approval attempt creates a RunArtifact:              │
│  • Successful approvals → status: "OK"                      │
│  • Blocked approvals → status: "BLOCKED"                    │
│  • Failed approvals → status: "ERROR"                       │
│                                                             │
│  Every toolpath generation creates a RunArtifact:           │
│  • Includes request hash                                    │
│  • Includes output hash                                     │
│  • Includes version stamps                                  │
│                                                             │
│  Artifacts are IMMUTABLE:                                   │
│  • No modification after creation                           │
│  • No deletion                                              │
│  • Content-addressed storage                                │
│                                                             │
│  VIOLATION = SECURITY INCIDENT                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Security Contract

| Zone | Path | Security Level | Authority |
|------|------|----------------|-----------|
| AUTHORITATIVE | `services/api/app/rmos/**` | CRITICAL | Full execution |
| ADVISORY | `services/api/app/_experimental/ai/**` | RESTRICTED | Propose only |
| ADVISORY | `services/api/app/_experimental/ai_graphics/**` | RESTRICTED | Propose only |
| ROUTING | `services/api/app/routers/**` | STANDARD | Thin wiring |
| DATA | `services/api/app/data/runs/**` | CRITICAL | RMOS only |
| DATA | `services/api/app/data/run_attachments/**` | CRITICAL | RMOS only |

---

## Automated Security Enforcement

### CI Pipeline (Mandatory)

| Check | Detects | Action on Violation |
|-------|---------|---------------------|
| Import boundaries | AI → RMOS imports | BLOCK PR |
| Forbidden calls | Authority function calls | BLOCK PR |
| Write paths | Writes to RMOS directories | BLOCK PR |

### Pre-commit Hooks (Recommended)

```bash
pip install pre-commit
pre-commit install
```

Catches violations before code reaches CI.

### Runtime Guards (Mandatory)

| Guard | Location | Action |
|-------|----------|--------|
| State machine | Workflow service | Reject invalid transitions |
| Feasibility gate | Approval endpoint | Block non-GREEN |
| Artifact validator | Run store | Reject malformed artifacts |

---

## Security Incident Classification

| Severity | Description | Examples |
|----------|-------------|----------|
| CRITICAL | Authority bypass | AI generating toolpaths directly |
| CRITICAL | Audit tampering | Modifying run artifacts |
| HIGH | Boundary violation | AI importing RMOS internals |
| HIGH | Feasibility bypass | Client feasibility accepted |
| MEDIUM | Policy violation | Missing version stamps |
| LOW | Configuration issue | Incorrect paths |

---

## Incident Response

### On Detection of Violation

1. **Immediate:** Block PR / deployment
2. **Investigation:** Determine scope and intent
3. **Remediation:** Fix code, update tests
4. **Review:** Post-incident analysis
5. **Prevention:** Update enforcement rules if needed

### Reporting Security Issues

- Report privately to repository maintainers
- Do NOT publish exploit details in public issues
- Use security@[project-domain] for sensitive reports
- Allow 90 days for mitigation before public disclosure

---

## Compliance Matrix

| ID | Security Requirement | Enforcement | Audit |
|----|---------------------|-------------|-------|
| S1 | Server-side feasibility | Runtime guard | Yes |
| S2 | Explicit approval required | State machine | Yes |
| S3 | Immutable audit trail | Run store | Yes |
| S4 | No AI → RMOS imports | CI + pre-commit | Yes |
| S5 | No authority calls from AI | CI + pre-commit | Yes |
| S6 | No AI writes to RMOS paths | CI + pre-commit | Yes |
| S7 | Version stamps on artifacts | Schema validation | Yes |
| S8 | Content-addressed attachments | Hash verification | Yes |

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-16 | Claude Opus 4.5 | Initial canonical specification |

---

## Amendment Process

Security contract amendments require:

1. **Security Review** — Mandatory security team review
2. **Threat Modeling** — Updated threat analysis
3. **Impact Assessment** — Downstream security implications
4. **Maintainer Approval** — Unanimous consent
5. **Audit Log Entry** — Document the change rationale

---

*This document is the authoritative security specification for trust boundaries.*
*Violations are treated as security incidents requiring immediate response.*
