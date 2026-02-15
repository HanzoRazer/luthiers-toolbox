<template>
  <div class="p-3 space-y-3">
    <h3 class="text-lg font-bold">
      SimLab - Arcs + Modal HUD + Time Scrub (Patch I1.2)
    </h3>
    <div class="flex gap-3 flex-wrap items-center">
      <button
        class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        @click="runSim"
      >
        Run Simulation
      </button>
      <button
        :disabled="!moves.length"
        class="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300 disabled:opacity-50"
        @click="downloadCSV"
      >
        Export CSV
      </button>
      <div class="ml-auto text-xs bg-slate-50 border rounded px-2 py-1">
        <b>Modes:</b> {{ modalString }}
      </div>
    </div>
    
    <textarea 
      v-model="code" 
      rows="8" 
      class="w-full border rounded p-2 font-mono text-xs" 
      placeholder="Paste G-code here (supports G2/G3 arcs)..."
    />
    
    <div
      v-if="summary"
      class="text-sm grid grid-cols-3 gap-2"
    >
      <div><b>Total XY (mm):</b> {{ summary.total_xy.toFixed(2) }}</div>
      <div><b>Total Z (mm):</b> {{ summary.total_z.toFixed(2) }}</div>
      <div><b>ETA (s):</b> {{ summary.est_seconds.toFixed(2) }}</div>
    </div>
    
    <div class="flex items-center gap-3">
      <button 
        :disabled="!moves.length" 
        class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
        @click="togglePlay"
      >
        {{ playing ? 'Pause' : 'Play' }}
      </button>
      <label class="flex items-center gap-2">
        Speed × 
        <input 
          v-model.number="speed" 
          type="number" 
          min="0.1" 
          max="10" 
          step="0.1" 
          class="w-20 px-2 py-1 border rounded"
        >
      </label>
      <input 
        v-model.number="tCursor" 
        type="range" 
        min="0" 
        :max="timelineMax" 
        class="flex-1" 
        @input="drawFrame"
      >
      <span class="text-xs">{{ tCursor.toFixed(2) }}s / {{ timelineMax.toFixed(2) }}s</span>
    </div>
    
    <canvas 
      ref="cv" 
      style="width:100%; height:360px; border:1px solid #e5e7eb; border-radius:8px; background:#fff"
    />
    
    <div
      v-if="issues.length"
      class="p-2 border rounded text-sm bg-yellow-50"
    >
      <b>Issues ({{ issues.length }}):</b>
      <ul class="list-disc pl-6">
        <li
          v-for="(it,idx) in issues"
          :key="idx"
        >
          [{{ it.type }}] - {{ it.msg || 'see move' }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { ref, computed, onMounted } from 'vue'

/**
 * SimLab Component - Patch I1.2
 * 
 * Features:
 * - G2/G3 arc rendering with IJK and R-format support
 * - Time-based scrubbing (instead of frame-based)
 * - Modal state HUD display
 * - Arc interpolation with proper sweep calculation
 * - Real-time playback with variable speed
 * 
 * Arc Math:
 * - IJK format: Center = (start.x + I, start.y + J)
 * - R format: Calculates center from radius and start/end points
 * - CW/CCW: G2 = clockwise, G3 = counter-clockwise
 * - Arc length: abs(sweep_angle) * radius
 */

type Move = { code:string, x?:number, y?:number, z?:number, i?:number, j?:number, t:number }

const code = ref(`(arcs sample)
G21 G90 G17 G94 F1200
G0 Z5
G0 X0 Y0
G1 Z-1 F300
G1 X60 Y0 F1200
G2 X60 Y40 I0 J20
G2 X0 Y40 I-30 J0
G2 X0 Y0 I0 J-20
G0 Z5
`)

const summary = ref<any>(null)
const modal = ref<any>(null)
const issues = ref<any[]>([])
const moves = ref<Move[]>([])
const cv = ref<HTMLCanvasElement|null>(null)

let ctx:CanvasRenderingContext2D
let W=0, H=0, dpr=1

const playing = ref(false)
const speed = ref(1.0)
const tCursor = ref(0.0)

const timelineMax = computed(()=> (summary.value?.est_seconds ?? 0))

const modalString = computed(()=> {
  if (!modal.value) return ''
  const m = modal.value
  return `${m.units} - ${m.plane} - ${m.abs?'G90':'G91'} - ${m.feed_mode} - F${m.F}`
})

function setup(){
  const c=cv.value!
  dpr=window.devicePixelRatio||1
  c.width=c.clientWidth*dpr
  c.height=c.clientHeight*dpr
  ctx=c.getContext('2d')!
  ctx.setTransform(dpr,0,0,dpr,0,0)
  W=c.clientWidth
  H=c.clientHeight
  drawFrame()
}

function grid(){
  ctx.strokeStyle='#f1f5f9'
  for (let x=0;x<W;x+=50){ 
    ctx.beginPath()
    ctx.moveTo(x,0)
    ctx.lineTo(x,H)
    ctx.stroke() 
  }
  for (let y=0;y<H;y+=50){ 
    ctx.beginPath()
    ctx.moveTo(0,y)
    ctx.lineTo(W,y)
    ctx.stroke() 
  }
}

function lerp(a:number,b:number,t:number){ 
  return a+(b-a)*t 
}

function drawFrame(){
  if (!ctx) return
  
  ctx.clearRect(0,0,W,H)
  grid()
  
  const mm = 1 // Scale factor (could be made adjustable)
  let t = 0
  let last = {x:0,y:0,z:5,code:'G0'}
  
  for (const m of moves.value){
    if (t + m.t < tCursor.value){
      // Fully completed move
      drawMove(last, m, 1, mm)
      last = { 
        x: m.x ?? last.x, 
        y: m.y ?? last.y, 
        z: m.z ?? last.z, 
        code: m.code 
      }
      t += m.t
      continue
    } else {
      // Partially completed move (interpolate)
      const rem = Math.max(0, tCursor.value - t) / Math.max(1e-9, m.t)
      drawMove(last, m, Math.min(1, rem), mm)
      break
    }
  }
}

function drawMove(last:any, m:Move, frac:number, mm:number){
  const code = m.code || 'G1'
  ctx.lineWidth = 2
  ctx.strokeStyle = (code==='G0') ? '#ef4444' : '#0ea5e9'
  
  // Arc moves (G2/G3)
  if (('i' in m) && ('j' in m) && m.i!=null && m.j!=null && m.x!=null && m.y!=null){
    const cx = last.x + (m.i||0)
    const cy = last.y + (m.j||0)
    const sx = last.x, sy = last.y
    const ex = m.x, ey = m.y
    const r = Math.hypot(sx-cx, sy-cy)
    
    // Interpolate arc with segments
    const segs = Math.max(8, Math.floor(64*frac))
    let px = sx, py = sy
    
    for (let k=1;k<=segs;k++){
      const tt = k/segs
      const a0 = Math.atan2(sy-cy, sx-cx)
      const a1 = Math.atan2(ey-cy, ex-cx)
      let da = (a1 - a0)
      
      // Determine sweep direction
      if (code==='G2'){ // CW
        while (da>0) da-=Math.PI*2 
      } else { // G3 CCW
        while (da<0) da+=Math.PI*2 
      }
      
      const ang = a0 + da*tt*frac
      const x = cx + r*Math.cos(ang)
      const y = cy + r*Math.sin(ang)
      
      ctx.beginPath()
      ctx.moveTo(px*mm, py*mm)
      ctx.lineTo(x*mm, y*mm)
      ctx.stroke()
      
      px=x; py=y
    }
  } else {
    // Linear moves (G0/G1)
    const x1 = last.x, y1 = last.y
    const x2 = (m.x ?? x1), y2 = (m.y ?? y1)
    const x = lerp(x1, x2, frac)
    const y = lerp(y1, y2, frac)
    
    ctx.beginPath()
    ctx.moveTo(x1*mm, y1*mm)
    ctx.lineTo(x*mm, y*mm)
    ctx.stroke()
  }
}

function step(){
  if (!playing.value) return
  
  tCursor.value = Math.min(timelineMax.value, tCursor.value + 0.016 * speed.value)
  drawFrame()
  
  if (tCursor.value >= timelineMax.value){ 
    playing.value = false
    return 
  }
  
  requestAnimationFrame(step)
}

function togglePlay(){
  if (!moves.value.length) return
  
  playing.value = !playing.value
  
  if (playing.value){ 
    requestAnimationFrame(step) 
  }
}

async function runSim(){
  const res = await api('/api/cam/simulate_gcode', { 
    method:'POST', 
    headers:{'Content-Type':'application/json'}, 
    body: JSON.stringify({ gcode: code.value }) 
  })
  
  const txt = await res.text()
  let json:any = null
  
  try { 
    json = JSON.parse(txt) 
  } catch { 
    json = null 
  }
  
  // Parse headers
  try { 
    summary.value = JSON.parse(res.headers.get('X-CAM-Summary') || '{}') 
  } catch { 
    summary.value = null 
  }
  
  try { 
    modal.value = JSON.parse(res.headers.get('X-CAM-Modal') || '{}') 
  } catch { 
    modal.value = null 
  }
  
  issues.value = json?.issues || []
  moves.value = json?.moves || []
  
  tCursor.value = 0
  playing.value=false
  drawFrame()
}

async function downloadCSV(){
  const res = await api('/api/cam/simulate_gcode', { 
    method:'POST', 
    headers:{'Content-Type':'application/json'}, 
    body: JSON.stringify({ gcode: code.value, as_csv: true }) 
  })
  
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href=url
  a.download='simulation.csv'
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(setup)
</script>
