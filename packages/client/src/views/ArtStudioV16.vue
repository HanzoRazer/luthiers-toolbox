<script setup lang="ts">
import { ref } from 'vue'
import SvgCanvas from '@/components/SvgCanvas.vue'
import ReliefGrid from '@/components/ReliefGrid.vue'
import { svgNormalize, svgOutline, svgSave, reliefPreview } from '@/api/v16'

const svgText = ref('<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"120\" height=\"60\"><rect x=\"4\" y=\"4\" width=\"112\" height=\"52\" fill=\"none\" stroke=\"black\"/></svg>')
const outlineJson = ref('')
const strokeWidth = ref(0.4)
const svgName = ref('demo_v16')

const gray = ref<number[][]>([ [0.0,0.5,1.0], [0.2,0.4,0.8], [0.0,0.3,0.6] ])
const verts = ref<number[][][]>([])
const zmin = ref(0.0)
const zmax = ref(1.2)
const scaleXY = ref(1.0)

async function doSvgNormalize(){
  const res = await svgNormalize(svgText.value)
  svgText.value = res.svg_text
}
async function doSvgOutline(){
  const res = await svgOutline(svgText.value, strokeWidth.value)
  outlineJson.value = JSON.stringify(res, null, 2)
}
async function doSvgSave(){
  const res = await svgSave(svgText.value, svgName.value)
  alert('Saved (stub): ' + svgName.value + ' — bytes_b64 length: ' + res.bytes_b64.length)
}
async function doReliefPreview(){
  const res = await reliefPreview(gray.value, zmin.value, zmax.value, scaleXY.value)
  verts.value = res.verts
}
</script>

<template>
  <div class="p-6 space-y-6">
    <h1 class="text-xl font-bold">
      Art Studio — Phase 16.0 (SVG Editor + Relief Mapper)
    </h1>

    <section class="border rounded p-4 space-y-3 bg-white">
      <h2 class="font-semibold">
        SVG Editor (stub)
      </h2>
      <textarea
        v-model="svgText"
        class="w-full h-28 border rounded p-2 font-mono text-xs"
      />
      <div class="flex gap-3">
        <button
          class="border rounded px-3 py-1"
          @click="doSvgNormalize"
        >
          Normalize
        </button>
        <label class="text-sm">Stroke→Outline width (mm)</label>
        <input
          v-model.number="strokeWidth"
          type="number"
          step="0.1"
          class="border rounded px-2 py-1 w-24"
        >
        <button
          class="border rounded px-3 py-1"
          @click="doSvgOutline"
        >
          Stroke→Outline
        </button>
        <input
          v-model="svgName"
          class="border rounded px-2 py-1"
          placeholder="name"
        >
        <button
          class="border rounded px-3 py-1"
          @click="doSvgSave"
        >
          Save
        </button>
      </div>
      <SvgCanvas :svg-text="svgText" />
      <div class="text-xs mt-2">
        <div class="font-semibold">
          Outline response (JSON)
        </div>
        <pre class="text-xs bg-gray-50 p-2 border rounded max-h-48 overflow-auto">{{ outlineJson }}</pre>
      </div>
    </section>

    <section class="border rounded p-4 space-y-3 bg-white">
      <h2 class="font-semibold">
        Relief Mapper (stub)
      </h2>
      <div class="flex flex-wrap gap-3 items-center text-sm">
        <label>Z min</label><input
          v-model.number="zmin"
          type="number"
          step="0.1"
          class="border rounded px-2 py-1 w-24"
        >
        <label>Z max</label><input
          v-model.number="zmax"
          type="number"
          step="0.1"
          class="border rounded px-2 py-1 w-24"
        >
        <label>Scale XY (mm)</label><input
          v-model.number="scaleXY"
          type="number"
          step="0.1"
          class="border rounded px-2 py-1 w-24"
        >
        <button
          class="border rounded px-3 py-1"
          @click="doReliefPreview"
        >
          Preview Heightmap
        </button>
      </div>
      <div class="text-xs">
        Grayscale array (0..1):
      </div>
      <textarea
        v-model="(gray as any)"
        class="w-full h-24 border rounded p-2 font-mono text-xs"
      />
      <ReliefGrid :verts="verts" />
    </section>
  </div>
</template>
