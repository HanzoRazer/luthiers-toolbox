<template>
  <div
    v-if="open"
    class="preview-drawer-overlay"
    @click.self="$emit('close')"
  >
    <div class="preview-drawer">
      <!-- Header -->
      <div class="drawer-header">
        <h3>NC Preview</h3>
        <button
          class="close-btn"
          aria-label="Close preview"
          @click="$emit('close')"
        >
          ✕
        </button>
      </div>

      <!-- Legend -->
      <div class="legend">
        <span class="legend-item">
          <span class="legend-box yellow" />
          FEED_HINT zones (adaptive slowdown)
        </span>
        <span class="legend-item">
          <span class="legend-box purple" />
          Trochoid arcs
        </span>
      </div>

      <!-- G-code display -->
      <div class="gcode-container">
        <pre class="gcode-lines">
          <div 
            v-for="(line, idx) in processedLines" 
            :key="idx"
            :class="getLineClass(line)"
            class="line"
          >
            <span class="line-number">{{ idx + 1 }}</span>
            <span class="line-content">{{ line.text }}</span>
          </div>
        </pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  open: boolean
  gcodeText: string
}

const props = defineProps<Props>()

defineEmits<{
  close: []
}>()

interface ProcessedLine {
  text: string
  inFeedHint: boolean
  isTrochoid: boolean
}

const processedLines = computed(() => {
  if (!props.gcodeText) return []
  
  const lines = props.gcodeText.split('\n')
  const processed: ProcessedLine[] = []
  let inFeedHint = false
  
  for (const line of lines) {
    const trimmed = line.trim()
    
    // Check for FEED_HINT START/END markers
    if (trimmed.includes('FEED_HINT START') || trimmed.includes('M52 P')) {
      inFeedHint = true
    } else if (trimmed.includes('FEED_HINT END') || trimmed.includes('M52 P100')) {
      inFeedHint = false
    }
    
    // Check for trochoid-related comments
    const isTrochoid = trimmed.includes('(TROCHOID') || 
                       trimmed.includes('trochoid') ||
                       (trimmed.startsWith('(') && trimmed.includes('arc'))
    
    processed.push({
      text: line,
      inFeedHint,
      isTrochoid
    })
  }
  
  return processed
})

function getLineClass(line: ProcessedLine): string {
  const classes: string[] = []
  
  if (line.inFeedHint) {
    classes.push('feed-hint-zone')
  }
  
  if (line.isTrochoid) {
    classes.push('trochoid-line')
  }
  
  return classes.join(' ')
}
</script>

<style scoped>
.preview-drawer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 9999;
  display: flex;
  justify-content: flex-end;
}

.preview-drawer {
  width: 42rem;
  max-width: 95vw;
  height: 100vh;
  background: white;
  box-shadow: -4px 0 16px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.drawer-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #6b7280;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  line-height: 1;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #e5e7eb;
  color: #111827;
}

.legend {
  display: flex;
  gap: 1.5rem;
  padding: 1rem 1.5rem;
  background: #f3f4f6;
  border-bottom: 1px solid #e5e7eb;
  font-size: 0.875rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #374151;
}

.legend-box {
  width: 16px;
  height: 16px;
  border-radius: 3px;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.legend-box.yellow {
  background: #fef3c7;
}

.legend-box.purple {
  background: #e9d5ff;
}

.gcode-container {
  flex: 1;
  overflow: auto;
  background: #1e1e1e;
  padding: 0;
}

.gcode-lines {
  margin: 0;
  padding: 1rem 0;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 0.875rem;
  line-height: 1.5;
  color: #d4d4d4;
}

.line {
  display: flex;
  padding: 0 1rem;
  min-height: 1.5rem;
}

.line-number {
  display: inline-block;
  width: 3rem;
  text-align: right;
  color: #858585;
  user-select: none;
  margin-right: 1rem;
  flex-shrink: 0;
}

.line-content {
  flex: 1;
  white-space: pre;
  word-break: break-all;
}

/* FEED_HINT zone highlighting */
.line.feed-hint-zone {
  background: rgba(253, 224, 71, 0.15);
}

.line.feed-hint-zone .line-content {
  color: #fde047;
  font-weight: 500;
}

/* Trochoid highlighting */
.line.trochoid-line .line-content {
  color: #c084fc;
  font-weight: 500;
}

/* Combined styles */
.line.feed-hint-zone.trochoid-line {
  background: rgba(253, 224, 71, 0.15);
}

.line.feed-hint-zone.trochoid-line .line-content {
  color: #d8b4fe;
  font-weight: 600;
}
</style>
