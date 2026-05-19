# Semantic Freeze Protocol

**Status:** Authoritative  
**Date:** 2026-05-16  
**Sprint:** MRP-5J

---

## Purpose

This document defines the protocol for freezing, versioning, and ratifying semantic vocabulary. It ensures ontology stability while permitting controlled evolution.

---

## Freeze Levels

### FROZEN

**Definition:** Term is locked. No changes permitted without formal deprecation process.

**Criteria:**
- Term is canonical in production systems
- Multiple consumers depend on stable meaning
- Breaking change would cause system failures

**Change process:**
1. Create new term with updated meaning
2. Add deprecation mapping to old term
3. Migrate consumers over defined period
4. Archive (do not delete) frozen term

### STABLE

**Definition:** Term is authoritative but may evolve through reconciliation workflow.

**Criteria:**
- Term is canonical within domain
- Consumers exist but migration is feasible
- Meaning may need refinement

**Change process:**
1. Propose change through reconciliation workflow
2. Obtain domain owner approval
3. Update registry with version increment
4. Notify dependent systems

### CANDIDATE

**Definition:** Term is proposed but not yet ratified.

**Criteria:**
- New term being introduced
- Definition under review
- Not yet in production use

**Change process:**
1. Propose term with definition
2. Review period (minimum 1 sprint)
3. Ratification or rejection
4. If ratified, promote to STABLE

### DEPRECATED

**Definition:** Term is scheduled for removal.

**Criteria:**
- Replaced by newer term
- Migration path defined
- Sunset date established

**Change process:**
1. Document replacement term
2. Add deprecation notice to registry
3. Sunset after migration period
4. Archive but do not delete

---

## Versioning Rules

### Semantic Version Format

```
{major}.{minor}.{patch}
```

- **major:** Breaking change to canonical meaning
- **minor:** Additive change (new terms, aliases)
- **patch:** Documentation or metadata fix

### Version Bump Criteria

| Change Type | Version Bump | Example |
|-------------|--------------|---------|
| New canonical term | minor | Adding `governed_experimental` |
| New alias | minor | Adding alias mapping |
| Definition refinement | minor | Clarifying meaning |
| Breaking meaning change | major | Redefining `translator` |
| Documentation fix | patch | Typo correction |
| Metadata update | patch | Adding source_document |

---

## Ratification Workflow

### Step 1: Proposal

Create proposal with:
- Term name
- Canonical definition
- Owning domain
- Justification
- Impact assessment

### Step 2: Domain Review

Domain owner evaluates:
- Consistency with domain vocabulary
- Conflict potential
- Consumer impact

### Step 3: Cross-Domain Check

Governance review evaluates:
- No collision with other domains
- Authority chain compliance
- Tier appropriateness

### Step 4: Ratification

If approved:
- Add to registry with STABLE status
- Increment version (minor)
- Document in changelog

If rejected:
- Document reason
- Optionally propose alternative

---

## Deprecation Rules

### Deprecation Notice Requirements

```json
{
  "term": "deprecated_term",
  "status": "DEPRECATED",
  "replacement": "new_term",
  "deprecation_date": "2026-05-16",
  "sunset_date": "2026-08-16",
  "reason": "Ambiguous; replaced with more precise term"
}
```

### Minimum Deprecation Period

- **Tier 1 terms:** 6 months minimum
- **Tier 2 terms:** 3 months minimum
- **Tier 3 terms:** 1 month minimum

### Sunset Behavior

After sunset date:
- Term remains in registry marked ARCHIVED
- Usage should produce warnings
- New code must not use deprecated term

---

## Emergency Change Protocol

For critical issues requiring immediate vocabulary change:

1. Document emergency justification
2. Obtain explicit human approval
3. Make change with major version bump
4. Conduct post-change review
5. Update all affected consumers

**Emergency criteria:**
- Security vulnerability
- Data corruption risk
- System-breaking conflict

---

## Alias Retirement

### Alias Lifecycle

1. **ACTIVE:** Alias in use, maps to canonical term
2. **TRANSITIONAL:** Migration in progress
3. **RETIRED:** No longer supported

### Retirement Process

1. Mark alias as TRANSITIONAL
2. Update consumers to use canonical term
3. After migration period, mark RETIRED
4. Remove from active alias resolution

---

## Related Documents

- `lifecycle_registry.json` - Lifecycle term registry
- `ontology_alias_registry.json` - Alias mappings
- `ONTOLOGY_RECONCILIATION_WORKFLOW.md` - Change workflow
