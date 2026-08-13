# Developer Handoff — An Exact-Zero Invariant Made Unreachable by Valid Input

**Date:** 2026-07-21 · **Origin:** Master All Strings, PR #3 (DO-003) · **Status:** found, fixed, verified

A real defect, caught during implementation. Written up because the failure *shape* is one that geometry and toolpath code is structurally prone to, and it produced no error of any kind.

Everything below is reproducible in this repository. Section 4 asks other teams to run one command against their own code; it reports nothing about their code and asserts nothing about it.

> Merge-order note: the referenced source lands with PR #3. Merge this after it.

---

## 1. The invariant

`SpatialPosition` binds open-string identity to an exact float equality (`models.py:187,191`):

```
is_open_string == True   ⟺   relative_semitone_position == 0.0
```

`relative_semitone_position` is **derived**, not supplied:

```python
relative = event.midi_note - string.open_midi_note - constraints.capo_position
```

## 2. The incident

A capo at fret 2 is `capo_position = 2.0`. Nothing in the contract forbids `2.5` — it is finite, non-negative, and passes every validator on `MappingConstraints`.

`midi_note` and `open_midi_note` are integers. So with `capo_position = 2.5`, `relative` is always half-integral and **can never equal 0.0**. The biconditional's left side becomes unsatisfiable, and every open-string candidate silently disappears — for every pitch, on every string:

```
capo=2.0: pitches that can be an OPEN string anywhere = 6
capo=2.5: pitches that can be an OPEN string anywhere = 0
```

No exception. No validation failure. Every candidate still valid, in range, correctly ordered, contract-conformant. The result set is simply **missing a category**, and the count of what is missing is zero — so there is nothing to compare against.

### The guard that existed did not work

There *was* a fretted-instrument check. It tested the wrong quantity — it validated `physical_semitone_position_from_nut`:

```python
physical = event.midi_note - string.open_midi_note   # capo not involved
```

That value is integer minus integer. **It is always integral, so the guard could never fire.** The fractional value lands in `relative`, which the guard never inspected. It read as protection and was none.

### What caught it

Not review, and not the guard. A test written from the *intent*:

```
test_fractional_capo_on_fretted_instrument_is_rejected
E  Failed: DID NOT RAISE SpatialMappingError
```

The test asserted the outcome the design required rather than the code path the implementation took, so it failed where the guard passed.

### The fix

Validate the quantity that actually carries the fraction, where the instrument mode and the constraint meet (`candidate_generation.py:141-148`) — a capo clamps behind a fret, so a fractional capo on a fretted instrument is inconsistent input, not an unusual one.

Separately, `_snap_to_integer` (`candidate_builders.py:53`) keeps `relative` exactly `0.0` when it is integral to within tolerance, so ordinary float noise cannot make the equality unreachable either.

## 3. The shape

> An exact-equality test on a **derived** value, where valid upstream input shifts the value off the tested lattice, making the branch unreachable and deleting a whole class of output without error.

Three properties, all present above:

- **The guard can sit on the wrong term.** The quantity that stays well-behaved is the one that gets checked; the fraction lands elsewhere.
- **Nothing is invalid.** No duplicate, no range violation, no bad type. Every individual output is correct. Only the *set* is wrong.
- **Absence has no signature.** A wrong value can be diffed against an expected value. A missing category diffs against nothing.

## 4. The check for other repositories

We have not read your code and are reporting nothing about it. This is a command to run.

**Step 1 — find exact-equality tests on floating-point values:**

```bash
git grep -nE '(==|!=)\s*0(\.0)?\b|\bis_zero\b|==\s*[0-9]+\.[0-9]+'
```

**Step 2 — for each hit, ask two questions:**

1. Is the compared value **derived** from arithmetic, or supplied directly? Supplied values are fine; derived ones are the candidates.
2. Is there an input that is **valid but unusual** — a fractional offset, a non-integral step, a rotated or scaled origin — that would move the value permanently off the tested value?

If yes to both: what disappears when that branch stops firing, and would anything say so?

**Step 3 — check the guard, if one exists.** Confirm it inspects the term that actually carries the variation. Ours did not, and it looked correct.

Highest-yield locations are exact-zero comparisons on computed geometry: depth or offset at zero, origin and seed-point detection, retract or clearance-plane equality, closure tests on a contour. The question is not whether the comparison is correct for ordinary input — it is whether some *legitimate* input makes it never true.

**Negative results are worth reporting.** An absent report cannot be distinguished from an absent check.

## 5. Status here

Fixed in DO-003, pinned by `test_fractional_capo_on_fretted_instrument_is_rejected` and `test_snapping_keeps_the_open_string_biconditional_exact`. 264 tests pass; 100% line coverage on both affected modules.

No open item remains in this repository. This document exists for the shape, not for an outstanding fault.
