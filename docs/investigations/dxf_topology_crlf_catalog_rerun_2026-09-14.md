# DXF-TOPO-CRLF-001 — catalog rerun through the repaired TopologyValidator (2026-09-14)

**Status:** findings record. Nothing in the catalog is changed by this PR (owner ruling
2026-09-14: record newly exposed defects; do not repair them here).
**Defect fixed:** `TopologyValidator` parsed decoded DXF text through `io.StringIO` without newline
translation, so ezdxf read every CRLF (or CR) file as an empty R12 document and the self-intersection
check examined zero entities. The export gate (`enforce_dxf_validation`) therefore blocked a
self-intersecting outline stored LF and allowed the identical outline stored CRLF. Found by the DXF
gate repair audit (`docs/investigations/dxf_gate_repair_audit_2026-09-14.md` §4, branch
`ci/dxf-gate-repair-001`).
**Fix:** `io.StringIO(text_content, newline=None)`, i.e. universal-newline parsing.

## Acceptance (95 catalog DXFs, ezdxf 1.4.4 / shapely 2.1.2, the CI versions)

For every file, patched validator vs `ezdxf.readfile` (ground truth), and each file re-encoded LF and
CRLF:

| Criterion | Result |
|---|---|
| LWPOLYLINE population seen by the validator == `ezdxf.readfile` | 95 / 95 match |
| LF copy and CRLF copy give an identical topology report (handles, count, issues) | 95 / 95 identical |
| Validator crashes | 0 |
| Catalog files stored CRLF | 73 |
| CRLF files that contain LWPOLYLINEs (the only entity type this check inspects) | 5 |
| CRLF files whose entities-checked count went from 0 to n | 5 |
| LWPOLYLINEs inspected for the first time | 31 |
| Files whose topology result changed | 2 (below) |

The other 68 CRLF files hold only LINE/POLYLINE/SPLINE geometry, which `check_self_intersections`
does not inspect in either version. For them the fix changes nothing.

Regression witness (`services/api/tests/test_topology_validator_line_endings.py`): 12 of 17 cases
fail on the unpatched module (every CRLF and CR case) and 17 of 17 pass with the fix.

## Newly exposed findings (not remediated here)

### F1 — `smart_guitar_front_v6_smoothed.dxf`: body outline self-intersects

`services/api/app/instrument_geometry/body/dxf/electric/smart_guitar_front_v6_smoothed.dxf`
(AC1024, CRLF). Entity handle `30`, layer `BODY_OUTLINE`, closed, 300 vertices, bbox
377.0 × 438.6 mm.

- One crossing: segments 226 and 234 (8 vertices apart) cross near (−105.66, −18.76).
- `make_valid` splits the ring into a 97,939 mm² body and a **10.8 mm² twisted loop**.
- The earlier `Smart-Guitar-v1_front.dxf` `BODY_OUTLINE` (60 vertices, bbox 376.8 × 438.1 mm) is
  valid, so the twist looks like it was introduced by the smoothing step. This is inferred from the
  two files, not traced.
- Before this fix the defect was invisible to every gate: the file is CRLF, so topology read
  nothing, and the asset gate never checks intersection.

Disposition: DXF Catalog Integrity quarantine **candidate**. It's a manufacturing body outline with a
demonstrated topological defect. Remediation belongs to that workstream; any design judgement
(which side of the twist is intended) needs owner adjudication.

### F2 — `LesPaul_CAM_Closed.dxf`: WIRING_CHANNEL paths now also flagged by topology

(AC1015, CRLF.) Newly reported on layer `WIRING_CHANNEL`: two "Degenerate polygon (only 2
vertices)" (handles `3D`, `3E`) and one "Self-intersecting polygon" (handle `3C`, open, 4 vertices).
The `3C` crossing involves the segment the validator adds to close the path (segments 1 and 3 of a
4-point path); the open path itself is simple. All pockets in the file (`CUTOUT`, `NECK_MORTISE`,
2 × `PICKUP_CAVITY`, `ELECTRONIC_CAVITIES`) remain closed and valid.

Disposition: unchanged. **UNADJUDICATED** pending the WIRING_CHANNEL CAM-consumer trace (owner
ruling 2026-09-14). This is not evidence of defective geometry or of valid geometry; it shows that
the validator treats every LWPOLYLINE as a polygon.

## DXF Validation Gate: now runs, and fails honestly (owner ruling 2026-09-14, option 2)

This PR also moves the `dxf_compat` import in `dxf_advanced_validation.py` from module level into
the two test-DXF builders. `app.util`'s `__init__` imports `fastapi`, and the DXF Validation Gate job
installs only `ezdxf` and `shapely`, so the job had been dying at import and checking nothing (red
on main since 2026-05). Run the way CI runs it (from `services/api`, ezdxf 1.4.4 + shapely 2.1.2,
no fastapi), `python -m app.ci.check_dxf_files` now completes: **95 files, 80 pass, 15 fail.**
Those 15 are real findings. The gate stays red on purpose: making it green is the separate DXF
catalog gate PR, with declarative asset/layer classes and evidence-backed quarantine records. No
catalog file or gate rule changes here.

| File(s) | Gate reason | Expected disposition (owner rulings 2026-09-14) |
|---|---|---|
| `classical_body`, `dreadnought_body`, `gibson_l_00_body`, `om_000_body`, `soprano_ukulele_body` | open, self-crossing polyline on `BODY_POINTS` | declared reference layer, exempt from outline rules |
| `carlos_jumbo_body`, `mandolin_body`, `jaguar_body`, `mustang_body` | "No CAM-compatible entities": body is one closed R12 POLYLINE | closed POLYLINE accepted as a body outline |
| `Stratocaster_body` | `BODY_OUTLINE` self-intersecting (folded ring) | quarantine candidate (strongest) |
| `smart_guitar_front_v6_smoothed` | `BODY_OUTLINE` self-intersecting (F1; visible only with this PR's CRLF fix) | quarantine candidate |
| `harmony_h44_body`, `concert_ukulele_body`, `octave_mandolin_body` | open `BODY_OUTLINE` (the uke and mandolin paths also cross themselves) | pending asset-intent adjudication |
| `LesPaul_CAM_Closed` | open / 2-point / self-crossing `WIRING_CHANNEL` paths (F2) | UNADJUDICATED pending CAM-consumer trace |

## Operational consequence of the fix

CRLF uploads are now topology-checked at export. A CRLF DXF containing a self-intersecting or
degenerate LWPOLYLINE that previously exported will now get the same 422 that the identical LF file
already got. That is the intended behaviour, not a regression. In the catalog, that applies to F1
and F2 only.
