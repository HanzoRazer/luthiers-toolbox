<script setup lang="ts">
import { ref } from 'vue'
import { helicalEntry, type HelicalReq } from '@/api/v161'

const form = ref<HelicalReq>({
  cx: 0, cy: 0, radius_mm: 6.0, direction: 'CCW',
  plane_z_mm: 5.0, start_z_mm: 0.0, z_target_mm: -3.0,
  pitch_mm_per_rev: 1.5, feed_xy_mm_min: 600, feed_z_mm_min: null,
  ij_mode: true, absolute: true, units_mm: true, safe_rapid: true,
  dwell_ms: 0, max_arc_degrees: 180,
  post_preset: 'GRBL'
})

const gcode = ref('')
const stats = ref<any>(null)
const busy = ref(false)
async function runHelix(){
  busy.value = true
  try{
    const res = await helicalEntry(form.value)
    gcode.value = res.gcode
    stats.value = res.stats
  }catch(e:any){
    alert(e?.message || String(e))
  }finally{
    busy.value = false
  }
}
</script>

<template>
  <div class="p-6 space-y-6">
    <h1 class="text-xl font-bold">Phase 16.1 — Helical Z‑Ramping</h1>
    <section class="border rounded p-4 bg-white space-y-3">
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
      <button class="border rounded px-3 py-1" :disabled="busy" @click="runHelix">Generate</button>
      <div v-if="stats" class="text-xs text-gray-600">Segments: {{ stats.segments }}, Revs: {{ stats.full_revs }} + {{ stats.rem_frac.toFixed(3) }}</div>
      <pre class="text-xs bg-gray-50 p-2 border rounded max-h-80 overflow-auto">{{ gcode }}</pre>
    </section>
  </div>
</template>
