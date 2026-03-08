"""Inspect J45 DIMS.dxf to inventory all geometry including bracing."""
import ezdxf

doc = ezdxf.readfile("Guitar Plans/J 45 Plans/J45 DIMS.dxf")
msp = doc.modelspace()

# Bounding box
all_x, all_y = [], []
for e in msp:
    try:
        if e.dxftype() == "LINE":
            all_x.extend([e.dxf.start.x, e.dxf.end.x])
            all_y.extend([e.dxf.start.y, e.dxf.end.y])
        elif e.dxftype() in ("CIRCLE", "ARC"):
            c = e.dxf.center
            r = e.dxf.radius
            all_x.extend([c.x - r, c.x + r])
            all_y.extend([c.y - r, c.y + r])
        elif e.dxftype() == "LWPOLYLINE":
            for p in e.get_points():
                all_x.append(p[0])
                all_y.append(p[1])
    except Exception:
        pass

print(f"Bounding box:")
print(f"  X: {min(all_x):.2f} to {max(all_x):.2f}  (span {max(all_x)-min(all_x):.2f})")
print(f"  Y: {min(all_y):.2f} to {max(all_y):.2f}  (span {max(all_y)-min(all_y):.2f})")

# Polylines sorted by area
print(f"\nLWPOLYLINES (top 15 by bbox area):")
polys = []
for e in msp:
    if e.dxftype() == "LWPOLYLINE":
        pts = list(e.get_points())
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        w = max(xs) - min(xs)
        h = max(ys) - min(ys)
        has_bulge = any(abs(p[4]) > 0.001 for p in pts if len(p) > 4)
        polys.append((len(pts), e.closed, w, h, min(xs), min(ys), has_bulge))
polys.sort(key=lambda x: x[2] * x[3], reverse=True)
for i, (npts, cl, w, h, mx, my, bulge) in enumerate(polys[:15]):
    print(f"  [{i}] pts={npts} closed={cl} size={w:.1f}x{h:.1f} at ({mx:.1f},{my:.1f}) bulge={bulge}")

# Circles
print(f"\nCIRCLES:")
for e in msp:
    if e.dxftype() == "CIRCLE":
        c = e.dxf.center
        r = e.dxf.radius
        print(f"  center=({c.x:.2f},{c.y:.2f}) r={r:.3f} d={r*2:.3f}")

# Text content
print(f"\nTEXT entries ({sum(1 for e in msp if e.dxftype()=='TEXT')}):")
for e in msp:
    if e.dxftype() == "TEXT":
        print(f"  '{e.dxf.text}' at ({e.dxf.insert.x:.1f},{e.dxf.insert.y:.1f})")

# Dimension entities
print(f"\nDIMENSION entries ({sum(1 for e in msp if e.dxftype()=='DIMENSION')}):")
for e in msp:
    if e.dxftype() == "DIMENSION":
        try:
            txt = e.dxf.get("text", "")
            dp = e.dxf.get("defpoint", None)
            if dp:
                print(f"  text='{txt}' defpoint=({dp.x:.2f},{dp.y:.2f})")
        except Exception:
            pass
