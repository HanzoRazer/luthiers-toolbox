/**
 * Production Shop — DXF Import Client
 * 
 * Drop-in upgrade for ps-import-normalize.html.
 * 
 * Strategy:
 *   1. Parse DXF in-browser with dxf-parser (fast, no round-trip for simple geometry)
 *   2. Any SPLINE entity → POST to /api/dxf/spline/evaluate for true NURBS evaluation
 *   3. Optionally send entire file to /api/dxf/parse-and-normalize for full server pipeline
 * 
 * Usage:
 *   import { DxfImportClient } from './dxfImportClient.js';
 *   const client = new DxfImportClient({ apiBase: '/api/dxf' });
 *   const result = await client.loadFile(file);
 *   // result.paths: [{id, type, layer, d, pointCount}]
 *   // result.bbox, result.layers, result.typeCounts
 */

const API_BASE = window.PS_API_BASE || '/api/dxf';

// ─── Simple geometry helpers (browser-side, no server needed) ─────────────────

function arcToPath(cx, cy, r, startDeg, endDeg, samples = 48) {
  let s = startDeg * Math.PI / 180;
  let e = endDeg   * Math.PI / 180;
  if (e < s) e += 2 * Math.PI;
  const pts = [];
  for (let i = 0; i <= samples; i++) {
    const a = s + (e - s) * i / samples;
    pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]);
  }
  return ptsToPath(pts);
}

function circleToPath(cx, cy, r) {
  return `M${(cx-r).toFixed(3)},${cy.toFixed(3)} ` +
         `A${r.toFixed(3)},${r.toFixed(3)},0,1,0,${(cx+r).toFixed(3)},${cy.toFixed(3)} ` +
         `A${r.toFixed(3)},${r.toFixed(3)},0,1,0,${(cx-r).toFixed(3)},${cy.toFixed(3)} Z`;
}

function ptsToPath(pts, closed = false) {
  if (!pts.length) return '';
  let d = `M${pts[0][0].toFixed(3)},${pts[0][1].toFixed(3)}`;
  for (let i = 1; i < pts.length; i++) d += `L${pts[i][0].toFixed(3)},${pts[i][1].toFixed(3)}`;
  if (closed) d += 'Z';
  return d;
}

function lwpolyToPoints(vertices) {
  const pts = [];
  for (let i = 0; i < vertices.length; i++) {
    const v = vertices[i];
    pts.push([v.x, v.y]);
    const bulge = v.bulge || 0;
    if (Math.abs(bulge) > 1e-6 && i < vertices.length - 1) {
      const nv = vertices[i + 1];
      const dx = nv.x - v.x, dy = nv.y - v.y;
      const d = Math.sqrt(dx * dx + dy * dy);
      if (d < 1e-10) continue;
      const r = d * (1 + bulge * bulge) / (4 * Math.abs(bulge));
      const mx = (v.x + nv.x) / 2, my = (v.y + nv.y) / 2;
      const px = -dy / d, py = dx / d;
      const dc = Math.sqrt(Math.max(r * r - (d / 2) ** 2, 0));
      const sign = bulge > 0 ? 1 : -1;
      const acx = mx + sign * dc * px, acy = my + sign * dc * py;
      const a1 = Math.atan2(v.y - acy, v.x - acx);
      let a2 = Math.atan2(nv.y - acy, nv.x - acx);
      if (bulge > 0 && a2 < a1) a2 += 2 * Math.PI;
      if (bulge < 0 && a2 > a1) a2 -= 2 * Math.PI;
      const steps = Math.max(8, Math.round(Math.abs(a2 - a1) / (2 * Math.PI) * 48));
      for (let j = 1; j <= steps; j++) {
        const a = a1 + (a2 - a1) * j / steps;
        pts.push([acx + r * Math.cos(a), acy + r * Math.sin(a)]);
      }
    }
  }
  return pts;
}

// ─── Spline: browser approximation (fallback) ─────────────────────────────────

function splineBrowserFallback(entity) {
  // Catmull-Rom through control points as approximation
  const pts = entity.controlPoints || entity.fitPoints || [];
  if (pts.length < 2) return '';
  let d = `M${pts[0].x.toFixed(3)},${pts[0].y.toFixed(3)}`;
  for (let i = 1; i < pts.length - 1; i++) {
    const cp = pts[i], next = pts[i + 1] || pts[i];
    d += `Q${cp.x.toFixed(3)},${cp.y.toFixed(3)},` +
         `${((cp.x + next.x) / 2).toFixed(3)},${((cp.y + next.y) / 2).toFixed(3)}`;
  }
  d += `L${pts[pts.length - 1].x.toFixed(3)},${pts[pts.length - 1].y.toFixed(3)}`;
  return d;
}

// ─── Spline: server evaluation ────────────────────────────────────────────────

async function evaluateSplineServer(entity, samples = 128) {
  try {
    const res = await fetch(`${API_BASE}/spline/evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        control_points: (entity.controlPoints || []).map(p => ({ x: p.x, y: p.y, z: p.z || 0 })),
        knot_values:    entity.knotValues || null,
        degree:         entity.degree || 3,
        fit_points:     (entity.fitPoints || []).map(p => ({ x: p.x, y: p.y })),
        closed:         entity.closed || false,
        samples,
      }),
    });
    if (!res.ok) throw new Error(`Server ${res.status}`);
    const data = await res.json();
    return { d: data.d, method: 'server', pointCount: data.point_count };
  } catch (err) {
    console.warn('Spline server eval failed, using browser fallback:', err.message);
    return { d: splineBrowserFallback(entity), method: 'browser_fallback', pointCount: 0 };
  }
}

// ─── Full server pipeline (preferred for production) ──────────────────────────

async function parseFullServer(file, opts = {}) {
  const form = new FormData();
  form.append('file', file);
  const params = new URLSearchParams({
    target_width:  opts.targetWidth  || 200,
    target_height: opts.targetHeight || 320,
    padding:       opts.padding      || 8,
    fit_mode:      opts.fitMode      || 'contain',
    flip_y:        opts.flipY !== false,
    samples:       opts.samples      || 96,
    ...(opts.layers ? { layers: opts.layers.join(',') } : {}),
  });
  const res = await fetch(`${API_BASE}/parse-and-normalize?${params}`, {
    method: 'POST', body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Server parse failed');
  }
  return res.json();
}

// ─── DxfImportClient ──────────────────────────────────────────────────────────

export class DxfImportClient {
  constructor({ apiBase = '/api/dxf', preferServer = true, splineSamples = 128 } = {}) {
    this.apiBase = apiBase;
    this.preferServer = preferServer;  // true → always use server for DXF
    this.splineSamples = splineSamples;
  }

  /**
   * Main entry point. Returns a normalized result object.
   * @param {File} file - SVG or DXF file
   * @param {object} opts - normalize options
   * @returns {Promise<ImportResult>}
   */
  async loadFile(file, opts = {}) {
    const ext = file.name.split('.').pop().toLowerCase();

    if (ext === 'svg') {
      return this._loadSVG(file, opts);
    } else if (ext === 'dxf') {
      return this.preferServer
        ? this._loadDXFServer(file, opts)
        : this._loadDXFBrowser(file, opts);
    }
    throw new Error(`Unsupported file type: ${ext}`);
  }

  // ── SVG: browser-native ────────────────────────────────────────────────────

  async _loadSVG(file, opts) {
    const text = await file.text();
    const doc = new DOMParser().parseFromString(text, 'image/svg+xml');
    const els = doc.querySelectorAll('path,rect,circle,ellipse,polyline,polygon,line');
    const paths = [];
    const colors = ['#8a4a2a','#3a6a8a','#4a8a5a','#7a5a2a','#5a3a7a','#8a6a2a'];

    els.forEach((el, i) => {
      const d = this._svgElToPath(el);
      if (!d) return;
      paths.push({
        id: `svg_${i}`,
        type: el.tagName.toLowerCase(),
        layer: '0',
        d,
        pointCount: (d.match(/[ML]/g) || []).length,
        color: colors[i % colors.length],
        visible: true,
        label: `${el.tagName.toLowerCase()} ${i + 1}`,
        method: 'browser_svg',
      });
    });

    const bbox = this._computeBbox(paths);
    return { paths, bbox, layers: ['0'], typeCounts: { svg: paths.length }, source: 'svg_browser' };
  }

  _svgElToPath(el) {
    const tag = el.tagName.toLowerCase();
    switch (tag) {
      case 'path':     return el.getAttribute('d');
      case 'rect': {
        const x = +el.getAttribute('x') || 0, y = +el.getAttribute('y') || 0;
        const w = +el.getAttribute('width') || 0, h = +el.getAttribute('height') || 0;
        return `M${x},${y}H${x+w}V${y+h}H${x}Z`;
      }
      case 'circle': {
        const cx = +el.getAttribute('cx') || 0, cy = +el.getAttribute('cy') || 0;
        const r = +el.getAttribute('r') || 0;
        return circleToPath(cx, cy, r);
      }
      case 'ellipse': {
        const cx = +el.getAttribute('cx') || 0, cy = +el.getAttribute('cy') || 0;
        const rx = +el.getAttribute('rx') || 0, ry = +el.getAttribute('ry') || 0;
        return `M${cx-rx},${cy} A${rx},${ry},0,1,0,${cx+rx},${cy} A${rx},${ry},0,1,0,${cx-rx},${cy} Z`;
      }
      case 'polyline': case 'polygon': {
        const pts = (el.getAttribute('points') || '').trim().split(/[\s,]+/);
        if (pts.length < 4) return null;
        let d = `M${pts[0]},${pts[1]}`;
        for (let i = 2; i < pts.length - 1; i += 2) d += `L${pts[i]},${pts[i+1]}`;
        if (tag === 'polygon') d += 'Z';
        return d;
      }
      case 'line': {
        const x1 = el.getAttribute('x1'), y1 = el.getAttribute('y1');
        const x2 = el.getAttribute('x2'), y2 = el.getAttribute('y2');
        return `M${x1},${y1}L${x2},${y2}`;
      }
      default: return null;
    }
  }

  // ── DXF: server pipeline ────────────────────────────────────────────────────

  async _loadDXFServer(file, opts) {
    const raw = await parseFullServer(file, opts);
    const colors = ['#8a4a2a','#3a6a8a','#4a8a5a','#7a5a2a','#5a3a7a','#8a6a2a','#6a4a8a','#3a8a6a'];
    return {
      paths: raw.paths.map((p, i) => ({
        ...p,
        color: colors[i % colors.length],
        visible: true,
        label: `${p.type} ${i + 1}${p.layer !== '0' ? ` [${p.layer}]` : ''}`,
        method: 'server',
      })),
      bbox: raw.bbox_raw,
      layers: raw.layers,
      typeCounts: raw.type_counts,
      source: 'dxf_server',
    };
  }

  // ── DXF: browser + selective server spline calls ────────────────────────────

  async _loadDXFBrowser(file, opts) {
    if (!window.DxfParser) throw new Error('DxfParser not loaded');
    const text = await file.text();
    const parser = new window.DxfParser();
    const dxf = parser.parseSync(text);
    const entities = dxf.entities || [];
    const colors = ['#8a4a2a','#3a6a8a','#4a8a5a','#7a5a2a','#5a3a7a','#8a6a2a','#6a4a8a','#3a8a6a'];
    const results = [];

    // Process splines concurrently
    const splineJobs = [];

    for (const ent of entities) {
      const type = ent.type;
      let d = null;
      let method = 'browser';

      if (type === 'SPLINE') {
        splineJobs.push({ ent, idx: results.length });
        results.push(null); // placeholder
        continue;
      }

      try {
        switch (type) {
          case 'LINE':
            d = `M${ent.start.x.toFixed(3)},${ent.start.y.toFixed(3)}L${ent.end.x.toFixed(3)},${ent.end.y.toFixed(3)}`;
            break;
          case 'LWPOLYLINE': case 'POLYLINE':
            d = ptsToPath(lwpolyToPoints(ent.vertices || []), ent.shape);
            break;
          case 'CIRCLE':
            d = circleToPath(ent.center.x, ent.center.y, ent.radius);
            break;
          case 'ARC':
            d = arcToPath(ent.center.x, ent.center.y, ent.radius, ent.startAngle, ent.endAngle);
            break;
        }
      } catch (e) { continue; }

      if (!d) continue;
      const i = results.length;
      results.push({
        id: `${type}_${i}`, type, layer: ent.layer || '0', d,
        pointCount: (d.match(/[ML]/g) || []).length,
        color: colors[i % colors.length], visible: true,
        label: `${type} ${i + 1}`, method,
      });
    }

    // Resolve splines (concurrent server calls)
    const splineResults = await Promise.all(
      splineJobs.map(({ ent }) => evaluateSplineServer(ent, this.splineSamples))
    );
    splineJobs.forEach(({ ent, idx }, j) => {
      const sr = splineResults[j];
      results[idx] = {
        id: `SPLINE_${idx}`, type: 'SPLINE', layer: ent.layer || '0', d: sr.d,
        pointCount: sr.pointCount,
        color: colors[idx % colors.length], visible: true,
        label: `SPLINE ${idx + 1}`,
        method: sr.method,
      };
    });

    const finalPaths = results.filter(Boolean);
    const bbox = this._computeBbox(finalPaths);

    return {
      paths: finalPaths, bbox,
      layers: [...new Set(finalPaths.map(p => p.layer))].sort(),
      typeCounts: finalPaths.reduce((acc, p) => { acc[p.type] = (acc[p.type] || 0) + 1; return acc; }, {}),
      source: 'dxf_browser_hybrid',
    };
  }

  // ── BBox ───────────────────────────────────────────────────────────────────

  _computeBbox(paths) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 100000 100000');
    svg.style.cssText = 'position:fixed;top:-9999px;left:-9999px;width:100000px;height:100000px;visibility:hidden';
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    paths.filter(p => p?.visible && p?.d).forEach(p => {
      const el = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      el.setAttribute('d', p.d); g.appendChild(el);
    });
    svg.appendChild(g); document.body.appendChild(svg);
    try {
      const bb = g.getBBox();
      document.body.removeChild(svg);
      if (!bb || (bb.width === 0 && bb.height === 0)) return null;
      return { minX: bb.x, minY: bb.y, maxX: bb.x + bb.width, maxY: bb.y + bb.height, w: bb.width, h: bb.height };
    } catch (e) { document.body.removeChild(svg); return null; }
  }
}

// ─── Default singleton for non-module contexts ────────────────────────────────
window.DxfImportClient = DxfImportClient;
