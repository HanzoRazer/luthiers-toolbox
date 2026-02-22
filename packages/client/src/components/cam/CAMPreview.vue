<template>
  <div class="p-3 space-y-2">
    <!-- H7.2: optional strict normalize toggle + visible issue count -->
    <div class="flex items-center gap-3 text-xs">
      <label class="inline-flex items-center gap-2">
        <input
          v-model="strictNormalize"
          type="checkbox"
        >
        <span>Strict CAM intent normalize</span>
      </label>
      <span
        v-if="normalizationIssues.length"
        class="text-amber-600"
      >
        Normalize issues: {{ normalizationIssues.length }}
      </span>
    </div>

    <!-- H7.2: show issues (non-breaking) -->
    <details
      v-if="normalizationIssues.length"
      class="text-xs mb-2"
    >
      <summary class="cursor-pointer text-amber-700 hover:underline">
        CAM intent normalization issues ({{ normalizationIssues.length }})
      </summary>
      <ul class="mt-2 ml-4 list-disc text-amber-700">
        <li
          v-for="(iss, idx) in normalizationIssues.slice(0, 50)"
          :key="idx"
        >
          <span
            v-if="iss.code"
            class="font-mono"
          >[{{ iss.code }}]</span>
          {{ iss.message }}
          <span
            v-if="iss.path"
            class="opacity-70"
          > ({{ iss.path }})</span>
        </li>
      </ul>
      <div
        v-if="normalizationIssues.length > 50"
        class="text-gray-500 mt-1"
      >
        Showing first 50...
      </div>
    </details>

    <div class="flex gap-3 flex-wrap items-center">
      <label>Tool ⌀ (mm) <input
        v-model.number="tool"
        type="number"
        style="width:90px"
      ></label>
      <label>Depth/Pass (mm) <input
        v-model.number="dpp"
        type="number"
        style="width:90px"
      ></label>
      <label>Stock (mm) <input
        v-model.number="stock"
        type="number"
        style="width:90px"
      ></label>
      <label>Feed XY (mm/min) <input
        v-model.number="fxy"
        type="number"
        style="width:110px"
      ></label>
      <label>Feed Z (mm/min) <input
        v-model.number="fz"
        type="number"
        style="width:110px"
      ></label>
      <label>Safe Z (mm) <input
        v-model.number="safeZ"
        type="number"
        style="width:90px"
      ></label>
      <label>Tabs <input
        v-model.number="tabs"
        type="number"
        style="width:70px"
      ></label>
      <select v-model="post">
        <option value="grbl">
          GRBL
        </option>
        <option value="mach4">
          Mach4
        </option>
        <option value="pathpilot">
          PathPilot
        </option>
        <option value="linuxcnc">
          LinuxCNC
        </option>
        <option value="masso">
          MASSO
        </option>
      </select>
      <button @click="simulate">
        Simulate & Preview
      </button>
      <button
        :disabled="!gcode"
        @click="download"
      >
        Download G-code
      </button>
    </div>
    <canvas
      ref="cv"
      style="width:100%;height:240px;border:1px solid #e5e7eb;border-radius:8px;background:#fff"
    />
    <div
      v-if="errorMessage"
      class="text-sm p-2 bg-red-50 border border-red-200 rounded text-red-800"
    >
      <b>Error:</b> {{ errorMessage }}
    </div>
    <div
      v-if="summary"
      class="text-sm grid grid-cols-2 gap-2"
    >
      <div><b>Post:</b> {{ summary.post }}</div>
      <div><b>Passes:</b> {{ summary.passes }}</div>
      <div><b>Total path (mm):</b> {{ summary.total_path_mm.toFixed(1) }}</div>
      <div><b>Estimated minutes:</b> {{ summary.est_minutes.toFixed(2) }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { normalizeCamIntent } from '@/services/rmosCamIntentApi'
import { cam } from '@/sdk/endpoints'
import { formatApiErrorForUi } from '@/sdk/core/errors'

// H7.2: normalize-first adoption controls / visibility
const strictNormalize = ref(false)
const normalizationIssues = ref<
  Array<{ code?: string; message: string; severity?: string; path?: string }>
>([])
const errorMessage = ref<string | null>(null)

function _summarizeIssues(issues: Array<{ message: string }>, max = 10): string {
  const head = issues.slice(0, max).map((i) => i.message).join("; ")
  return issues.length > max ? `${head}; ...` : head
}

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
  normalizationIssues.value = []
  errorMessage.value = null

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

  try {
    // H7.2.1: Normalize intent and call the intent-native endpoint
    const intentDraft: any = {
      operation: "roughing_gcode",
      mode: "router_3axis",
      params: payload,
    }

    const norm = await normalizeCamIntent(
      { intent: intentDraft, strict: false },
      { requestId: `CAMPreview.simulate.${Date.now()}` }
    )
    normalizationIssues.value = norm.issues ?? []

    if (strictNormalize.value && normalizationIssues.value.length > 0) {
      throw new Error(
        `CAM intent normalization failed (strict): ${_summarizeIssues(normalizationIssues.value)}`
      )
    }

    // H8.3.2: Use SDK helper with typed response and automatic header parsing
    const result = await cam.roughingGcodeIntent(norm.intent as unknown as Record<string, unknown>, strictNormalize.value)
    
    gcode.value = result.gcode
    summary.value = result.summary
  
    // Parse passes from G-code
    const passPolys: Array<Array<[number,number]>> = []
    const lines = result.gcode.split('\n')
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
  } catch (e) {
    // H8.3.2: Consistent UI error normalization with request-id visibility
    errorMessage.value = formatApiErrorForUi(e)
    gcode.value = ''
    summary.value = null
  }
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
