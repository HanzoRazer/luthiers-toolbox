# Security Policy — Luthier's ToolBox / RMOS

## Core Security Principle

RMOS is the **execution authority**. AI is **advisory only**.

Any code that can produce manufacturing outputs (toolpaths, G-code, run artifacts) must be:
- deterministic
- server-side authoritative
- governed by feasibility + approval + audit trails

## Trust Boundaries

### Authoritative Zone (Production)
- `services/api/app/rmos/**`
- Determines feasibility and safety policy outcomes
- Controls workflow approvals
- Generates toolpaths
- Persists immutable run artifacts

### Advisory Zone (AI Sandbox)
- `services/api/app/_experimental/ai/**`
- `services/api/app/_experimental/ai_graphics/**`
- May propose candidates and parameter changes
- Must not approve, generate toolpaths, or persist run artifacts
- Must not import RMOS internals

## Non-Negotiable Invariants

1. **Server-side feasibility enforcement is mandatory**
   - Client feasibility is ignored/stripped
   - Feasibility must be recomputed on the server for any manufacturing action

2. **Toolpaths require explicit APPROVED workflow state**
   - `/api/workflow/approve` is required before `/api/rmos/toolpaths`

3. **Immutable run artifact persistence**
   - Every approval attempt and toolpath generation is recorded
   - Blocked approvals are recorded as well (audit-grade behavior)

## Automated Enforcement

The repository uses CI and local pre-commit hooks to enforce governance:
- AI sandbox import boundary checks
- Forbidden calls from AI sandbox into RMOS authority paths
- Forbidden write-path patterns for AI sandbox code

Violations must fail CI and should fail locally before commit.

## Directory Contract

| Zone | Path | Authority |
|------|------|-----------|
| Authoritative | `services/api/app/rmos/**` | Execution authority |
| Advisory | `services/api/app/_experimental/ai/**` | Proposal only |
| Advisory | `services/api/app/_experimental/ai_graphics/**` | Proposal only |
| Routing | `services/api/app/routers/**` | Thin wiring only |

## Reporting Issues

- Security issues should be reported privately to repository maintainers.
- Do not publish exploit details in public issues until mitigated.
