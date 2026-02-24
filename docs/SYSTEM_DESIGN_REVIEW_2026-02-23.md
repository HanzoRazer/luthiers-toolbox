# System Design Review: Luthiers-ToolBox

**Date:** 2026-02-23
**Reviewer:** Critical System Design Review (Top 1% Standard)
**Version:** Current main branch
**Codebase Size:** 411,000 LOC

---

## Executive Summary

Luthiers-ToolBox is a full-stack CNC guitar manufacturing platform with authentic domain expertise but significant technical debt. The system demonstrates genuine lutherie knowledge (fret math, chipload physics, multi-post G-code) but has grown beyond sustainable complexity for a single-developer project.

**Overall Score: 5.0/10**

The most critical issue is **reliability** (3/10): 1,719 bare or generic exception handlers in safety-critical code paths create unacceptable risk for a system generating CNC toolpaths.

---

## Assumptions

1. **Single-developer project** targeting small-batch guitar luthiers (1-10 person shops)
2. **Target users**: Skilled craftspeople with moderate technical literacy but not software engineers
3. **CNC machines** in scope are hobbyist/prosumer (GRBL, Mach4) not industrial (Fanuc, Siemens)
4. **Production readiness** is the goal, not prototype/research
5. **Safety-critical context**: Physical manufacturing where bad G-code can damage tools, workpieces, or operators
6. **411K LOC** is representative of actual complexity (not generated/vendored)
7. **Railway.app** is the production deployment target (PaaS, not bare metal)
8. **sg-spec** integration is core, not optional (Smart Guitar ecosystem)

---

## Category Evaluations

### 1. Purpose Clarity

**Score: 6/10**

#### Justification
- **Strength**: Domain expertise is authentic and deep. Fret math, chipload physics, multi-post G-code generation demonstrate genuine lutherie knowledge.
- **Weakness**: The system tries to do too much. It's simultaneously a CAM toolpath generator, a safety orchestration system (RMOS), an art studio, a batch sawing system, an audio analyzer integration layer, and a calculator hub.
- **Evidence**: 1,060 route decorators across 82 routers. This is 3-5x what a focused product should have.

#### Improvements
1. **Define the ONE core job**: Is this a "DXF to G-code converter for guitar parts" or a "complete guitar manufacturing orchestration platform"?
2. **Create a product hierarchy**: Primary (CAM), Secondary (RMOS safety), Tertiary (Art Studio, Calculators)
3. **Sunset features aggressively**: If a module has <5% usage, deprecate it
4. **User story map**: Document 3-5 primary user journeys. Everything not on those journeys is a candidate for removal

---

### 2. User Fit

**Score: 5/10**

#### Justification
- **Strength**: Deep domain language (frets, purfling, rosettes, chipload) signals genuine user empathy
- **Weakness**: The mental model assumes too much CNC expertise. A luthier who knows wood may not understand "trochoidal insertion," "adaptive stepover," or "jerk-aware time estimation"
- **Evidence**: RMOS feasibility rules (F001-F029) use engineering terms like "DOC:diameter > 5:1" without explaining what DOC means
- **Risk**: Users will either ignore the safety warnings (dangerous) or be overwhelmed and abandon the tool

#### Improvements
1. **Plain-language rule explanations**: Instead of "F020: Excessive DOC in hardwood," show "Your cut is 15mm deep with a 3mm bit in maple. This will likely snap the bit. Reduce depth to 5mm or use a larger bit."
2. **Guided workflows**: Add a "New User" mode with step-by-step wizards
3. **Material presets**: "I'm cutting mahogany with a 6mm endmill" -> auto-populate safe defaults
4. **Visual feedback**: Show the toolpath overlaid on the workpiece before generating G-code
5. **User research**: Interview 5 actual luthiers. Record their confusion points

---

### 3. Usability

**Score: 4/10**

#### Justification
- **Strength**: Vue 3 + Vite frontend is modern. Type safety with TypeScript reduces runtime errors
- **Weakness**: 146K LOC frontend with 500+ line Vue components suggests UI complexity
- **Evidence**: DxfPreflightValidator.vue was 536 LOC. ArtStudioBracing.vue was 622 LOC. These are single-screen components
- **Risk**: Slow render times, confusing state management, difficult debugging

#### Improvements
1. **Component size limit enforcement**: Add CI gate blocking >300 LOC components
2. **Design system**: Create a `@luthiers-toolbox/ui` package with standardized buttons, inputs, modals
3. **Loading states**: Many API calls lack loading indicators. Add skeleton screens
4. **Error boundaries**: Catch and display errors gracefully
5. **Mobile responsiveness**: No evidence of mobile testing. Luthiers may use tablets in workshops
6. **Accessibility audit**: Run axe-core. Zero mention of WCAG compliance

---

### 4. Reliability

**Score: 3/10** (CRITICAL)

#### Justification
- **Critical flaw**: 1,622 `except Exception` blocks and 97 bare `except:` clauses. This catches SystemExit, KeyboardInterrupt, and hides bugs
- **Safety impact**: In safety-critical code (rmos/, cam/, saw_lab/), swallowed exceptions can lead to bad G-code generation without user notification
- **Evidence**: The CHIEF_ENGINEER_HANDOFF.md explicitly calls this out as the #1 remediation priority
- **Test coverage**: Claims "100% coverage" in badges but actual coverage is <30%

#### Improvements
1. **Exception audit (immediate)**: Replace all bare `except:` with specific exception types
2. **Fail-fast in safety paths**: RMOS should NEVER swallow exceptions. If feasibility calculation fails, RED result, not silent pass
3. **Circuit breakers**: Add timeout and retry logic to external calls (OpenAI, sg-spec)
4. **Structured logging**: Replace `print()` and `console.error()` with structured JSON logging
5. **Chaos testing**: Intentionally inject failures to verify graceful degradation
6. **Coverage gate**: Block PRs below 60% line coverage. Increase to 80% over 6 months

---

### 5. Manufacturability / Maintainability

**Score: 4/10**

#### Justification
- **Strength**: Recent governance work (router registry, boundary enforcement, deprecation budget) shows awareness
- **Weakness**: 411K LOC for a single-developer project is unmaintainable
- **Evidence**: 19+ files exceed 500 lines. saw_lab/batch_router.py is 2,724 lines. runs_v2/store.py is 1,733 lines
- **Debt accumulation**: 685 markdown files (12 MB) including session logs

#### Improvements
1. **LOC budget**: Set a total budget (e.g., 200K LOC). Every new feature must delete equivalent old code
2. **God-object breakup**: Prioritize batch_router.py, store.py, api_runs.py for decomposition
3. **Module boundaries**: Enforce with `import-linter` or similar
4. **Documentation cleanup**: Delete session logs. Keep only: README, API reference, ADRs
5. **Dependency audit**: 56 GitHub Actions workflows is excessive. Consolidate to <20
6. **Dead code removal**: The 190-file stale `client/` directory should have been deleted months ago

---

### 6. Cost

**Score: 6/10**

#### Justification
- **Strength**: Railway.app PaaS reduces ops burden. SQLite for dev avoids database costs
- **Weakness**: AI integrations (OpenAI DALL-E, GPT-4 Vision) have unbounded cost exposure
- **Evidence**: `telemetry_cost_mapping_policy_v1.json` exists but no enforcement code found
- **Risk**: A user generating 100 relief maps in a loop could incur hundreds of dollars in API costs

#### Improvements
1. **Hard cost caps**: Implement per-user daily limits on AI calls. Default to $5/day
2. **Cost preview**: Before AI operations, show estimated cost
3. **Caching**: Cache identical prompts. Serve cached result for duplicate requests
4. **Tiered service**: Free tier with no AI. Paid tier with AI features
5. **Self-hosted alternatives**: For image generation, consider Stable Diffusion local deployment
6. **Infrastructure right-sizing**: Set max Railway replicas to 2 to cap costs

---

### 7. Safety

**Score: 5/10**

#### Justification
- **Strength**: RMOS is a genuine safety system with 22 rules, RED/YELLOW/GREEN decisions, and immutable audit trails
- **Weakness**: The system can be bypassed. Override buttons exist for YELLOW decisions
- **Evidence**: `RMOS_ALLOW_RED_OVERRIDE=1` environment variable can bypass RED blocks
- **Physical risk**: Bad G-code can shatter bits, destroy workpieces, or injure operators

#### Improvements
1. **Remove RED override**: No environment variable should bypass safety-critical blocks. Ever.
2. **Operator authentication**: Require login before generating G-code. Log who generated what
3. **Override audit trail**: If YELLOW is overridden, require a reason text. Store permanently
4. **Simulation mandate**: Don't allow G-code download without first viewing simulation
5. **Machine-specific limits**: Different CNC controllers have different capabilities
6. **Disclaimer acceptance**: Force users to acknowledge risk before first download
7. **Emergency stop guidance**: Include E-stop instructions in G-code comments

---

### 8. Scalability

**Score: 7/10**

#### Justification
- **Strength**: FastAPI with async is architecturally sound. Docker + Railway enables horizontal scaling
- **Weakness**: 411K LOC will slow CI/CD. 56 GitHub Actions workflows is CI sprawl
- **Evidence**: Current build time not documented but likely >10 minutes
- **Scaling target**: Unclear. Is this for 10 users or 10,000?

#### Improvements
1. **Define scale target**: "500 concurrent users, 10,000 G-code generations/day" or similar
2. **Load testing**: Run k6 or Locust against production. Identify bottlenecks
3. **Cache strategy**: Add Redis for session state, G-code caching, rate limiting
4. **CDN for static assets**: Vue bundle should be served from CDN, not app server
5. **Background jobs**: G-code generation can take seconds. Move to background queue
6. **Database indexing**: Ensure PostgreSQL tables have indexes on run_id, created_at, user_id
7. **Workflow consolidation**: Merge 56 workflows into 10 matrix-based workflows

---

### 9. Aesthetics

**Score: 5/10**

#### Justification
- **Strength**: Tailwind CSS provides consistency. Dark mode mentioned in docs
- **Weakness**: No design system. No Figma. No brand guidelines
- **Evidence**: CSS modules per component rather than shared design tokens
- **Impact**: Professional appearance builds trust in safety-critical tools

#### Improvements
1. **Design tokens**: Define colors, spacing, typography in `packages/shared/design-tokens.ts`
2. **Component library**: Build storybook for shared components
3. **Typography scale**: Use consistent heading sizes
4. **Color palette**: Define semantic colors mapped to RMOS risk levels
5. **Loading animations**: Replace spinners with skeleton screens
6. **Iconography**: Standardize on one icon set (Lucide or Heroicons)
7. **Professional landing page**: First impression matters

---

## Summary Scorecard

| Category | Score | Priority |
|----------|-------|----------|
| Purpose Clarity | 6/10 | Medium |
| User Fit | 5/10 | High |
| Usability | 4/10 | High |
| **Reliability** | **3/10** | **Critical** |
| Maintainability | 4/10 | High |
| Cost | 6/10 | Medium |
| Safety | 5/10 | High |
| Scalability | 7/10 | Low |
| Aesthetics | 5/10 | Low |
| **Overall** | **5.0/10** | |

---

## Top 5 Immediate Actions

| Priority | Action | Effort | Impact |
|----------|--------|--------|--------|
| 1 | **Exception handling audit**: Replace 1,719 bare/generic exceptions | 1-2 weeks | Critical |
| 2 | **Remove RED override**: Delete `RMOS_ALLOW_RED_OVERRIDE` env var | 1 day | High |
| 3 | **Define product scope**: Write 1-page doc on what this IS and ISN'T | 1 day | Medium |
| 4 | **User interviews**: Talk to 5 luthiers, record sessions | 1 week | High |
| 5 | **Delete dead code**: Remove stale `client/`, backups, duplicates | 1 day | Medium |

---

## Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Swallowed exception causes bad G-code | High | Severe (injury/damage) | Exception audit |
| AI cost overrun | Medium | High (financial) | Cost caps |
| Contributor burnout (411K LOC) | High | High (project death) | Aggressive code deletion |
| User abandonment (complexity) | Medium | High | Guided workflows |
| Security breach (no auth) | Medium | Medium | Add authentication |

---

## Architecture Strengths

1. **RMOS safety system** with immutable audit trails
2. **Boundary enforcement** via CI (tap_tone imports blocked)
3. **Contract-driven development** with JSON schemas
4. **Router registry** for centralized API governance
5. **Multi-post G-code support** (GRBL, Mach4, LinuxCNC, PathPilot, MASSO)
6. **Authentic domain expertise** in lutherie

---

## Architecture Weaknesses

1. **God objects**: Multiple files >1,000 LOC
2. **Exception swallowing**: 1,719 problematic handlers
3. **Test coverage gap**: <30% actual vs "100%" claimed
4. **Documentation sprawl**: 685 markdown files (12 MB)
5. **Scope creep**: 1,060 routes for what should be a focused tool
6. **No authentication**: Anyone can generate G-code

---

## Conclusion

Luthiers-ToolBox has a solid architectural foundation and genuine domain expertise, but it has accumulated significant technical debt that threatens reliability and maintainability. The most urgent issue is exception handling in safety-critical paths.

**Recommendation**: Pause feature development for 4-6 weeks to address reliability (exception audit), safety (remove RED override), and maintainability (delete dead code, decompose god objects). The system is not production-ready in its current state for safety-critical CNC operations.

---

*Review conducted using critical system design methodology. Scores reflect professional production standards, not hobby project expectations.*
