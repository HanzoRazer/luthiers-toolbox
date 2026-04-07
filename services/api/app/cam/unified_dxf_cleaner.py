#!/usr/bin/env python3
import argparse, ezdxf

def main():
    ap = argparse.ArgumentParser(description="Unified DXF Cleaner for Guitar Projects")  
    ap.add_argument("--infile", required=True, help="Input DXF file")
    ap.add_argument("--out", required=True, help="Output DXF file")
    ap.add_argument("--preserve-layers", action="store_true", help="Preserve original layer names")
    ap.add_argument("--split-perimeter", action="store_true", help="Split perimeter vs interior geometry")
    ap.add_argument("--keep", type=str, help="Comma-separated list of layers to keep")
    ap.add_argument("--tol", type=float, default=0.1, help="Tolerance for closing gaps")
    args = ap.parse_args()

    doc = ezdxf.readfile(args.infile)
    msp = doc.modelspace()

    keep_layers = set([l.strip() for l in args.keep.split(",")]) if args.keep else None

    closed_polylines = []
    for e in msp:
        if e.dxftype() in ["LWPOLYLINE", "POLYLINE"]:
            if keep_layers and e.dxf.layer not in keep_layers:
                continue
            if not e.closed:
                e.closed = True
            closed_polylines.append(e)

    newdoc = ezdxf.new("R2010")
    newmsp = newdoc.modelspace()

    for e in closed_polylines:
        newe = newmsp.add_lwpolyline(e.get_points("xy"), dxfattribs={"closed": True})
        if args.preserve_layers:
            newe.dxf.layer = e.dxf.layer

    newdoc.saveas(args.out)
    print(f"Saved {len(closed_polylines)} closed polylines to {args.out}")

if __name__ == "__main__":
    main()
