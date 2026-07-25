# RPMCC24 — Repository Patch Manifest Control Center
### Governance charter · established 2026-07-24

> **What this is.** The per-PR patch-manifest gate that every merge passes through.
> Formerly called "CBSP21," it grew from a ~100-word anti-under-scoping note into a
> full manifest-and-coverage apparatus because a real need — repository-wide patch-scope
> control — had no instrument, and it filled the void. This document **names it honestly**
> and **governs it**, so the gate that governs every merge is itself governed.

---

## 1. Identity and provenance

- **Name:** Repository Patch Manifest Control Center (RPMCC24).
- **Lineage:** evolved from CBSP21 (Computer Bot Scoping Protocol, 2025-12-21). During the
  governance sprint it was characterized as an "anti-hallucination measure"; it has since
  grown into something different — patch-scope and architecture-scan control. **The drift
  is acknowledged, not corrected:** it reflects a living codebase filling a real void.
- **Why renamed:** the CBSP21 name described *anti-under-scoping of document reads*. The
  apparatus enforces *completeness of patch declaration*. Same spirit, different object —
  keeping the old name was a name≠behavior divergence in the tool that exists to catch
  exactly that. RPMCC24 names the behavior as it actually is.
- **Owner:** Ross (HanzoRazer). Changes to RPMCC24's schema, gates, or thresholds are an
  owner decision, not an incidental edit inside an unrelated PR.

### 1a. Full lineage — recorded, not retconned (2026-07-24 reconciliation)

The provenance above is the *origin*. The apparatus acquired a second name during its
drift, and that second name is written into the repo. Both are real; they belong to
different eras of the same drifting artifact. Recording the whole lineage — rather than
picking a winner — is the honest move, and it is the point of this charter.

| Era | Dates | Name in use | What it was | Where recorded |
|---|---|---|---|---|
| Origin | 2025-12-21 | CBSP21 — *Computer Bot Scoping Protocol* | ~100-word markdown **social contract** against under-scoping document reads (the "50% answer" problem) | the original note; reinstated as [CBSP21_v2.md](CBSP21_v2.md) |
| Drift | 2026-01 → 2026-07 | CBSP21 — *"Code Batch Submission Protocol v2.1"* | the patch-manifest + coverage apparatus (`.cbsp21/`, gate scripts) it grew into after being rescanned, praised, and rewritten | [../CBSP21.md](../CBSP21.md) |
| Charter | 2026-07-24 → | **RPMCC24** | the same apparatus, now honestly named, owned, and governed | this document |

**Key reconciliation point.** [../CBSP21.md](../CBSP21.md) calling the apparatus "Code
Batch Submission Protocol, always about patch submission + coverage" is **evidence of the
drift, not a refutation of it.** It is a *post-drift* description that back-projected the
drifted state onto the origin — the drifted thing having already been renamed once,
informally, without governance. That name is real, but it reflects the patch-manifest era,
**not** the 2025-12-21 anti-under-scoping origin. RPMCC24 is doing that rename *properly
this time* (owned, provenanced, charter'd), and preserving the full history rather than
erasing either end of it.

- [../CBSP21.md](../CBSP21.md) is **superseded by this charter**, not deleted. Deleting it
  would repeat the erase-the-history move this whole exercise exists to reverse. It is
  marked superseded and pointed here; it stands as a dated artifact of the patch-manifest
  era.
- The origin end of the lineage — the anti-under-scoping read gate — is **not** part of
  RPMCC24. It is a different job, reinstated separately as CBSP21 v2 (see §5).

---

## 2. What it enforces today (the honest current spec)

The apparatus is its own spec — there is no prose the machinery merely describes. It is:

- **`.cbsp21/patch_input.schema.json`** — the manifest schema (`cbsp21_patch_input_v1`).
- **`scripts/ci/check_cbsp21_gate.py`** and **`check_cbsp21_patch_input.py`** — the two gates.
- **`.cbsp21/patches/<patch-id>.json`** — one manifest per PR.

Each PR **must declare every changed file** in a `files[]` block, each with `path` and,
where applicable, `intent`, `scan_targets`, `risk` (low/medium/high), `behavior_change`,
and `verification[]`. A **`coverage_min`** (default **0.95**) sets the declared-coverage
floor. An optional **`architecture_scan`** block records a scan id, a risk_summary
(critical/high/medium/low counts), findings, and an `acknowledged` flag.

Selection is automatic: the gates discover every manifest in `.cbsp21/patches/` (plus the
legacy shared file if present) and validate the diff against the manifest that best covers
the changed files. Stale manifests are ignored.

### 2a. Name-only rename — the machinery keeps its identifiers

**The rename is legibility and governance, not a filesystem migration.** The human-facing
name is RPMCC24; the on-disk apparatus **retains** its `.cbsp21/` prefix and `cbsp21_*`
identifiers for continuity:

- `.cbsp21/` directory, `.cbsp21/patches/`, `.cbsp21/patch_input.schema.json`
- the schema `$id` / `schema` value `cbsp21_patch_input_v1`
- `scripts/ci/check_cbsp21_gate.py`, `check_cbsp21_patch_input.py`,
  `cbsp21_manifest_discovery.py`
- every existing and historical `.cbsp21/patches/*.json` manifest

Renaming these on disk would **break every existing and historical manifest — including
the manifests on in-flight PRs — for no functional benefit.** The `.cbsp21/` prefix is now
a stable *artifact-name*, like a package that kept its old import path after a rebrand:
completely normal, and the honest choice. This is the extend-don't-break discipline applied
to the governor itself — a name change that would break live references isn't worth the
churn, so the name lives in the *charter and docs* and the *machinery keeps its stable
identifiers*.

---

## 3. Known characteristics (the scars, recorded so they aren't rediscovered)

- **Base-sensitivity.** Coverage is computed over a changed-file set derived by diff. A
  stale base injects foreign files → false low-coverage reds (the #193 50% incident). The
  merge-base diff fix (#211) addresses this. **Always confirm the branch base before
  trusting a coverage red.**
- **Per-PR-manifest design** replaced a single shared `patch_input.json` that made every
  second concurrent PR hand-resolve a conflict. Distinct filenames removed that footgun.
- **Two gates, not one:** `check_cbsp21_patch_input.py` (declaration completeness) and
  `check_cbsp21_gate.py` (coverage). They can disagree — a green input gate with a red
  coverage gate is the base-staleness signature, not a manifest defect.

---

## 4. Governance protocol (the part that makes the governor governed)

RPMCC24 changes go through the same discipline it imposes on everything else:

- **Owner-gated changes.** Schema, threshold (`coverage_min`), or gate-script changes are
  their own PR, labeled as an RPMCC24 change, reviewed as infrastructure — never bundled
  into an unrelated PR under a "docs" or "fix" label.
- **Provenance required.** Every future change to RPMCC24 records why, in this file's
  changelog. An unexplained change to the merge-governing gate is forbidden — the gate
  that governs merges may not itself drift unprovenanced.
- **No silent threshold moves.** Changing `coverage_min` is a governance decision (it
  changes what passes for every PR). It is recorded here with a reason, never edited
  quietly in the schema.
- **Exemptions are explicit.** Regions intentionally outside patch-manifest control (e.g.
  throwaway prototypes) are named here, not left to the gate to flag as failures.

### Changelog
- `2026-07-24` — Established RPMCC24 charter; named the apparatus, assigned ownership,
  recorded provenance and the base-sensitivity scar. (Renamed from CBSP21; CBSP21 reinstated
  separately as a true scope gate — see CBSP21_v2.) Reconciliation: recorded the full
  lineage including the "Code Batch Submission Protocol" patch-manifest era
  ([../CBSP21.md](../CBSP21.md)), marked that doc superseded, and fixed the rename as
  **name-only** — `.cbsp21/`/`cbsp21_*` identifiers retained to avoid breaking existing and
  historical manifests. No code, path, or schema `$id` change in this pass.

---

## 5. Relationship to CBSP21 (the split)

RPMCC24 is **not** the original CBSP21 job. CBSP21's original purpose — preventing
under-scoped *document reads* (the 50%-answer problem) — is a different gate, reinstated
separately as **CBSP21 v2** ([CBSP21_v2.md](CBSP21_v2.md)), this time structural rather
than social. RPMCC24 governs *patches*; CBSP21 v2 governs *reads*. Two fences, two jobs,
both with teeth.
