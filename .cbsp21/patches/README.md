# CBSP21 per-PR patch manifests

Each PR declares its patch intent in its **own** manifest file in this
directory, named for the patch:

```
.cbsp21/patches/<patch-id>.json
```

## Why this directory exists

Previously every PR wrote its manifest to the single shared file
`.cbsp21/patch_input.json`. Because all PRs edited one path, any two open PRs
conflicted on it — every second PR to merge had to hand-resolve the manifest
(keep-ours) before it could land. One file, one lock, endless collisions.

Per-PR files have **distinct names**, so two PRs never touch the same path and
their manifests merge cleanly. The footgun is gone.

## How selection works

Both gates (`scripts/ci/check_cbsp21_gate.py` and
`scripts/ci/check_cbsp21_patch_input.py`) auto-discover every manifest here,
plus the legacy `.cbsp21/patch_input.json` if present, and validate the diff
against the **single** manifest that best covers the changed files.

Three outcomes matter (CBSP21-DIAG-001 / BR-046):

1. **Applicable + complete** — a manifest covers the changed files and meets
   `coverage_min` → pass.
2. **Applicable + incomplete** — a related manifest wins selection but leaves
   uncovered files → fail, naming that manifest and the uncovered paths.
3. **No applicable manifest** — changed files exist but **no** candidate covers
   any of them → fail with an explicit *no applicable manifest* message. Stale
   historical manifests are **not** printed as the governing manifest at 0%
   coverage.

Empty diffs (no non-internal changed files) keep the prior no-op selection
semantics and are not treated as a missing-manifest failure. Explicit
`--manifest` always uses the path you supply, even if coverage is 0%.

Pruning old manifests remains welcome housekeeping; selection no longer depends
on cleanup to avoid false attribution.

## Authoring

Copy `.cbsp21/patch_input.json.example` to `.cbsp21/patches/<patch-id>.json` and
fill it in. The manifest must satisfy both gate schemas (top-level `schema`,
`schema_version`, `patch_id`, `scope`, `diff_articulation`, `verification`, and
a `files[]` block) — see any recent manifest for a complete example.

The legacy single-file path still works for in-flight PRs, but new PRs should
land their manifest here.
