<template>
  <div class="rosette-canvas-container">
    <div class="canvas-toolbar">
      <button 
        v-for="tool in tools" 
        :key="tool.id"
        :class="{ active: activeTool === tool.id }"
        :title="tool.label"
        @click="activeTool = tool.id"
      >
        {{ tool.icon }}
      </button>
      <div class="toolbar-divider" />
      <button
        title="Clear canvas"
        @click="clearCanvas"
      >
        🗑️
      </button>
      <button
        title="Undo last"
        @click="undoLast"
      >
        ↶
      </button>
    </div>
    
    <div 
      ref="canvasContainer" 
      class="canvas-workspace"
      @mousedown="handleMouseDown"
      @mousemove="handleMouseMove"
      @mouseup="handleMouseUp"
      @mouseleave="handleMouseUp"
    >
      <!-- SVG canvas will be injected here -->
    </div>

    <div class="canvas-info">
      <span>Tool: {{ currentToolLabel }}</span>
      <span>Segments: {{ segments.length }}</span>
      <span>{{ Math.round(soundholeDiameter) }}mm soundhole</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
// TODO: Uncomment after npm install @svgdotjs/svg.js
// import { SVG, Svg } from '@svgdotjs/svg.js'

interface RosetteSegment {
  id: string
  type: 'strip' | 'circle' | 'arc'
  points: Array<{ x: number, y: number }>
  material: string
  angle?: number
}

const props = defineProps<{
  soundholeDiameter: number
  rosetteWidth: number
  symmetryCount: number
  showGrid: boolean
  initialSegments?: RosetteSegment[]
}>()

const emit = defineEmits<{
  segmentsChanged: [segments: RosetteSegment[]]
}>()

const canvasContainer = ref<HTMLDivElement | null>(null)
// let svgCanvas: Svg | null = null
const segments = ref<RosetteSegment[]>([])

const activeTool = ref<'select' | 'strip' | 'radialCopy' | 'mirror'>('select')
const isDrawing = ref(false)
const currentPoints = ref<Array<{ x: number, y: number }>>([])

const tools: Array<{ id: 'select' | 'strip' | 'radialCopy' | 'mirror', icon: string, label: string }> = [
  { id: 'select', icon: '↖️', label: 'Select' },
  { id: 'strip', icon: '📏', label: 'Draw Strip' },
  { id: 'radialCopy', icon: '🔄', label: 'Radial Copy' },
  { id: 'mirror', icon: '🪞', label: 'Mirror' }
]

const currentToolLabel = computed(() => {
  return tools.find(t => t.id === activeTool.value)?.label || 'Select'
})

// Watch for external segment updates
watch(() => props.initialSegments, (newSegments) => {
  if (newSegments) {
    segments.value = [...newSegments]
    drawSegments()
  }
}, { deep: true })

onMounted(() => {
  initCanvas()
})

watch(() => [props.soundholeDiameter, props.rosetteWidth, props.symmetryCount], () => {
  redrawCanvas()
})

function initCanvas() {
  if (!canvasContainer.value) return
  
  // TODO: Initialize SVG.js canvas after npm install
  // For now, create a basic SVG element
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
  svg.setAttribute('width', '600')
  svg.setAttribute('height', '600')
  svg.setAttribute('viewBox', '0 0 600 600')
  svg.style.background = '#fafafa'
  svg.style.border = '1px solid #ddd'
  svg.style.borderRadius = '4px'
  
  canvasContainer.value.innerHTML = ''
  canvasContainer.value.appendChild(svg)
  
  drawGuides()
}

function drawGuides() {
  const svg = canvasContainer.value?.querySelector('svg')
  if (!svg) return
  
  const centerX = 300
  const centerY = 300
  const innerRadius = (props.soundholeDiameter / 2) * 2 // Scale for visibility
  const outerRadius = innerRadius + (props.rosetteWidth * 2)
  
  // Clear existing guides
  const existingGuides = svg.querySelectorAll('.guide')
  existingGuides.forEach(g => g.remove())
  
  // Draw soundhole circle (inner)
  const innerCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle')
  innerCircle.setAttribute('cx', String(centerX))
  innerCircle.setAttribute('cy', String(centerY))
  innerCircle.setAttribute('r', String(innerRadius))
  innerCircle.setAttribute('fill', 'none')
  innerCircle.setAttribute('stroke', '#94a3b8')
  innerCircle.setAttribute('stroke-width', '2')
  innerCircle.setAttribute('stroke-dasharray', '5,5')
  innerCircle.classList.add('guide')
  svg.appendChild(innerCircle)
  
  // Draw rosette outer circle
  const outerCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle')
  outerCircle.setAttribute('cx', String(centerX))
  outerCircle.setAttribute('cy', String(centerY))
  outerCircle.setAttribute('r', String(outerRadius))
  outerCircle.setAttribute('fill', 'none')
  outerCircle.setAttribute('stroke', '#94a3b8')
  outerCircle.setAttribute('stroke-width', '2')
  outerCircle.setAttribute('stroke-dasharray', '5,5')
  outerCircle.classList.add('guide')
  svg.appendChild(outerCircle)
  
  // Draw radial symmetry lines
  if (props.showGrid && props.symmetryCount > 0) {
    const angleStep = 360 / props.symmetryCount
    for (let i = 0; i < props.symmetryCount; i++) {
      const angle = (i * angleStep) * Math.PI / 180
      const x1 = centerX
      const y1 = centerY
      const x2 = centerX + Math.cos(angle) * outerRadius * 1.2
      const y2 = centerY + Math.sin(angle) * outerRadius * 1.2
      
      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line')
      line.setAttribute('x1', String(x1))
      line.setAttribute('y1', String(y1))
      line.setAttribute('x2', String(x2))
      line.setAttribute('y2', String(y2))
      line.setAttribute('stroke', '#cbd5e1')
      line.setAttribute('stroke-width', '1')
      line.setAttribute('stroke-dasharray', '3,3')
      line.classList.add('guide')
      svg.appendChild(line)
    }
  }
  
  // Draw center crosshair
  const hLine = document.createElementNS('http://www.w3.org/2000/svg', 'line')
  hLine.setAttribute('x1', String(centerX - 10))
  hLine.setAttribute('y1', String(centerY))
  hLine.setAttribute('x2', String(centerX + 10))
  hLine.setAttribute('y2', String(centerY))
  hLine.setAttribute('stroke', '#64748b')
  hLine.setAttribute('stroke-width', '2')
  hLine.classList.add('guide')
  svg.appendChild(hLine)
  
  const vLine = document.createElementNS('http://www.w3.org/2000/svg', 'line')
  vLine.setAttribute('x1', String(centerX))
  vLine.setAttribute('y1', String(centerY - 10))
  vLine.setAttribute('x2', String(centerX))
  vLine.setAttribute('y2', String(centerY + 10))
  vLine.setAttribute('stroke', '#64748b')
  vLine.setAttribute('stroke-width', '2')
  vLine.classList.add('guide')
  svg.appendChild(vLine)
}

function redrawCanvas() {
  initCanvas()
  drawSegments()
}

function drawSegments() {
  const svg = canvasContainer.value?.querySelector('svg')
  if (!svg || segments.value.length === 0) return
  
  // Clear existing segments
  const existingSegments = svg.querySelectorAll('.segment')
  existingSegments.forEach(s => s.remove())
  
  // Material colors (matching MaterialPalette)
  const materialColors: Record<string, string> = {
    maple: '#F5E6D3',
    walnut: '#5C4033',
    ebony: '#1a1a1a',
    rosewood: '#3E2723',
    figured_maple: '#F5E6D3',
    mahogany: '#6B4423',
    cherry: '#8B4513',
    wenge: '#2B1810',
    bloodwood: '#8B0000',
    padauk: '#D2691E',
    purpleheart: '#6A0DAD',
    yellowheart: '#FFD700'
  }
  
  // Render each segment as a polygon
  segments.value.forEach(segment => {
    const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon')
    const pointsStr = segment.points.map(p => `${p.x},${p.y}`).join(' ')
    polygon.setAttribute('points', pointsStr)
    polygon.setAttribute('fill', materialColors[segment.material] || '#667eea')
    polygon.setAttribute('stroke', '#334155')
    polygon.setAttribute('stroke-width', '1')
    polygon.setAttribute('opacity', '0.8')
    polygon.classList.add('segment')
    svg.appendChild(polygon)
  })
}

function handleMouseDown(e: MouseEvent) {
  if (activeTool.value === 'strip') {
    isDrawing.value = true
    const rect = (e.target as HTMLElement).getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    currentPoints.value = [{ x, y }]
  }
}

function handleMouseMove(e: MouseEvent) {
  if (isDrawing.value && activeTool.value === 'strip') {
    const rect = (e.target as HTMLElement).getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    currentPoints.value.push({ x, y })
    // TODO: Draw preview line
  }
}

function handleMouseUp(_e: MouseEvent) {
  if (isDrawing.value && currentPoints.value.length > 1) {
    // Create segment from drawn points
    const newSegment: RosetteSegment = {
      id: `seg_${Date.now()}`,
      type: 'strip',
      points: [...currentPoints.value],
      material: 'maple'
    }
    segments.value.push(newSegment)
    emit('segmentsChanged', segments.value)
  }
  
  isDrawing.value = false
  currentPoints.value = []
}

function clearCanvas() {
  segments.value = []
  emit('segmentsChanged', segments.value)
  redrawCanvas()
}

function undoLast() {
  if (segments.value.length > 0) {
    segments.value.pop()
    emit('segmentsChanged', segments.value)
    redrawCanvas()
  }
}
</script>

<style scoped>
.rosette-canvas-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.canvas-toolbar {
  display: flex;
  gap: 0.25rem;
  padding: 0.5rem;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  align-items: center;
}

.canvas-toolbar button {
  width: 36px;
  height: 36px;
  border: 1px solid #cbd5e1;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.canvas-toolbar button:hover {
  background: #f1f5f9;
  border-color: #94a3b8;
}

.canvas-toolbar button.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
  box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
}

.toolbar-divider {
  width: 1px;
  height: 24px;
  background: #cbd5e1;
  margin: 0 0.25rem;
}

.canvas-workspace {
  flex: 1;
  position: relative;
  overflow: hidden;
  cursor: crosshair;
}

.canvas-info {
  display: flex;
  gap: 1rem;
  padding: 0.5rem;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
  font-size: 0.75rem;
  color: #64748b;
}

.canvas-info span {
  padding: 0 0.5rem;
  border-left: 1px solid #cbd5e1;
}

.canvas-info span:first-child {
  border-left: none;
}
</style>
