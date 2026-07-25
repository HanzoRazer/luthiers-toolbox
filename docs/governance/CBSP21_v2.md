# CBSP21 v2 — Computer Bot Scoping Protocol
### Reinstated 2026-07-24 as a true gate, not a social contract

> **Original intent (2025-12-21):** stop a bot from reading 50% of a document and
> answering as if it read all of it. Under-scoping of source material.
>
> **Why the original failed:** it was a ~100-word markdown note — a *social contract*.
> Terminals routed around it; it was "mostly ignored unless called out each turn." A
> fence that only asks does not hold. (It then drifted into the patch-manifest apparatus
> now named RPMCC24 — a different job entirely; see [RPMCC24_CHARTER.md](RPMCC24_CHARTER.md).)
>
> **This version has teeth.** Same intent, structural enforcement.

---

## The rule (still ~100 words, because the intent was always simple)

Before answering from any provided document, file, or upload, the responder must **declare
the scope it actually consumed**:

- **what** was read (files, sections, line ranges — not "the document"),
- **how much** of the available material that represents,
- **what was NOT read** and why (truncated, skipped, unavailable),
- and it must **not** present a partial read as a complete one.

If scope is incomplete, say so **before** answering, and either complete the read or bound
the answer to what was actually covered. A partial read presented as whole is a CBSP21
violation.

---

## Why the original didn't hold, and what changes

| Original (social) | v2 (structural) |
|---|---|
| A note asking for complete reads | An explicit **scope declaration** the answer must carry |
| Enforced by the reader's goodwill | Enforced by a **required, checkable artifact** |
| Ignorable — "pretend not to see it" | **Absent declaration = incomplete answer**, by definition |
| Re-issued every turn by the human | Stated once, structurally expected every turn |

**The February lesson applied:** the luthiers-toolbox was full of social contracts that
didn't hold until they were converted to structure (branch protection, required checks,
process-exclusive authority). CBSP21 v2 is that same conversion, applied to the reading
problem instead of the merging problem.

---

## How to give it teeth (pick the enforcement level that fits)

CBSP21 v2 is a *pattern*; enforce it at whichever level is available:

1. **Response-level (immediate, zero-infra).** Every answer drawn from a document opens with
   a one-line scope stamp: `SCOPE: read <what>, <N%> of available, did NOT read <what>`.
   An answer without the stamp is treated as unscoped and untrusted. This alone restores the
   original intent — it makes the omission *visible* instead of silent. **This is the level
   adopted now** — a documented convention, no code.
2. **Prompt-level (durable).** The scope-declaration requirement lives in the system/setup
   so it is expected structurally, not re-issued per turn. This is what the original note
   should have been but couldn't be in 2025. **Named as the durable follow-up** (a
   `CLAUDE.md` rule or a hook) — its own small change, not part of this docs pass.
3. **Artifact-level (strongest, for pipelines).** When a bot processes documents in an
   automated flow, emit a scope manifest alongside the output (read-set, coverage, skipped)
   and gate on it — the RPMCC24 pattern, applied to reads: no scope manifest, no accepted
   output. **Deferred** — build only if/when an automated document-processing pipeline needs
   it; do not build it speculatively.

The point is identical at every level: **make the under-scope loud.** The original failed
because under-scoping was silent and the rule was optional. v2 makes the scope *declared* —
so a partial read can't masquerade as a whole one, because the absence of the declaration
is itself the tell.

---

## Provenance
- `2025-12-21` — CBSP21 v1 created (100-word social contract). Ignored in practice; drifted.
- `2026-07-24` — CBSP21 v2: original anti-under-scoping intent reinstated as a structural
  scope-declaration gate. The patch-manifest apparatus that CBSP21 v1 drifted into is
  renamed RPMCC24 and governed separately ([RPMCC24_CHARTER.md](RPMCC24_CHARTER.md)). Two
  fences, two jobs.
- **Owner:** Ross (HanzoRazer).
