# CONTRACTS_GOVERNANCE_SCENARIO_B_v1

**Status:** Normative (Enforced by CI)
**Effective Date:** 2026-01-10
**Scenario:** B — Vendor + Pin + Verify (Byte-for-byte parity)

---

## Purpose

Prevent silent contract drift between **ToolBox (canonical producer/ledger constraints)** and **Smart Guitar (consumer runtime)** without requiring a monorepo, schema registry, or cross-repo runtime imports.

This policy standardizes:
- where contracts live,
- how they are published,
- how consumers sync,
- and how CI blocks drift or "stealth breaking" changes.

---

## Key Decisions (Locked)

### 1) Parity Mode (v1)
**Byte-for-byte parity** is the default and required.

- Schema files are compared exactly as bytes.
- This is an intentional "tripwire" to catch drift early.
- A later evolution may add semantic/normalized parity, but v1 is strict.

### 2) Canonical Publisher
**ToolBox `main`** is the publishing signal.

When a contract change is merged to ToolBox `main`, that version is considered published for downstream consumers.

### 3) Consumer Sync Ownership
**Smart Guitar owns schema sync + provenance.**

Smart Guitar may propose schema changes via PRs, but:
- ToolBox remains canonical for final contract publication,
- Smart Guitar is responsible for updating its vendored copy after publication.

### 4) Breaking Change Authority
Breaking changes are controlled via:
- a checklist discipline, and
- CI enforcement rules defined below.

No single person is the authority; the process is.

---

## Files & Locations

### Canonical contracts (ToolBox)
`contracts/*.schema.json`

### Vendored contracts (Smart Guitar / sg-spec)
`contracts/*.schema.json`
Vendored copies must match ToolBox byte-for-byte for the same version.

### Required hash file (both repos)
For every `*.schema.json`, a sibling `*.schema.sha256` must exist:

- Format: **single line**
- Content: **64 lowercase hex chars only**
- Example:
  - `contracts/smart_guitar_toolbox_telemetry_v1.schema.sha256`

### Public release sentinel (both repos)
`contracts/CONTRACTS_VERSION.json`

```json
{
  "public_released": true,
  "tag": "TOOLBOX-CONTRACTS-2026.01"
}
```

If `public_released` is `true`, then v1 contracts become immutable (see below).

### Changelog (both repos)

`contracts/CHANGELOG.md`

---

## Immutability Rules

### Pre-release behavior

Before `contracts/CONTRACTS_VERSION.json.public_released=true`:

* v1 contracts may receive **non-breaking** edits.

### Post-release behavior (immutability activated)

After `public_released=true`:

* `*_v1.schema.json` is immutable
* `*_v1.schema.sha256` is immutable

Any change must become a new major version:

* `*_v2.schema.json`
* `*_v2.schema.sha256`

---

## Changelog Policy (Required)

Any change to:

* `contracts/*.schema.json` or
* `contracts/*.schema.sha256`

MUST include a change to:

* `contracts/CHANGELOG.md`

And the changelog **diff** must mention each changed contract stem (e.g. `smart_guitar_toolbox_telemetry_v1`).

This prevents "touched changelog but empty/no-op" and ensures reviewable intent.

---

## CI Enforcement (Tiny Gate)

A repository-local CI gate enforces:

1. **SHA format**

* all `contracts/*.schema.sha256` must be a single 64-hex lowercase line

2. **Changelog discipline**

* if any schema/hash changes, `contracts/CHANGELOG.md` must change
* and the **diff** must mention each changed contract stem

3. **v1 immutability after public release**

* if `public_released=true`, any touched `*_v1.schema.json` or `*_v1.schema.sha256` fails CI

Gate implementation is intentionally:

* repo-local (uses `git diff <base>...HEAD`)
* does not call GitHub APIs
* does not fetch other repos
* fails fast with explicit reasons

---

## Update Workflow (ToolBox → Smart Guitar)

### ToolBox contract update

1. Open PR against ToolBox.
2. Update `contracts/*.schema.json`
3. Update `contracts/*.schema.sha256`
4. Update `contracts/CHANGELOG.md` with an entry that includes the contract stem
5. Merge to ToolBox `main` (this is the publish signal)

### Smart Guitar sync after publish

1. Copy the schema file from ToolBox `main` into Smart Guitar `contracts/`
2. Copy the matching `.schema.sha256`
3. Update Smart Guitar `contracts/CHANGELOG.md` referencing the same contract stem
4. Smart Guitar CI enforces parity + governance rules.

---

## Breaking Change Definition (Operational)

Breaking includes any of:

* removing required fields
* changing types
* tightening enums in a way that rejects previously valid payloads
* changing required/optional status
* changing `additionalProperties` behavior in a restrictive way

Breaking changes require:

* a new major schema version (v2, v3, …)
* and must not modify v1 once public released.

---

## Future Evolution (v1 → v1.1, optional)

Scenario B may later adopt **semantic parity** (normalized JSON hashing) to reduce formatting-only churn.

This evolution MUST:

* preserve the governance rules above (changelog, immutability, publish signal),
* and only replace the parity calculation method.

---

## Appendix: Why Scenario B Exists

Scenario B is a deliberate "moat" mechanism:

* ToolBox remains a manufacturing/governance system
* Smart Guitar remains a separate ecosystem
* Contracts are the sole boundary
* CI prevents silent drift and feature creep across that boundary
