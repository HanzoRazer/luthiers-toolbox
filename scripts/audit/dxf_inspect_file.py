#!/usr/bin/env python3
"""
dxf_inspect_file.py — read-only DXF inspector for the DXF format-flow audit.

Given a DXF file (or raw bytes on stdin), report:
  - declared $ACADVER (e.g. AC1009 = R12, AC1015 = R2000) and ezdxf's version label
  - entity-type histogram (LINE / LWPOLYLINE / POLYLINE / CIRCLE / ARC / SPLINE / TEXT / ...)
  - a declared-vs-emitted consistency verdict (D6): does the file declare a pre-R13
    version while emitting LWPOLYLINE (an R13+ entity)?
  - $EXTMIN / $EXTMAX header extents, if present (sentinel-vs-geometry sanity, FYI)

This is an AUDIT helper, NOT production code. It only READS — it never writes or
edits a DXF. Reusable by the later CLEAN / CONSOLIDATE streams to spot-check artifacts.

Usage:
    python dxf_inspect_file.py FILE.dxf [FILE2.dxf ...]
    python dxf_inspect_file.py --json FILE.dxf
    cat FILE.dxf | python dxf_inspect_file.py -          # read bytes from stdin

Requires ezdxf (read-only). If ezdxf is unavailable, falls back to a minimal
group-code scan for $ACADVER and entity-type counts so the tool still reports
something in an ezdxf-less shell.
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
import tempfile
from pathlib import Path

# AC version code -> human label (per Autodesk DXF spec).
ACADVER_LABELS = {
    "AC1006": "R10",
    "AC1009": "R12",
    "AC1012": "R13",
    "AC1014": "R14",
    "AC1015": "R2000",
    "AC1018": "R2004",
    "AC1021": "R2007",
    "AC1024": "R2010",
    "AC1027": "R2013",
    "AC1032": "R2018",
}

# Entities that only exist in R13 (AC1012) and later. Emitting any of these in a
# file that declares R10/R12 is an internal inconsistency (D6).
R13_PLUS_ENTITIES = {"LWPOLYLINE", "SPLINE", "MTEXT", "HATCH", "ELLIPSE", "REGION"}

# AC codes that predate R13.
PRE_R13_ACADVER = {"AC1006", "AC1009"}


def _version_rank(acadver: str) -> int:
    order = list(ACADVER_LABELS.keys())
    return order.index(acadver) if acadver in order else -1


def inspect_with_ezdxf(path: str) -> dict:
    import ezdxf  # local import so the fallback path works without it

    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    hist: collections.Counter = collections.Counter(e.dxftype() for e in msp)
    acadver = doc.dxfversion
    header = doc.header
    extmin = header.get("$EXTMIN")
    extmax = header.get("$EXTMAX")
    return _build_report(acadver, hist, extmin, extmax, source="ezdxf")


def inspect_fallback(data: bytes) -> dict:
    """Minimal group-code scan when ezdxf is unavailable.

    Counts entity-type tokens that follow a '0' group code, and reads $ACADVER.
    Approximate (does not parse blocks vs modelspace), but enough for a version +
    entity-type sanity check.
    """
    text = data.decode("utf-8", errors="replace").replace("\r\n", "\n")
    lines = text.split("\n")
    acadver = ""
    hist: collections.Counter = collections.Counter()
    i = 0
    n = len(lines)
    known_entities = {
        "LINE", "LWPOLYLINE", "POLYLINE", "CIRCLE", "ARC", "SPLINE",
        "TEXT", "MTEXT", "POINT", "ELLIPSE", "HATCH", "INSERT", "VERTEX",
    }
    while i < n - 1:
        code = lines[i].strip()
        val = lines[i + 1].strip()
        if code == "9" and val == "$ACADVER" and i + 3 < n:
            acadver = lines[i + 3].strip()
        elif code == "0" and val in known_entities:
            hist[val] += 1
        i += 1
    return _build_report(acadver, hist, None, None, source="fallback-groupcode")


def _build_report(acadver, hist, extmin, extmax, source) -> dict:
    label = ACADVER_LABELS.get(acadver, "?")
    emitted_r13plus = sorted(set(hist) & R13_PLUS_ENTITIES)
    inconsistent = bool(emitted_r13plus) and acadver in PRE_R13_ACADVER
    verdict = "OK"
    if inconsistent:
        verdict = (
            f"INCONSISTENT: declares {acadver}({label}) but emits R13+ "
            f"entities {emitted_r13plus}"
        )
    return {
        "source": source,
        "acadver": acadver,
        "version_label": label,
        "entities": dict(sorted(hist.items(), key=lambda kv: (-kv[1], kv[0]))),
        "entity_total": sum(hist.values()),
        "emitted_r13plus": emitted_r13plus,
        "declared_vs_emitted": verdict,
        "extmin": list(extmin) if extmin is not None else None,
        "extmax": list(extmax) if extmax is not None else None,
    }


def inspect(path_or_dash: str) -> dict:
    if path_or_dash == "-":
        data = sys.stdin.buffer.read()
        try:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".dxf", mode="wb"
            ) as tmp:
                tmp.write(data)
                tmp_path = tmp.name
            try:
                return inspect_with_ezdxf(tmp_path)
            finally:
                Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            return inspect_fallback(data)
    try:
        return inspect_with_ezdxf(path_or_dash)
    except ImportError:
        return inspect_fallback(Path(path_or_dash).read_bytes())
    except Exception as exc:
        # Malformed file ezdxf won't parse — still report a group-code-scan view,
        # tagged so the caller knows ezdxf rejected it (useful for the freeze cases).
        rep = inspect_fallback(Path(path_or_dash).read_bytes())
        rep["source"] = f"fallback-groupcode (ezdxf rejected: {type(exc).__name__})"
        return rep


def _format_human(path: str, rep: dict) -> str:
    lines = [
        f"=== {path}",
        f"  declared : {rep['acadver']} ({rep['version_label']})   [via {rep['source']}]",
        f"  entities : {rep['entity_total']} total  {rep['entities']}",
        f"  D6 check : {rep['declared_vs_emitted']}",
    ]
    if rep["extmin"] is not None or rep["extmax"] is not None:
        lines.append(f"  extents  : EXTMIN={rep['extmin']} EXTMAX={rep['extmax']}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Read-only DXF version+entity inspector.")
    ap.add_argument("files", nargs="+", help="DXF file path(s), or '-' for stdin bytes")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = ap.parse_args(argv)

    results = {}
    for f in args.files:
        try:
            results[f] = inspect(f)
        except Exception as exc:  # report-and-continue; never abort the batch
            results[f] = {"error": f"{type(exc).__name__}: {exc}"}

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for f, rep in results.items():
            if "error" in rep:
                print(f"=== {f}\n  ERROR: {rep['error']}")
            else:
                print(_format_human(f, rep))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
