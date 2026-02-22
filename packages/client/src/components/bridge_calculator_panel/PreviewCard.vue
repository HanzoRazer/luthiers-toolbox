<template>
  <section class="calc-card preview-card">
    <h4>Preview (not to scale)</h4>
    <svg
      :viewBox="svgViewBox"
      preserveAspectRatio="xMidYMid meet"
      class="preview"
    >
      <line
        :x1="0"
        :y1="-svgH/2"
        :x2="0"
        :y2="svgH/2"
        stroke="#cbd5f5"
        stroke-dasharray="2,2"
        stroke-width="0.3"
      />
      <line
        :x1="scale"
        y1="-3"
        :x2="scale"
        y2="3"
        stroke="#94a3b8"
        stroke-width="0.4"
      />
      <line
        :x1="treble.x"
        :y1="treble.y"
        :x2="bass.x"
        :y2="bass.y"
        stroke="#0ea5e9"
        stroke-width="0.7"
      />
      <polygon
        :points="slotPolygonPoints"
        fill="rgba(14,165,233,0.2)"
        stroke="#0284c7"
        stroke-width="0.5"
      />
      <circle
        :cx="treble.x"
        :cy="treble.y"
        r="0.8"
        fill="#0ea5e9"
      />
      <circle
        :cx="bass.x"
        :cy="bass.y"
        r="0.8"
        fill="#0ea5e9"
      />
    </svg>

    <div class="action-row">
      <button
        class="btn"
        @click="$emit('copyJSON')"
      >
        Copy JSON
      </button>
      <button
        class="btn"
        @click="$emit('downloadSVG')"
      >
        Download SVG
      </button>
      <button
        class="btn btn-export"
        :disabled="exporting"
        @click="$emit('exportDXF')"
      >
        {{ exporting ? 'Exporting…' : 'Export DXF' }}
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
interface Point {
  x: number
  y: number
}

defineProps<{
  svgViewBox: string
  svgH: number
  scale: number
  treble: Point
  bass: Point
  slotPolygonPoints: string
  exporting: boolean
}>()

defineEmits<{
  copyJSON: []
  downloadSVG: []
  exportDXF: []
}>()
</script>

<style scoped>
.calc-card {
  background: #f9fafb;
  border-radius: 0.75rem;
  padding: 1.25rem;
  border: 1px solid #e5e7eb;
}

.calc-card h4 {
  margin: 0 0 1rem 0;
  font-size: 1.125rem;
}

.preview-card {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.preview {
  width: 100%;
  height: 320px;
  background: #fff;
  border: 1px dashed #e2e8f0;
  border-radius: 0.5rem;
}

.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.375rem;
  background: #3b82f6;
  color: white;
  font-weight: 500;
  cursor: pointer;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-export {
  background: #10b981;
}
</style>
