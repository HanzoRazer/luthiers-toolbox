<!--
Luthier's Tool Box - CNC Guitar Lutherie CAD/CAM Toolbox
Bridge Calculator - Acoustic bridge geometry calculator

Part of Phase P2.3: Bridge Calculator Integration
Repository: HanzoRazer/luthiers-toolbox
Created: January 2025

Features:
- Saddle height calculation (action + neck angle)
- String spacing (nut to bridge)
- Compensation (intonation offsets)
- Preset support (Martin, Taylor, Gibson, Classical, 12-string)
- Interactive SVG preview with slot visualization
- MM/inch unit toggle
- String gauge presets (light, medium, heavy)
- Action presets (low, medium, high)
-->

<template>
  <div class="bridge-calculator">
    <header class="bc-row">
      <h2>🌉 Bridge Calculator</h2>
      <div class="bc-row gap">
        <label class="switch">
          <input type="checkbox" v-model="isMM" />
          <span>Units: {{ isMM ? 'mm' : 'in' }}</span>
        </label>
        <select v-model="presetFamily">
          <option v-for="p in familyPresets" :key="p.id" :value="p.id">
            {{ p.label }}
          </option>
        </select>
        <select v-model="gaugePresetId">
          <option v-for="g in gaugePresets" :key="g.id" :value="g.id">
            {{ g.label }}
          </option>
        </select>
        <select v-model="actionPresetId">
          <option v-for="a in actionPresets" :key="a.id" :value="a.id">
            {{ a.label }}
          </option>
        </select>
        <button class="btn" @click="applyPresets">Apply Presets</button>
      </div>
    </header>

    <section class="grid">
      <div class="panel">
        <h3>Scale & Geometry</h3>

        <div class="field">
          <label>Scale length</label>
          <div class="ctrl">
            <input type="number" v-model.number="ui.scale" step="0.01" />
            <span class="unit">{{ unitLabel }}</span>
          </div>
        </div>

        <div class="field">
          <label>Saddle string spread (1st–6th)</label>
          <div class="ctrl">
            <input type="number" v-model.number="ui.spread" step="0.01" />
            <span class="unit">{{ unitLabel }}</span>
          </div>
        </div>

        <div class="field">
          <label>Compensation — Treble (C<sub>t</sub>)</label>
          <div class="ctrl">
            <input type="number" v-model.number="ui.compTreble" step="0.01" />
            <span class="unit">{{ unitLabel }}</span>
          </div>
        </div>

        <div class="field">
          <label>Compensation — Bass (C<sub>b</sub>)</label>
          <div class="ctrl">
            <input type="number" v-model.number="ui.compBass" step="0.01" />
            <span class="unit">{{ unitLabel }}</span>
          </div>
        </div>

        <div class="field">
          <label>Slot width</label>
          <div class="ctrl">
            <input type="number" v-model.number="ui.slotWidth" step="0.01" />
            <span class="unit">{{ unitLabel }}</span>
          </div>
        </div>

        <div class="field">
          <label>Slot length (visual)</label>
          <div class="ctrl">
            <input type="number" v-model.number="ui.slotLength" step="0.1" />
            <span class="unit">{{ unitLabel }}</span>
          </div>
        </div>

        <div class="summary">
          <div><strong>Angle θ:</strong> {{ angleDeg.toFixed(3) }}°</div>
          <div><strong>Treble saddle X:</strong> {{ fmt(treble.x) }} {{ unitLabel }}</div>
          <div><strong>Bass saddle X:</strong> {{ fmt(bass.x) }} {{ unitLabel }}</div>
        </div>
      </div>

      <div class="panel">
        <h3>Preview (not to scale on screen)</h3>
        <svg :viewBox="svgViewBox" preserveAspectRatio="xMidYMid meet" class="preview">
          <!-- centerline -->
          <line :x1="0" :y1="-svgH/2" :x2="0" :y2="svgH/2" stroke="#d1d5db" stroke-width="0.2"/>
          <!-- nut at x=0 -->
          <line :x1="0" :y1="-svgH/2" :x2="0" :y2="svgH/2" stroke="#94a3b8" stroke-dasharray="2,2" stroke-width="0.2"/>
          <!-- scale tick -->
          <line :x1="scale" y1="-3" :x2="scale" y2="3" stroke="#94a3b8" stroke-width="0.3"/>
          <text :x="scale + 1" y="-2" font-size="2" fill="#64748b">SL</text>

          <!-- saddle line -->
          <line :x1="treble.x" :y1="treble.y" :x2="bass.x" :y2="bass.y" stroke="#0ea5e9" stroke-width="0.5"/>
          <!-- slot polygon -->
          <polygon :points="slotPolygonPoints" fill="rgba(14,165,233,0.25)" stroke="#0284c7" stroke-width="0.4"/>

          <!-- labels -->
          <circle :cx="treble.x" :cy="treble.y" r="0.7" fill="#0ea5e9"/>
          <text :x="treble.x + 1" :y="treble.y - 1" font-size="2" fill="#0ea5e9">Treble</text>
          <circle :cx="bass.x" :cy="bass.y" r="0.7" fill="#0ea5e9"/>
          <text :x="bass.x + 1" :y="bass.y - 1" font-size="2" fill="#0ea5e9">Bass</text>
        </svg>

        <div class="bc-row gap">
          <button class="btn" @click="copyJSON">Copy JSON</button>
          <button class="btn" @click="downloadSVG">Download SVG</button>
          <button class="btn btn-export" @click="exportDXF">Export DXF</button>
        </div>
      </div>
    </section>

    <details class="panel">
      <summary><strong>Math & Notes</strong></summary>
      <p>
        Saddle endpoints are computed on a centerline coordinate system with the nut at x=0.
        Treble endpoint: (x, y) = (SL + C<sub>t</sub>, -S/2). Bass endpoint: (SL + C<sub>b</sub>, +S/2).
        Angle: θ = atan((C<sub>b</sub> - C<sub>t</sub>) / S).
      </p>
      <p>
        Presets simply seed <em>spread</em>, <em>C<sub>t</sub></em>, <em>C<sub>b</sub></em>. Gauge/Action presets nudge compensation.
        Always final-intonate on the instrument.
      </p>
    </details>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue';

/** -------------------------
 *  Presets
 *  ------------------------- */
type FamilyPreset = { id: string; label: string; scale_in: number; spread_mm: number; Ct_mm: number; Cb_mm: number; slotWidth_mm: number; slotLen_mm: number };
const familyPresets: FamilyPreset[] = [
  { id:'lp',    label:'Les Paul (24.75")', scale_in:24.75, spread_mm:52.0, Ct_mm:1.5, Cb_mm:3.0, slotWidth_mm:3.0, slotLen_mm:75 },
  { id:'strat', label:'Strat/Tele (25.5")', scale_in:25.5, spread_mm:52.5, Ct_mm:2.0, Cb_mm:3.5, slotWidth_mm:3.0, slotLen_mm:75 },
  { id:'om',    label:'OM Acoustic (25.4")', scale_in:25.4, spread_mm:54.0, Ct_mm:2.0, Cb_mm:4.2, slotWidth_mm:3.2, slotLen_mm:80 },
  { id:'dread', label:'Dread (25.4")',      scale_in:25.4, spread_mm:54.0, Ct_mm:2.0, Cb_mm:4.5, slotWidth_mm:3.2, slotLen_mm:80 },
  { id:'arch',  label:'Archtop (25.0")',    scale_in:25.0, spread_mm:52.0, Ct_mm:1.8, Cb_mm:3.2, slotWidth_mm:3.0, slotLen_mm:75 },
];

type SimplePreset = { id: string; label: string; deltaTreble_mm: number; deltaBass_mm: number };
const gaugePresets: SimplePreset[] = [
  { id:'light',  label:'Light Gauge',        deltaTreble_mm:-0.3, deltaBass_mm:-0.3 },
  { id:'medium', label:'Medium Gauge',       deltaTreble_mm: 0.0, deltaBass_mm: 0.0 },
  { id:'heavy',  label:'Heavy Gauge',        deltaTreble_mm:+0.3, deltaBass_mm:+0.4 },
];
const actionPresets: SimplePreset[] = [
  { id:'low',    label:'Low Action',         deltaTreble_mm:-0.2, deltaBass_mm:-0.2 },
  { id:'standard',label:'Standard Action',   deltaTreble_mm: 0.0, deltaBass_mm: 0.0 },
  { id:'high',   label:'High Action',        deltaTreble_mm:+0.3, deltaBass_mm:+0.4 },
];

const presetFamily = ref<FamilyPreset['id']>('strat');
const gaugePresetId = ref<SimplePreset['id']>('medium');
const actionPresetId = ref<SimplePreset['id']>('standard');

/** -------------------------
 *  Units helpers
 *  ------------------------- */
const isMM = ref(true);
const unitLabel = computed(()=> isMM.value ? 'mm' : 'in');
const in2mm = (x:number)=> x*25.4;
const mm2in = (x:number)=> x/25.4;

const ui = reactive({
  // core
  scale: in2mm(25.5),      // working units (mm or in, see isMM)
  spread: 52.5,
  compTreble: 2.0,
  compBass: 3.5,
  slotWidth: 3.0,
  slotLength: 75.0,
});

// load default family (Strat)
applyFamilyPreset(presetFamily.value);

/** Load the currently selected family and convert to current units */
function applyFamilyPreset(id: string){
  const f = familyPresets.find(p=>p.id===id)!;
  // internal UI fields follow current units
  if (isMM.value){
    ui.scale      = in2mm(f.scale_in);
    ui.spread     = f.spread_mm;
    ui.compTreble = f.Ct_mm;
    ui.compBass   = f.Cb_mm;
    ui.slotWidth  = f.slotWidth_mm;
    ui.slotLength = f.slotLen_mm;
  } else {
    ui.scale      = f.scale_in;
    ui.spread     = mm2in(f.spread_mm);
    ui.compTreble = mm2in(f.Ct_mm);
    ui.compBass   = mm2in(f.Cb_mm);
    ui.slotWidth  = mm2in(f.slotWidth_mm);
    ui.slotLength = mm2in(f.slotLen_mm);
  }
}

/** Apply gauge/action nudges on top of the family preset */
function applyPresets(){
  applyFamilyPreset(presetFamily.value);
  const g = gaugePresets.find(x=>x.id===gaugePresetId.value)!;
  const a = actionPresets.find(x=>x.id===actionPresetId.value)!;

  const dT = g.deltaTreble_mm + a.deltaTreble_mm;
  const dB = g.deltaBass_mm   + a.deltaBass_mm;

  if (isMM.value){
    ui.compTreble += dT;
    ui.compBass   += dB;
  } else {
    ui.compTreble += mm2in(dT);
    ui.compBass   += mm2in(dB);
  }
}

/** Toggle units while preserving absolute values */
watchUnits();
function watchUnits(){
  // simple reactive bridge: when units flip, convert all numeric fields
  let last = isMM.value;
  setInterval(()=>{
    if (isMM.value !== last){
      if (isMM.value){
        ui.scale      = in2mm(ui.scale);
        ui.spread     = in2mm(ui.spread);
        ui.compTreble = in2mm(ui.compTreble);
        ui.compBass   = in2mm(ui.compBass);
        ui.slotWidth  = in2mm(ui.slotWidth);
        ui.slotLength = in2mm(ui.slotLength);
      } else {
        ui.scale      = mm2in(ui.scale);
        ui.spread     = mm2in(ui.spread);
        ui.compTreble = mm2in(ui.compTreble);
        ui.compBass   = mm2in(ui.compBass);
        ui.slotWidth  = mm2in(ui.slotWidth);
        ui.slotLength = mm2in(ui.slotLength);
      }
      last = isMM.value;
    }
  }, 120);
}

/** -------------------------
 *  Geometry & math
 *  ------------------------- */
const scale = computed(()=> ui.scale);
const spread = computed(()=> ui.spread);
const Ct = computed(()=> ui.compTreble);
const Cb = computed(()=> ui.compBass);

const angleRad = computed(()=> Math.atan((Cb.value - Ct.value) / Math.max(spread.value, 1e-6)));
const angleDeg = computed(()=> angleRad.value * 180/Math.PI);

// Endpoints in (x,y): nut at x=0; +x towards bridge; +y towards bass side
const treble = computed(()=> ({ x: scale.value + Ct.value, y: -spread.value/2 }));
const bass   = computed(()=> ({ x: scale.value + Cb.value, y:  spread.value/2 }));

// Slot polygon (rectangle around the line segment, width = slotWidth)
const slotPoly = computed(()=>{
  const x1 = treble.value.x, y1 = treble.value.y;
  const x2 = bass.value.x,   y2 = bass.value.y;
  const dx = x2 - x1, dy = y2 - y1;
  const L = Math.hypot(dx,dy) || 1;
  const nx = -dy / L, ny = dx / L; // unit normal
  const half = ui.slotWidth/2;

  // Extend visually to slotLength along the segment from midpoint
  const mx = (x1+x2)/2, my = (y1+y2)/2;
  const tx = dx / L, ty = dy / L;
  const halfLen = ui.slotLength/2;

  const A = { x: mx - halfLen*tx + half*nx, y: my - halfLen*ty + half*ny };
  const B = { x: mx + halfLen*tx + half*nx, y: my + halfLen*ty + half*ny };
  const C = { x: mx + halfLen*tx - half*nx, y: my + halfLen*ty - half*ny };
  const D = { x: mx - halfLen*tx - half*nx, y: my - halfLen*ty - half*ny };
  return [A,B,C,D];
});

// SVG framing (auto-fit around geometry)
const svgPadding = 10; // in current units
const svgW = computed(()=> (Math.max(treble.value.x, bass.value.x) + svgPadding) - Math.min(0, treble.value.x, bass.value.x) + svgPadding);
const svgH = computed(()=> spread.value + svgPadding*2);
const svgViewBox = computed(()=>{
  const minX = Math.min(0, treble.value.x, bass.value.x) - svgPadding;
  const minY = -spread.value/2 - svgPadding;
  return `${minX} ${minY} ${svgW.value} ${svgH.value}`;
});

// Helpers
function fmt(n:number){ return (isMM.value ? n : n).toFixed(2); } // value already in chosen units

const slotPolygonPoints = computed(()=> slotPoly.value.map(p=>`${p.x},${p.y}`).join(' '));

/** -------------------------
 *  Exporters
 *  ------------------------- */
function currentModel(){
  return {
    units: isMM.value ? 'mm' : 'in',
    scaleLength: round2(ui.scale),
    stringSpread: round2(ui.spread),
    compTreble: round2(ui.compTreble),
    compBass: round2(ui.compBass),
    slotWidth: round2(ui.slotWidth),
    slotLength: round2(ui.slotLength),
    angleDeg: round3(angleDeg.value),
    endpoints: {
      treble: { x: round3(treble.value.x), y: round3(treble.value.y) },
      bass:   { x: round3(bass.value.x),   y: round3(bass.value.y) }
    },
    slotPolygon: slotPoly.value.map(p=> ({ x: round3(p.x), y: round3(p.y) }))
  };
}
function round2(x:number){ return Math.round(x*100)/100; }
function round3(x:number){ return Math.round(x*1000)/1000; }

async function copyJSON(){
  const j = JSON.stringify(currentModel(), null, 2);
  await navigator.clipboard.writeText(j);
  alert('Model JSON copied to clipboard.');
}

function downloadSVG(){
  const vb = svgViewBox.value.split(' ');
  const [minX, minY, w, h] = vb.map(Number);
  const svg =
`<svg xmlns="http://www.w3.org/2000/svg" viewBox="${minX} ${minY} ${w} ${h}">
  <line x1="0" y1="${-svgH.value/2}" x2="0" y2="${svgH.value/2}" stroke="#d1d5db" stroke-width="0.2"/>
  <line x1="${scale.value}" y1="-3" x2="${scale.value}" y2="3" stroke="#94a3b8" stroke-width="0.3"/>
  <line x1="${treble.value.x}" y1="${treble.value.y}" x2="${bass.value.x}" y2="${bass.value.y}" stroke="#0ea5e9" stroke-width="0.5"/>
  <polygon points="${slotPolygonPoints.value}" fill="rgba(14,165,233,0.25)" stroke="#0284c7" stroke-width="0.4"/>
</svg>`;
  const blob = new Blob([svg], { type: 'image/svg+xml' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `saddle_slot_${isMM.value ? 'mm' : 'in'}.svg`;
  a.click();
  URL.revokeObjectURL(url);
}

async function exportDXF(){
  try {
    const model = currentModel();
    const payload = {
      geometry: model,
      filename: `bridge_${model.scaleLength.toFixed(1)}${model.units}_ct${model.compTreble.toFixed(1)}_cb${model.compBass.toFixed(1)}`
    };
    
    const response = await fetch('/cam/bridge/export_dxf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    if (!response.ok) {
      const error = await response.text();
      throw new Error(`DXF export failed: ${error}`);
    }
    
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${payload.filename}.dxf`;
    a.click();
    URL.revokeObjectURL(url);
    
  } catch (err: any) {
    console.error('DXF export error:', err);
    alert(`DXF export failed: ${err.message}`);
  }
}
</script>

<style scoped>
.bridge-calculator { display:flex; flex-direction:column; gap:1rem; font-family:system-ui, -apple-system, Segoe UI, Roboto, Arial; padding: 1rem; }
.bc-row { display:flex; align-items:center; justify-content:space-between; gap:0.75rem; flex-wrap:wrap; }
.bc-row.gap { gap:0.5rem; }
.grid { display:grid; grid-template-columns: 1fr 1fr; gap:1rem; }
.panel { border:1px solid #e5e7eb; border-radius:12px; padding:1rem; background:#fff; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }
.field { display:flex; align-items:center; justify-content:space-between; margin:0.4rem 0; }
.field label { color:#334155; font-weight:600; }
.ctrl { display:flex; align-items:center; gap:0.5rem; }
input[type="number"] { width:9rem; padding:0.35rem 0.5rem; border:1px solid #cbd5e1; border-radius:8px; }
select { padding:0.35rem 0.5rem; border:1px solid #cbd5e1; border-radius:8px; }
.switch { display:flex; align-items:center; gap:0.4rem; color:#334155; }
.summary { margin-top:0.75rem; display:grid; gap:0.25rem; color:#0f172a; }
.preview { width:100%; height:380px; background:#f8fafc; border:1px dashed #e2e8f0; border-radius:8px; }
.btn { background:#0ea5e9; color:#fff; border:none; border-radius:8px; padding:0.5rem 0.8rem; cursor:pointer; font-weight: 500; }
.btn:hover { background:#0284c7; }
.btn-export { background:#10b981; }
.btn-export:hover { background:#059669; }
details.panel { grid-column:1 / -1; }
details summary { cursor: pointer; padding: 0.5rem; background: #f1f5f9; border-radius: 6px; }
details summary:hover { background: #e2e8f0; }
@media (max-width: 1100px) {
  .grid { grid-template-columns: 1fr; }
}
</style>
