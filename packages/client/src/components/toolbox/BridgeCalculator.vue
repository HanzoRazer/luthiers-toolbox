<!--
The Production Shop - CNC Guitar Lutherie CAD/CAM
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
          <input
            v-model="isMM"
            type="checkbox"
          >
          <span>Units: {{ isMM ? 'mm' : 'in' }}</span>
        </label>
        <select v-model="presetFamily">
          <option
            v-for="p in familyPresets"
            :key="p.id"
            :value="p.id"
          >
            {{ p.label }}
          </option>
        </select>
        <select v-model="gaugePresetId">
          <option
            v-for="g in gaugePresets"
            :key="g.id"
            :value="g.id"
          >
            {{ g.label }}
          </option>
        </select>
        <select v-model="actionPresetId">
          <option
            v-for="a in actionPresets"
            :key="a.id"
            :value="a.id"
          >
            {{ a.label }}
          </option>
        </select>
        <button
          class="btn"
          @click="handleApplyPresets"
        >
          Apply Presets
        </button>
      </div>
    </header>

    <section class="grid">
      <div class="panel">
        <h3>Scale & Geometry</h3>

        <div class="field">
          <label>Scale length</label>
          <div class="ctrl">
            <input
              v-model.number="ui.scale"
              type="number"
              step="0.01"
            >
            <span class="unit">{{ unitLabel }}</span>
          </div>
        </div>

        <div class="field">
          <label>Saddle string spread (1st–6th)</label>
          <div class="ctrl">
            <input
              v-model.number="ui.spread"
              type="number"
              step="0.01"
            >
            <span class="unit">{{ unitLabel }}</span>
          </div>
        </div>

        <div class="field">
          <label>Compensation — Treble (C<sub>t</sub>)</label>
          <div class="ctrl">
            <input
              v-model.number="ui.compTreble"
              type="number"
              step="0.01"
            >
            <span class="unit">{{ unitLabel }}</span>
          </div>
        </div>

        <div class="field">
          <label>Compensation — Bass (C<sub>b</sub>)</label>
          <div class="ctrl">
            <input
              v-model.number="ui.compBass"
              type="number"
              step="0.01"
            >
            <span class="unit">{{ unitLabel }}</span>
          </div>
        </div>

        <div class="field">
          <label>Slot width</label>
          <div class="ctrl">
            <input
              v-model.number="ui.slotWidth"
              type="number"
              step="0.01"
            >
            <span class="unit">{{ unitLabel }}</span>
          </div>
        </div>

        <div class="field">
          <label>Slot length (visual)</label>
          <div class="ctrl">
            <input
              v-model.number="ui.slotLength"
              type="number"
              step="0.1"
            >
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
        <svg
          :viewBox="svgViewBox"
          preserveAspectRatio="xMidYMid meet"
          class="preview"
        >
          <!-- centerline -->
          <line
            :x1="0"
            :y1="-svgH/2"
            :x2="0"
            :y2="svgH/2"
            stroke="#d1d5db"
            stroke-width="0.2"
          />
          <!-- nut at x=0 -->
          <line
            :x1="0"
            :y1="-svgH/2"
            :x2="0"
            :y2="svgH/2"
            stroke="#94a3b8"
            stroke-dasharray="2,2"
            stroke-width="0.2"
          />
          <!-- scale tick -->
          <line
            :x1="scale"
            y1="-3"
            :x2="scale"
            y2="3"
            stroke="#94a3b8"
            stroke-width="0.3"
          />
          <text
            :x="scale + 1"
            y="-2"
            font-size="2"
            fill="#64748b"
          >SL</text>

          <!-- saddle line -->
          <line
            :x1="treble.x"
            :y1="treble.y"
            :x2="bass.x"
            :y2="bass.y"
            stroke="#0ea5e9"
            stroke-width="0.5"
          />
          <!-- slot polygon -->
          <polygon
            :points="slotPolygonPoints"
            fill="rgba(14,165,233,0.25)"
            stroke="#0284c7"
            stroke-width="0.4"
          />

          <!-- labels -->
          <circle
            :cx="treble.x"
            :cy="treble.y"
            r="0.7"
            fill="#0ea5e9"
          />
          <text
            :x="treble.x + 1"
            :y="treble.y - 1"
            font-size="2"
            fill="#0ea5e9"
          >Treble</text>
          <circle
            :cx="bass.x"
            :cy="bass.y"
            r="0.7"
            fill="#0ea5e9"
          />
          <text
            :x="bass.x + 1"
            :y="bass.y - 1"
            font-size="2"
            fill="#0ea5e9"
          >Bass</text>
        </svg>

        <div class="bc-row gap">
          <button
            class="btn"
            @click="copyJSON"
          >
            Copy JSON
          </button>
          <button
            class="btn"
            @click="downloadSVG"
          >
            Download SVG
          </button>
          <button
            class="btn btn-export"
            @click="exportDXF"
          >
            Export DXF
          </button>
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
import { onMounted } from "vue";
import {
  useBridgePresets,
  useBridgeUnits,
  useBridgeGeometry,
  useBridgeExport,
} from "./composables";

// Presets
const {
  presetFamily,
  gaugePresetId,
  actionPresetId,
  familyPresets,
  gaugePresets,
  actionPresets,
} = useBridgePresets();

// Units & UI state
const {
  isMM,
  unitLabel,
  ui,
  applyFamilyPreset,
  applyPresets,
  setupUnitWatch,
} = useBridgeUnits();

// Geometry calculations
const {
  scale,
  angleDeg,
  treble,
  bass,
  slotPoly,
  slotPolygonPoints,
  svgH,
  svgViewBox,
  fmt,
} = useBridgeGeometry(ui, isMM);

// Export functions
const { copyJSON, downloadSVG, exportDXF } = useBridgeExport(
  ui,
  isMM,
  angleDeg,
  treble,
  bass,
  slotPoly,
  svgViewBox,
  svgH,
  scale,
  slotPolygonPoints
);

// Apply default preset on mount
onMounted(() => {
  applyFamilyPreset(presetFamily.value);
  setupUnitWatch();
});

function handleApplyPresets() {
  applyPresets(presetFamily.value, gaugePresetId.value, actionPresetId.value);
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
