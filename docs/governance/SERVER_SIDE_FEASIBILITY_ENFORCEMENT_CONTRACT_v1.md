# Server-Side Feasibility Enforcement Contract

**Document Type:** Canonical Governance Specification
**Version:** 1.0
**Effective Date:** December 17, 2025
**Status:** AUTHORITATIVE
**Precedence:** PRIMARY - All implementations MUST conform

---

## Governance Statement

This document establishes the **canonical contract** for server-side feasibility enforcement within the Luthier's ToolBox RMOS (Rosette Manufacturing Orchestration System). All toolpath generation implementations MUST conform to the specifications herein. Deviation from this contract is prohibited without formal amendment through the governance review process.

### Governing Principles

1. **Zero Client Trust** — Client-provided feasibility is ALWAYS ignored
2. **Server Authority** — Only server-computed feasibility is authoritative
3. **Single Source of Truth** — One feasibility engine, used by both API and internal calls
4. **Non-Bypassable Safety** — RED/UNKNOWN risk levels cannot be circumvented
5. **Audit Trail** — All decisions include authoritative feasibility for traceability

### Subordinate Documents

All implementation documents, guides, and code comments related to feasibility enforcement are subordinate to this contract.

---

## Scope

| In Scope | Out of Scope |
|----------|--------------|
| Toolpath generation safety gates | Client-side UI feasibility display |
| Server-side feasibility recomputation | Advisory-only feasibility warnings |
| Safety decision enforcement | SKU-specific override policies |
| Audit trail requirements | Historical migration strategies |

---

## Architectural Rule (MANDATORY)

```
+---------------------------------------------------------------------+
|                                                                     |
|   Client feasibility  =  ADVISORY ONLY (ignored by server)          |
|   Server feasibility  =  AUTHORITATIVE (enforced always)            |
|                                                                     |
+---------------------------------------------------------------------+
```

Even if the client sends a feasibility block:
- It is **IGNORED**
- It is **RECOMPUTED** server-side
- Discrepancies are **DETECTABLE and AUDITABLE**

---

## Behavioral Requirements

| Requirement | Before (Prohibited) | After (Required) |
|-------------|---------------------|------------------|
| Feasibility Source | `/api/rmos/toolpaths` trusts client | Client feasibility stripped and ignored |
| Safety Computation | Depends on client honesty | Recomputed server-side every time |
| RED Handling | Could be bypassed by lying client | RED/UNKNOWN = hard stop, non-bypassable |
| Audit Trail | No record of decisions | Authoritative feasibility in all responses |

---

## Implementation Architecture

### File Structure (Reference)

```
services/api/app/rmos/
+-- services/
|   +-- feasibility_service.py     # Internal feasibility adapter
+-- api/
|   +-- rmos_feasibility_router.py # Public API + internal function
|   +-- rmos_toolpaths_router.py   # Server-side enforcement
+-- tests/
    +-- test_toolpaths_server_side_feasibility.py  # Trust boundary tests
```

### Internal Feasibility Service Contract

```python
def recompute_feasibility_for_toolpaths(
    *,
    tool_id: str,
    req: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Server-side authoritative feasibility computation.

    INVARIANTS:
    - Ignores any client-provided feasibility
    - Uses the same engine as /api/rmos/feasibility
    - Returns the full feasibility payload
    - NEVER returns None or empty dict
    """
```

### Toolpaths Router Contract

```python
@router.post("/api/rmos/toolpaths")
def rmos_toolpaths(req: Dict[str, Any]):
    """
    MANDATORY FLOW:
    1. Strip client feasibility
    2. Recompute feasibility server-side
    3. Evaluate safety decision
    4. Block if RED/UNKNOWN (HTTP 409)
    5. Include authoritative_feasibility in all responses
    """
```

---

## Data Flow Specification

```
+-----------------------------------------------------------------------------+
|                     SERVER-SIDE ENFORCEMENT FLOW                             |
+-----------------------------------------------------------------------------+
|                                                                             |
|   Client Request                                                            |
|   +-------------------------------------+                                   |
|   | {                                   |                                   |
|   |   "tool_id": "saw:blade_v1",        |                                   |
|   |   "feasibility": {...} <-- IGNORED  |                                   |
|   |   "blade": {...},                   |                                   |
|   |   "material": "maple"               |                                   |
|   | }                                   |                                   |
|   +------------------+------------------+                                   |
|                      |                                                      |
|                      v                                                      |
|   +-------------------------------------+                                   |
|   |  Strip client feasibility           |                                   |
|   |  clean_req.pop("feasibility")       |                                   |
|   +------------------+------------------+                                   |
|                      |                                                      |
|                      v                                                      |
|   +-------------------------------------+                                   |
|   |  RECOMPUTE FEASIBILITY              |                                   |
|   |  (Same engine as /api/feasibility)  |                                   |
|   +------------------+------------------+                                   |
|                      |                                                      |
|                      v                                                      |
|   +-------------------------------------+                                   |
|   |  SAFETY DECISION                    |                                   |
|   |                                     |                                   |
|   |  risk_level = RED?                  |                                   |
|   |       |                             |                                   |
|   |       +-- YES --> HTTP 409 (blocked)|                                   |
|   |       |          + authoritative    |                                   |
|   |       |            feasibility      |                                   |
|   |       |                             |                                   |
|   |       +-- NO  --> Generate toolpaths|                                   |
|   +-------------------------------------+                                   |
|                                                                             |
+-----------------------------------------------------------------------------+
```

---

## Safety Policy Specification

### Risk Level Handling

| Risk Level | Action | HTTP Status | Override Allowed |
|------------|--------|-------------|------------------|
| GREEN | Proceed | 200 | N/A |
| YELLOW | Proceed with warnings | 200 | N/A |
| RED | Block | 409 | NO |
| UNKNOWN | Block (treat as RED) | 409 | NO |

### Blocked Response Schema

```json
{
  "detail": {
    "message": "Toolpath generation blocked by server-side safety policy.",
    "decision": {
      "risk_level": "RED",
      "score": 25,
      "block_reason": "Rim speed exceeds safe threshold",
      "warnings": [],
      "details": {}
    },
    "mode": "saw",
    "tool_id": "saw:kerf_cut_v1",
    "authoritative_feasibility": { ... }
  }
}
```

---

## Test Requirements

All implementations MUST include tests proving:

1. **Client feasibility is ignored** — GREEN client claim + RED server params = BLOCKED
2. **Server feasibility is authoritative** — Decision matches server computation
3. **Audit trail is complete** — `authoritative_feasibility` present in all responses

---

## Strategic Benefits

### Immediate

| Benefit | Description |
|---------|-------------|
| **Certifiable** | Safety decisions are server-controlled, auditable |
| **Non-bypassable** | Malicious clients cannot skip safety checks |
| **Consistent** | One feasibility engine, one source of truth |
| **Debuggable** | Authoritative feasibility included in error responses |

### Future SKU Support

| Tier | Behavior |
|------|----------|
| **Hobbyist** | Feasibility advisory only (warnings shown, not enforced) |
| **Pro** | YELLOW allowed with acknowledgment, RED blocked |
| **Enterprise** | RED never overridable, all decisions logged and signed |

---

## Compliance Verification

Implementations are compliant when:

- [ ] Client feasibility is stripped before processing
- [ ] Feasibility is recomputed server-side for every toolpath request
- [ ] RED/UNKNOWN risk levels result in HTTP 409
- [ ] All responses include `authoritative_feasibility`
- [ ] Tests prove client feasibility is ignored

---

## Amendment Process

Changes to this contract require:
1. Formal proposal with justification
2. Security review for safety implications
3. Version increment (v1.0 -> v1.1 or v2.0)
4. Update to all subordinate implementations

---

## Summary

This contract encodes a fundamental engineering principle:

> **The system that generates the action must also verify the safety.**

By recomputing feasibility server-side for every toolpath request, we guarantee:
1. No toolpath is generated without a safety check
2. The safety check uses authoritative (not client-provided) data
3. Every blocked request includes evidence for why it was blocked
4. Future audits can trace decisions to their source

**This is the difference between a CAM system and a manufacturing decision engine.**

---

## Document Control

| Field | Value |
|-------|-------|
| Document ID | GOV-SSFE-001 |
| Classification | Internal - Engineering |
| Owner | RMOS Architecture Team |
| Last Review | December 17, 2025 |
| Next Review | March 17, 2026 |
