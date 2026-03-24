"""Generate Smart Guitar DXF from spec data."""
import json
import ezdxf
import math

spec = json.load(open(
    'app/instrument_geometry/body/specs/smart_guitar_v1.json', encoding='utf-8'))

doc = ezdxf.new('R2010')
doc.units = ezdxf.units.MM
msp = doc.modelspace()

# ── Layer definitions ──────────────────────────────────
layer_defs = {
    'BODY_OUTLINE':  7,   # white
    'NECK_POCKET':   1,   # red
    'NECK_PICKUP':   3,   # green
    'BRIDGE_PICKUP': 3,
    'BRIDGE_ROUTE':  5,   # blue
    'PI_CAVITY':     4,   # cyan
    'ARDUINO_POCKET':4,
    'ANTENNA':       6,   # magenta
    'CONTROL_PLATE': 6,
    'OUTPUT_JACK':   2,   # yellow
    'USB_PORT':      2,
    'BOLT_HOLES':    1,
    'DIM_REFERENCE': 9,   # gray (reference only)
}
for name, color in layer_defs.items():
    doc.layers.add(name, dxfattribs={'color': color})

# ── Body dimensions ────────────────────────────────────
body   = spec['body']['dimensions']
BL     = body['length_mm']           # 444.5
BW     = body['width_max_mm']        # 368.3
BT     = body['thickness_mm']        # 44.45
LBW    = spec['body']['lower_bout']['width_mm']   # 304.8
UBW    = spec['body']['upper_section']['width_mm'] # 254.0

hl = BL / 2   # 222.25  half-length  (Y+ = toward neck)
hw = BW / 2   # 184.15  half-width
lbh = LBW / 2 # 152.4   lower bout half
ubh = UBW / 2 # 127.0   upper bout half

# ── Helper: rounded-corner rectangle (centered) ────────
def add_rounded_rect(layer, cx, cy, length, width, r=3.0):
    if r <= 0:
        pts = [
            (cx - width/2, cy - length/2),
            (cx + width/2, cy - length/2),
            (cx + width/2, cy + length/2),
            (cx - width/2, cy + length/2),
        ]
        msp.add_lwpolyline(pts,
            dxfattribs={'layer': layer}, close=True)
        return
    x0, y0 = cx - width/2,  cy - length/2
    x1, y1 = cx + width/2,  cy + length/2
    # Build polyline with bulge arcs at corners
    # bulge = tan(angle/4), 90-deg arc => bulge = tan(45) = 1.0
    b = 1.0   # 90-degree arc
    pts_with_bulge = [
        (x0 + r, y0, 0),
        (x1 - r, y0, 0),
        (x1 - r, y0, b),
        (x1,     y0 + r, 0),
        (x1,     y1 - r, 0),
        (x1,     y1 - r, b),
        (x1 - r, y1, 0),
        (x0 + r, y1, 0),
        (x0 + r, y1, b),
        (x0,     y1 - r, 0),
        (x0,     y0 + r, 0),
        (x0,     y0 + r, b),
    ]
    pl = msp.add_lwpolyline(pts_with_bulge,
        dxfattribs={'layer': layer}, close=True)
    pl.set_points(
        [(p[0], p[1], 0, 0, p[2]) for p in pts_with_bulge])

# ── BODY OUTLINE ───────────────────────────────────────
# Explorer-Klein hybrid — 48 points, origin at center
# Y+ toward neck, X+ toward treble side
def body_outline():
    pts = []
    # right side — neck to tail
    pts += [
        ( ubh * 0.15,  hl),            # top center neck
        ( ubh * 0.85,  hl * 0.82),     # upper right
        ( hw   * 0.90, hl * 0.62),     # right shoulder
        ( hw,          hl * 0.35),     # right upper waist
        ( hw,          hl * 0.10),     # right mid
        ( hw   * 0.98, -hl * 0.08),    # right lower
        ( hw   * 0.92, -hl * 0.28),    # right lower bout top
        ( hw   * 0.88, -hl * 0.50),    # right lower bout
        ( hw   * 0.78, -hl * 0.68),    # right lower bout bottom
        ( lbh  * 0.90, -hl * 0.82),    # right V approach
        ( lbh  * 0.40, -hl * 0.96),    # right V near
        ( 0,           -hl),           # V bottom center
        (-lbh  * 0.40, -hl * 0.96),    # left V near
        (-lbh  * 0.90, -hl * 0.82),    # left V approach
        (-hw   * 0.78, -hl * 0.68),    # left lower bout bottom
    ]
    # left side — Klein ergonomic cutaways
    pts += [
        (-hw   * 0.88, -hl * 0.50),    # left lower bout
        (-hw   * 0.92, -hl * 0.28),    # left lower bout top
        (-hw   * 0.98, -hl * 0.08),    # left lower
        (-hw,           hl * 0.10),    # left mid
        (-hw,           hl * 0.35),    # left upper waist
        (-hw   * 0.95,  hl * 0.50),    # left shoulder lower
        # Klein ergonomic upper-body void starts
        (-hw   * 0.80,  hl * 0.62),    # void entry
        (-ubh  * 0.95,  hl * 0.70),    # void inner edge
        (-ubh  * 0.75,  hl * 0.78),    # void upper
        (-ubh  * 0.50,  hl * 0.85),    # klein cutaway apex
        (-ubh  * 0.25,  hl * 0.90),    # re-entry
        (-ubh  * 0.10,  hl * 0.94),    # near center
        ( ubh  * 0.05,  hl * 0.97),    # top center approach
        ( ubh  * 0.15,  hl),           # close at top center
    ]
    msp.add_lwpolyline(pts,
        dxfattribs={'layer': 'BODY_OUTLINE'}, close=True)

body_outline()

# ── Cavities from spec ─────────────────────────────────
cavs = spec['cavities']

# NECK POCKET (bolt-on, centered at top)
np_d = cavs['neck_pocket']['dimensions_mm']
np_p = cavs['neck_pocket']['body_position_mm']
# Y coord: y_from_top measured from top of body (hl)
np_cy = hl - np_p['y_from_top'] - np_d['length'] / 2
add_rounded_rect('NECK_POCKET',
    cx=0, cy=np_cy,
    length=np_d['length'], width=np_d['width'],
    r=np_d['corner_radius'])

# BOLT HOLES
for bolt in cavs['neck_pocket']['bolt_pattern'][
        'positions_from_pocket_center_mm']:
    msp.add_circle(
        center=(bolt['x'], np_cy + bolt['y']),
        radius=cavs['neck_pocket']['bolt_pattern'][
            'pilot_hole_mm'] / 2,
        dxfattribs={'layer': 'BOLT_HOLES'})

# NECK PICKUP
nu_d = cavs['neck_pickup_route']['dimensions_mm']
nu_p = cavs['neck_pickup_route']['body_position_mm']
nu_cy = hl - nu_p['y_from_top']
add_rounded_rect('NECK_PICKUP',
    cx=0, cy=nu_cy,
    length=nu_d['length'], width=nu_d['width'],
    r=nu_d['corner_radius'])

# BRIDGE PICKUP
bu_d = cavs['bridge_pickup_route']['dimensions_mm']
bu_p = cavs['bridge_pickup_route']['body_position_mm']
bu_cy = hl - bu_p['y_from_top']
add_rounded_rect('BRIDGE_PICKUP',
    cx=0, cy=bu_cy,
    length=bu_d['length'], width=bu_d['width'],
    r=bu_d['corner_radius'])

# BRIDGE ROUTE (headless bridge mounting)
br_d = cavs['bridge_route']['dimensions_mm']
br_p = cavs['bridge_route']['body_position_mm']
br_cy = hl - br_p.get('y_from_top', 320)
add_rounded_rect('BRIDGE_ROUTE',
    cx=0, cy=br_cy,
    length=br_d.get('bridge_length', 95),
    width=br_d.get('bridge_width', 42),
    r=br_d.get('corner_radius', 3.0))

# REAR ELECTRONICS — Pi 5
pi_d = cavs['rear_electronics_cavity']['dimensions_mm']
pi_p = cavs['rear_electronics_cavity'].get('body_position_mm', {})
pi_cx = pi_p.get('x_offset_from_center', 36.8)
pi_cy = hl - pi_p.get('y_from_top', 275.7)
add_rounded_rect('PI_CAVITY',
    cx=pi_cx, cy=pi_cy,
    length=pi_d['length'], width=pi_d['width'],
    r=pi_d.get('corner_radius', 6.0))

# ARDUINO POCKET
ar_d = cavs['arduino_preamp_pocket']['dimensions_mm']
ar_p = cavs['arduino_preamp_pocket']['body_position_mm']
ar_cx = ar_p.get('x_offset_from_center', 36.8)
ar_cy = hl - ar_p.get('y_from_top', 133.5)
add_rounded_rect('ARDUINO_POCKET',
    cx=ar_cx, cy=ar_cy,
    length=ar_d['length'], width=ar_d['width'],
    r=ar_d.get('corner_radius', 4.0))

# ANTENNA RECESS
an_d = cavs['antenna_recess']['dimensions_mm']
an_p = cavs['antenna_recess']['body_position_mm']
an_cx = an_p.get('x_offset_from_center', -22.2)
an_cy = hl - an_p.get('y_from_top', 202.6)
add_rounded_rect('ANTENNA',
    cx=an_cx, cy=an_cy,
    length=an_d.get('length', 50),
    width=an_d.get('width', 30),
    r=2.0)

# CONTROL PLATE SURFACE
cp_d = cavs['control_plate_surface']['dimensions_mm']
cp_p = cavs['control_plate_surface']['body_position_mm']
cp_cx = cp_p.get('x_center', 55.2)
cp_cy = hl - cp_p.get('y_from_top', 346.7)
add_rounded_rect('CONTROL_PLATE',
    cx=cp_cx, cy=cp_cy,
    length=cp_d.get('length', 100),
    width=cp_d.get('width', 50),
    r=cp_d.get('corner_radius', 6.35))

# OUTPUT JACK (circular bore footprint)
oj_p = cavs['output_jack']['body_position_mm']
oj_x = oj_p.get('x_from_center', 110.4)
oj_y = hl - oj_p.get('y_from_top', 391.2)
msp.add_circle(center=(oj_x, oj_y),
    radius=6.35,
    dxfattribs={'layer': 'OUTPUT_JACK'})

# USB-C PORT (edge slot footprint)
usb_p = cavs['usb_c_port']['body_position_mm']
usb_y = hl - usb_p.get('y_from_top', 239.4)
add_rounded_rect('USB_PORT',
    cx=hw - 3.5, cy=usb_y,
    length=6.5, width=12.0,
    r=1.0)

# ── Save ───────────────────────────────────────────────
out = 'data/smart_guitar_v3_from_spec.dxf'
doc.saveas(out)
print(f'Saved: {out}')

# ── Verify ─────────────────────────────────────────────
doc2 = ezdxf.readfile(out)
print()
print('Layer inventory:')
for layer in doc2.layers:
    count = sum(1 for e in doc2.modelspace()
                if e.dxf.layer == layer.dxf.name)
    if count > 0:
        print(f'  {layer.dxf.name}: {count} entities')

# Bounding box
from ezdxf import bbox
box = bbox.extents(doc2.modelspace())
if box.has_data:
    print()
    print(f'Bounding box: {box.size.x:.1f} x {box.size.y:.1f} mm')
    print(f'  X: {box.extmin.x:.1f} to {box.extmax.x:.1f}')
    print(f'  Y: {box.extmin.y:.1f} to {box.extmax.y:.1f}')
