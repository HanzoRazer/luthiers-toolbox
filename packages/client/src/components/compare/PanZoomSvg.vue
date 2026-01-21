<template>
  <svg
    :width="width"
    :height="height"
    tabindex="0"
    :style="{ cursor: dragging ? 'grabbing' : 'grab', background: '#fff' }"
    @mousedown="onMouseDown"
    @wheel.prevent="onWheel"
    @keydown="onKeyDown"
  >
    <g :transform="transform">
      <polyline
        v-if="moves && moves.length > 1"
        :points="toPoints(moves)"
        :stroke="color"
        :stroke-opacity="opacity"
        fill="none"
        stroke-width="2"
      />
    </g>
  </svg>
</template>
<script setup lang="ts">
import { ref, watch, defineProps, defineEmits, computed } from 'vue'
const props = defineProps<{
  moves: any[],
  color: string,
  opacity: number,
  syncState?: { scale: number, tx: number, ty: number } | null
}>()
const emit = defineEmits(['update-viewport', 'render-error'])
const width = 500
const height = 400
const scale = ref(1)
const tx = ref(0)
const ty = ref(0)
const dragging = ref(false)
const last = ref({ x: 0, y: 0 })

watch(() => props.syncState, (v) => {
  if (v) {
    scale.value = v.scale
    tx.value = v.tx
    ty.value = v.ty
  }
})

function toPoints(moves: any[]) {
  if (!moves) return ''
  return moves
    .filter(m => m.x !== undefined && m.y !== undefined)
    .map(m => `${m.x * scale.value + tx.value},${height - (m.y * scale.value + ty.value)}`)
    .join(' ')
}

function onMouseDown(e: MouseEvent) {
  dragging.value = true
  last.value = { x: e.clientX, y: e.clientY }
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
}
function onMouseMove(e: MouseEvent) {
  if (!dragging.value) return
  tx.value += e.clientX - last.value.x
  ty.value += e.clientY - last.value.y
  last.value = { x: e.clientX, y: e.clientY }
  emit('update-viewport', { scale: scale.value, tx: tx.value, ty: ty.value })
}
function onMouseUp() {
  dragging.value = false
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', onMouseUp)
}
function onWheel(e: WheelEvent) {
  const factor = e.deltaY < 0 ? 1.1 : 0.9
  scale.value *= factor
  emit('update-viewport', { scale: scale.value, tx: tx.value, ty: ty.value })
}
function onKeyDown(e: KeyboardEvent) {
  if (e.key === '0') {
    scale.value = 1; tx.value = 0; ty.value = 0
    emit('update-viewport', { scale: scale.value, tx: tx.value, ty: ty.value })
  }
}
const transform = computed(() => `scale(${scale.value}) translate(${tx.value / scale.value},${ty.value / scale.value})`)
</script>
<style scoped>
svg { outline: none; }
</style>
