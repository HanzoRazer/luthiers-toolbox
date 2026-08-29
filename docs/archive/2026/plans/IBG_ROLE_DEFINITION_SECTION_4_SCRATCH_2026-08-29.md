# Scratch: IBG evaluator / selection scope (unmerged PR #336)

**Status:** SCRATCH — not governance, not ratified, not owed  
**Copied from:** unmerged PR #336 (`cursor/ibg-role-definition-amendment-5bd1`, commit `a6b5fea8`)  
**Why this file exists:** PR #336 is being closed without merge. The §4 evaluator language
existed only on that branch. This copy keeps it retrievable. It does not amend
`IBG_ROLE_DEFINITION.md` and does not authorize a selector.

H0 (AGE ≠ IBG) is unaffected. This text never landed on `main`.

---

## Evaluation and selection scope (from PR #336 §4)

The repository holds several render technologies, none of which satisfies quality, file size,
and text fidelity simultaneously. Selecting and composing among them requires a component that
knows what an instrument body is. IBG is the only production component that holds that
knowledge.

IBG **may** therefore:

| Capability | Scope | Constraint |
|---|---|---|
| Evaluate a candidate outline against instrument-domain knowledge | `INSTRUMENT_SPECS`, `FAMILY_DEFAULTS`, landmark constraints, expected dimensions | Returns a judgement, never a mutation of the input |
| Evaluate **several** candidate outlines from different render lanes in one call | A portfolio, not a single result | Same constraint |
| Return a selection and a stated reason to an upstream caller | Advisory response only | The caller decides; IBG does not invoke a renderer |
| Persist which lane succeeded against which document signature | The Loop 2 strategy cache | Cache is advisory; a cache hit never bypasses evaluation |
| Use non-deterministic reasoning **in the evaluator** | Evaluation and selection only | The solver stays deterministic; an evaluator's verdict may not alter solver output |

Former role-definition sentence: *"IBG is a one-way consumer of vectorizer output. No feedback loop exists upstream."*

Replacement proposed on #336 (not landed):

```text
IBG is a downstream consumer of render output AND an advisory evaluator of it.
An upstream feedback path is permitted. It is advisory in both directions:
IBG does not select on the caller's behalf, and the caller does not gain
authority over IBG's math by supplying candidates.
```

Pipeline sketch from #336 §6 (not landed):

```text
Render lanes (upstream, plural)
    │  candidate outlines
    ▼
IBG evaluator ──────── advisory selection + reason ────► caller
    │  selected outline
    ▼
IBG solver  (deterministic, locked)
    │  solved body model
    ▼
CAM pipeline (downstream)
```

The evaluator and the solver are separate concerns inside one package. The solver's contract is
unchanged by the presence of the evaluator, and the solver must remain callable without it.

---

*Scratch only. Implementation still requires its own Dev Order.*
