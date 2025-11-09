<script setup lang="ts">
import { ref, watch } from 'vue'
import Toast from '@/components/Toast.vue'
import { previewInfill } from '@/api/infill'
import { sendToProject } from '@/api/vcarve'

const toastRef = ref<InstanceType<typeof Toast> | null>(null)
const projectId = ref('demo-project')
const projectTarget = ref<'Body'|'Headstock'|'Rosette'>('Rosette')

const settings = ref<any>({ feed_rate_mm_min: 800, rpm: 12000, safe_z_mm: 5.0, v_bit_angle_deg: 60, depth_mm: 2.0 })
const flatClear = ref(true)
const flatMode = ref<'raster'|'contour'>('raster')
const rasterAngle = ref(45)
const stepOver = ref(1.2)
const approxStrokeWidth = ref(1.2)
const centerlinesSvg = ref<string>('')
const fillPolygons = ref<number[][][] | null>(null)

const previewSvg = ref<string>('')
const previewStats = ref<any>(null)
const isPreviewing = ref(false)

async function refreshPreview(){
  try{
    isPreviewing.value = true
    const body:any = {
      mode: flatMode.value,
      flat_stepover_mm: stepOver.value,
      raster_angle_deg: flatMode.value === 'raster' ? rasterAngle.value : 0,
      approx_stroke_width_mm: approxStrokeWidth.value
    }
    if (fillPolygons.value && fillPolygons.value.length){
      body.polygons = fillPolygons.value
    } else if (centerlinesSvg.value){
      body.centerlines_svg = centerlinesSvg.value
    }
    const res = await previewInfill(body)
    previewSvg.value = res.svg || ''
    previewStats.value = res.stats || null
  } catch(e:any){
    toastRef.value?.show('Preview failed: ' + (e?.message || 'error'))
  } finally {
    isPreviewing.value = false
  }
}
watch([flatMode, rasterAngle, stepOver, approxStrokeWidth], ()=>{ if (flatClear.value) refreshPreview() })

async function doSend(){
  try{
    const payload:any = {
      projectId: projectId.value,
      target: projectTarget.value,
      svg: null, gcode: null, dxf: null,
      settings: {
        ...settings.value,
        flat_clear: flatClear.value,
        flat_clear_mode: flatMode.value,
        raster_angle_deg: rasterAngle.value,
        flat_stepover_mm: stepOver.value,
        approx_stroke_width_mm: approxStrokeWidth.value
      },
      run_opt: true,
      run_metrics: false
    }
    const res = await sendToProject(payload)
    const parts:string[] = []
    for (const item of (res?.notify_results||[])){
      const [k, v] = Object.entries(item)[0] as any
      const r = v?.result
      if (r?.url) parts.push(`${k}:${r.status_code}`)
    }
    toastRef.value?.show('CAM → ' + (parts.join(' | ')||'sent'))
  }catch(e:any){
    toastRef.value?.show('Send failed: ' + (e?.message||'error'))
  }
}
</script>

<template>
  <div class="p-6 space-y-4">
    <h1 class="text-xl font-bold">Art Studio — Preview Infill</h1>

    <div class="flex flex-wrap gap-3 text-sm items-center">
      <label>Project:</label>
      <input v-model="projectId" class="border rounded px-2 py-1"/>
      <label>Target:</label>
      <select v-model="projectTarget" class="border rounded px-2 py-1">
        <option>Body</option><option>Headstock</option><option>Rosette</option>
      </select>
      <button class="ml-4 rounded-lg px-3 py-1 border hover:shadow" @click="doSend">Send to Project</button>
    </div>

    <div class="border rounded p-3 space-y-2">
      <div class="font-semibold text-sm">Flat‑clear options</div>
      <label><input type="checkbox" v-model="flatClear" @change="flatClear && refreshPreview()"> Enable</label>
      <div class="flex flex-wrap gap-4 items-center text-sm">
        <label>Mode:</label>
        <select v-model="flatMode" class="border rounded px-2 py-1">
          <option value="raster">Raster</option>
          <option value="contour">Contour</option>
        </select>
        <template v-if="flatMode==='raster'">
          <label>Angle (deg):</label>
          <input v-model.number="rasterAngle" type="number" class="border rounded px-2 py-1 w-20"/>
        </template>
        <label>Step‑over (mm):</label>
        <input v-model.number="stepOver" type="number" class="border rounded px-2 py-1 w-24"/>
        <label>Approx stroke width (mm):</label>
        <input v-model.number="approxStrokeWidth" type="number" class="border rounded px-2 py-1 w-24"/>
        <button class="rounded-lg px-3 py-1 border hover:shadow" @click="refreshPreview" :disabled="!flatClear || isPreviewing">
          {{ isPreviewing ? 'Previewing…' : 'Preview infill' }}
        </button>
      </div>
      <p class="text-xs opacity-60">Tip: provide explicit regions if you have them; else we infer from centerlines + approx stroke width.</p>
    </div>

    <div v-if="previewSvg" class="border rounded p-3 bg-white">
      <div class="text-sm font-semibold mb-2">Preview</div>
      <div v-html="previewSvg" class="max-h-[520px] overflow-auto border rounded"></div>
      <div v-if="previewStats" class="mt-2 text-xs opacity-70">
        <span>Total spans: {{ previewStats.total_spans || 0 }}</span> ·
        <span>Total length (est.): {{ (previewStats.total_len || 0).toFixed(1) }} mm</span>
      </div>
    </div>

    <Toast ref="toastRef" />
  </div>
</template>
