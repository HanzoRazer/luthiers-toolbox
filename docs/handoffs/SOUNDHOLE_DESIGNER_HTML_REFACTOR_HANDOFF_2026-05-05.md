# Soundhole Designer HTML — Refactor & Spiral Integration Handoff

**Date:** 2026-05-05  
**Status:** Archived incorrectly — requires relocation and spiral geometry integration  
**Current Location:** `docs/archive/photo_vectorizer_patches/soundhole_designer.html`  
**Target Location:** `tools/soundhole_designer.html` or `packages/client/public/tools/`

---

## 1. Executive Summary

The `soundhole_designer.html` is a **fully functional, production-quality standalone Helmholtz calculator** that was incorrectly placed in the vectorizer patches archive. It has no relationship to the photo vectorizer.

This tool implements comprehensive acoustic physics including:
- Helmholtz resonance with plate-air coupling
- Multi-port systems (top + side ports)
- Two-cavity Selmer/Maccaferri internal resonator modeling
- Structural stiffness analysis with bracing prescriptions
- Inverse solver (target f_H → solve for diameter)
- Body volume calculator with calibrated 1.83× factor

**Gap:** The tool supports round, oval, and f-hole soundholes but **does not support spiral geometry** — the Williams 2019 logarithmic spiral slot system already implemented in the backend.

---

## 2. Current Architecture

### 2.1 File Structure (Single HTML)

```
soundhole_designer.html (1,200+ lines)
├── <style>      — CSS custom properties, Production Shop branding
├── <body>       — Tab bar + 3-column layout
│   ├── LEFT     — Controls (presets, body params, ports)
│   ├── CENTER   — Tab content (Design canvas, Inverse Solver, Body Dims, Two-Cavity)
│   └── RIGHT    — Results (f_H, warnings, curves, stiffness, bracing)
└── <script>     — Physics engine + UI logic (~800 lines JS)
```

### 2.2 Design System

| Variable | Value | Purpose |
|----------|-------|---------|
| `--bg0` | `#0d0c09` | Primary background |
| `--br` | `#c8962e` | Brand gold |
| `--br2` | `#e0b84a` | Accent gold |
| `--blue` | `#5b8fa8` | Side port indicator |
| `--mono` | DM Mono | Code/data font |
| `--serif` | Playfair Display | Headlines |

### 2.3 Tab Structure

| Tab | ID | Purpose |
|-----|-----|---------|
| Design | `tabDesign` | Interactive canvas with drag/scroll |
| Inverse Solver | `tabInverse` | Target f_H → solve diameter |
| Body Dimensions | `tabBodydims` | Physical measurements → volume |
| Two-Cavity | `tabSelmer` | Selmer/Maccaferri internal resonator |

---

## 3. Physics Engine

### 3.1 Constants

```javascript
const C = 343;        // Speed of sound m/s
const K0 = 1.7;       // End correction factor (default)
const G0 = 0.02;      // Perimeter correction γ (default)
const PMF = 0.92;     // Plate-air coupling factor
const RF = 0.15;      // Ring width safety factor
const RMIN = 6;       // Minimum ring width mm
```

### 3.2 Core Functions

| Function | Purpose | Formula |
|----------|---------|---------|
| `Leff(a, p, t, k, g)` | Effective acoustic length | `t + k × (1 + γ × P/√A) × r` |
| `helmholtz(vol, ports, k, g)` | Multi-port Helmholtz | `f = (c/2π) × √(A_total / (V × L_eff_weighted)) × PMF` |
| `ringChk(r, w)` | Ring width structural check | `w_min = max(r × 0.15, 6mm)` |
| `placChk(x, bl)` | Position validation | Valid: 20%–70% of body length |
| `curve(vol, d, t, k, g)` | Sensitivity sweep | f_H vs diameter ±25mm |
| `invSolve(target, vol, t, k, g, spd)` | Inverse solve | Bisection search for diameter |
| `twoCav(...)` | Two-cavity eigenvalue | Exact 2×2 matrix solution |
| `bodyVol(lb, ub, w, bl, de, dn, sf)` | Volume from dimensions | Calibrated 1.83× factor |

### 3.3 Effective Length Model

```javascript
function Leff(a, p, t, k, g) {
  if (a <= 0) return t;
  const r = Math.sqrt(a / Math.PI);
  return t + k * (1 + g * p / Math.sqrt(a)) * r;
}
```

**Parameters:**
- `a` — Port area (m²)
- `p` — Port perimeter (m)
- `t` — Plate thickness (m)
- `k` — End correction factor (default 1.7)
- `g` — Perimeter correction γ (default 0.02)

### 3.4 Two-Cavity Exact Solution

```javascript
// κ² = c²·A_ap / (L_eff_ap·√(V_main·V_res))
// ω±² = (ω₁²+ω₂²)/2 ± √(((ω₁²-ω₂²)/2)² + κ⁴)
```

This replaces empirical 10% repulsion approximations with an exact eigenvalue solution.

---

## 4. State Management

### 4.1 Global State Object

```javascript
let S = {
  vol: 17.5,           // Body volume (L)
  blen: 495,           // Body length (mm)
  topThick: 2.5,       // Top thickness (mm)
  ring: 8,             // Ring width (mm)
  xn: 165,             // X from neck (mm)
  gamma: 0.02,         // Perimeter correction
  k0: 1.7,             // End correction
  top: [{              // Top ports array
    id: 1,
    type: 'circle',    // 'circle' | 'oval' | 'fhole'
    d: 96,             // Diameter (mm)
    w: 90,             // Width (for oval/fhole)
    h: 120,            // Height (for oval/fhole)
    t: 2.5,            // Plate thickness at port
    lbl: 'Main soundhole'
  }],
  side: [],            // Side ports array
  preset: 'martin_om',
  res: null,           // Computed results
  tab: 'design'
};
```

### 4.2 Port Types

```javascript
const PTYP = {
  round:     { lbl: 'Round',     pf: 1.0,  desc: '...' },
  oval:      { lbl: 'Oval',      pf: 1.15, desc: '...' },
  slot:      { lbl: 'Slot',      pf: 2.2,  desc: '...' },
  chambered: { lbl: 'Chambered', pf: 1.0,  desc: '...' },
};
```

**Gap:** No `spiral` type exists. This is where spiral geometry must be added.

---

## 5. Presets System

### 5.1 Current Presets

```javascript
const PRESETS = [
  { id: 'martin_om',   lbl: 'Martin OM',    hz: 108, vol: 17.5, ... },
  { id: 'martin_d28',  lbl: 'D-28 Dread.',  hz: 98,  vol: 22.0, ... },
  { id: 'gibson_j45',  lbl: 'Gibson J-45',  hz: 100, vol: 21.0, ... },
  { id: 'classical',   lbl: 'Classical',    hz: 96,  vol: 19.0, ... },
  { id: 'selmer',      lbl: 'Selmer Oval',  hz: 100, vol: 20.0, ... },
  { id: 'om_side',     lbl: 'OM + Side',    hz: 112, vol: 17.5, ... },
  { id: 'benedetto',   lbl: 'Benedetto F',  hz: 90,  vol: 24.0, ... },
];
```

### 5.2 Required Spiral Presets

From `soundhole_presets.py`:

| Preset ID | Slot Width | Turns | k | Target f_H |
|-----------|------------|-------|---|------------|
| `spiral_standard_14mm` | 14mm | 1.1 | 0.18 | TBD |
| `spiral_compact_12mm` | 12mm | 1.0 | 0.18 | TBD |
| `spiral_wide_18mm` | 18mm | 1.2 | 0.18 | TBD |
| `carlos_jumbo_dual` | 14mm × 2 | 1.1 | 0.18 | 90–105 Hz |

---

## 6. Structural Analysis

### 6.1 Stiffness Reduction Model

```javascript
const STIFF_K = 0.798;  // Gore-calibrated

function computeStiffness(holeArea_m2, xFromNeck_mm, bodyLength_mm,
                          plateLen_mm, plateWid_mm, bracingRestore) {
  const plateArea = (plateLen_mm/1000) * (plateWid_mm/1000);
  const areaRatio = holeArea_m2 / plateArea;
  const xFrac = xFromNeck_mm / bodyLength_mm;
  const W = Math.sin(Math.PI * xFrac);  // Mode coupling weight
  const rawRed = STIFF_K * Math.pow(areaRatio, 0.75) * W;
  const netRed = rawRed * (1 - bracingRestore);
  return { rawRed, netRed, ... };
}
```

### 6.2 Bracing Prescriptions

```javascript
const BRAC_PRESCRIPTIONS = [
  { maxRaw: 3.0,  status: 'OK',         patch: false, braces: 0 },
  { maxRaw: 5.0,  status: 'RECOMMENDED', patch: false, braces: 0 },
  { maxRaw: 6.5,  status: 'REQUIRED',   patch: true,  braces: 2 },
  { maxRaw: 8.0,  status: 'REQUIRED',   patch: true,  braces: 2 },
  { maxRaw: 999, status: 'CRITICAL',   patch: true,  braces: 4 },
];
```

---

## 7. Spiral Geometry Integration Plan

### 7.1 New Port Type

Add to `PTYP`:

```javascript
spiral: {
  lbl: 'Spiral',
  pf: 2.0,  // Williams 2019: P/A = 2/slot_width
  desc: 'Logarithmic spiral slot — distributed acoustic filter (Williams 2019)'
}
```

### 7.2 Extended State Schema

```javascript
// New spiral port in S.top array
{
  id: 1,
  type: 'spiral',
  start_radius_mm: 10.0,
  growth_rate_k: 0.18,
  turns: 1.1,
  slot_width_mm: 14.0,
  rotation_deg: 0.0,
  center_x_mm: 0.0,
  center_y_mm: 0.0,
  t: 2.5,
  lbl: 'Spiral soundhole'
}
```

### 7.3 Spiral Geometry Functions (Port from Backend)

```javascript
// From spiral_acoustic_model.py — port to JS

function spiralPathLength(startRadius_mm, k, turns) {
  const r0 = startRadius_mm / 1000;
  const theta = turns * 2 * Math.PI;
  if (Math.abs(k) < 1e-9) return r0 * theta;
  const r1 = r0 * Math.exp(k * theta);
  return Math.sqrt(1 + k * k) * (r1 - r0) / k;
}

function spiralArea(startRadius_mm, k, turns, slotWidth_mm) {
  const pathLen = spiralPathLength(startRadius_mm, k, turns);
  return (slotWidth_mm / 1000) * pathLen;
}

function spiralPerimeter(startRadius_mm, k, turns, slotWidth_mm) {
  const pathLen = spiralPathLength(startRadius_mm, k, turns);
  return 2 * pathLen + 2 * (slotWidth_mm / 1000);
}

function spiralEffectiveLength(startRadius_mm, k, turns, slotWidth_mm, 
                                topThick_mm, alpha = 0.85, beta = 0.08) {
  const t = topThick_mm / 1000;
  const w = slotWidth_mm / 1000;
  const pathLen = spiralPathLength(startRadius_mm, k, turns);
  return t + alpha * w + beta * pathLen;
}
```

### 7.4 Update buildPorts()

```javascript
function buildPorts() {
  const t = S.top.map(p => {
    if (p.type === 'circle') {
      const r = (p.d / 2) / 1000;
      return { a: Math.PI * r * r, p: 2 * Math.PI * r, t: p.t / 1000, l: p.lbl, loc: 'top' };
    }
    if (p.type === 'oval') {
      // ... existing oval code ...
    }
    if (p.type === 'spiral') {
      const area = spiralArea(p.start_radius_mm, p.growth_rate_k, p.turns, p.slot_width_mm);
      const perim = spiralPerimeter(p.start_radius_mm, p.growth_rate_k, p.turns, p.slot_width_mm);
      const leff = spiralEffectiveLength(
        p.start_radius_mm, p.growth_rate_k, p.turns, p.slot_width_mm,
        p.t, 0.85, 0.08  // alpha, beta — calibration constants
      );
      return { a: area, p: perim, t: leff, l: p.lbl, loc: 'top', _spiral: p };
    }
    // ... fhole ...
  });
  // ... side ports ...
}
```

### 7.5 Spiral Canvas Rendering

```javascript
function drawSpiralOnCanvas(ctx, p, cx, cy, scale) {
  const r0 = p.start_radius_mm * scale;
  const k = p.growth_rate_k;
  const turns = p.turns;
  const w = p.slot_width_mm * scale;
  const rot = (p.rotation_deg || 0) * Math.PI / 180;
  
  const steps = Math.ceil(turns * 60);
  const thetaMax = turns * 2 * Math.PI;
  
  // Draw centerline
  ctx.beginPath();
  for (let i = 0; i <= steps; i++) {
    const theta = (i / steps) * thetaMax;
    const r = r0 * Math.exp(k * theta);
    const x = cx + r * Math.cos(theta + rot);
    const y = cy + r * Math.sin(theta + rot);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.strokeStyle = '#c8962e';
  ctx.lineWidth = w;
  ctx.lineCap = 'round';
  ctx.stroke();
  
  // Draw slot edges (offset by ±w/2)
  // ... perpendicular offset algorithm from spiral_geometry.py ...
}
```

### 7.6 Spiral UI Controls

Add to `renderTopPorts()`:

```javascript
if (p.type === 'spiral') {
  d.innerHTML += `
    <div class="f"><span class="fk">Start radius</span>
      <input type="number" class="fv n" data-k="start_radius_mm" value="${p.start_radius_mm}" min="5" max="25" step="0.5">
      <span class="fu">mm</span></div>
    <div class="f"><span class="fk">Growth rate k</span>
      <input type="number" class="fv n" data-k="growth_rate_k" value="${p.growth_rate_k}" min="0.05" max="0.40" step="0.01"></div>
    <div class="f"><span class="fk">Turns</span>
      <input type="number" class="fv n" data-k="turns" value="${p.turns}" min="0.5" max="2.5" step="0.1"></div>
    <div class="f"><span class="fk">Slot width</span>
      <input type="number" class="fv n" data-k="slot_width_mm" value="${p.slot_width_mm}" min="8" max="30" step="1">
      <span class="fu">mm</span></div>
    <div class="f"><span class="fk">Rotation</span>
      <input type="number" class="fv n" data-k="rotation_deg" value="${p.rotation_deg || 0}" min="0" max="360" step="15">
      <span class="fu">°</span></div>
    <div style="font-size:7px;color:var(--dim3);margin-top:4px">
      P:A = ${(2 / p.slot_width_mm).toFixed(3)} mm⁻¹ · 
      Williams threshold: >0.10 mm⁻¹
    </div>
  `;
}
```

### 7.7 Dual-Spiral Support

For Carlos Jumbo dual-spiral configuration:

```javascript
// Add to PRESETS
{
  id: 'carlos_jumbo',
  lbl: 'Carlos Jumbo',
  hz: 98,  // Target
  vol: 21.0,
  bl: 520,
  xf: 0.52,
  ring: 0,  // No ring for spiral
  note: 'Dual logarithmic spiral — displaced f-hole logic per Williams 2019.',
  top: [
    {
      id: 1, type: 'spiral',
      start_radius_mm: 10.0, growth_rate_k: 0.18, turns: 1.1,
      slot_width_mm: 14.0, rotation_deg: 270,
      center_x_mm: -88.0, center_y_mm: -62.0,
      t: 2.6, lbl: 'Upper bass-side spiral'
    },
    {
      id: 2, type: 'spiral',
      start_radius_mm: 10.0, growth_rate_k: 0.18, turns: 1.1,
      slot_width_mm: 14.0, rotation_deg: 90,
      center_x_mm: 78.0, center_y_mm: 112.0,
      t: 2.6, lbl: 'Lower treble-side spiral'
    }
  ],
  side: []
}
```

---

## 8. Calibration Constants Integration

### 8.1 Current Hardcoded Values

| Constant | Current | Source |
|----------|---------|--------|
| `alpha` (slot end correction) | 0.85 | Literature estimate |
| `beta` (distributed path factor) | 0.08 | Empirical guess |
| `loss_scale` | 1.0 | Placeholder |

### 8.2 Integration with Calibration System

Once `spiral_calibration_solver.py` produces calibrated constants:

```javascript
// Load from API or localStorage
const SPIRAL_CALIBRATION = {
  alpha: 0.85,       // Update after field calibration
  beta: 0.08,        // Update after field calibration
  loss_scale: 1.0,   // Update after field calibration
  calibration_date: null,
  calibration_id: null
};

function spiralEffectiveLength(...) {
  // Use SPIRAL_CALIBRATION.alpha, SPIRAL_CALIBRATION.beta
}
```

---

## 9. Refactoring Tasks

### 9.1 Immediate (Before Spiral Integration)

| Task | Priority | Notes |
|------|----------|-------|
| Relocate file | HIGH | Move from archive to `tools/` |
| Add to gitignore exceptions | HIGH | Ensure not re-archived |
| Verify functionality | HIGH | Test all 4 tabs work |
| Document in CLAUDE.md | MEDIUM | Add to "Standalone Tools" section |

### 9.2 Spiral Integration

| Task | Priority | Notes |
|------|----------|-------|
| Add spiral type to PTYP | HIGH | New port type constant |
| Port spiral geometry functions | HIGH | From `spiral_acoustic_model.py` |
| Update buildPorts() | HIGH | Handle spiral type |
| Add spiral UI controls | HIGH | Start radius, k, turns, slot width |
| Canvas spiral rendering | MEDIUM | Logarithmic spiral drawing |
| Add spiral presets | MEDIUM | standard_14mm, carlos_jumbo, etc. |
| Dual-spiral canvas layout | MEDIUM | Two spirals with offset centers |

### 9.3 Future Enhancements

| Task | Priority | Notes |
|------|----------|-------|
| API integration | LOW | Fetch presets from backend |
| DXF export | LOW | Generate spiral DXF from UI |
| Calibration loading | LOW | Load calibrated constants from API |
| Vue component parity | LOW | Sync with SpiralSoundholeDesigner.vue |

---

## 10. File Dependencies

### 10.1 Backend Files to Reference

| File | Purpose |
|------|---------|
| `spiral_acoustic_model.py` | Spiral L_eff, loss model, multi-port |
| `spiral_q_fh_solver.py` | Forward/inverse solver |
| `soundhole_presets.py` | SPIRAL_PRESETS dictionary |
| `spiral_geometry.py` | SpiralSpec, geometry computation |

### 10.2 Existing Vue Components

| File | Purpose |
|------|---------|
| `SoundholeDesignerView.vue` | Main view wrapper |
| `SpiralSoundholeDesigner.vue` | Spiral-specific component |

The standalone HTML should remain independent but feature-compatible with these Vue components.

---

## 11. Testing Checklist

### 11.1 Existing Functionality

- [ ] Martin OM preset loads correctly
- [ ] D-28 preset calculates ~98 Hz
- [ ] Selmer oval preset works
- [ ] Side port addition works
- [ ] Inverse solver finds correct diameter
- [ ] Body dimensions calculator works
- [ ] Two-cavity model calculates eigenvalues
- [ ] Stiffness panel updates
- [ ] Bracing prescription displays

### 11.2 After Spiral Integration

- [ ] Spiral port type appears in dropdown
- [ ] Spiral parameters render in UI
- [ ] Spiral area/perimeter calculate correctly
- [ ] Spiral L_eff uses correct formula
- [ ] Helmholtz frequency reasonable for spiral
- [ ] Spiral renders on canvas
- [ ] Dual-spiral preset loads
- [ ] Carlos Jumbo target f_H ~90–105 Hz
- [ ] P:A ratio displays correctly

---

## 12. References

| Resource | Location |
|----------|----------|
| Williams 2019 | mwguitars.com.au Parts 7-8 |
| Spiral Developer Handoff | `docs/handoffs/SPIRAL_SOUNDHOLE_DEVELOPER_HANDOFF_2026-05-03.md` |
| Spiral Acoustic Model | `spiral_acoustic_model.py` |
| Backend Presets | `soundhole_presets.py` |
| Spiral Geometry Engine | `spiral_geometry.py` |

---

*Handoff prepared by Claude Code*  
*For The Production Shop — luthiers-toolbox*  
*2026-05-05*
