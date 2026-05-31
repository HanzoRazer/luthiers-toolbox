# Three-Loop / Vectorizer AGE Conflation — Reproducible Evidence Packet

**Purpose:** Settle the conflation question with primary-source, machine-checkable
evidence. Every claim below is a command you run yourself plus the exact output.
No narrative, no interpretation required to verify. If your output differs, the
claim is wrong — that is the point.

**Anchored to:** `luthiers-toolbox` @ commit `7210d780ace78cf3be493e66c1219c04a78692a7`
(`fix/toolpath-animation`), and `vectorizer-sandbox` @ `HEAD`.
Run `git rev-parse HEAD` in each repo first; if the runtime SHA differs, re-verify.

> **What "the conflation" means, stated precisely:** CLAUDE.md (the runtime
> instruction file) at one point declared a *three-loop feedback architecture* +
> an *Agentic Guidance Engine (VectorizerAGE)*, naming classes `ValidatedExtractor`,
> `AdaptiveExtractor`, `VectorizerAGE`, and framed it as **"APPROVED DESIGN — DO NOT
> BYPASS."** The conflation claim is: **that architecture was never approved and
> never implemented — it is a documentation artifact, not a deployed system.** The
> facts below test exactly that, and nothing more.

---

## FACT 1 — The named architecture exists in ZERO code files (both repos)

```bash
# Runtime repo — class definitions (git-tracked .py only):
git -C luthiers-toolbox grep -nE "class (ValidatedExtractor|AdaptiveExtractor|VectorizerAGE)\b" -- '*.py' | wc -l
# => 0

# Sandbox repo — same:
git -C vectorizer-sandbox grep -nE "class (ValidatedExtractor|AdaptiveExtractor|VectorizerAGE)\b" -- '*.py' | wc -l
# => 0

# Runtime — ANY mention of the names in any .py (excluding archive/):
git -C luthiers-toolbox grep -lE "VectorizerAGE|ValidatedExtractor|AdaptiveExtractor" -- '*.py' | grep -v archive | wc -l
# => 0
```

**Result: 0 / 0 / 0.** The three named classes are defined nowhere, instantiated
nowhere, imported nowhere, in either repository. This is the load-bearing fact.

---

## FACT 2 — The names appear ONLY in markdown (prose), and only 5 files

```bash
git -C luthiers-toolbox grep -lE "VectorizerAGE|ValidatedExtractor|AdaptiveExtractor"
```
```
CLAUDE.md
docs/handoffs/DEV_HANDOFF_2026-05-30_THREE_LOOP_CONFLATION_REMOVAL.md
docs/handoffs/FEEDBACK_LOOP_SYSTEM_HANDOFF.md
docs/handoffs/VECTORIZER_GEOMETRY_AUDIT_HANDOFF_2026-05-11.md
docs/handoffs/VECTOR_1B_LOOP2_PROVENANCE_AUDIT.md
```
All 5 are `.md`. Every occurrence of the architecture is a *description*, never an
implementation. (File-extension tally: `5 md`, `0 py`.)

---

## FACT 3 — CLAUDE.md has ALREADY been corrected (commit-anchored)

```bash
git -C luthiers-toolbox grep -nE "EXPERIMENTAL, SANDBOXED|never approved|DO NOT BYPASS|APPROVED DESIGN" -- CLAUDE.md
```
```
CLAUDE.md:218:## VECTORIZER ARCHITECTURE NOTES (three-loop / AGE) — EXPERIMENTAL, SANDBOXED
CLAUDE.md:224:> "VECTORIZER ARCHITECTURE DECISION — DO NOT BYPASS / APPROVED DESIGN." That framing was
CLAUDE.md:227:> - The three-loop feedback architecture (+ AGE) is **experimental, was never approved
```
Line 218 is the *current* header (EXPERIMENTAL, SANDBOXED). Line 224 quotes the old
"DO NOT BYPASS / APPROVED DESIGN" language **only to retract it.** The single commit
that did this:

```bash
git -C luthiers-toolbox log --oneline -S "EXPERIMENTAL, SANDBOXED" -- CLAUDE.md
# => 8fad48d9 docs: remove three-loop/AGE "approved design" conflation from runtime instructions
```
The fix is real, in history, and named for exactly what it is.

---

## FACT 4 — What IS real runtime code (so the correction is not "delete everything")

The scale-validation gate is genuine, shipped, and **independent of the three loops:**
```bash
git -C luthiers-toolbox grep -nE "def _safe_dxf_save|def validate_scale_before_export" -- services/blueprint-import/vectorizer_phase3.py
# => :104:def _safe_dxf_save(...)
# => :2336:def validate_scale_before_export(...)
```
The conflation removal does **not** touch this. Real code stays; only the unbuilt
"approved architecture" narrative was corrected.

---

## FACT 5 — Two-repository model is real (collision surface is real too)

```bash
# Same filename, different file, on the runtime import seam — a genuine collision risk:
git -C luthiers-toolbox show HEAD:services/api/app/util/dxf_compat.py        | wc -l   # => 176
git -C luthiers-toolbox show HEAD:services/blueprint-import/dxf_compat.py    | wc -l   # => 200

# Runtime vs sandbox copy of the main vectorizer — sandbox is a stale snapshot:
git -C luthiers-toolbox  show HEAD:services/blueprint-import/vectorizer_phase3.py | wc -l  # => 4182
git -C vectorizer-sandbox show HEAD:src/incubation/vectorizer_phase3.py          | wc -l  # => 3407
# delta = 775 lines; sandbox scale-gate hits = 0 (it predates the gate)
```
These confirm the *seam* the remediation is protecting is real, while keeping the
two facts separate: (a) the AGE architecture is unbuilt (FACT 1), and (b) the
runtime↔sandbox import seam has real collision risk worth fixing. Don't let anyone
merge those two into one claim — they are independent.

---

## How to read this packet

- **FACT 1 is the whole argument.** If three classes framed as "approved, do not
  bypass" exist in zero code files, the "approved design" framing was unsubstantiated.
- **FACT 3 shows it's already fixed in docs** (commit `8fad48d9`), so the dispute is
  not "should we fix it" — it's done; this packet just lets you confirm it independently.
- **FACTS 4–5 prevent the opposite over-correction:** real code and a real collision
  risk remain and should not be discarded along with the retracted narrative.

Every number here is regenerable. If a future commit changes them, re-run the
commands — the packet is the method, not just the snapshot.
