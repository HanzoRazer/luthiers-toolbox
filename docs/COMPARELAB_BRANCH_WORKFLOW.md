# CompareLab Branch Workflow & Upload Protocol

**Branch:** `feature/comparelab-b22-arc`  
**Status:** Active Development  
**Last Updated:** December 2, 2025

---

## Overview

This document describes the development workflow for CompareLab B22.x protocol implementations, including upload procedures, branch management, and integration patterns.

---

## Branch Structure

### Current Branch: `feature/comparelab-b22-arc`

**Purpose:** CompareLab B22.x protocol series development

**Scope:**
- B22.8 state machine and UI guardrails
- B22.8 skeleton integration (layer system, bbox support)
- B22.9+ future protocol implementations
- Compare automation backend endpoints

**Protected Files:**
- `client/src/composables/useCompareState.ts` - State machine core
- `client/src/composables/useCompareState.spec.ts` - Test suite
- `client/src/components/compare/*` - CompareLab UI components
- `services/api/app/routers/compare_automation_router.py` - Backend stub
- `docs/B22_*.md` - Protocol documentation

---

## Upload Protocol (B22.x Series)

> **📋 PROTOCOL GOVERNANCE:**  
> All B22.x protocol uploads MUST follow this standardized format.  
> Non-compliant uploads will require revision before implementation.

### Protocol Numbering Convention

**Format:** `B22.<minor>`

**Semantic Versioning:**
- **Major (B22 → B23):** Breaking changes to state machine API
- **Minor (B22.8 → B22.9):** New features, additive changes only
- **Implicit Patch:** Bug fixes within same protocol (no renumbering)

**Examples:**
- `B22.8` - State machine + guardrails
- `B22.9` - TBD (next upload)
- `B22.10` - TBD
- `B23.0` - Breaking change (if needed)

### Upload Structure

> **⚠️ MANDATORY SECTIONS:**  
> Protocol uploads missing these sections will be rejected.  
> Use the template at end of this document to ensure compliance.

Each protocol upload **MUST** include:

1. **Protocol Document** (Markdown or text)
   - Clear objectives and scope
   - Component/file targets
   - Implementation patterns
   - Guardrails and constraints
   - Example code snippets

2. **Clarification Questions** (Optional)
   - If protocol ambiguous, agent will ask 8 question groups
   - User provides detailed answers
   - Implementation proceeds after clarification

3. **Skeleton Code** (Optional but recommended)
   - TypeScript interfaces
   - Vue component templates
   - Python Pydantic models
   - Example usage patterns

### Upload Checklist

> **🔒 GATE REQUIREMENTS:**  
> All checkboxes MUST be ✅ before uploading next protocol.  
> Skipping checklist items will block implementation.

Before uploading next protocol (B22.9+):

- [ ] **Previous protocol complete:** All files committed with proper message
- [ ] **Tests passing:** `npm run test` shows all green
- [ ] **Manual testing complete:** All checklist items verified
- [ ] **Documentation updated:** All affected README/docs modified
- [ ] **No merge conflicts:** `git fetch && git rebase origin/main` clean
- [ ] **Protocol document clear:** Unambiguous instructions with examples
- [ ] **Guardrails reviewed:** No violations of B22.8 protocol rules
- [ ] **Backward compatible:** Or marked as breaking change (B23.0)

---

## Implementation Workflow

### Phase 1: Protocol Review

**Agent Actions:**
1. Parse protocol document
2. Identify target files and components
3. Check for conflicts with existing code
4. Ask clarification questions (if needed)

**User Actions:**
1. Upload protocol document
2. Answer clarification questions (if asked)
3. Approve implementation plan

### Phase 2: Implementation

**Agent Actions:**
1. Create/modify files per protocol spec
2. Follow existing patterns (B22.8 as template)
3. Add developer notes and guardrail comments
4. Update TypeScript types and interfaces
5. Wire components through parent chain

**Typical File Changes:**
- 4-6 TypeScript/Vue files per protocol
- 1-2 documentation files
- 0-1 backend router files (if API changes)
- 1 test file (unit or integration)

### Phase 3: Verification

**Agent Actions:**
1. Create manual test checklist
2. Document commit commands
3. Update implementation summary

**User Actions:**
1. Run unit tests: `cd client && npm run test`
2. Run manual tests: Follow checklist
3. Review changes: `git diff`
4. Commit changes: Use provided commit message

### Phase 4: Documentation

**Auto-Generated Docs:**
- `B<protocol>_IMPLEMENTATION_SUMMARY.md` - Full implementation details
- `B<protocol>_TEST_SETUP.md` - Testing guide (if new tests added)
- Component README updates (this file)

**Manual Updates:**
- Architecture decision records (if pattern changes)
- API contract documentation (if backend changes)

---

## File Organization

### Frontend Structure

```
client/src/
├── composables/
│   ├── useCompareState.ts          # State machine (B22.8 core)
│   └── useCompareState.spec.ts     # Unit tests (B22.8 tests)
├── components/compare/
│   ├── README.md                   # This file
│   ├── CompareLabView.vue          # Main view (state owner)
│   ├── CompareBaselinePicker.vue   # Baseline selector
│   ├── CompareSvgDualViewer.vue    # SVG display pass-through
│   ├── DualSvgDisplay.vue          # SVG panes + layer controls
│   └── CompareDiffViewer.vue       # Diff summary + export
└── views/
    └── CompareLabView.vue          # Router view wrapper
```

### Backend Structure

```
services/api/app/
├── routers/
│   └── compare_automation_router.py  # /api/compare/run endpoint
└── main.py                          # Router registration
```

### Documentation Structure

```
docs/
├── B22_8_IMPLEMENTATION_SUMMARY.md    # B22.8 core + tests
├── B22_8_SKELETON_INTEGRATION.md     # B22.8 skeleton enhancements
├── B22_8_TEST_SETUP.md               # Vitest setup guide
├── COMPARELAB_DEV_CHECKLIST.md       # Manual testing
└── COMPARELAB_BRANCH_WORKFLOW.md     # This file
```

---

## Git Workflow

### Commit Message Convention

**Format:**
```
B<protocol>: <Brief summary>

<Detailed description>

Features:
- Feature 1
- Feature 2

<Technical details>

<Status/notes>
```

**Example:**
```
B22.8: Compare state machine and UI guardrails + unit tests

- Add useCompareState composable for centralized state
- Add skeleton loading with shimmer animation
- Disable overlay controls during computation
- Show warning banners for disabled reasons
- Add 40+ unit tests with Vitest

Files changed: 10 (6 modified, 4 created)
Test coverage: 100% target for state machine
Backward compatible: Yes

B22.8 protocol complete. Ready for B22.9.
```

### Commit Strategy

**Option 1: Single Commit per Protocol** (Recommended)
```bash
# Stage all protocol files
git add client/src/composables/useCompareState.ts
git add client/src/components/compare/*.vue
git add docs/B22_*.md

# Commit with protocol message
git commit -m "B22.8: State machine and UI guardrails"
```

**Option 2: Incremental Commits**
```bash
# Commit 1: Core implementation
git commit -m "B22.8 Core: State machine composable"

# Commit 2: UI integration
git commit -m "B22.8 UI: Wire components to state machine"

# Commit 3: Tests
git commit -m "B22.8 Tests: Add unit test suite"

# Commit 4: Docs
git commit -m "B22.8 Docs: Implementation summary"
```

### Branch Hygiene

**Keep branch up-to-date:**
```bash
# Fetch latest main
git fetch origin main

# Rebase onto main (if no conflicts)
git rebase origin/main

# Or merge main (if conflicts expected)
git merge origin/main
```

**Clean up before merge:**
```bash
# Squash commits if desired
git rebase -i origin/main

# Run tests one final time
cd client && npm run test

# Push to remote
git push origin feature/comparelab-b22-arc
```

---

## Testing Strategy

### Unit Tests (Automated)

**Framework:** Vitest + jsdom

**Location:** `client/src/composables/useCompareState.spec.ts`

**Run Tests:**
```bash
cd client
npm run test                    # Run once
npm run test:watch              # Watch mode
npm run test:coverage           # Coverage report
npm run test useCompareState    # Specific file
```

**Coverage Target:** 100% for state machine core

**CI Integration:** GitHub Actions runs tests on push

### Manual Tests (Checklist)

**Location:** `docs/COMPARELAB_DEV_CHECKLIST.md`

**Steps:**
1. Load geometry in CompareLab
2. Select baseline
3. Trigger diff computation
4. Verify skeleton display (shimmer animation)
5. Verify controls disabled during computation
6. Verify error banner on failure
7. Verify layer controls (if present)

**When to Run:**
- After implementing new protocol
- Before committing changes
- After resolving merge conflicts
- Before creating pull request

### Integration Tests (Future)

**Planned:**
- E2E tests with Playwright/Cypress
- Backend API contract tests
- Full workflow tests (upload → compare → export)

---

## Protocol Upload Examples

### Example 1: B22.8 Core (Actual)

**Upload:**
```
Protocol B22.8: Guardrails & State Machine

Objectives:
1. Create useCompareState composable
2. Add skeleton loading UI
3. Disable controls during computation
4. Show warning banners for errors

Files to modify:
- Create client/src/composables/useCompareState.ts
- Modify client/src/views/CompareLabView.vue
- Modify client/src/components/compare/*.vue
```

**Result:** 10 files modified, 40+ tests added

### Example 2: B22.8 Skeleton (Actual)

**Upload:**
```
Skeleton code for layer system:

// Types
export interface CompareLayerInfo {
  id: string
  inLeft: boolean
  inRight: boolean
  hasDiff?: boolean
  enabled: boolean
}

// UI component template
<div class="compare-layers-panel">
  <ul>
    <li v-for="layer in layers">
      <input type="checkbox" :checked="layer.enabled" />
      {{ layer.id }}
    </li>
  </ul>
</div>
```

**Result:** 4 files enhanced with layer system

### Example 3: B22.9 (Future - Hypothetical)

**Upload:**
```
Protocol B22.9: Zoom-to-Diff & Pan Controls

Objectives:
1. Implement viewport zoom using activeBBox
2. Add pan controls to SVG panes
3. Sync viewport across left/right panes
4. Add "Reset Zoom" button

Files to modify:
- client/src/components/compare/DualSvgDisplay.vue
- Add client/src/composables/useSvgViewport.ts
```

**Expected Result:** 3 files modified, new composable created

---

## Collaboration Pattern

### Agent-User Interaction Flow

```
User uploads protocol
       ↓
Agent reviews protocol
       ↓
Agent asks clarification questions (if needed)
       ↓
User answers questions
       ↓
Agent implements changes
       ↓
Agent creates documentation
       ↓
Agent provides commit command
       ↓
User runs tests & commits
       ↓
User uploads next protocol (B22.9+)
```

### Communication Protocol

**Agent provides:**
- File-by-file change summary
- Commit message (ready to paste)
- Test commands
- Manual testing checklist
- Documentation links

**User provides:**
- Protocol specifications
- Clarification answers
- Test results confirmation
- Merge conflict resolution (if needed)
- Final approval for commit

---

## Merge Strategy

### To Main Branch

**Prerequisites:**
- [ ] All B22.x protocols complete
- [ ] All tests passing
- [ ] Manual testing complete
- [ ] Documentation complete
- [ ] No conflicts with main
- [ ] Code review approved (if required)

**Merge Command:**
```bash
# Switch to main
git checkout main

# Pull latest
git pull origin main

# Merge feature branch
git merge --no-ff feature/comparelab-b22-arc

# Push to remote
git push origin main
```

**Post-Merge:**
- [ ] Delete feature branch (if done)
- [ ] Create release tag (if versioned)
- [ ] Update changelog
- [ ] Notify team

---

## Common Issues & Solutions

### Issue: Protocol upload unclear

**Solution:**
- Agent will ask clarification questions
- User should provide detailed answers
- Reference existing patterns (B22.8 as example)

### Issue: Merge conflicts with main

**Solution:**
```bash
# Fetch latest main
git fetch origin main

# Rebase and resolve conflicts
git rebase origin/main

# Run tests after resolving
npm run test
```

### Issue: Tests failing after implementation

**Solution:**
1. Check test output for specific failures
2. Verify types match between composable and tests
3. Check for missing mocks or imports
4. Run `npm run test:coverage` to see what's untested

### Issue: Protocol depends on unimplemented feature

**Solution:**
- Implement prerequisite features first
- Or add stub/placeholder with TODO comment
- Document dependency in protocol notes

---

## Best Practices

### For Protocol Uploads

1. **Be Specific:** Include file paths, function names, exact patterns
2. **Provide Examples:** Show before/after code snippets
3. **Reference Existing:** Point to similar patterns in codebase
4. **Include Types:** TypeScript interfaces and type definitions
5. **Clarify Scope:** What's in scope, what's out of scope

### For Implementation

1. **Follow Patterns:** Use existing B22.8 as template
2. **Add Comments:** Developer notes explaining why (not just what)
3. **Test First:** Consider test cases while implementing
4. **Document As You Go:** Don't defer docs to end
5. **Keep Commits Clean:** Meaningful messages, logical grouping

### For Testing

1. **Unit Test Core:** 100% coverage for state machines and utilities
2. **Manual Test UI:** Follow checklist for user-facing changes
3. **Test Error Paths:** Don't just test happy path
4. **Test Edge Cases:** Empty arrays, null values, concurrent operations
5. **Test Accessibility:** Keyboard navigation, screen reader labels

---

## Protocol Handoff Template

> **📝 REQUIRED FORMAT:**  
> Copy this template for every new protocol upload.  
> Fill in ALL sections (use "N/A" if not applicable).  
> Incomplete protocols will be returned for revision.

Use this template when uploading new protocols:

```markdown
# Protocol B22.<X>: <Title>

## Objectives
1. <Primary objective>
2. <Secondary objective>

## Scope
- Files to modify: <list>
- Files to create: <list>
- Tests required: <type>

## Implementation Details
<Describe approach, patterns, algorithms>

## Type Definitions
```typescript
<Include TypeScript interfaces>
```

## Component Templates
```vue
<Include Vue template snippets>
```

## Backend Changes (if any)
```python
<Include FastAPI router/model changes>
```

## Success Criteria
- [ ] <Criterion 1>
- [ ] <Criterion 2>

## Testing
- Unit tests: <what to test>
- Manual tests: <steps to verify>

## Dependencies
- Requires: <list prerequisites>
- Blocks: <list dependents>

## Questions for Agent
1. <Question 1>?
2. <Question 2>?

## Protocol Compliance Declaration
- [ ] I have reviewed B22.8 guardrails and this protocol complies
- [ ] This protocol is backward compatible (or marked B23.0 if breaking)
- [ ] All template sections completed
- [ ] Gate requirements checklist verified
```

---

## Protocol Review Criteria

Agent will verify protocol against these criteria before implementation:

### Completeness Check
- [ ] All mandatory template sections filled
- [ ] File paths specified (not vague descriptions)
- [ ] Type definitions included (TypeScript interfaces)
- [ ] Success criteria measurable and testable
- [ ] Dependencies clearly stated

### Compliance Check
- [ ] No guardrail violations (Rule 1-5)
- [ ] Props-down/events-up pattern maintained
- [ ] State machine not bypassed
- [ ] Error handling follows protocol
- [ ] Testing strategy defined

### Quality Check
- [ ] Clear implementation approach (not ambiguous)
- [ ] Examples provided for complex patterns
- [ ] Edge cases considered
- [ ] Performance implications noted
- [ ] Security considerations (if applicable)

### Rejection Reasons

Protocol will be **returned for revision** if:

1. **Missing Critical Sections:** No type definitions, no file paths, no success criteria
2. **Guardrail Violations:** Proposes manual state mutations or bypassing composable
3. **Ambiguous Instructions:** Multiple interpretations possible
4. **Incomplete Dependencies:** Requires unspecified features
5. **Breaking Changes Unmarked:** Changes API without B23.0 version bump
6. **No Testing Strategy:** Doesn't specify how to verify implementation

**Resolution:** User provides clarification or revised protocol

---

## Status Dashboard

### B22.8 Protocol Status

| Component | Status | Files | Tests | Docs |
|-----------|--------|-------|-------|------|
| Core State Machine | ✅ | 1 | 40+ | ✅ |
| UI Integration | ✅ | 6 | Manual | ✅ |
| Skeleton Enhancement | ✅ | 4 | Unit | ✅ |
| Backend Stub | ✅ | 1 | - | - |

### Future Protocols

| Protocol | Status | Description |
|----------|--------|-------------|
| B22.9 | 📋 Planned | TBD (awaiting upload) |
| B22.10 | 📋 Planned | TBD |
| B23.0 | 💭 Future | Breaking changes (if needed) |

---

## Quick Reference

### Commands

```bash
# Run tests
cd client && npm run test

# Watch tests
npm run test:watch

# Coverage report
npm run test:coverage

# Commit changes
git add <files>
git commit -m "B22.X: <summary>"
git push origin feature/comparelab-b22-arc

# Update from main
git fetch origin main
git rebase origin/main
```

### File Locations

```
State Machine:   client/src/composables/useCompareState.ts
Tests:           client/src/composables/useCompareState.spec.ts
Components:      client/src/components/compare/*.vue
Backend:         services/api/app/routers/compare_automation_router.py
Documentation:   docs/B22_*.md
```

### Key Contacts

- **Repository:** github.com/HanzoRazer/luthiers-toolbox
- **Branch:** feature/comparelab-b22-arc
- **Protocol Series:** B22.x (CompareLab state machine)

---

**Workflow Status:** ✅ Active  
**Current Protocol:** B22.8 Complete  
**Next Protocol:** B22.9 (awaiting specification)  
**Last Updated:** December 2, 2025
