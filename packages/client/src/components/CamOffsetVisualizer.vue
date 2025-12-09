<template>
  <div class="border rounded-lg bg-white relative select-none">
    <div class="flex items-center justify-between px-3 py-2 border-b">
      <div class="text-xs text-gray-600">
        <span class="font-semibold">Offset Preview</span>
        <span v-if="meta" class="ml-2">passes: {{ meta.count }}</span>
      </div>
      <div v-if="bbox" class="text-[10px] text-gray-500">
        bbox: [{{ fmt(bbox.minx) }}, {{ fmt(bbox.miny) }}] → [{{ fmt(bbox.maxx) }}, {{ fmt(bbox.maxy) }}]
      </div>
    </div>

    <div class="p-3">
      <div
        class="w-full h-96 bg-gray-50 border rounded overflow-hidden relative"
        @wheel.prevent="onWheel"
        @pointerdown="onPointerDown"
        @pointermove="onPointerMove"
        @pointerup="onPointerUp"
        @pointerleave="onPointerUp"
      >
        <!-- tiny toolbar -->
        <div class="absolute right-2 top-2 z-10 flex gap-1">
          <button class="px-2 py-1 text-[11px] border rounded bg-white" @click="zoomBy(1.2)">+</button>
          <button class="px-2 py-1 text-[11px] border rounded bg-white" @click="zoomBy(1/1.2)">−</button>
          <button class="px-2 py-1 text-[11px] border rounded bg-white" @click="resetView">Reset</button>
          <button class="px-2 py-1 text-[11px] border rounded bg-white" @click="exportSvg()">SVG</button>
        </div>
        <svg :viewBox="viewBox" class="w-full h-full" ref="svgRef" xmlns="http://www.w3.org/2000/svg">
          <!-- faint grid -->
          <g v-if="bbox" opacity="0.25">
            <line :x1="0" :y1="vh/2" :x2="vw" :y2="vh/2" stroke="lightgray" stroke-width="0.5"/>
            <line :x1="vw/2" :y1="0" :x2="vw/2" :y2="vh" stroke="lightgray" stroke-width="0.5"/>
          </g>

          <!-- world transform -->
          <g :transform="worldTransform">
            <!-- passes -->
            <g v-for="(p, i) in normalized" :key="i"
               @pointerenter="setHover(i)"
               @pointerleave="setHover(null)"
               @click="setSelect(i)"
               style="cursor: crosshair">
              <polyline
                :points="toPolyline(p)"
                :stroke="strokeFor(i)"
                fill="none"
                :stroke-width="strokeWidthFor(i)"
              />
            </g>
          </g>
        </svg>
        <!-- tooltip -->
        <div v-if="tooltip.visible" class="pointer-events-none absolute text-[11px] bg-white/95 border rounded px-2 py-1 shadow z-20"
             :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }">
          <div v-if="hoverIdx !== null && passStats && passStats[hoverIdx]">
            <div><span class="font-semibold">Pass {{ passStats[hoverIdx].idx }}</span></div>
            <div>Pts: {{ passStats[hoverIdx].pts }}</div>
            <div>Len: {{ passStats[hoverIdx].length.toFixed(2) }} {{ units }}</div>
          </div>
          <div v-else>pass</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, defineExpose } from 'vue'

type Pt = [number, number]
type Pass = { idx: number; pts: Pt[] }
type BBox = { minx: number; miny: number; maxx: number; maxy: number }

const props = defineProps<{
  passes: Pass[] | null
  bbox: BBox | null
  padding?: number
  meta?: { count: number } | null
  passStats?: Array<{ idx: number; pts: number; length: number }> | null
  units?: 'mm' | 'inch'
}>()
const emit = defineEmits<{
  (e: 'hover', idx: number | null): void
  (e: 'select', idx: number | null): void
}>()

const pad = computed(() => props.padding ?? 20)
const vw = 1000
const vh = 800

const viewBox = computed(() => `0 0 ${vw} ${vh}`)

function fmt (n: number) {
  return n.toFixed(2)
}

// styling helpers
const palette = ['#111827', '#2563eb', '#059669', '#b45309', '#7c3aed']
function baseStroke(i: number) { return palette[i % palette.length] }
const hoverIdx = ref<number | null>(null)
const selectedIdx = ref<number | null>(null)
function strokeFor(i: number) {
  if (selectedIdx.value === i) return '#ef4444' // highlight selected (red)
  if (hoverIdx.value === i) return '#0ea5e9'    // hover (sky)
  return baseStroke(i)
}
function strokeWidthFor(i: number) {
  if (selectedIdx.value === i) return 3.0
  if (hoverIdx.value === i) return 2.2
  return 1.6
}
function setHover(i: number | null) { hoverIdx.value = i; emit('hover', i) }
function setSelect(i: number | null) { selectedIdx.value = i; emit('select', i) }

const normalized = computed(() => {
  if (!props.passes || !props.bbox) return []
  const { minx, miny, maxx, maxy } = props.bbox
  const w = Math.max(1e-6, maxx - minx)
  const h = Math.max(1e-6, maxy - miny)
  const sx = (vw - 2 * pad.value) / w
  const sy = (vh - 2 * pad.value) / h
  const s = Math.min(sx, sy) // uniform scale
  const ox = (vw - s * w) / 2 - s * minx
  const oy = (vh - s * h) / 2 - s * miny

  // flip Y for SVG so +Y is up visually (optional, feels CAD-like)
  const flipY = true

  return props.passes.map(p => {
    const pts = p.pts.map(([x, y]) => {
      const X = s * x + ox
      const Y = s * y + oy
      return [X, flipY ? (vh - Y) : Y] as Pt
    })
    return pts
  })
})

function toPolyline(pts: Pt[]) {
  return pts.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' ')
}

// ------------ Pan / Zoom --------------
const world = reactive({ k: 1, tx: 0, ty: 0 })
const worldTransform = computed(() => `translate(${world.tx},${world.ty}) scale(${world.k})`)
function resetView() { world.k = 1; world.tx = 0; world.ty = 0; }
function zoomBy(factor: number) {
  // zoom at center of viewport
  const cx = vw / 2, cy = vh / 2
  zoomAt(cx, cy, factor)
}
function zoomAt(vx: number, vy: number, factor: number) {
  const k2 = Math.min(50, Math.max(0.1, world.k * factor))
  const dx = vx - (vx - world.tx) * (k2 / world.k)
  const dy = vy - (vy - world.ty) * (k2 / world.k)
  world.k = k2
  world.tx = dx
  world.ty = dy
}

const dragging = reactive({ active: false, x: 0, y: 0, tx0: 0, ty0: 0 })
const tooltip = reactive({ visible: false, x: 0, y: 0 })
const units = computed(() => props.units ?? 'mm')

function onWheel(e: WheelEvent) {
  const factor = e.deltaY < 0 ? 1.1 : 1/1.1
  // position relative to SVG viewport
  const target = e.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  const vx = (e.clientX - rect.left) * (vw / rect.width)
  const vy = (e.clientY - rect.top)  * (vh / rect.height)
  zoomAt(vx, vy, factor)
}
function onPointerDown(e: PointerEvent) {
  (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
  dragging.active = true
  dragging.x = e.clientX
  dragging.y = e.clientY
  dragging.tx0 = world.tx
  dragging.ty0 = world.ty
}
function onPointerMove(e: PointerEvent) {
  // tooltip track
  const target = e.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  tooltip.x = e.clientX - rect.left + 8
  tooltip.y = e.clientY - rect.top + 8
  tooltip.visible = hoverIdx.value !== null
  if (!dragging.active) return
  const dx = e.clientX - dragging.x
  const dy = e.clientY - dragging.y
  world.tx = dragging.tx0 + dx
  world.ty = dragging.ty0 + dy
}
function onPointerUp(e: PointerEvent) {
  try { (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId) } catch {}
  dragging.active = false
}

// SVG export
const svgRef = ref<SVGSVGElement | null>(null)
function exportSvg(fileName = 'offset_preview.svg') {
  const svg = svgRef.value
  if (!svg) return
  // clone to ensure xmlns attributes
  const clone = svg.cloneNode(true) as SVGSVGElement
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
  clone.setAttribute('version', '1.1')
  // ensure background is preserved via rect if desired (optional)
  // serialize
  const data = new XMLSerializer().serializeToString(clone)
  const blob = new Blob([data], { type: 'image/svg+xml;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = fileName
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
defineExpose({ exportSvg })
</script>
