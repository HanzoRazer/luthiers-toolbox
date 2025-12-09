<template>
  <div class="p-3 space-y-2">
    <div class="flex gap-3 flex-wrap items-center">
      <label>Tool ⌀ (mm) <input type="number" v-model.number="tool" style="width:90px"></label>
      <label>Depth/Pass (mm) <input type="number" v-model.number="dpp" style="width:90px"></label>
      <label>Stock (mm) <input type="number" v-model.number="stock" style="width:90px"></label>
      <label>Feed XY (mm/min) <input type="number" v-model.number="fxy" style="width:110px"></label>
      <label>Feed Z (mm/min) <input type="number" v-model.number="fz" style="width:110px"></label>
      <label>Safe Z (mm) <input type="number" v-model.number="safeZ" style="width:90px"></label>
      <label>Tabs <input type="number" v-model.number="tabs" style="width:70px"></label>
      <select v-model="post">
        <option value="grbl">GRBL</option>
        <option value="mach4">Mach4</option>
        <option value="pathpilot">PathPilot</option>
        <option value="linuxcnc">LinuxCNC</option>
        <option value="masso">MASSO</option>
      </select>
      <button @click="simulate">Simulate & Preview</button>
      <button :disabled="!gcode" @click="download">Download G-code</button>
    </div>
    <canvas ref="cv" style="width:100%;height:240px;border:1px solid #e5e7eb;border-radius:8px;background:#fff"></canvas>
    <div v-if="summary" class="text-sm grid grid-cols-2 gap-2">
      <div><b>Post:</b> {{ summary.post }}</div>
      <div><b>Passes:</b> {{ summary.passes }}</div>
      <div><b>Total path (mm):</b> {{ summary.total_path_mm.toFixed(1) }}</div>
      <div><b>Estimated minutes:</b> {{ summary.est_minutes.toFixed(2) }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const cv = ref<HTMLCanvasElement|null>(null)
let ctx:CanvasRenderingContext2D, W=0, H=0, dpr=1

const tool = ref(3.175), dpp = ref(1.5), stock = ref(6.0)
const fxy = ref(1200.0), fz = ref(300.0), safeZ = ref(5.0), tabs = ref(0)
const post = ref<'grbl'|'mach4'|'pathpilot'|'linuxcnc'|'masso'>('grbl')
const gcode = ref<string>('')
const summary = ref<any>(null)

const sampleEntities = ref<any[]>([
  { type: 'line', A:[40,40], B:[260,40] },
  { type: 'arc', center:[260,60], radius:20, start_angle:270, end_angle:0 },
  { type: 'line', A:[280,60], B:[280,200] },
  { type: 'arc', center:[260,200], radius:20, start_angle:0, end_angle:90 },
  { type: 'line', A:[260,220], B:[40,220] },
  { type: 'arc', center:[40,200], radius:20, start_angle:90, end_angle:180 },
  { type: 'line', A:[20,200], B:[20,60] },
  { type: 'arc', center:[40,60], radius:20, start_angle:180, end_angle:270 },
  { type: 'line', A:[40,40], B:[260,40] }
])

function setup(){
  const c=cv.value!
  dpr=window.devicePixelRatio||1
  c.width=c.clientWidth*dpr
  c.height=c.clientHeight*dpr
  ctx=c.getContext('2d')!
  ctx.setTransform(dpr,0,0,dpr,0,0)
  W=c.clientWidth
  H=c.clientHeight
  draw([])
}

function draw(passes: Array<Array<[number,number]>>){
  ctx.clearRect(0,0,W,H)
  
  // Grid
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
  
  // Passes
  const colors = ['#0ea5e9','#22c55e','#f97316','#a855f7','#ef4444']
  passes.forEach((poly, pi)=>{
    ctx.strokeStyle = colors[pi % colors.length]
    ctx.lineWidth = 2
    ctx.beginPath()
    poly.forEach((p,i)=>{
      if(i===0) ctx.moveTo(p[0],p[1])
      else ctx.lineTo(p[0],p[1])
    })
    ctx.stroke()
  })
}

async function simulate(){
  const payload = {
    entities: sampleEntities.value,
    tool_diameter: tool.value,
    depth_per_pass: dpp.value,
    stock_thickness: stock.value,
    feed_xy: fxy.value,
    feed_z: fz.value,
    safe_z: safeZ.value,
    tabs_count: tabs.value,
    tab_width: 10,
    tab_height: 1.5,
    post: post.value
  }
  
  const res = await fetch('/cam/roughing_gcode', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify(payload)
  })
  
  gcode.value = await res.text()
  
  try {
    summary.value = JSON.parse(res.headers.get('X-CAM-Summary') || '{}')
  } catch {
    summary.value = null
  }
  
  // Parse passes from G-code
  const passPolys: Array<Array<[number,number]>> = []
  const lines = gcode.value.split('\n')
  let current: Array<[number,number]> = []
  
  for (const ln of lines){
    if (ln.includes('(Pass ')){
      if (current.length) passPolys.push(current)
      current = []
    }
    if (ln.startsWith('G1 X')){
      const m = ln.match(/X([\d\.-]+) Y([\d\.-]+)/)
      if (m){
        current.push([parseFloat(m[1]), parseFloat(m[2])])
      }
    }
  }
  
  if (current.length) passPolys.push(current)
  draw(passPolys)
}

function download(){
  const blob=new Blob([gcode.value],{type:'text/x-gcode'})
  const url=URL.createObjectURL(blob)
  const a=document.createElement('a')
  a.href=url
  a.download='roughing.nc'
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(setup)
</script>
