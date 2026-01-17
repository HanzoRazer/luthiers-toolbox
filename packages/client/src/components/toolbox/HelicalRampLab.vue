<!--
Luthier's Tool Box - CNC Guitar Lutherie CAD/CAM Toolbox
Helical Ramp Lab - Interactive helical Z-ramping tool

Part of Art Studio v16.1: Helical Z-Ramping
Repository: HanzoRazer/luthiers-toolbox
Created: January 2025

Features:
- Interactive helical plunge entry generator
- CW/CCW direction selection
- Post-processor preset support (GRBL, Mach3, Haas, Marlin)
- IJ mode vs R word mode toggle
- Configurable pitch, feed rates, arc segmentation
- Real-time G-code generation
- Arc statistics display (revolutions, segments)
-->

<script setup lang="ts">
import { ref } from 'vue'
import { helicalEntry, type HelicalReq } from '@/api/v161'

// Extended form type with safety validation parameters  
type HelicalFormData = HelicalReq & {
  tool_diameter_mm: number;
  material: string;
  spindle_rpm: number;
};

const form = ref<HelicalFormData>({
  cx: 0, cy: 0, radius_mm: 6.0, direction: 'CCW',
  plane_z_mm: 5.0, start_z_mm: 0.0, z_target_mm: -3.0,
  pitch_mm_per_rev: 1.5, feed_xy_mm_min: 600, feed_z_mm_min: null,
  ij_mode: true, absolute: true, units_mm: true, safe_rapid: true,
  dwell_ms: 0, max_arc_degrees: 180,
  post_preset: 'GRBL',
  // Safety validation parameters
  tool_diameter_mm: 6.0,
  material: 'hardwood',
  spindle_rpm: 18000
})

const gcode = ref('')
const stats = ref<any>(null)
const warnings = ref<string[]>([])
const busy = ref(false)

async function runHelix(){
  busy.value = true
  warnings.value = []
  try{
    const res = await helicalEntry(form.value)
    gcode.value = res.gcode
    stats.value = res.stats
    warnings.value = res.warnings || []
  }catch(e:any){
    alert(e?.message || String(e))
  }finally{
    busy.value = false
  }
}

function downloadGcode() {
  const blob = new Blob([gcode.value], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `helical_${form.value.radius_mm}mm_${form.value.pitch_mm_per_rev}pitch.nc`
  a.click()
  URL.revokeObjectURL(url)
}

function copyGcode() {
  if (gcode.value) {
    navigator.clipboard.writeText(gcode.value).then(() => {
      alert('G-code copied to clipboard!')
    }).catch(err => {
      console.error('Failed to copy:', err)
    })
  }
}
</script>

<template>
  <div class="p-6 space-y-6">
    <h1 class="text-xl font-bold">Phase 16.1 — Helical Z‑Ramping <span class="text-sm font-normal text-gray-600">(Production Safety Enabled)</span></h1>
    
    <!-- Safety Validation Parameters -->
    <section class="border rounded p-4 bg-blue-50 space-y-3">
      <h2 class="text-sm font-bold text-blue-900">Safety Validation Parameters</h2>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
        <label class="flex items-center gap-2">Tool Ø (mm)
          <input v-model.number="form.tool_diameter_mm" type="number" step="0.1" class="border rounded px-2 py-1 w-24"/>
        </label>
        <label class="flex items-center gap-2">Material
          <select v-model="form.material" class="border rounded px-2 py-1">
            <option value="hardwood">Hardwood</option>
            <option value="softwood">Softwood</option>
            <option value="plywood">Plywood</option>
            <option value="mdf">MDF</option>
            <option value="acrylic">Acrylic</option>
            <option value="aluminum">Aluminum</option>
          </select>
        </label>
        <label class="flex items-center gap-2">RPM
          <input v-model.number="form.spindle_rpm" type="number" step="1000" class="border rounded px-2 py-1 w-24"/>
        </label>
      </div>
      <p class="text-xs text-blue-800">
        💡 These parameters enable automatic safety checks for chipload, thin-wall risk, and feed rate validation.
      </p>
    </section>

    <!-- Helical Parameters -->
    <section class="border rounded p-4 bg-white space-y-3">
      <h2 class="text-sm font-bold">Helical Parameters</h2>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
        <label class="flex items-center gap-2">Preset
          <select v-model="form.post_preset" class="border rounded px-2 py-1">
            <option value="GRBL">GRBL</option>
            <option value="Mach3">Mach3</option>
            <option value="Haas">Haas (R-mode, G4 S)</option>
            <option value="Marlin">Marlin</option>
          </select>
        </label>
        <label class="flex items-center gap-2">CX <input v-model.number="form.cx" type="number" step="0.1" class="border rounded px-2 py-1 w-28"/></label>
        <label class="flex items-center gap-2">CY <input v-model.number="form.cy" type="number" step="0.1" class="border rounded px-2 py-1 w-28"/></label>
        <label class="flex items-center gap-2">Radius <input v-model.number="form.radius_mm" type="number" step="0.1" class="border rounded px-2 py-1 w-28"/></label>
        <label class="flex items-center gap-2">Dir
          <select v-model="form.direction" class="border rounded px-2 py-1">
            <option value="CCW">CCW (G3)</option>
            <option value="CW">CW (G2)</option>
          </select>
        </label>
        <label class="flex items-center gap-2">Plane Z <input v-model.number="form.plane_z_mm" type="number" step="0.1" class="border rounded px-2 py-1 w-28"/></label>
        <label class="flex items-center gap-2">Start Z <input v-model.number="form.start_z_mm" type="number" step="0.1" class="border rounded px-2 py-1 w-28"/></label>
        <label class="flex items-center gap-2">Target Z <input v-model.number="form.z_target_mm" type="number" step="0.1" class="border rounded px-2 py-1 w-28"/></label>
        <label class="flex items-center gap-2">Pitch/rev <input v-model.number="form.pitch_mm_per_rev" type="number" step="0.1" class="border rounded px-2 py-1 w-28"/></label>
        <label class="flex items-center gap-2">Feed XY <input v-model.number="form.feed_xy_mm_min" type="number" step="1" class="border rounded px-2 py-1 w-28"/></label>
        <label class="flex items-center gap-2">Max arc ° <input v-model.number="form.max_arc_degrees" type="number" step="1" class="border rounded px-2 py-1 w-28"/></label>
        <label class="flex items-center gap-2"><input type="checkbox" v-model="form.ij_mode"/> IJ mode</label>
        <label class="flex items-center gap-2"><input type="checkbox" v-model="form.safe_rapid"/> Safe rapid</label>
      </div>
      <p class="text-xs text-gray-600">
        Preset notes: <b>Haas</b> uses <code>R</code>-mode arcs and <code>G4 S</code> (seconds).
        Others default to <code>I,J</code> and <code>G4 P</code> (milliseconds).
      </p>
      <button class="border rounded px-4 py-2 bg-blue-600 text-white font-bold hover:bg-blue-700 disabled:opacity-50" :disabled="busy" @click="runHelix">
        {{ busy ? 'Generating...' : 'Generate Helical Toolpath' }}
      </button>
    </section>

    <!-- Safety Warnings (if any) -->
    <section v-if="warnings.length > 0" class="border-2 border-yellow-500 rounded p-4 bg-yellow-50 space-y-2">
      <h2 class="text-sm font-bold text-yellow-900 flex items-center gap-2">
        <span class="text-2xl">⚠️</span>
        Safety Warnings ({{ warnings.length }})
      </h2>
      <ul class="list-disc list-inside space-y-1 text-sm text-yellow-900">
        <li v-for="(warning, idx) in warnings" :key="idx" class="leading-relaxed">{{ warning }}</li>
      </ul>
      <p class="text-xs text-yellow-800 mt-3 pt-3 border-t border-yellow-300">
        <b>⚡ Action Required:</b> Review warnings above before running G-code on your machine. 
        Adjust parameters (radius, pitch, feed, RPM) to resolve critical issues.
      </p>
    </section>

    <!-- Statistics -->
    <section v-if="stats" class="border rounded p-4 bg-green-50 space-y-2">
      <h2 class="text-sm font-bold text-green-900">Toolpath Statistics</h2>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm text-green-900">
        <div><b>Revolutions:</b> {{ stats.revolutions }}</div>
        <div><b>Segments:</b> {{ stats.segments }}</div>
        <div><b>Length:</b> {{ stats.length_mm }} mm</div>
        <div><b>Time:</b> {{ stats.time_s }} s ({{ (stats.time_s / 60).toFixed(1) }} min)</div>
        <div v-if="stats.chipload_mm"><b>Chipload:</b> {{ stats.chipload_mm }} mm/tooth</div>
        <div><b>Engagement:</b> {{ stats.engagement_angle_avg }}°</div>
        <div><b>Arc Mode:</b> {{ stats.arc_mode }}</div>
        <div><b>Post:</b> {{ stats.post_preset }}</div>
      </div>
      <div v-if="stats.warning_count > 0" class="text-xs text-yellow-700 pt-2 border-t border-green-200">
        ⚠️ {{ stats.warning_count }} warning(s) detected - see above for details
      </div>
    </section>

    <!-- G-code Output -->
    <section v-if="gcode" class="border rounded p-4 bg-gray-50 space-y-2">
      <h2 class="text-sm font-bold">G-code Output</h2>
      <pre class="text-xs bg-white p-3 border rounded max-h-96 overflow-auto font-mono">{{ gcode }}</pre>
      <div class="flex gap-2">
        <button @click="copyGcode" class="border rounded px-3 py-1 text-xs bg-white hover:bg-gray-100">
          📋 Copy to Clipboard
        </button>
        <button @click="downloadGcode" class="border rounded px-3 py-1 text-xs bg-white hover:bg-gray-100">
          💾 Download .nc File
        </button>
      </div>
    </section>
  </div>
</template>
