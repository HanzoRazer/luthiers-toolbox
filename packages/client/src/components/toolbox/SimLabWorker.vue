<template>
  <div class="p-3 space-y-3">
    <h3 class="text-lg font-bold">
      SimLab - Worker Renderer (Patch I1.3)
    </h3>
    <div class="flex gap-3">
      <button
        class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        @click="runSim"
      >
        Run Simulation
      </button>
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
        @input="postFrame"
      >
      <span class="text-xs">{{ tCursor.toFixed(2) }}s / {{ timelineMax.toFixed(2) }}s</span>
    </div>
    
    <canvas 
      ref="cv" 
      style="width:100%; height:360px; border:1px solid #e5e7eb; border-radius:8px; background:#fff"
    />
    
    <div class="text-xs text-gray-500 mt-2">
      Using OffscreenCanvas in Web Worker for non-blocking rendering. 
      Ideal for large G-code files (10K+ moves).
    </div>
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { ref, onMounted, computed } from 'vue'

/**
 * SimLabWorker Component - Patch I1.3
 * 
 * Web Worker-based renderer for large G-code files
 * 
 * Features:
 * - OffscreenCanvas rendering in separate thread
 * - Non-blocking UI during heavy rendering
 * - Same arc math as I1.2 (G2/G3 support)
 * - Time-based scrubbing
 * - Ideal for files with 10,000+ moves
 * 
 * Architecture:
 * - Main thread: Vue component, state management, API calls
 * - Worker thread: Canvas rendering, arc interpolation
 * - Communication via postMessage (transferable OffscreenCanvas)
 */

type Move = { code:string, x?:number, y?:number, z?:number, i?:number, j?:number, t:number }

const cv = ref<HTMLCanvasElement|null>(null)
let worker: Worker | null = null

const moves = ref<Move[]>([])
const summary = ref<any>(null)
const playing = ref(false)
const speed = ref(1.0)
const tCursor = ref(0.0)

const timelineMax = computed(()=> (summary.value?.est_seconds ?? 0))

function initWorker(){
  try {
    // Create worker from external file
    worker = new Worker(new URL('../workers/sim_worker.ts', import.meta.url), { type: 'module' })
    
    const c = cv.value!
    
    // Transfer canvas control to worker (if supported)
    const off = (c as any).transferControlToOffscreen ? (c as any).transferControlToOffscreen() : null
    
    if (off){
      worker.postMessage({ 
        type:'init', 
        canvas: off, 
        width: c.clientWidth, 
        height: c.clientHeight 
      }, [off as any])
    } else {
      console.warn('OffscreenCanvas not supported, falling back to main thread')
    }
  } catch (error) {
    console.error('Worker initialization failed:', error)
  }
}

function postFrame(){
  if (!worker) return
  
  worker.postMessage({ 
    type:'frame', 
    moves: moves.value, 
    tCursor: tCursor.value 
  })
}

function step(){
  if (!playing.value) return
  
  tCursor.value = Math.min(timelineMax.value, tCursor.value + 0.016 * speed.value)
  postFrame()
  
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
  const gcode = `G21 G90 G17 F1200
G0 Z5
G0 X0 Y0
G1 Z-1 F300
G1 X60 Y0 F1200
G2 X60 Y40 I0 J20
G2 X0 Y40 I-30 J0
G2 X0 Y0 I0 J-20
G0 Z5
`
  
  try {
    const res = await api('/api/cam/simulate_gcode', { 
      method:'POST', 
      headers:{'Content-Type':'application/json'}, 
      body: JSON.stringify({ gcode }) 
    })
    
    const txt = await res.text()
    let json:any = null
    
    try { 
      json = JSON.parse(txt) 
    } catch {}
    
    summary.value = JSON.parse(res.headers.get('X-CAM-Summary') || '{}')
    moves.value = json?.moves || []
    
    tCursor.value = 0
    playing.value=false
    postFrame()
  } catch (error) {
    console.error('Simulation failed:', error)
  }
}

onMounted(()=>{ 
  initWorker() 
})
</script>
