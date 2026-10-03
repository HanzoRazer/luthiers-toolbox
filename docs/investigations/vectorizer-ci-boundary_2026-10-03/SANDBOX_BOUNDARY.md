# Sandbox boundary — existing records this increment must not duplicate

This increment creates **no output taxonomy, no benchmark and no disposition**. It reuses what
exists, and where nothing exists it says so.

## Boundary table

| Existing record | Vocabulary / specimens | Current authority | Effect on this increment |
|---|---|---|---|
| `body_lexicon.md` — vectorizer-sandbox `scripts/vectorize/references/body_lexicon.md` (+ `body_grammar_evidence/BODY_LEXICON_A1.md`) | Body **geometry**: registration to a frame, which closed geometry is the body (with a rejection ledger), template fields, anatomical zones, crossings, frame limitations | Its own status line: "DRAFT — definitions, not capability. No code implements this." Sandbox branch `ibg-grammar-001`, not the sandbox default branch | **No mapping.** It defines body geometry, not output or artifact classes, so it has no term for the Cuatro roles |
| VEC-ROOT-001 — `docs/audit/VEC-ROOT-001_eligibility_body_definition.md` (merged, PR #387, `1ee2eb1399c6cd8ec2bf99a95343e261134146d3`) | §8 acceptance criteria: Cuatro and L-00 eligibility, no certified text block, text masking not sufficient alone, archtop must not regress | Committed audit finding on `main` | **Not duplicated.** None of the five tests separated here implements a §8 criterion. Separating them removes no VEC-ROOT-001 coverage |
| Commit `c8ad3ae445d7fa190d3ffdc2397e40232d86e60e` | §8 as a failing harness, `services/api/tests/vec_root_001/` | **Unmerged harness-branch artifact**: on `origin/vec-root-001-harness` only, not an ancestor of `main`; no PR by owner ruling | **Not evaluated or merged here.** If it ever lands, its corpus-dependent tests are candidates for the same `vectorizer_regression` marker; that is its own decision |
| `docs/governance/VECTORIZER_COMPONENT_LIFECYCLE.md` (2026-05-20, "ACTIVE GOVERNANCE", "single source of truth for vectorizer-adjacent component states") | Lifecycle states incl. `ACTIVE`, `SANDBOX`, `ABANDONED` ("safe to retire after parity check"), `ARCHAEOLOGICAL_RESEARCH` | Committed governance on `main` | **Cited, unchanged.** It is the closest existing disposition record. It records `edge_to_dxf.py` grouping as `ACTIVE (degraded observability)` and `CleanupMode.ENHANCED` — the mode the separated tests run — as `EXPERIMENTAL` / `SANDBOX`, "Not MVP default" |
| `docs/governance/VECTORIZER_CANONICAL_PATHS.md` (2026-05-20, "ARCHAEOLOGY_COMPLETE") | Path classes `CANONICAL_PRODUCTION`, `CANONICAL_RECOVERY`, … | Committed on `main` | **Cited, unchanged.** Records `enhanced` as `PRODUCTION` (50k-300k entities). **Conflicts with the lifecycle registry above on `ENHANCED`; not resolved here** |
| Retain / replace / retire records | — | — | **No record using those terms was found** in either repository. The two governance documents above are the nearest equivalents and are cited, not extended |

## Vocabulary rulings recorded

| Term | Status | Used here? |
|---|---|---|
| `benchmark witness`, `plan-package artifact` | plain-language candidate roles, unproven | yes, as candidates only (`CUATRO_PROVENANCE.md`) |
| `ROLE_UNRESOLVED` | disposition for both Cuatro paths | yes |
| `ARCHIVAL_TRACE`, `DESIGN_CANDIDATE` | proposed by the handoff; **absent from the full history of both repositories**; not established authority | **no — not introduced** |
| `CAM_READY` | established separately in vectorizer-sandbox `governance/cam_ready_lock/` (R2000 lock; includes a Melody Maker signature) | no. **Neither Cuatro file inherits it**, and the Melody Maker PDF used by these tests does not either |

## Where the lexicon is, and a correction

| Fact | Evidence |
|---|---|
| Introduced | vectorizer-sandbox `1d77f0e4e9ae337f63d8eef47f9ae8191f309d96`, 2026-09-15, "preserve owner body lexicon draft" |
| Last changed | `d588164ce1cd9ed1a09b24dd6705ee5c5756bdc2`, 2026-09-15 |
| Branch | `ibg-grammar-001`, head `f95cea71978fadc96cafca6766f91c62751a4efc` |
| Remote presence | **Present on the sandbox remote**: `git ls-remote origin refs/heads/ibg-grammar-001` returns `f95cea71…`, and the file exists at that head. Not on the sandbox default branch; no merge recorded |
| Absent from this repository | `git log --all --name-only` over all 4,228 LTB commits: no `*lexicon*` path |

**Correction carried in this record.** During intake the lexicon was first reported as "not
locatable", then as "committed locally, on no remote branch". Both were wrong. The second came
from `git branch -r --contains`: the local sandbox clone's fetch refspec tracks only `master`
(the remote has 43 branches), so a remote-tracking query cannot see `ibg-grammar-001`. Remote
presence was then verified directly with `ls-remote`. The durability risk is therefore not
"local only"; it is "on an unmerged sandbox branch".

**Stale statement on `main`, not edited here.** VEC-ROOT-001 §5a (written 2026-09-19) says the
lexicon "has never been committed". It had been committed in vectorizer-sandbox on 2026-09-15; the
§5a search covered this repository's tree only. §5a's citation rules (cite as a draft, mark it
unimplemented) still hold. Correcting §5a is out of scope.
