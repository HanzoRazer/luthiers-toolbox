<template>
  <div class="space-y-3">
    <!-- Post-Processor Chooser -->
    <PostChooser v-model="selectedPosts" @preview="openPreview"/>

    <!-- Geometry Overlay -->
    <div class="p-3 border rounded space-y-2">
      <h3 class="text-base font-semibold">Geometry Overlay (DXF/SVG parity)</h3>

      <div class="flex flex-wrap gap-2 items-center">
        <button class="px-3 py-1 border rounded" @click="checkParity">Check Parity</button>
        <span v-if="report"><b>RMS:</b> {{ report.rms_error_mm }} mm · <b>Max:</b> {{ report.max_error_mm }} mm · <b>Pass:</b> {{ report.pass }}</span>

        <span class="mx-2"></span>

        <!-- Units toggle -->
        <div class="ml-2">
          <span class="text-sm mr-1">Units:</span>
          <button class="px-2 py-1 border rounded" :class="units==='mm' ? 'bg-gray-100' : ''" @click="setUnits('mm')">mm (G21)</button>
          <button class="px-2 py-1 border rounded" :class="units==='inch' ? 'bg-gray-100' : ''" @click="setUnits('inch')">inch (G20)</button>
        </div>

        <span class="mx-2"></span>

        <!-- Export buttons -->
        <button class="px-3 py-1 border rounded" @click="exportDXF">Export DXF</button>
        <button class="px-3 py-1 border rounded" @click="exportSVG">Export SVG</button>
        <button class="px-3 py-1 border rounded" @click="exportGcode">Export G-code</button>
        <button class="px-3 py-1 border rounded bg-blue-50" @click="exportBundle">Export Bundle (ZIP)</button>
        <button class="px-3 py-1 border rounded bg-green-50" @click="exportMultiPostBundle">Export Multi-Post Bundle (ZIP)</button>
      </div>

      <canvas ref="cv" style="width:100%;height:360px;border:1px solid #e5e7eb;border-radius:8px;"></canvas>
    </div>

    <!-- Post Preview Drawer -->
    <PostPreviewDrawer v-model="drawerOpen" :post-id="previewPostId" :gcode="gcode" :units="units"/>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PostChooser from './PostChooser.vue'
import PostPreviewDrawer from './PostPreviewDrawer.vue'

const report = ref<any>(null)
const cv = ref<HTMLCanvasElement|null>(null)
let ctx:CanvasRenderingContext2D, W=0, H=0, dpr=1

const units = ref<'mm'|'inch'>('mm')      // 🔹 units toggle state
const postId = ref('GRBL')                 // 🔹 post-processor selector (for single exports)

// Post-processor selection & preview
const selectedPosts = ref<string[]>(JSON.parse(localStorage.getItem('toolbox.selectedPosts') || '["GRBL"]'))
const drawerOpen = ref(false)
const previewPostId = ref<string | null>(null)

function openPreview(id: string){
  previewPostId.value = id
  drawerOpen.value = true
}

// Example in-memory geometry and gcode used by parity + exports.
// If you already load geometry from /geometry/import elsewhere, replace these.
const geometry = ref({
  units: 'mm',
  paths: [
    { type:'line', x1:0, y1:0, x2:60, y2:0 },
    { type:'arc', cx:30, cy:20, r:20, start:180, end:0, cw:false }
  ]
})

const gcode = ref(`G21 G90 G17 F1200
G0 Z5
G0 X0 Y0
G1 Z-1 F300
G1 X60 Y0
G3 X60 Y40 I0 J20
G3 X0 Y40 I-30 J0
G3 X0 Y0 I0 J-20
G0 Z5
`)

function scaleGeomClient(g: any, target: 'mm' | 'inch') {
  const src = (g.units || 'mm').toLowerCase()
  const dst = (target || 'mm').toLowerCase()
  if (src === dst) return { ...g }
  const k = (src === 'mm' && dst === 'inch') ? 0.03937007874015748
    : (src === 'inch' && dst === 'mm') ? 25.4 : 1
  return {
    ...g,
    units: dst,
    paths: g.paths.map((s: any) => ({
      ...s,
      x1: typeof s.x1 === 'number' ? s.x1 * k : s.x1,
      y1: typeof s.y1 === 'number' ? s.y1 * k : s.y1,
      x2: typeof s.x2 === 'number' ? s.x2 * k : s.x2,
      y2: typeof s.y2 === 'number' ? s.y2 * k : s.y2,
      cx: typeof s.cx === 'number' ? s.cx * k : s.cx,
      cy: typeof s.cy === 'number' ? s.cy * k : s.cy,
      r: typeof s.r === 'number' ? s.r * k : s.r,
    }))
  }
}

function setUnits(u: 'mm' | 'inch') {
  // rescale geometry *values* and set units
  const scaled = scaleGeomClient(geometry.value, u)
  geometry.value = scaled
  units.value = u
}

function setup(){
  const c=cv.value!; dpr=window.devicePixelRatio||1; c.width=c.clientWidth*dpr; c.height=c.clientHeight*dpr
  ctx=c.getContext('2d')!; ctx.setTransform(dpr,0,0,dpr,0,0); W=c.clientWidth; H=c.clientHeight
  draw([],[])
}

function draw(geom: any[], path: any[]) {
  ctx.clearRect(0, 0, W, H)
  
  const line = (x1: number, y1: number, x2: number, y2: number) => {
    ctx.beginPath()
    ctx.moveTo(x1, y1)
    ctx.lineTo(x2, y2)
    ctx.stroke()
  }
  
  const arc = (cx: number, cy: number, r: number, a0: number, a1: number) => {
    const n = 64
    let px = cx + r * Math.cos(a0)
    let py = cy + r * Math.sin(a0)
    for (let k = 1; k <= n; k++) {
      const t = k / n
      const a = a0 + (a1 - a0) * t
      const x = cx + r * Math.cos(a)
      const y = cy + r * Math.sin(a)
      line(px, py, x, y)
      px = x
      py = y
    }
  }
  
  const arcseg = (cx: number, cy: number, r: number, deg0: number, deg1: number, cw: boolean) => {
    let a0 = deg0 * Math.PI / 180
    let a1 = deg1 * Math.PI / 180
    if (cw) {
      while (a1 > a0) a1 -= Math.PI * 2
    } else {
      while (a1 < a0) a1 += Math.PI * 2
    }
    arc(cx, cy, r, a0, a1)
  }

  // Draw geometry (gray)
  ctx.strokeStyle = '#cbd5e1'
  ctx.lineWidth = 1.5
  for (const s of geom) {
    if (s.type === 'line') line(s.x1, s.y1, s.x2, s.y2)
    else if (s.type === 'arc') arcseg(s.cx, s.cy, s.r, s.start, s.end, !!s.cw)
  }

  // Draw toolpath (blue)
  ctx.strokeStyle = '#0ea5e9'
  ctx.lineWidth = 2
  let last = { x: 0, y: 0 }
  for (const m of path) {
    if (m.code === 'G0' || m.code === 'G1') {
      if ('x' in m && 'y' in m) {
        line(last.x, last.y, m.x, m.y)
        last = { x: m.x, y: m.y }
      }
    } else if (m.code === 'G2' || m.code === 'G3') {
      const sx = last.x
      const sy = last.y
      const cx = sx + (m.i || 0)
      const cy = sy + (m.j || 0)
      const ex = m.x
      const ey = m.y
      const cw = (m.code === 'G2')
      const r = Math.hypot(sx - cx, sy - cy)
      let a0 = Math.atan2(sy - cy, sx - cx)
      let a1 = Math.atan2(ey - cy, ex - cx)
      if (cw) {
        while (a1 > a0) a1 -= Math.PI * 2
      } else {
        while (a1 < a0) a1 += Math.PI * 2
      }
      arc(cx, cy, r, a0, a1)
      last = { x: ex, y: ey }
    }
  }
}

async function checkParity(){
  const res = await fetch('/api/geometry/parity', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ geometry: geometry.value, gcode: gcode.value, tolerance_mm: 0.1 })
  })
  report.value = await res.json()

  const sim = await fetch('/api/cam/simulate_gcode', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ gcode: gcode.value })
  }).then(r=>r.json())
  draw(geometry.value.paths, sim.moves || [])
}

async function exportDXF(){
  const r = await fetch('/api/geometry/export?fmt=dxf', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ geometry: geometry.value, post_id: postId.value })
  })
  const blob = await r.blob()
  downloadBlob(blob, 'export.dxf')
}
async function exportSVG(){
  const r = await fetch('/api/geometry/export?fmt=svg', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ geometry: geometry.value, post_id: postId.value })
  })
  const blob = await r.blob()
  downloadBlob(blob, 'export.svg')
}
async function exportGcode(){
  const r = await fetch('/api/geometry/export_gcode', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ gcode: gcode.value, units: units.value, post_id: postId.value })
  })
  const blob = await r.blob()
  downloadBlob(blob, 'program.nc')
}
async function exportBundle(){
  const r = await fetch('/api/geometry/export_bundle', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ geometry: geometry.value, gcode: gcode.value, post_id: postId.value })
  })
  const blob = await r.blob()
  downloadBlob(blob, 'ToolBox_Export_Bundle.zip')
}

async function exportMultiPostBundle(){
  const posts = selectedPosts.value?.length ? selectedPosts.value : ['GRBL']
  const r = await fetch('/api/geometry/export_bundle_multi', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({
      geometry: geometry.value,     // server can rescale too
      gcode: gcode.value,
      post_ids: posts,
      target_units: units.value     // ensure server outputs in UI-selected units
    })
  })
  const blob = await r.blob()
  downloadBlob(blob, 'ToolBox_Export_MultiPost.zip')
}

function downloadBlob(blob: Blob, filename: string){
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename; document.body.appendChild(a)
  a.click(); a.remove(); URL.revokeObjectURL(url)
}

onMounted(setup)
</script>
