# Phase-2 → Analyzer Promotion Checklist (v1)

Owner(s): feature lead + schema owner  
Target path: `scripts/phase2/<feature>/` → `modes/<feature>/` (frozen)

## Required (all must pass)

| # | Requirement | Verification |
|---|-------------|--------------|
| 1 | **Coverage ≥ 80%** (pytest) | `coverage xml` attached in PR |
| 2 | **Contracts present** in `contracts/schemas/` | `schema_id` + `schema_version` declared |
| 3 | **Provenance** | All CLIs emit hashes + env (temp_C, rh_pct where relevant) |
| 4 | **Audio I/O** | Only via `modes/_shared/wav_io.py` |
| 5 | **ADR** for non-trivial algorithms | Motivation, options, decision documented |
| 6 | **Two approvals** | Schema owner + repo owner |
| 7 | **Stabilization** | 30 days in `scripts/phase2/` with no breaking changes |
| 8 | **Cross-repo validation** | ToolBox ingest test green |
| 9 | **No advisory language** | CI guard passes (`no-logic-creep.yml`) |
| 10 | **Filename invariants** | Tests enforce no aliases |

---

## Promotion Flow

```
┌─────────────────────┐     checklist      ┌─────────────────────┐
│   scripts/phase2/   │ ────────────────▶  │       modes/        │
│   (experimental)    │     complete       │     (production)    │
└─────────────────────┘                    └─────────────────────┘
         │                                          │
         │                                          │
         └────────────────────┬─────────────────────┘
                              │
                       ┌──────▼──────┐
                       │  CI + Tests │
                       │  must pass  │
                       └─────────────┘
```

---

## Freeze Gate

After sign-off and move to `modes/`, any breaking change requires a **MAJOR schema version bump**.

---

## Sign-Off Record

| Date | Feature | Schema Owner | Repo Owner | PR |
|------|---------|--------------|------------|-----|
| — | — | — | — | — |

---

*Adopted: 2026-01-01*
