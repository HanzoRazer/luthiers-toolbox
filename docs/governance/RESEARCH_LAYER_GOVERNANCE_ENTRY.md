# Research Layer Governance Entry

**Layer:** `docs/research/`  
**Authority:** `research/non-authoritative`  
**Status:** ACTIVE  
**Governance Tier:** None (institutional memory only)

---

## Purpose

This document registers the research layer (`docs/research/`) in the governance inventory with explicit **non-authoritative** status. The research layer is discoverable and cross-linked but does not carry operational authority.

---

## Authority Declaration

```yaml
authority: research/non-authoritative
ci_blocking: false
operational_weight: 0
promotion_path: explicit Dev Order required
```

**What research documents may do:**
- Record discoveries, lineage, and institutional memory
- Cross-link to governance and operational documents
- Preserve topology ideas and semantic findings
- Document pipeline continuity and failure modes

**What research documents may NOT do:**
- Block CI
- Define operational policy
- Authorize runtime behavior changes
- Establish canonical paths without governance ratification

---

## Promotion Path

Research findings become operational authority only through explicit Dev Orders:

```text
Research discovery → Dev Order → Governance ratification → Runtime implementation
```

There is no implicit promotion. A finding recorded in `docs/research/` remains non-authoritative until:

1. A Dev Order explicitly references the finding
2. Governance documentation is created/updated
3. Runtime implementation follows governance, not research

---

## Research Wave Index

The research layer spans multiple waves documented in [RESEARCH_WAVE_INDEX.md](../research/RESEARCH_WAVE_INDEX.md):

| Wave | Era | Theme | Authority Status |
|------|-----|-------|------------------|
| 0 | Dec 2025 | Pre-constitutional boundaries | Historical lineage |
| A | Apr 2026 | Reconstruction intelligence | Lineage; IBG production active |
| B | Apr–May 2026 | Evaluation science | Migrated to vectorizer-sandbox |
| C | Mar–May 2026 | Semantic cognition | R&D excluded from spine |
| D | May 2026 | Constitutional runtime | Lineage for governance docs |
| E | May 2026 | Workflow / IBG intake | Lineage for IBG workflow |
| 1B | May 2026 | Semantic interpretation trace | Docs-only observability |

---

## Governance Integration Points

Research documents are cross-referenced from these operational documents:

| Operational Document | Research Reference | Purpose |
|---------------------|-------------------|---------|
| `MULTI_REPO_GOVERNANCE_CONVERGENCE_REPORT.md` | Research wave context | Convergence history |
| `EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md` | IBG lineage | BLOCKED_PROVENANCE context |
| `IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md` | Research Waves A/D/E | IBG constitutional foundation |
| `VECTORIZER_SANDBOX_MIGRATION_PLAN.md` | Wave C modules | Migration tracking |

---

## CI Classification

| Check | Applies to Research? | Reason |
|-------|---------------------|--------|
| Authority chain audit | No | Research has no authority |
| Export lifecycle validation | No | Research does not export |
| Capability registry | No | Research does not register capabilities |
| Document structure tests | Yes | Structural integrity only |

---

## Inventory Metadata

For governance inventory builder consumption:

```json
{
  "layer": "docs/research/",
  "authority": "research/non-authoritative",
  "category": "advisory",
  "ci_blocking": false,
  "promotion_requires": "explicit_dev_order",
  "cross_links": [
    "docs/governance/MULTI_REPO_GOVERNANCE_CONVERGENCE_REPORT.md",
    "docs/governance/EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md",
    "docs/governance/IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md"
  ],
  "primary_index": "docs/research/RESEARCH_WAVE_INDEX.md"
}
```

---

## Related Documents

| Document | Location | Role |
|----------|----------|------|
| Research README | [docs/research/README.md](../research/README.md) | Layer introduction |
| Research Wave Index | [docs/research/RESEARCH_WAVE_INDEX.md](../research/RESEARCH_WAVE_INDEX.md) | Time-indexed waves |
| Platform 1A Alignment | [docs/research/RESEARCH_PLATFORM_1A_ALIGNMENT.md](../research/RESEARCH_PLATFORM_1A_ALIGNMENT.md) | Constitutional Q&A |
| Governance Authority Hierarchy | [GOVERNANCE_AUTHORITY_HIERARCHY.md](GOVERNANCE_AUTHORITY_HIERARCHY.md) | Tier definitions |

---

*Research Layer Governance Entry — 2026-05-24*
