<template>
  <div
    ref="containerRef"
    class="artstudio-canvas"
  >
    <canvas
      ref="canvasRef"
      class="artstudio-canvas__surface"
      @wheel="onWheel"
      @mousedown="onMouseDown"
      @mousemove="onMouseMove"
      @mouseup="onMouseUp"
      @mouseleave="onMouseUp"
    />

    <!-- Overlay controls -->
    <div class="artstudio-canvas__controls">
      <button
        title="Reset View"
        @click="resetView"
      >
        ⌂
      </button>
      <button
        title="Zoom In"
        @click="zoomIn"
      >
        +
      </button>
      <button
        title="Zoom Out"
        @click="zoomOut"
      >
        −
      </button>
      <span class="zoom-level">{{ Math.round(zoom * 100) }}%</span>
    </div>

    <!-- Coordinate display -->
    <div
      v-if="mouseCoords"
      class="artstudio-canvas__coords"
    >
      X: {{ mouseCoords.x.toFixed(2) }} Y: {{ mouseCoords.y.toFixed(2) }}
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * ArtStudioCanvas - CAD-style canvas with pan/zoom for ArtStudio.
 *
 * REFACTORED: Uses composables for cleaner separation of concerns.
 */
import { onMounted, onBeforeUnmount, watch } from 'vue'
import { useArtStudioEngine } from '@/stores/useArtStudioEngine'
import {
  useCanvasState,
  useCanvasDrawing,
  useCanvasInteraction
} from './composables'

// =============================================================================
// PROPS
// =============================================================================

const props = defineProps<{
  showToolpaths?: boolean
  showFretboard?: boolean
  showFretSlots?: boolean
  gridSize?: number
}>()

// =============================================================================
// COMPOSABLES
// =============================================================================

const engine = useArtStudioEngine()

// State
const {
  containerRef,
  canvasRef,
  ctx,
  zoom,
  panX,
  panY,
  isDragging,
  lastMouse,
  mouseCoords
} = useCanvasState()

// Drawing
const { draw } = useCanvasDrawing(canvasRef, ctx, zoom, panX, panY, props)

// Interaction
const {
  onWheel,
  onMouseDown,
  onMouseMove,
  onMouseUp,
  resetView,
  zoomIn,
  zoomOut
} = useCanvasInteraction(canvasRef, zoom, panX, panY, isDragging, lastMouse, mouseCoords, draw)

// =============================================================================
// LIFECYCLE
// =============================================================================

function resize(): void {
  const canvas = canvasRef.value
  const container = containerRef.value
  if (!canvas || !container) return

  canvas.width = container.clientWidth
  canvas.height = container.clientHeight
  draw()
}

onMounted(() => {
  const canvas = canvasRef.value
  if (!canvas) return

  const context = canvas.getContext('2d')
  if (!context) return
  ctx.value = context

  window.addEventListener('resize', resize)
  resize()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
})

// Watch for data changes
watch(
  () => [
    engine.currentPaths.value,
    engine.toolpaths.value,
    engine.fretboardOutline.value,
    engine.fretSlots.value
  ],
  () => draw(),
  { deep: true }
)

// =============================================================================
// EXPOSE
// =============================================================================

defineExpose({
  resetView,
  zoomIn,
  zoomOut,
  draw
})
</script>

<style scoped>
.artstudio-canvas {
  position: relative;
  width: 100%;
  height: 100%;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  overflow: hidden;
}

.artstudio-canvas__surface {
  width: 100%;
  height: 100%;
  display: block;
  cursor: grab;
}

.artstudio-canvas__surface:active {
  cursor: grabbing;
}

.artstudio-canvas__controls {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 4px;
  align-items: center;
  background: rgba(255, 255, 255, 0.9);
  padding: 4px 8px;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.artstudio-canvas__controls button {
  width: 28px;
  height: 28px;
  border: 1px solid #dee2e6;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.artstudio-canvas__controls button:hover {
  background: #e9ecef;
}

.zoom-level {
  font-size: 12px;
  color: #6c757d;
  min-width: 40px;
  text-align: center;
}

.artstudio-canvas__coords {
  position: absolute;
  bottom: 8px;
  left: 8px;
  font-size: 11px;
  font-family: monospace;
  color: #6c757d;
  background: rgba(255, 255, 255, 0.9);
  padding: 2px 6px;
  border-radius: 2px;
}
</style>
