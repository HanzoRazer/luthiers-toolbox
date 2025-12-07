<template>
  <div class="p-4 space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-sm font-semibold">Offset Lab</h2>
        <p class="text-[11px] text-gray-500">Preview pyclipper inward offsets → SVG</p>
      </div>
      <span class="text-[10px] text-gray-400">/lab/offset</span>
    </div>

    <div class="grid md:grid-cols-[1.2fr,1.3fr] gap-4">
      <!-- Left: controls -->
      <div class="space-y-3">
        <div class="border rounded-lg p-3 bg-white space-y-2">
          <div class="flex items-center justify-between">
            <h3 class="text-xs font-semibold text-gray-700">Input Polygon</h3>
            <button class="px-2 py-1 rounded border text-[11px]" @click="loadRect(40,30)">Load 40×30 rectangle</button>
          </div>
          <textarea v-model="polyJson" class="w-full h-40 border rounded px-2 py-1 text-[11px] font-mono" spellcheck="false"/>
          <p class="text-[10px] text-gray-500">Format: [[x,y], [x,y], ...] (closed optional)</p>
        </div>

        <div class="border rounded-lg p-3 bg-white space-y-2">
          <div class="grid grid-cols-2 gap-2 text-[11px]">
            <label class="flex flex-col gap-1">
              <span>Units</span>
              <select v-model="units" class="border rounded px-2 py-1">
                <option value="mm">mm</option>
                <option value="inch">inch</option>
              </select>
            </label>
            <label class="flex flex-col gap-1">
              <span>Tool ⌀</span>
              <input type="number" v-model.number="toolDia" step="0.1" min="0.1" class="border rounded px-2 py-1"/>
            </label>
            <label class="flex flex-col gap-1">
              <span>Stepover (0–1)</span>
              <input type="number" v-model.number="stepover" step="0.05" min="0.05" max="0.95" class="border rounded px-2 py-1"/>
            </label>
            <label class="flex flex-col gap-1">
              <span>Link mode</span>
              <select v-model="linkMode" class="border rounded px-2 py-1">
                <option value="arc">Arc</option>
                <option value="linear">Linear</option>
              </select>
            </label>
          </div>

          <div class="grid grid-cols-3 gap-2 text-[11px] mt-2">
            <label class="flex flex-col gap-1">
              <span>Preset name</span>
              <input
                v-model="presetName"
                placeholder="e.g. OM_Hog_Offset"
                class="border rounded px-2 py-1"
              />
            </label>
            <label class="flex flex-col gap-1">
              <span>Machine ID</span>
              <input
                v-model="machineId"
                placeholder="e.g. haas_vf2"
                class="border rounded px-2 py-1"
              />
            </label>
            <label class="flex flex-col gap-1">
              <span>Post ID</span>
              <input
                v-model="postId"
                placeholder="e.g. haas_ngc"
                class="border rounded px-2 py-1"
              />
            </label>
          </div>

          <div class="flex gap-2">
            <button class="px-3 py-1.5 rounded bg-gray-900 text-white text-[11px]" @click="preview">Preview offsets</button>
            <button class="px-3 py-1.5 rounded border text-[11px]" @click="getGcode">Get G-code</button>
            <button class="px-3 py-1.5 rounded border text-[11px]" :disabled="!passes?.length" @click="exportSvg">Export SVG</button>
            <button class="px-3 py-1.5 rounded border text-[11px]" :disabled="!gcode" @click="downloadGcode">Download G-code</button>
          </div>

          <p v-if="err" class="text-[11px] text-red-600">{{ err }}</p>
        </div>

        <!-- Pass list -->
        <div v-if="passStats?.length" class="border rounded-lg p-3 bg-white space-y-2">
          <div class="flex items-center justify-between">
            <h3 class="text-xs font-semibold text-gray-700">Passes</h3>
            <span class="text-[10px] text-gray-500">{{ passStats.length }} total</span>
          </div>
          <div class="max-h-40 overflow-auto text-[11px]">
            <table class="w-full">
              <thead>
                <tr class="text-left text-gray-500">
                  <th class="px-1 py-1">#</th>
                  <th class="px-1 py-1">Pts</th>
                  <th class="px-1 py-1">Len ({{ units }})</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(p,i) in passStats" :key="i"
                    class="hover:bg-gray-50 cursor-pointer"
                    @mouseenter="hoverIdx = i"
                    @mouseleave="hoverIdx = null"
                    @click="selectedIdx = i">
                  <td class="px-1 py-1">{{ p.idx }}</td>
                  <td class="px-1 py-1">{{ p.pts }}</td>
                  <td class="px-1 py-1">{{ p.length.toFixed(2) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-if="gcode" class="border rounded-lg p-3 bg-white space-y-2">
          <div class="flex items-center justify-between">
            <h3 class="text-xs font-semibold text-gray-700">G-code</h3>
            <button class="px-2 py-1 rounded border text-[11px]" @click="gcode=''">Clear</button>
          </div>
          <textarea readonly :value="gcode" class="w-full h-48 border rounded px-2 py-1 text-[11px] font-mono"></textarea>
        </div>
      </div>

      <!-- Right: SVG -->
      <CamOffsetVisualizer
        ref="vizRef"
        :passes="passes"
        :bbox="bbox"
        :meta="meta"
        :pass-stats="passStats"
        :units="units"
        @hover="i => hoverIdx = i"
        @select="i => selectedIdx = i"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import CamOffsetVisualizer from '@/components/CamOffsetVisualizer.vue'

type Pt = [number, number]
type Pass = { idx: number; pts: Pt[] }
type BBox = { minx: number; miny: number; maxx: number; maxy: number }

const units = ref<'mm'|'inch'>('mm')
const toolDia = ref(6.0)
const stepover = ref(0.4)
const linkMode = ref<'arc'|'linear'>('arc')

const presetName = ref<string>('')
const machineId = ref<string>('')
const postId = ref<string>('')

const route = useRoute()

const polyJson = ref<string>('')
const passes = ref<Pass[] | null>(null)
const bbox = ref<BBox | null>(null)
const meta = ref<any | null>(null)
const err = ref<string | null>(null)
const gcode = ref<string>('')
const passStats = ref<Array<{ idx:number; pts:number; length:number }>>([])
const hoverIdx = ref<number|null>(null)
const selectedIdx = ref<number|null>(null)
const vizRef = ref<any>(null)

function loadRect(w: number, h: number) {
  const pts: Pt[] = [[0,0],[w,0],[w,h],[0,h],[0,0]]
  polyJson.value = JSON.stringify(pts, null, 2)
}

function polylineLength(pts: Pt[]): number {
  if (!pts || pts.length < 2) return 0
  let sum = 0
  for (let i=1; i<pts.length; i++) {
    const [x0,y0] = pts[i-1]; const [x1,y1] = pts[i]
    const dx = x1 - x0, dy = y1 - y0
    sum += Math.hypot(dx, dy)
  }
  // close if not closed
  const [xa,ya] = pts[0]; const [xb,yb] = pts[pts.length-1]
  if (xa !== xb || ya !== yb) sum += Math.hypot(xa - xb, ya - yb)
  return sum
}

async function preview() {
  err.value = null
  passes.value = null
  bbox.value = null
  meta.value = null
  passStats.value = []
  try {
    const pts = JSON.parse(polyJson.value || '[]') as Pt[]
    const body = { polygon: pts, tool_dia: toolDia.value, stepover: stepover.value, link_mode: linkMode.value, units: units.value }
    const resp = await fetch('/cam/polygon_offset.preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    if (!resp.ok) throw new Error(await resp.text())
    const data = await resp.json()
    passes.value = data.passes
    bbox.value = data.bbox
    meta.value = data.meta
    // compute per-pass lengths in current units
    passStats.value = (passes.value ?? []).map(p => ({
      idx: p.idx,
      pts: p.pts.length,
      length: polylineLength(p.pts)
    }))
  } catch (e: any) {
    err.value = e?.message || String(e)
  }
}

async function getGcode() {
  err.value = null
  gcode.value = ''
  try {
    const pts = JSON.parse(polyJson.value || '[]') as Pt[]
    const body = { polygon: pts, tool_dia: toolDia.value, stepover: stepover.value, link_mode: linkMode.value, units: units.value }
    const resp = await fetch('/cam/polygon_offset.nc', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    if (!resp.ok) throw new Error(await resp.text())
    gcode.value = await resp.text()
  } catch (e: any) {
    err.value = e?.message || String(e)
  }
}

function safeSlug(src: string, fallback: string): string {
  const val = (src || fallback).trim()
  if (!val) return fallback
  // replace spaces with _, strip nasty chars
  return val
    .replace(/\s+/g, '_')
    .replace(/[^a-zA-Z0-9_\-]+/g, '')
    .toLowerCase()
}

function exportSvg() {
  const preset = safeSlug(presetName.value, 'preset')
  const mach = safeSlug(machineId.value, 'machine')
  const post = safeSlug(postId.value, 'post')
  const fname = `offset_preview_${preset}_${mach}_${post}_${Date.now()}.svg`
  vizRef.value?.exportSvg?.(fname)
}

function downloadGcode() {
  if (!gcode.value) return
  const preset = safeSlug(presetName.value, 'preset')
  const mach = safeSlug(machineId.value, 'machine')
  const post = safeSlug(postId.value, 'post')
  const fname = `offset_${preset}_${mach}_${post}_${units.value}_${toolDia.value}dia_${Date.now()}.nc`
  const blob = new Blob([gcode.value], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = fname
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

// --- Preset Bridge (querystring + localStorage) ---
function loadBridgeContext() {
  // 1) Query params take priority
  const q = route.query
  const qPreset = typeof q.preset === 'string' ? q.preset : null
  const qMachine = typeof q.machine_id === 'string' ? q.machine_id : null
  const qPost = typeof q.post_id === 'string' ? q.post_id : null

  if (qPreset) presetName.value = qPreset
  if (qMachine) machineId.value = qMachine
  if (qPost) postId.value = qPost

  // 2) Fill missing values from localStorage
  if (!presetName.value) {
    const v = localStorage.getItem('offsetLab.presetName')
    if (v) presetName.value = v
  }
  if (!machineId.value) {
    const v = localStorage.getItem('offsetLab.machineId')
    if (v) machineId.value = v
  }
  if (!postId.value) {
    const v = localStorage.getItem('offsetLab.postId')
    if (v) postId.value = v
  }
}

onMounted(() => {
  loadBridgeContext()
})

// Keep localStorage in sync when user edits these fields in Offset Lab
watch(presetName, v => {
  localStorage.setItem('offsetLab.presetName', v ?? '')
})
watch(machineId, v => {
  localStorage.setItem('offsetLab.machineId', v ?? '')
})
watch(postId, v => {
  localStorage.setItem('offsetLab.postId', v ?? '')
})
</script>
