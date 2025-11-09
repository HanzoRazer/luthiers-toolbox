<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Toast from '@/components/Toast.vue'
import ToolpathPreview3D from '@/components/ToolpathPreview3D.vue'
import { fetchPosts, postV155 } from '@/api/postv155'

const toastRef = ref<InstanceType<typeof Toast> | null>(null)

const presets = ref<any>({})
const presetName = ref<string>('GRBL')
const poly = ref<string>(JSON.stringify([[0,0],[20,0],[20,10],[0,10],[0,0]]))
const zCut = ref(-1.0)
const feed = ref(600)
const planeZ = ref(5.0)

const leadType = ref<'none'|'tangent'|'arc'>('tangent')
const leadLen = ref(3.0)
const leadR = ref(2.0)

const crcMode = ref<'none'|'left'|'right'>('none')
const crcDia = ref<number|undefined>(undefined)
const dNum = ref<number|undefined>(undefined)

const filletR = ref(0.4)
const filletAng = ref(20.0)

const gcode = ref<string>('')
const spans3d = ref<any[]>([])

onMounted(async () => {
  try {
    const data = await fetchPosts()
    presets.value = data.presets || {}
    if(!presets.value[presetName.value]) presetName.value = Object.keys(presets.value)[0] || 'GRBL'
  } catch(e:any){
    toastRef.value?.show('Failed to load posts: ' + (e?.message||'error'))
  }
})

async function run(){
  try{
    const body:any = {
      contour: JSON.parse(poly.value),
      z_cut_mm: zCut.value,
      feed_mm_min: feed.value,
      plane_z_mm: planeZ.value,
      preset: presetName.value,
      lead_type: leadType.value,
      lead_len_mm: leadLen.value,
      lead_arc_radius_mm: leadR.value,
      crc_mode: crcMode.value,
      crc_diameter_mm: crcDia.value ?? null,
      d_number: dNum.value ?? null,
      fillet_radius_mm: filletR.value,
      fillet_angle_min_deg: filletAng.value
    }
    const res = await postV155(body)
    gcode.value = res.gcode || ''
    spans3d.value = res.spans || []
  }catch(e:any){
    toastRef.value?.show('v15.5 failed: ' + (e?.message||'error'))
  }
}
</script>

<template>
  <div class="p-6 space-y-4">
    <h1 class="text-xl font-bold">Art Studio — Phase 15.5 (Post Presets + Lead-in/out + CRC-ready)</h1>

    <div class="border rounded p-3 space-y-2">
      <div class="text-sm font-semibold">Preset</div>
      <select v-model="presetName" class="border rounded px-2 py-1">
        <option v-for="(cfg, name) in presets" :key="name" :value="name">{{ name }}</option>
      </select>
    </div>

    <div class="border rounded p-3 space-y-2">
      <div class="text-sm font-semibold">Contour (polyline, closed)</div>
      <textarea v-model="poly" class="w-full h-28 border rounded p-2 font-mono text-xs"></textarea>
      <div class="flex flex-wrap gap-4 text-sm items-center">
        <label>Z cut</label><input v-model.number="zCut" type="number" step="0.1" class="border rounded px-2 py-1 w-24" />
        <label>Feed</label><input v-model.number="feed" type="number" step="10" class="border rounded px-2 py-1 w-24" />
        <label>Safe Z</label><input v-model.number="planeZ" type="number" step="0.5" class="border rounded px-2 py-1 w-24" />
      </div>
    </div>

    <div class="border rounded p-3 space-y-2">
      <div class="text-sm font-semibold">Lead-in/out & CRC</div>
      <div class="flex flex-wrap gap-6 text-sm items-center">
        <label class="inline-flex items-center gap-2">
          <span>Lead</span>
          <select v-model="leadType" class="border rounded px-2 py-1">
            <option value="none">None</option>
            <option value="tangent">Tangent</option>
            <option value="arc">Arc</option>
          </select>
        </label>
        <label>Lead length</label><input v-model.number="leadLen" type="number" step="0.1" class="border rounded px-2 py-1 w-24" />
        <label>Lead radius</label><input v-model.number="leadR" type="number" step="0.1" class="border rounded px-2 py-1 w-24" />
        <label class="inline-flex items-center gap-2">
          <span>CRC</span>
          <select v-model="crcMode" class="border rounded px-2 py-1">
            <option value="none">None</option>
            <option value="left">G41 (Left)</option>
            <option value="right">G42 (Right)</option>
          </select>
        </label>
        <label>D#</label><input v-model.number="dNum" type="number" step="1" class="border rounded px-2 py-1 w-20" />
        <label>CRC diameter</label><input v-model.number="crcDia" type="number" step="0.01" class="border rounded px-2 py-1 w-28" />
      </div>
    </div>

    <div class="border rounded p-3 space-y-2">
      <div class="text-sm font-semibold">Corner smoothing</div>
      <div class="flex flex-wrap gap-6 text-sm items-center">
        <label>Fillet radius</label><input v-model.number="filletR" type="number" step="0.05" class="border rounded px-2 py-1 w-28" />
        <label>Min corner angle (°)</label><input v-model.number="filletAng" type="number" step="1" class="border rounded px-2 py-1 w-28" />
        <button class="rounded px-3 py-1 border" @click="run">Generate</button>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div class="border rounded p-2 bg-white">
        <div class="text-xs font-semibold mb-1">3D Preview</div>
        <ToolpathPreview3D :spans="spans3d" :height="420" />
      </div>
      <div class="border rounded p-2 bg-white">
        <div class="text-xs font-semibold mb-1">G-code</div>
        <pre class="text-xs overflow-auto max-h-[420px] whitespace-pre-wrap">{{ gcode }}</pre>
      </div>
    </div>

    <Toast ref="toastRef" />
  </div>
</template>
