# LTB-R12-002 — Divergence Record

**Order:** LTB-R12-002 (§9.11 — divergences from the repair source, enumerated with reasons)
**Repo:** `luthiers-toolbox`, branch `fix/ltb-r12-002`, base `main` @ `22e6768`
**Repair source:** `vectorizer-sandbox` `origin/master` (`e32e9da`), `scripts/vectorize/r12_convert.py`
**Date:** 2026-09-17
**Method:** every row below was **measured** against this branch, not read from source (D2).

---

## 1. §9.3 was never executed — correction

**§9.3 requires:** *"All 30 collected tests pass with no assertion, fixture or expected
value modified."*

**It was not performed, and no commit on this branch attempted it.** The branch is:

```
3294fd04 reproduce G1-G4     8ddffc9d consolidator fixture   219e4767 repair G1's endpoint test
26865f7e G1                  533c40b1 G2                     65be53c4 G4
75bdf42e G3                  57e10f65 D5
```

Nothing adds the sandbox suite. `services/api/tests/test_r12_convert.py` is **LTB's own
file from PR #381**, not the transported suite:

| | sandbox `tests/skills/test_r12_convert.py` | LTB `services/api/tests/test_r12_convert.py` |
|---|---|---|
| test functions | 28 (30 collected) | 10 |
| names in common | **0** | **0** |

**A claim made on this mistake must be withdrawn.** Commit `75bdf42e`'s message states
"76 passed locally on 3.13 (the 30 transported tests included)". The 76 were real; the 30
were not among them. The file was assumed to be the transported suite and the assumption
was never checked.

**How it surfaced.** Commit 7 broke `test_custom_linetype_is_refused`. Modifying a
transported assertion is D1/A4's stop-for-review trigger, so the provenance was checked
before touching it — and there was no transport to violate. Had that test not broken,
§9.3 would have been reported met on an unexamined assumption.

**Ruling (owner, 2026-09-17): do not run the 28 against LTB's module.** They would fail on
design differences that are neither gaps nor divergences, each needing adjudication —
defect, valid alternative, or a test asserting sandbox internals. That is a pile of
judgement calls, not a result. §2 below is what replaces it.

---

## 2. The delta, measured

**Correction to the framing that prompted this section.** On finding the test inventories
disjoint, the working conclusion was *"two independent implementations, not a copy."*
**The measurements do not support that, and it is withdrawn.** The module was transported;
only the tests were not:

- LTB's module docstring: *"Transported from vectorizer-sandbox PR #101."*
- Private helpers with identical names in both: `_carry`, `_table_attributes`,
  `_semantics`, `semantic_record`, `verify_saved_file`, `FORMAT_LIMITED_LAYER_ATTRIBUTES`.
- **20 of 21 probed behaviours are identical.** Independent designs do not agree that often.

The accurate statement: **one transported module, two test suites, and drift since.** The
divergence surface is therefore small and enumerable — which is what the table shows —
rather than unbounded.

Each row exercises LTB's module directly. The sandbox suite was **not** run.

| # | Behaviour the sandbox suite asserts | LTB, measured | Verdict |
|---|---|---|---|
| 1 | LWPOLYLINE → R12 POLYLINE, shape intact | POLYLINE, 4 vertices, closed, `{'LWPOLYLINE->POLYLINE': 1}` | same |
| 2 | No entity lost source → saved | `missing_from_saved_file == []` | same |
| 3 | Layer and style tables carried | `BODY.color=3`, `NOTES` defined in saved styles | same |
| 4 | Verification reopens the written file | reopens from disk in `verify_saved_file` | same |
| 5 | The gate is semantic, not a count | LWPOLYLINE→POLYLINE accepted as equal meaning | same |
| 6 | A moved vertex fails though counts match | `FidelityError` | same |
| 7 | A moved vertex **z** fails | `FidelityError` | same |
| 8 | A lost **bulge** fails | `FidelityError` (see caution B) | same |
| 9 | A lost layer definition fails | `FidelityError` | same |
| 10 | A changed style font fails | `FidelityError` | same |
| 11 | A changed text alignment fails | `FidelityError` | same |
| 12 | LWPOLYLINE elevation survives as POLYLINE elevation | `Vec3`, z=5.0 | same (G1) |
| 13 | Custom linetype name is carried | carried, `{'status': 'created', 'pattern': [0.25, 0.25]}` | same (D5.2) |
| 14 | Reserved layer `0` updated from source | `color=5` | same (G2) |
| 15 | Reserved `Standard` style updated | `font=arial.ttf` | same (G2/G4) |
| 16 | INSERT refused, not copied | refused | same |
| 17 | Paper-space refused | refused | same |
| 18 | R12-impossible entities refused, not dropped | SPLINE refused | same |
| 19 | Success replaces the destination | `AC1009` written | same |
| 20 | Unconvertible leaves the destination intact, no temp | preserved, `temp_left=none` | same (G3) |
| 21 | `convert_file` forwards an R12 encoding | `encoding` parameter present, cp1252 save OK | same |
| 22 | Format-forced losses reported, not hidden | `{'BODY': {'true_color':…, 'lineweight':50, 'plot':1}}` | same |
| 23 | `semantic_record` refuses unimplemented types | `FidelityError` | same |
| 24 | Failure types carry exit codes | `ConversionError=3, UnconvertibleEntity=7, FidelityError=8` | same |
| 25 | The old `add_foreign_entity` path loses the contour | saved **EMPTY** vs `['POLYLINE']` | same |
| **26** | **An unsupported target version is refused** | **`convert_document(doc, "R2000")` → ACCEPTED, produced `AC1015`** | **DIVERGES** |

### Row 26 — the one divergence still open

`_require_r12` exists in the sandbox and **not** in LTB (`hasattr → False`). Measured:

```
convert_document(doc, "R2000")   -> ACCEPTED, produced AC1015
convert_document(doc, "R13")     -> DXFVersionError   (ezdxf's, not ours)
convert_document(doc, "nonsense")-> ValueError        (ezdxf's, not ours)
convert_file(..., "R2000")       -> ACCEPTED
```

A module named `r12_convert` will produce a non-R12 document on request, and the report
will label it correctly while every guarantee around it assumes R12: `R12_VERIFIED` types,
the `AC1009`-keyed format-limited tables, LWPOLYLINE→POLYLINE conversion. The refusals for
`R13` and `nonsense` come from ezdxf by accident, not from a contract.

**No production exposure:** the only endpoint hardcodes `"R12"`, and the two client
callers (§3) do not pass a version. This is a latent trap for the next caller, not a live
defect.

**Not fixed here.** §13 scopes this order to G1–G4 plus the two named divergences, and
adding a refusal is a behaviour change nobody asked for. It wants a one-line order:
restore `_require_r12` in `convert_document`, with a test.

---

## 3. Endpoint behaviour change, per caller

One caller-visible change ships in this branch. Both callers are read-only consumers of
the response; neither inspects `conversion_report`.

| Caller | File | Effect |
|---|---|---|
| CurveLab | `packages/client/src/api/curvelab.ts:37` | A DXF using a custom linetype now returns **200** where it returned **422**. No client change required; a previously-failing file now succeeds. |
| DXF preflight toolbox | `packages/client/src/components/toolbox/dxf-preflight/useDxfPreflightValidation.ts:104` | Same. Error-handling paths for 422 remain correct for the refusals that still apply (SPLINE, INSERT, paper-space, 3D polyline). |

**Nothing that used to succeed now fails.** The change is strictly a narrowing of the
refusal set. `convert_file`'s new same-path refusal (D5.1) is not reachable from either
caller — the endpoint writes to a `NamedTemporaryFile` it creates.

---

## 4. `ezdxf` — recorded, not pinned (A1)

| | |
|---|---|
| Declared requirement | `services/api/requirements.txt:38` → `ezdxf>=1.1.0` (**unchanged**) |
| Validated locally | **1.4.2** (Python 3.13, the interpreter this branch's tests run under locally) |
| Validated in sandbox | **1.4.3** |
| CI | whatever `>=1.1.0` resolves to; CI is the verdict per A5 |

Both 1.4.2 and 1.4.3 produce the measurements above. Not pinned, per A1: two files declare
`ezdxf>=1.1.0` and pinning one splits them.

---

## 5. Measurement cautions

Recorded so nobody re-derives them as findings.

**A. `layers.add(name, dxfattribs={...})` is accepted and silently ignored.** The signature
is `add(name, *, color=…, linetype=…, …)` — keyword-only. A fixture written as
`doc.layers.add("GUIDE", dxfattribs={"linetype": "HIDDEN2"})` produces a layer whose
linetype is still `Continuous`, with no error. One fixture in
`test_r12_convert_divergences.py` was built this way and asserted real behaviour against a
document that never had the attribute set — **a test measuring nothing looks identical to
one measuring correctly.** That fixture now asserts its own construction before proceeding.

**B. The first bulge probe was vacuous and its result was wrong.** It built a contour with
no bulges, then "removed" bulges that were already `0.0`, and reported that LTB fails to
detect bulge loss. LTB records bulge (`r12_convert.py:402`) and detects its loss; row 8 is
the corrected measurement, taken with a real arc (`format="xyseb"`, bulge 0.5). **A probe
whose mutation changes nothing reports the absence of a check that is present.**

**C. A leak check must diff, not glob.** See commit `75bdf42e`: a script globbing
`*.dxf.tmp` in the shared system temp directory reported survivors left by an earlier
mutation experiment. Snapshot before, assert on the difference.

**D. `git show master:<path>` on a stale local ref reports a file absent that exists.**
Local `master` was 4 commits behind `origin/master`; the repair source resolved only
against `origin/master`. Appendix C's verification used `origin/master` and stands, but its
prose says "anchor to `master`" — on a stale clone those differ.
