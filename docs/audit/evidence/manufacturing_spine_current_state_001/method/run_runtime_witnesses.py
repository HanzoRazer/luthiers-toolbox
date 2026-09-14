"""G2-MANUFACTURING-SPINE-001 — runtime witness harness (evidence method, not product).

One safe, in-process witness per capability against the current app, with
ephemeral RMOS/art-studio state. No network, no machine control, no production
DB, no planted artifacts, no project or auth context.

Every witness here is labelled SYNTHETIC_PROBE (D5a): inputs are either repo
fixtures (cited by file) or minimal constructed geometry. Synthetic evidence can
support EXERCISED / EFFECTIVE; it can never support CONSUMED.

Reading rules this harness applies — stated so the verdicts can be audited:

* EXERCISED needs a *valid* request reaching the capability's decision path.
  A policy 409 on a valid request counts (that is the route's full behaviour);
  a 404 for a nonexistent retrieval id does not (it only proves the route is
  live) and is recorded as wiring support.
* EFFECTIVE needs an *input-derived* check: output extents against the supplied
  geometry, a canned cycle at the supplied hole, supplied moves preserved by a
  transform. A structurally valid program with no input-derived check is
  EFFECTIVE UNKNOWN, never YES. A 200 alone proves nothing (order §10 Step D).
* A proven non-effect (409 / 400 with no program) is EFFECTIVE NO, with the
  witness as its evidence.

Usage::

    python run_runtime_witnesses.py <repo_root> <out.json>
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import math
import os
import re
import sys
import tempfile

REPO, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(REPO, "services", "api"))

_tmp = tempfile.mkdtemp(prefix="g2_spine_")
_runs = os.path.join(_tmp, "rmos_runs")
os.makedirs(_runs, exist_ok=True)
with open(os.path.join(_runs, "_index.json"), "w", encoding="utf-8") as fh:
    fh.write("{}")
os.environ.update({
    "RMOS_RUNS_DIR": _runs,
    "RMOS_RUN_ATTACHMENTS_DIR": os.path.join(_tmp, "att"),
    "RMOS_ARTIFACT_ROOT": os.path.join(_tmp, "run_artifacts"),
    "ART_STUDIO_DB_PATH": os.path.join(_tmp, "art.db"),
    "ENV": "test",
})

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)

STAGE2 = "services/api/tests/rmos/test_manufacturing_authority_stage2.py"
POCKET = "services/api/tests/cam/test_pocketing_intent_migration.py"
RECT = [{"x": 0.0, "y": 0.0}, {"x": 80.0, "y": 0.0}, {"x": 80.0, "y": 50.0}, {"x": 0.0, "y": 50.0}]
SANE_ADAPTIVE = {
    "loops": [{"pts": [[0, 0], [100, 0], [100, 60], [0, 60]]}], "units": "mm", "tool_d": 6.0,
    "stepover": 0.45, "stepdown": 2.0, "margin": 0.5, "strategy": "Spiral", "smoothing": 0.5,
    "climb": True, "feed_xy": 1200.0, "safe_z": 5.0, "z_rough": -1.5,
}
WORD = re.compile(r"([XYZ])\s*(-?\d+(?:\.\d+)?)")


def minimal_dxf_rect(w: float, h: float) -> bytes:
    import ezdxf  # repo dependency; absence is recorded, not faked
    doc = ezdxf.new("R2000")
    doc.modelspace().add_lwpolyline([(0, 0), (w, 0), (w, h), (0, h)], close=True)
    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode("utf-8")


def _find_program(obj, depth=0):
    """Locate a program string in a JSON body. Shapes seen on current main:
    ``{"gcode": str}``, ``{"gcode": {"text": str}}`` (rmos-wrap) and
    ``{"data": {"gcode": str}}`` (v1-dxf)."""
    if depth > 3 or not isinstance(obj, dict):
        return ""
    for k in ("gcode", "program", "nc"):
        v = obj.get(k)
        if isinstance(v, str):
            return v
        if isinstance(v, dict) and isinstance(v.get("text"), str):
            return v["text"]
    for v in obj.values():
        if isinstance(v, dict):
            found = _find_program(v, depth + 1)
            if found:
                return found
    return ""


def program_text(resp):
    ctype = resp.headers.get("content-type", "")
    if "json" in ctype:
        try:
            return _find_program(resp.json()), ctype
        except ValueError:
            return "", ctype
    return resp.text, ctype


def analyse(text: str) -> dict:
    """Modal-aware program reader.

    Cutting motion is G1/G2/G3 and stays modal until another motion word.
    Probe moves are G38.x (GRBL/LinuxCNC) and G31 (Fanuc Macro B / Mach3) —
    both were seen or are plausible on current main, so both are recognised.
    """
    x = y = z = None
    pts = []
    path = []  # (x, y) sequence of cutting / probing endpoints, in order
    zs = []
    motion = cycles = probes = 0
    mode = None
    for raw in text.splitlines():
        line = raw.split(";")[0].split("(")[0].strip().upper()
        if not line or line.startswith("#"):
            continue
        words = re.findall(r"G(\d+(?:\.\d+)?)", line)
        for w in words:
            g = float(w)
            if g in (0, 1, 2, 3):
                mode = int(g)
            elif g in (81, 82, 83):
                mode = "cycle"
            elif g == 31 or 38 <= g < 39:
                mode = "probe"
        has_xy = bool(re.search(r"[XY]\s*-?\d", line))
        for axis, val in WORD.findall(line):
            v = float(val)
            if axis == "X":
                x = v
            elif axis == "Y":
                y = v
            else:
                z = v
                zs.append(v)
        if not has_xy and not re.search(r"Z\s*-?\d", line):
            continue
        if mode in (1, 2, 3):
            motion += 1
        elif mode == "cycle" and has_xy:
            cycles += 1
        elif mode == "probe":
            probes += 1
        # A Z-only cutting move (a plunge) at a known XY is still a cutting
        # position: V-carve starts every stroke that way. Run 2 of this harness
        # dropped those points and wrongly collapsed the V-carve extent to X=20.
        if x is not None and y is not None and mode in (1, 2, 3, "cycle", "probe"):
            if mode == "cycle" and not has_xy:
                continue
            pts.append((x, y))
            if mode in (1, 2, 3):
                path.append((x, y))
    ext = None
    if pts:
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        ext = {"x_min": min(xs), "x_max": max(xs), "y_min": min(ys), "y_max": max(ys),
               "x_span": round(max(xs) - min(xs), 3), "y_span": round(max(ys) - min(ys), 3)}
    return {
        "lines": len(text.splitlines()), "cut_moves": motion, "canned_cycles": cycles,
        "probe_moves": probes, "units_g21": "G21" in text.upper(),
        "units_g20": "G20" in text.upper(), "min_z": min(zs) if zs else None,
        "placeholder": "TODO" in text.upper(), "xy_extent": ext,
        "_path": path,
    }


def swept_coverage(path, box, tool_d, cell=1.0):
    """Fraction of the box area lying within tool radius of the cutting path.

    A pocket-clearing program should approach 1.0 (less margins and corner
    radii). Straight segments between consecutive endpoints are sampled every
    half-cell; G2/G3 arcs are treated as chords, which can only *under*-state
    coverage slightly. This measures what the program would cut, not intent.
    """
    x0, y0, x1, y1 = box
    r2 = (tool_d / 2.0) ** 2
    nx, ny = int((x1 - x0) / cell), int((y1 - y0) / cell)
    hit = [[False] * ny for _ in range(nx)]
    samples = []
    for (ax, ay), (bx, by) in zip(path, path[1:]):
        n = max(1, int(math.hypot(bx - ax, by - ay) / (cell / 2)))
        samples.extend((ax + (bx - ax) * t / n, ay + (by - ay) * t / n) for t in range(n + 1))
    reach = int(math.ceil((tool_d / 2.0) / cell)) + 1
    for sx, sy in samples:
        ci, cj = int((sx - x0) / cell), int((sy - y0) / cell)
        for i in range(max(0, ci - reach), min(nx, ci + reach + 1)):
            cx = x0 + (i + 0.5) * cell
            for j in range(max(0, cj - reach), min(ny, cj + reach + 1)):
                if not hit[i][j]:
                    cy = y0 + (j + 0.5) * cell
                    if (cx - sx) ** 2 + (cy - sy) ** 2 <= r2:
                        hit[i][j] = True
    total = nx * ny
    return round(sum(map(sum, hit)) / total, 4) if total else None


def check_clearing(box, tool_d, min_cov, tol=1.0):
    """A pocket-clearing op must stay inside the pocket AND clear most of it."""
    def _c(a):
        e = a["xy_extent"]
        if not e:
            return False, "no XY cutting moves"
        cov = swept_coverage(a["_path"], box, tool_d)
        a["swept_coverage"] = cov
        inside = within(e, box, tol)
        ok = inside and cov is not None and cov >= min_cov
        return ok, (f"swept coverage {cov:.1%} of the {box[2]-box[0]:g}x{box[3]-box[1]:g} pocket "
                    f"(need >= {min_cov:.0%}); inside pocket: {inside}; extent {e}")
    return _c


def within(ext, box, tol):
    x0, y0, x1, y1 = box
    return (ext["x_min"] >= x0 - tol and ext["x_max"] <= x1 + tol
            and ext["y_min"] >= y0 - tol and ext["y_max"] <= y1 + tol)


def covers(ext, box, frac):
    x0, y0, x1, y1 = box
    return ext["x_span"] >= frac * (x1 - x0) and ext["y_span"] >= frac * (y1 - y0)


def check_box(box, tol, frac):
    def _c(a):
        e = a["xy_extent"]
        if not e:
            return False, "no XY cutting moves"
        ok = within(e, box, tol) and covers(e, box, frac)
        return ok, f"extent {e} vs input box {box} (tol {tol}, coverage >= {frac:.0%})"
    return _c


def check_span(major, minor, lo=0.8, hi=1.25):
    def _c(a):
        e = a["xy_extent"]
        if not e:
            return False, "no XY cutting moves"
        spans = sorted([e["x_span"], e["y_span"]], reverse=True)
        want = sorted([major, minor], reverse=True)
        ok = all(lo * w <= s <= hi * w for s, w in zip(spans, want))
        return ok, f"spans {spans} vs input-derived {want} (x{lo}..x{hi})"
    return _c


def check_hole(xh, yh):
    def _c(a):
        return a["canned_cycles"] > 0, f"{a['canned_cycles']} canned cycle line(s); hole at ({xh},{yh})"
    return _c


# --------------------------------------------------------------------------- cases
# expect: EMIT (success + program), BLOCKED (policy 409, no program),
#         BROKEN (400 after evaluator, no program), ADVISORY (JSON advice),
#         TRANSFORM (supplied program preserved)
CASES = [
    dict(cap="retract", expect="BLOCKED", method="POST", path="/api/cam/retract/gcode/download",
         json={"strategy": "direct", "features": []}, source=f"repo_fixture:{STAGE2}:160"),
    dict(cap="adaptive", expect="EMIT", method="POST", path="/api/cam/pocket/adaptive/gcode",
         json=SANE_ADAPTIVE, source=f"repo_fixture:{STAGE2}:24",
         effective=check_clearing((0, 0, 100, 60), 6.0, 0.80)),
    dict(cap="drilling", expect="EMIT", method="POST", path="/api/cam/drilling/gcode",
         json={"holes": [{"x": 10, "y": 10, "z": -5, "feed": 500}], "cycle": "G83",
               "peck_q": 2.0, "safe_z": 5.0, "units": "mm"},
         source=f"repo_fixture:{STAGE2}:113", effective=check_hole(10, 10)),
    dict(cap="profiling", expect="EMIT", method="POST", path="/api/cam/profiling/gcode",
         json={"contour": RECT}, source=f"repo_fixture:{STAGE2}:252",
         effective=check_box((0, 0, 80, 50), 12.0, 0.9)),
    dict(cap="vcarve", expect="EMIT", method="POST", path="/api/cam/vcarve/production/gcode",
         json={"paths": [{"points": [{"x": 0, "y": 0}, {"x": 20, "y": 0}, {"x": 20, "y": 10}],
                          "is_closed": False}], "bit_angle_deg": 60.0, "target_line_width_mm": 2.0},
         source=f"repo_fixture:{STAGE2}:267", effective=check_box((0, 0, 20, 10), 3.0, 0.8)),
    dict(cap="roughing", expect="BLOCKED", method="POST", path="/api/cam/toolpath/roughing/gcode",
         json={"width": 80.0, "height": 50.0, "stepdown": 2.0, "stepover": 0.4, "feed": 1200.0,
               "safe_z": 5.0}, source=f"repo_fixture:{STAGE2}:175"),
    dict(cap="helical", expect="BLOCKED", method="POST", path="/api/cam/toolpath/helical_entry",
         json={"cx": 0.0, "cy": 0.0, "radius_mm": 6.0, "z_target_mm": -3.0, "pitch_mm_per_rev": 1.5},
         source=f"repo_fixture:{STAGE2}:186"),
    dict(cap="biarc-contour", expect="BLOCKED", method="POST", path="/api/cam/toolpath/biarc/gcode",
         json={"path": [{"x": 0, "y": 0}, {"x": 40, "y": 0}, {"x": 40, "y": 20}], "z": -2.0,
               "feed": 800.0}, source=f"repo_fixture:{STAGE2}:197"),
    dict(cap="rosette", expect="BROKEN", method="POST", path="/api/cam/rosette/plan-toolpath",
         json={"inner_radius": 10.0, "outer_radius": 40.0, "tool_d": 3.0, "cut_depth": 2.0,
               "feed_xy": 800.0}, source=f"repo_fixture:{STAGE2}:330"),
    dict(cap="probing", expect="EMIT", method="POST", path="/api/probe/boss/gcode",
         json={"pattern": "boss_circular", "estimated_diameter": 50.0, "estimated_center_x": 0.0,
               "estimated_center_y": 0.0, "probe_count": 4, "approach_distance": 5.0},
         source="constructed_minimal",
         # probe moves start at radius d/2 + approach = 30 and cross the boss
         effective=check_span(50.0 + 2 * 5.0, 50.0 + 2 * 5.0, 0.95, 1.05)),
    dict(cap="binding", expect="EMIT", method="POST", path="/api/cam/binding/channel/gcode",
         json={"body_outline": RECT}, source=f"repo_fixture:{STAGE2}:355",
         effective=check_box((0, 0, 80, 50), 15.0, 0.9)),
    dict(cap="inlay", expect="EMIT", method="POST", path="/api/art-studio/inlay/export-gcode",
         json={"pattern_type": "dot", "fret_positions": [3, 5, 7, 9, 12], "double_at_12": False,
               "marker_diameter_mm": 6.0, "scale_length_mm": 648.0, "pocket_depth_mm": 1.5},
         source="constructed_minimal",
         # dots sit mid-fret; 3rd-fret dot ~86.9 mm, 12th ~315.1 mm from the nut.
         # Minor span is the tool CENTRE path: marker 6.0 - tool 3.175 = 2.825 mm.
         # (Corrected after run 1, which wrongly expected the marker diameter.)
         effective=check_span(315.1 - 86.9, 6.0 - 3.175, 0.85, 1.3)),
    dict(cap="radius-dish", expect="EMIT", method="POST", path="/api/acoustics/radius-dish/generate-gcode",
         json={"radius_ft": 25.0, "dish_width_mm": 200.0, "dish_length_mm": 300.0,
               "ball_nose_dia_mm": 12.7, "stepover_mm": 6.0, "include_roughing": False},
         source="constructed_minimal", effective=check_span(300.0, 200.0, 0.8, 1.2)),
    dict(cap="feeds-speeds", expect="ADVISORY", method="POST", path="/api/cam/opt/feeds-speeds",
         json={"tool_id": "endmill_6mm", "material": "hardwood", "strategy": "roughing"},
         source=f"repo_fixture:{STAGE2}:367"),
    dict(cap="cam-guitar", expect="EMIT", method="POST",
         path="/api/cam/guitar/acoustic/dreadnought/body/gcode",
         json={"tool_diameter_mm": 6.35, "total_depth_mm": 3.0, "stepdown_mm": 3.0, "tab_count": 4},
         source="constructed_minimal", effective=None,
         note="acoustic body routes need no project/auth; project routes withheld"),
    dict(cap="cam-post", expect="EMIT", method="POST", path="/api/cam/post/post_v155",
         json={"contour": [[0, 0], [50, 0], [50, 30], [0, 30], [0, 0]], "z_cut_mm": -1.0},
         source="constructed_minimal", effective=check_box((0, 0, 50, 30), 6.0, 0.9)),
    dict(cap="geometry", expect="TRANSFORM", method="POST", path="/api/geometry/export_gcode",
         json={"gcode": "G21\nG90\nG0 X0 Y0\nG1 X10 Y0 F500\nG1 X10 Y10\nM30\n", "units": "mm"},
         source="constructed_minimal", preserve=["X10 Y0", "X10 Y10"]),
    dict(cap="headstock-transition", expect="EMIT", method="POST", path="/api/headstock/transition/gcode",
         json={"nut_width_mm": 43.0, "y_margin_mm": 5.0, "blend_length_mm": 22.0},
         source="constructed_minimal", effective=None,
         note="no input-derived envelope established for the blend surface"),
    dict(cap="neck-gcode", expect="EMIT", method="POST", path="/api/neck/gcode/generate",
         json={"headstock_style": "paddle", "profile": "c"}, source="constructed_minimal",
         effective=None, note="scale_length units not established from the contract"),
    dict(cap="pocketing", expect="EMIT", method="POST", path="/api/cam/pocketing/intent-gcode",
         json={"mode": "router_3axis", "units": "mm",
               "design": {"boundary": [{"x": 0, "y": 0}, {"x": 100, "y": 0}, {"x": 100, "y": 100},
                                       {"x": 0, "y": 100}], "islands": [], "pocket_depth_mm": 6.0,
                          "tool_diameter_mm": 6.0, "stepover_percent": 50.0},
               "context": {"stepdown_mm": 2.0, "feed_rate_mm_min": 1500.0}, "options": {}},
         source=f"repo_fixture:{POCKET}:139", effective=check_clearing((0, 0, 100, 100), 6.0, 0.80)),
    dict(cap="polygon-offset", expect="EMIT", method="POST", path="/api/cam/polygon_offset_governed.nc",
         json={"polygon": [[0, 0], [60, 0], [60, 40], [0, 40], [0, 0]], "tool_dia": 6.0, "stepover": 0.4},
         source=f"repo_fixture:{STAGE2}:380", effective=check_clearing((0, 0, 60, 40), 6.0, 0.80)),
    dict(cap="rmos-wrap", expect="EMIT", method="POST", path="/api/rmos/wrap/mvp/dxf-to-grbl",
         multipart="dxf_rect_60x40", form={"tool_d": "6.0"}, source="constructed_minimal",
         effective=check_clearing((0, 0, 60, 40), 6.0, 0.80)),
    dict(cap="v1-dxf", expect="EMIT", method="POST", path="/api/v1/dxf/cam/gcode",
         json_dxf_b64="dxf_rect_60x40", json={"operation": "profile", "tool_diameter_mm": 6.0},
         source="constructed_minimal", effective=check_box((0, 0, 60, 40), 7.0, 0.5)),
]

WITHHELD = {
    "vision": ("NOT_OBTAINED_SAFELY",
               "photo-to-G-code depends on an external AI service; `openai` is also not installed "
               "in the witness environment. No safe local witness exists."),
    "saw-batch": ("UNKNOWN",
                  "retrieval of a saw-lab execution artifact; producing one needs the multi-step saw "
                  "batch flow. Not attempted in this baseline. Missing-id 404 recorded as wiring only."),
}


def run_case(c):
    rec = {k: c[k] for k in ("cap", "expect", "method", "path", "source")}
    rec["synthetic_probe"] = True
    if c.get("note"):
        rec["note"] = c["note"]
    try:
        if c.get("multipart"):
            dxf = minimal_dxf_rect(60, 40)
            rec["request"] = {"multipart_file": "rect_60x40.dxf (constructed, %d bytes)" % len(dxf),
                              "form": c.get("form")}
            resp = client.post(c["path"], files={"file": ("rect_60x40.dxf", dxf, "application/dxf")},
                               data=c.get("form") or {})
        elif c.get("json_dxf_b64"):
            body = dict(c["json"])
            body["dxf_base64"] = base64.b64encode(minimal_dxf_rect(60, 40)).decode("ascii")
            rec["request"] = {**c["json"], "dxf_base64": "<constructed rect_60x40.dxf, base64>"}
            resp = client.post(c["path"], json=body)
        else:
            rec["request"] = c.get("json")
            resp = client.request(c["method"], c["path"], json=c.get("json"))
    except Exception as exc:  # recorded, never swallowed
        rec.update(status=None, exception=f"{type(exc).__name__}: {exc}")
        rec.update(exercised="UNKNOWN", effective="UNKNOWN")
        return rec

    text, ctype = program_text(resp)
    body_bytes = resp.content or b""
    rec.update({
        "status": resp.status_code, "content_type": ctype, "bytes": len(body_bytes),
        "body_sha256": hashlib.sha256(body_bytes).hexdigest(),
        "headers": {h: resp.headers[h] for h in ("x-run-id", "x-risk-level", "x-gcode-sha256",
                                                 "x-toolbox-lane") if h in resp.headers},
    })
    a = analyse(text)
    rec["analysis"] = a
    rec["excerpt"] = "\n".join(text.splitlines()[:8])[:600]
    if resp.status_code >= 400:
        try:
            rec["error_detail"] = json.dumps(resp.json())[:400]
        except ValueError:
            rec["error_detail"] = resp.text[:400]

    has_program = a["cut_moves"] > 0 or a["canned_cycles"] > 0 or a["probe_moves"] > 0
    exp = c["expect"]
    if exp == "BLOCKED":
        ok = resp.status_code == 409 and not has_program
        rec["exercised"] = "YES" if ok else "UNKNOWN"
        rec["effective"] = "NO" if ok else "UNKNOWN"
        rec["effective_basis"] = "policy 409 on a valid request; no program emitted" if ok else \
            f"expected 409 without program, got {resp.status_code}"
    elif exp == "BROKEN":
        ok = resp.status_code == 400 and not has_program
        rec["exercised"] = "YES" if ok else "UNKNOWN"
        rec["effective"] = "NO" if ok else "UNKNOWN"
        rec["effective_basis"] = "400 after the evaluator ran; no program emitted" if ok else \
            f"expected 400 without program, got {resp.status_code}"
    elif exp == "ADVISORY":
        try:
            data = resp.json()
        except ValueError:
            data = {}
        nums = {k: data.get(k) for k in ("feed_xy", "rpm") if isinstance(data.get(k), (int, float))}
        rec["exercised"] = "YES" if resp.status_code == 200 else "UNKNOWN"
        ok = resp.status_code == 200 and nums and all(v > 0 for v in nums.values()) and not has_program
        rec["effective"] = "YES" if ok else "UNKNOWN"
        rec["effective_basis"] = f"advisory JSON with positive {sorted(nums)}; no program" if ok else \
            "advisory values not established"
    elif exp == "TRANSFORM":
        rec["exercised"] = "YES" if resp.status_code == 200 else "UNKNOWN"
        kept = [p for p in c["preserve"] if p in text.upper().replace("  ", " ")]
        ok = resp.status_code == 200 and len(kept) == len(c["preserve"])
        rec["effective"] = "YES" if ok else "UNKNOWN"
        rec["effective_basis"] = f"supplied moves preserved: {kept} of {c['preserve']}"
    else:  # EMIT
        success = resp.status_code == 200 and has_program and not a["placeholder"]
        rec["exercised"] = "YES" if resp.status_code == 200 else "UNKNOWN"
        if resp.status_code == 200 and a["placeholder"]:
            rec["effective"] = "NO"
            rec["effective_basis"] = "200 but the program is a placeholder (TODO), not a toolpath"
        elif not success:
            rec["effective"] = "UNKNOWN"
            rec["effective_basis"] = f"no program to evaluate (status {resp.status_code})"
        elif c.get("effective") is None:
            rec["effective"] = "UNKNOWN"
            rec["effective_basis"] = ("valid program, but no input-derived check was established; "
                                      "structure alone does not prove EFFECTIVE")
        else:
            ok, why = c["effective"](a)
            rec["effective"] = "YES" if ok else "UNKNOWN"
            rec["effective_basis"] = why
    return rec


def operator_pack_chain():
    """Mint a run through the product's own governed path, then retrieve its pack.

    Not a planted artifact: the run is created by the product's own persistence,
    exactly as a user's request would create it. Run 1 of this harness used an
    adaptive run and got 409 "missing required attachments: dxf_input, cam_plan,
    manifest, gcode_output" — the pack is built for DXF->CAM runs, which is what
    the rmos-wrap MVP route persists. So the chain starts there.
    """
    rec = {"cap": "operator-pack", "expect": "RETRIEVE", "method": "GET",
           "path": "/api/rmos/runs_v2/{run_id}/operator-pack", "synthetic_probe": True,
           "source": "chain: rmos-wrap dxf-to-grbl (constructed rect_60x40.dxf) -> run_id -> operator-pack"}
    gen = client.post("/api/rmos/wrap/mvp/dxf-to-grbl",
                      files={"file": ("rect_60x40.dxf", minimal_dxf_rect(60, 40), "application/dxf")},
                      data={"tool_d": "6.0"})
    try:
        run_id = gen.json().get("run_id")
    except ValueError:
        run_id = None
    rec["upstream"] = {"status": gen.status_code, "run_id": run_id}
    if not run_id:
        rec.update(exercised="UNKNOWN", effective="UNKNOWN",
                   effective_basis="upstream generation returned no run id")
        return rec
    resp = client.get(f"/api/rmos/runs_v2/{run_id}/operator-pack")
    rec.update(status=resp.status_code, content_type=resp.headers.get("content-type", ""),
               bytes=len(resp.content or b""), body_sha256=hashlib.sha256(resp.content or b"").hexdigest())
    if resp.status_code != 200:
        rec["error_detail"] = resp.text[:400]
        rec.update(exercised="YES" if resp.status_code in (404, 409, 422) else "UNKNOWN",
                   effective="UNKNOWN",
                   effective_basis=f"pack not produced for a real run id (status {resp.status_code})")
        return rec
    import zipfile
    try:
        z = zipfile.ZipFile(io.BytesIO(resp.content))
        names = z.namelist()
        gcode_members = [n for n in names if n.lower().endswith((".nc", ".gcode", ".ngc", ".tap"))]
        rec["zip_members"] = names[:20]
        ok = bool(gcode_members)
        rec.update(exercised="YES", effective="YES" if ok else "UNKNOWN",
                   effective_basis=f"zip with program member(s) {gcode_members}" if ok else
                   "zip returned but no program member identified")
    except zipfile.BadZipFile:
        rec.update(exercised="YES", effective="UNKNOWN", effective_basis="200 but body is not a zip")
    return rec


def retrieval_wiring(cap, path):
    resp = client.get(path)
    return {"cap": cap, "path": path, "status": resp.status_code, "role": "wiring_support_only",
            "note": "missing-id request: proves the route is live, not that it retrieves"}


def adaptive_plan_diagnostic():
    """Does the adaptive *planner* cover the pocket, independent of G-code emission?

    /plan is not a machine-output route (the registry says so); it is read here
    only to localise an EFFECTIVE failure to the planner or to the emitter.
    """
    resp = client.post("/api/cam/pocket/adaptive/plan", json=SANE_ADAPTIVE)
    rec = {"path": "/api/cam/pocket/adaptive/plan", "status": resp.status_code,
           "request": "repo_fixture SANE_ADAPTIVE (same input as the adaptive witness)"}
    try:
        data = resp.json()
    except ValueError:
        rec["note"] = "non-JSON body"
        return rec
    moves = data.get("moves") if isinstance(data, dict) else None
    rec["keys"] = sorted(data)[:20] if isinstance(data, dict) else None
    if isinstance(moves, list):
        pts = [(m.get("x"), m.get("y")) for m in moves
               if isinstance(m, dict) and m.get("x") is not None and m.get("y") is not None]
        cut = [(m.get("x"), m.get("y")) for m in moves
               if isinstance(m, dict) and str(m.get("code", "")).upper() in ("G1", "G2", "G3")
               and m.get("x") is not None and m.get("y") is not None]
        rec["move_count"] = len(moves)
        rec["cut_move_count"] = len(cut)
        if pts:
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            rec["xy_extent"] = {"x_min": min(xs), "x_max": max(xs), "y_min": min(ys), "y_max": max(ys)}
        rec["swept_coverage"] = swept_coverage(cut, (0, 0, 100, 60), 6.0) if len(cut) > 1 else None
    for k in ("stats", "metrics", "summary"):
        if isinstance(data, dict) and isinstance(data.get(k), dict):
            rec[k] = {kk: vv for kk, vv in list(data[k].items())[:12]}
    return rec


results = []
for case in CASES:
    results.append(run_case(case))
results.append(operator_pack_chain())
diagnostics = {"adaptive_plan": adaptive_plan_diagnostic()}
wiring = [retrieval_wiring("operator-pack", "/api/rmos/runs_v2/does-not-exist/operator-pack"),
          retrieval_wiring("saw-batch", "/api/saw/batch/executions/does-not-exist/gcode")]

import fastapi  # noqa: E402

out = {
    "order": "G2-MANUFACTURING-SPINE-001",
    "harness": "docs/audit/evidence/manufacturing_spine_current_state_001/method/run_runtime_witnesses.py",
    "python": sys.version.split()[0],
    "fastapi": fastapi.__version__,
    "ephemeral_state_root": "<tempdir, discarded>",
    # _path is the full point list used for coverage; drop it so the frozen
    # evidence stays small and reviewable (D9). body_sha256 pins the body.
    "witnesses": [
        {**w, "analysis": {k: v for k, v in (w.get("analysis") or {}).items() if k != "_path"}}
        if w.get("analysis") else w
        for w in results
    ],
    "diagnostics": diagnostics,
    "wiring_support": wiring,
    "withheld": {k: {"status": v[0], "reason": v[1]} for k, v in WITHHELD.items()},
}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2)
print(f"witnesses={len(results)} withheld={len(WITHHELD)} -> {OUT}")
