# DXF gate repair audit — old vs new, rule by rule (2026-09-14)

> **Later corrections (landed with DXF-CATALOG-GATE-001; the audit text below is kept as written):**
> - **Versions.** Ruling 3 below (R2010 allowed for classified stored catalog files) is **superseded**.
>   Owner ruling 2026-09-14: only R12 is approved; R2000 is allowed only in the canonical vectorizer
>   system (bucket ①, paid-tier `cam_ready_r2000`). Stored catalog files are R12 only, with no R2000 or
>   R2010 allowance.
> - **Closed R12 POLYLINE (F5).** This audit recommended treating a closed POLYLINE as CAM-compatible.
>   That is **reversed**: the runtime export pre-check (DXFPreflight) rejects POLYLINE-only files, and the
>   CAM lanes behind the export gate read closed LWPOLYLINE only. Accepting POLYLINE in CI would claim
>   export-readiness the runtime does not grant. The four POLYLINE bodies carry quarantine records instead.
> - **P1 (CRLF)** is fixed on main by #372; the Files gate import crash by #372's second commit.
> - Resolution of every rule is in `docs/investigations/dxf_catalog_gate_classification_2026-09-14.md`.

**Status:** read-only audit. No gate code changed. Evidence for the dedicated DXF gate repair PR.
**Subject:** the 16 gate-repair commits that were on PR #370 (`0f52d4bb..ed592d50`), reverted out of
#370 by `ec377a68` and preserved intact on branch `ci/dxf-gate-repair-001` (head `ed592d50`).
**Old** = gate code at `5fc483e4` (identical to main `0679dbf6` for every gate file).
**New** = gate code at `ed592d50`.
**Toolchain:** Python 3.11.9, ezdxf 1.4.4, shapely 2.1.2. These are the versions the CI jobs install.
**Catalog:** the 95 DXFs under `services/api/app/instrument_geometry/` at `ed592d50` (byte-identical to
the git blobs; `.gitattributes` has `*.dxf binary`, so CI sees these exact bytes).

## Owner rulings this audit is measured against (2026-09-13)

1. #370 is custody-only; the gate repair gets its own PR. **Done:** `ec377a68`. #370 is back to
   `UNSTABLE` with all 12 required checks green.
2. The Files gate stays an **export-readiness** gate. Files that fall short are fixed or go on a
   **named quarantine/exception list with reason and owner**. No blanket downgrade to warnings.
   Body-outline rules apply only where the asset class requires one.
3. LTB *emits* R12/R2000 only. R2010 is allowed for *stored catalog* files only when explicitly
   classified.
4. Open outlines in a named body DXF are defects unless the file or registry says otherwise.
   `LesPaul_CAM_Closed.dxf` is a separate DXF-integrity finding, not INV-037 remediation.
5. Complexity stays under 15; do not raise baselines to make a gate pass.

## Headline

- **Keep:** the lazy import, R12 LINE-loop recognition, closed R12 POLYLINE acceptance, and the
  empty-modelspace hard failure (it *tightens* the old gate).
- **Reject:** every change that turns an ERROR into a warning: open outline, self-intersection,
  preflight crash, no closed contour. These let real malformed body outlines through
  (`Stratocaster_body.dxf`, `harmony_h44_body.dxf`, `concert_ukulele_body.dxf`,
  `octave_mandolin_body.dxf`).
- **Rework:** the global R2010 allowance becomes a per-file classified allowlist, and CIRCLE stops
  counting as a body contour.
- **Found along the way, pre-existing, separate orders:** the export gate's self-intersection check
  is **blind to CRLF DXFs** (73 of 95 catalog files are CRLF); proven through
  `enforce_dxf_validation`. Details in §4.

## 1. Witness results (synthetic, 22 files)

Body shape: 64-point ellipse, 350 × 450 mm. "PASS~W" means passed with warnings.
LF line endings unless marked CRLF.

| Witness | Label | Assets old | Assets new | Files old | Files new |
|---|---|---|---|---|---|
| W01 R12 closed LINE loop | VALID | FAIL | PASS | PASS | PASS |
| W02 R12 open LINE chain (1 segment missing) | MALFORMED | FAIL | **PASS~W** | PASS | PASS |
| W03 R12 half body closed by a centreline LINE | AMBIGUOUS | FAIL | PASS | PASS | PASS |
| W04 open body LWPOLYLINE + closed border rectangle | MALFORMED | PASS | PASS | FAIL | **PASS~W** |
| W05 lone 6 mm CIRCLE, no body | MALFORMED | FAIL | **PASS~W** | PASS | PASS |
| W06 R2010 closed LWPOLYLINE | VALID* | FAIL | PASS | PASS | PASS |
| W07 R2013 closed LWPOLYLINE | MALFORMED | FAIL | FAIL | PASS | PASS |
| W08 symmetric bow-tie (zero net area) | MALFORMED | PASS~W | PASS~W | CRASH | CRASH |
| W09 open LWPOLYLINE only | MALFORMED | FAIL | **PASS~W** | FAIL | **PASS~W** |
| W10 R12 closed POLYLINE | VALID | PASS | PASS | FAIL | PASS~W |
| W11 closed SPLINE only | AMBIGUOUS | FAIL | PASS~W | FAIL | PASS~W |
| W12 TEXT only | MALFORMED | FAIL | FAIL | FAIL | FAIL |
| W13 empty modelspace | MALFORMED | FAIL | FAIL | **PASS** | FAIL |
| W14 good body + 2-point LWPOLYLINE | MALFORMED | PASS | PASS | FAIL | FAIL |
| W15 R12 LINE bow-tie | MALFORMED | FAIL | **PASS~W** | PASS | PASS |
| W16 closed LWPOLYLINE (control) | VALID | PASS | PASS | PASS | PASS |
| W17 R12 closed LINE loop + dangling mark | VALID | FAIL | PASS | PASS | PASS |
| W18 R12 LINE loop with a 0.5 mm gap | MALFORMED | FAIL | **PASS~W** | PASS | PASS |
| W19 figure-8 closed LWPOLYLINE (non-zero area) | MALFORMED | PASS~W | PASS~W | FAIL | **PASS~W** |
| X01 W19 saved with CRLF | MALFORMED | PASS~W | PASS~W | **PASS** | **PASS** |
| X02 W16 saved with CRLF | VALID | PASS | PASS | PASS | PASS |
| X03 lone 2-point LWPOLYLINE, CRLF | MALFORMED | FAIL | **PASS~W** | FAIL | FAIL |

Bold = a malformed file that the gate accepts.

## 2. Real catalog results (95 files)

| Gate | Old | New |
|---|---|---|
| Assets | 19 pass / 76 fail | 95 pass / 0 fail |
| Files (logic run locally; in CI the old job crashes at import and checks nothing) | 81 pass / 14 fail | 94 pass / 1 fail |

Catalog classes by directory: `body/dxf/acoustic` 11, `body/dxf/electric` 18, `body/dxf/other` 4,
`reference_dxf/cuatro` 62.

## 3. Rule by rule

### Files gate — `services/api/app/ci/check_dxf_files.py` (born fail-closed for export, `34388e38`)

**F0. Import isolation** (`dxf_advanced_validation.py`, `dxf_compat` import moved into the two test
fixture functions).
Old: the CI job dies at import (`fastapi` is not installed), so it checks nothing. New: it runs all 95
files (CI run on `ed592d50`). The `ci/file_size_baseline.json` bump (620 → 623) is exactly this
edit: 1 line removed, 4 added. **KEEP both.**

**F1. Version compare: string → numeric.** Behaviour is the same for every real `AC1xxx` code;
no witness differs. **Neutral.** Gap it does not close: the Files gate has no maximum version, so W07
(R2013) passes both old and new. Ruling 3 needs a maximum here.

**F2. Empty modelspace → hard fail (new).** Old *passed* an empty DXF (W13); new fails it.
**KEEP.** This is a real tightening.

**F3. No drawable geometry → hard fail (new).** W12 fails both; the new message is clearer.
**KEEP.**

**F4. Open LWPOLYLINE: ERROR → warning.** Malformed now accepted: W04, W09. Real files: 8.
- In 5 of them, the open polyline is on a `BODY_POINTS` layer next to a clean closed
  `BODY_OUTLINE`: `classical_body`, `dreadnought_body`, `gibson_l_00_body`, `om_000_body`,
  `soprano_ukulele_body`. These paths revisit their own vertices (31 to 865 repeats), so they are
  point data, not contours. That's a legitimate reason to exempt the *layer*.
- In 3 of them the open polyline *is* the body outline: `harmony_h44_body`, `concert_ukulele_body`,
  `octave_mandolin_body`.

**REJECT the blanket downgrade.** Replace it with declared layer classes: `BODY_POINTS` is
reference-only; `BODY_OUTLINE` must be closed.

**F5. "No CAM-compatible entities" → warning when POLYLINE/SPLINE/ELLIPSE present.**
Valid witness formerly rejected: W10 closed R12 POLYLINE. Real files: `carlos_jumbo_body`,
`mandolin_body`, `jaguar_body`, `mustang_body`, each one closed R12 POLYLINE. Also accepted:
W11, closed SPLINE only (ambiguous). From reading the code (no witness built): any file whose only
geometry is an *open* POLYLINE, SPLINE or ELLIPSE is accepted too, because the downgrade keys on the
entity *type* being present, not on the entity being closed. **KEEP the intent, narrow it:** treat a *closed* POLYLINE as
CAM-compatible. Nothing else is downgraded.

**F6. Self-intersecting polygon: ERROR → warning.** W19: old FAIL → new PASS. Real files: 8.
5 are the `BODY_POINTS` point paths above. 3 are real body outlines:
- `Stratocaster_body.dxf`: the only entity, a closed `BODY_OUTLINE`, is an invalid ring. It spans
  322 × 459 mm but its net area is 5 mm², with 26 repeated vertices, so it folds back on itself.
  **This is the real-catalog malformed witness that the new gate lets through.** It also passes the
  Assets gate, old and new.
- `concert_ukulele_body.dxf` and `octave_mandolin_body.dxf`: open outlines that cross themselves.

**REJECT.**

**F7. Preflight crash → "skipped" warning (was FAIL).** No witness triggered a crash, so this rule
is unmeasured. **REJECT on contract:** a check that crashed has not passed. In a fail-closed gate
that is a failure.

**F8. Remaining preflight ERRORs still block.** W14 and X03 fail both. Real: `LesPaul_CAM_Closed.dxf`
is the one remaining red. **KEEP the rule.** Correction to my 2026-09-13 note: the file's two 2-point
polylines are on the `WIRING_CHANNEL` layer, next to a third 4-point channel path. Every pocket
(`CUTOUT`, `NECK_MORTISE`, 2× `PICKUP_CAVITY`, `ELECTRONIC_CAVITIES`) is closed and valid. The
channel paths look like open routing centrelines, so this may be a layer-class question (open-path
layers) rather than broken geometry. It stays a separate DXF-integrity finding (ruling 4).

### Assets gate — `scripts/validate_dxf_assets.py`

**A1. Closed-contour recognition.** Old: closed LWPOLYLINE or POLYLINE only. New: adds closed LINE
loops (graph face walk, 0.05 mm endpoint snap) and CIRCLE.
- Valid, formerly rejected: W01, W17. Real: `jazzmaster_body.dxf` (41 LINEs, 1 loop) and
  `Cuatro_Venezolano_body.dxf` (306 LINEs, 1 loop).
- The loop detector correctly rejects W02 (open chain), W15 (bow-tie) and W18 (0.5 mm gap) as
  0 loops. They then pass anyway through A3.
- Malformed, newly accepted: **W05, a lone 6 mm CIRCLE, counts as a body contour.**
- "At least one closed contour anywhere" is not evidence of a body outline. 62 of the 66 real files
  this rule alone flips are blueprint traces in `reference_dxf/cuatro/` (all 62 files in that
  directory), where text glyphs and dimension boxes form closed loops.
  `cuatro_puertoriqueño_simple.dxf` counts 3,841 of them. The other 4 are body files:
  `jazzmaster_body`, `Cuatro_Venezolano_body`, and the two `Gibson-Melody-Maker_phase3` LINE dumps
  (63 and 917 loops, so also not clean outlines).

**KEEP LINE-loop detection. DROP CIRCLE as a body contour.** For the body class, the contour that
must be closed is the outline layer (or the largest contour), not any contour.

**A2. Versions.** Old: R12–R2000 allowed. New: R12–R2010 allowed, R2013+ blocked. W07 (R2013) still
fails. It affects 10 real AC1024 files: `flying_v_full`, `flying_v_body`, `gibson_explorer_body`,
`harmony_h44_body`, `smart_guitar_back_v6_smoothed`, `smart_guitar_front_v6_smoothed`,
`concert_ukulele_body`, `octave_mandolin_body`, `orchestra_model_body_view`,
`orchestra_model_clean`. Defects in the new code: the rejection message still says "Use R12 (AC1009)
or R14 (AC1014)", and the module docstring still says "not AC1024". **REWORK** into a per-file
classified allowlist (ruling 3).

**A3. No closed contour: ERROR → warning when any drawable geometry exists.** Malformed now
accepted: W02, W09, W15, W18, X03 (a lone 2-point line). Real: `harmony_h44_body` (1 open entity,
389 pts), `concert_ukulele_body` (14 pts), `octave_mandolin_body` (52 pts). Only text-only and empty
files still fail. **REJECT** (ruling 2); these go on the quarantine list instead.

**A4. CIRCLE points included in bounds.** Neutral.

### Complexity

`check_dxf_files.py::validate_dxf_file` is complexity 22 at `ed592d50` (limit 15; required
`debt-gates`). The rework must split it; the complexity baseline stays as is.

## 4. Pre-existing defects found during the audit (not caused by the repair; separate orders)

**P1. The self-intersection check is blind to CRLF DXFs, in CI and in the runtime export gate.**
`TopologyValidator.__init__` does `ezdxf.read(io.StringIO(dxf_bytes.decode("cp1252")))`. On CRLF
input, ezdxf parses an empty R12 document, so the check examines 0 entities and reports nothing.
DXFPreflight uses a different read path and is not affected. Proof on main's code (`5fc483e4`,
`app/cam` identical to main), through the runtime gate `enforce_dxf_validation`:

```text
W19_r2000_figure8_closed   (LF)    EXPORT BLOCKED  HTTPException 422 DXF_VALIDATION_FAILED
X01_crlf_figure8_closed    (CRLF)  EXPORT ALLOWED  topology entities_checked=0 issues=0
W16_r2000_closed_lwpoly_control (LF)    EXPORT ALLOWED  entities_checked=1
X02_crlf_closed_lwpoly_control  (CRLF)  EXPORT ALLOWED  entities_checked=0
```

73 of the 95 catalog DXFs are stored CRLF. `io.StringIO` does no newline translation on any
platform, so Linux CI behaves the same way.

**P2. `TopologyValidator._suggest_repair` divides by the polygon's area.** A self-intersecting
polygon with exactly zero net area (W08) raises `ZeroDivisionError`. It escapes
`check_dxf_files.validate_dxf_file` (witnessed) and, by code reading, `run_full_validation`, which
only catches `ValueError`, `TypeError` and `AttributeError`. So the runtime gate raises instead of
returning a 422. Only the contrived W08
has triggered it so far; no catalog file does. Low severity.

**P3. `Stratocaster_body.dxf` outline is a folded ring** (see F6). It's a catalog defect, and it is
invisible to the Assets gate old and new.

**P4. Coarse acoustic outlines.** `BODY_OUTLINE` has 9 to 65 vertices (dreadnought 12, OM 10,
L-00 13, soprano uke 9). The Assets gate's under-50-points warning never fires because it counts the
dense `BODY_POINTS` vertices too. Informational.

## 5. Reproduction

Scratch harness (not repo code): `make_witnesses.py OUTDIR` builds the 22 witnesses.
`run_gate.py {assets|files} TREE OUT.jsonl TARGET...` runs one gate version from an extracted tree
(`git archive 5fc483e4` / `git archive ed592d50`) and writes one JSON row per file. Old and new
Files-gate trees are imported in separate processes because both are the `app` package.
The runtime proof calls `app.cam.dxf_validation_gate.enforce_dxf_validation` directly.
