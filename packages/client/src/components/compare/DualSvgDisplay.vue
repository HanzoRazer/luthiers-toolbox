<!--
  B22.8: DualSvgDisplay.vue — Compare Mode SVG Dual Display
  
  State Management Pattern:
  - All state flows from useCompareState composable via props
  - isComputingDiff controls skeleton/loading display
  - overlayDisabled controls mode toggle availability
  - diffDisabledReason displays warning banner
  
  DO NOT mutate isComputingDiff or overlayDisabled locally.
  Emit mode change requests to parent instead.
-->
<template>
  <div class="dual-svg-display">
    <!-- B22.8: Disabled reason banner -->
    <div
      v-if="diffDisabledReason"
      class="diff-disabled-banner"
    >
      <span class="warning-icon">⚠</span>
      <span>Diff disabled: {{ diffDisabledReason }}</span>
    </div>

    <!-- B22.8: Loading skeleton -->
    <DiffSkeletonLoader v-if="isComputingDiff" />

    <!-- Normal display when not computing -->
    <div
      v-else
      class="svg-panes-container"
    >
      <div class="svg-pane left">
        <h4>Baseline</h4>
        <PanZoomSvg
          v-if="isValidMoves(baseline?.moves)"
          :moves="baseline?.moves"
          :color="'blue'"
          :opacity="opacityA"
          :sync-state="syncViewports ? sharedViewport : null"
          @update-viewport="(v: any) => updateViewport('left', v)"
          @render-error="$emit('render-error', $event)"
        />
        <div
          v-else
          class="placeholder"
        >
          No valid baseline data
        </div>
      </div>
      <div class="svg-pane right">
        <h4>Candidate</h4>
        <PanZoomSvg
          v-if="isValidMoves(candidate?.moves)"
          :moves="candidate?.moves"
          :color="'green'"
          :opacity="opacityB"
          :sync-state="syncViewports ? sharedViewport : null"
          @update-viewport="(v: any) => updateViewport('right', v)"
          @render-error="$emit('render-error', $event)"
        />
        <div
          v-else
          class="placeholder"
        >
          No valid candidate data
        </div>
      </div>
    </div>
    
    <div
      v-if="diffMode !== 'none' && diff && !isComputingDiff"
      class="overlay-pane"
    >
      <div class="diff-toolbar">
        <!-- B22.8: Disable mode toggles when overlay disabled -->
        <label :title="overlayDisabled ? `Diff disabled: ${diffDisabledReason || ''}` : ''">
          <input 
            v-model="localDiffMode" 
            type="radio" 
            value="overlay"
            :disabled="overlayDisabled"
          > Overlay
        </label>
        <label :title="overlayDisabled ? `Diff disabled: ${diffDisabledReason || ''}` : ''">
          <input 
            v-model="localDiffMode" 
            type="radio" 
            value="delta"
            :disabled="overlayDisabled"
          > Delta Only
        </label>
        <span class="legend">
          <span class="legend-item"><span class="legend-color add" /> Additions</span>
          <span class="legend-item"><span class="legend-color remove" /> Removals</span>
        </span>
      </div>
      <h4>Diff Overlay</h4>
      <svg
        :width="width"
        :height="height"
      >
        <g
          v-if="localDiffMode === 'overlay' && diff.overlay_svg"
          v-html="diff.overlay_svg"
        />
        <g v-else-if="localDiffMode === 'delta'">
          <polyline
            v-if="diff.additions && diff.additions.length > 1"
            :points="toPoints(diff.additions)"
            stroke="#2ecc40"
            stroke-width="2.5"
            fill="none"
            stroke-opacity="0.95"
          />
          <polyline
            v-if="diff.removals && diff.removals.length > 1"
            :points="toPoints(diff.removals)"
            stroke="#ff4136"
            stroke-width="2.5"
            fill="none"
            stroke-opacity="0.95"
          />
        </g>
      </svg>
    </div>
    
    <!-- B22.8 skeleton: Layer controls panel -->
    <LayersPanel
      v-if="layers && layers.length > 0 && !isComputingDiff"
      :layers="layers"
      @toggle-layer="(id, enabled) => emit('toggle-layer', id, enabled)"
    />
  </div>
</template>
<script setup lang="ts">
import { ref, defineProps, defineEmits, watch } from 'vue'
import { DiffSkeletonLoader, LayersPanel } from './dual-svg'
function isValidMoves(moves: any) {
  if (!Array.isArray(moves)) return false;
  if (moves.length < 2) return false;
  for (let i = 0; i < moves.length; ++i) {
    const m = moves[i];
    if (!m || typeof m.x !== 'number' || typeof m.y !== 'number') return false;
  }
  return true;
}
const props = defineProps<{
  baseline: any,
  candidate: any,
  diff: any,
  opacityA: number,
  opacityB: number,
  diffMode: string,
  syncViewports: boolean,
  // B22.8: State machine props
  isComputingDiff?: boolean,
  overlayDisabled?: boolean,
  diffDisabledReason?: string | null,
  // B22.8 skeleton: Layer system props
  layers?: Array<{ id: string; inLeft: boolean; inRight: boolean; hasDiff?: boolean; enabled: boolean }>
}>()
const emit = defineEmits(['render-error', 'toggle-layer', 'update:mode'])
const width = 500
const height = 400
const sharedViewport = ref({ scale: 1, tx: 0, ty: 0 })
const localDiffMode = ref(props.diffMode || 'overlay')
watch(() => props.diffMode, v => { if (v) localDiffMode.value = v })
function updateViewport(_which: 'left' | 'right', v: { scale: number, tx: number, ty: number }) {
  if (props.syncViewports) sharedViewport.value = v
}
function toPoints(moves: any[]) {
  if (!moves) return ''
  return moves
    .filter(m => m.x !== undefined && m.y !== undefined)
    .map(m => `${m.x * sharedViewport.value.scale + sharedViewport.value.tx},${height - (m.y * sharedViewport.value.scale + sharedViewport.value.ty)}`)
    .join(' ')
}

</script>
<style scoped>
.dual-svg-display {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* B22.8: Disabled reason banner */
.diff-disabled-banner {
  background: #fef3c7;
  border: 1px solid #f59e0b;
  color: #92400e;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.warning-icon {
  font-size: 1.2rem;
}

.svg-panes-container {
  display: flex;
  gap: 2rem;
}

.svg-pane {
  flex: 1;
  background: #fafbfc;
  border: 1px solid #ddd;
  padding: 1rem;
}
</style>
.overlay-pane {
  flex: 1 1 100%;
  margin-top: 2rem;
  background: #f0f0f0;
  border: 1px dashed #bbb;
  padding: 1rem;
}
.diff-toolbar {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 0.5rem;
}
.diff-toolbar label {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

/* B22.8: Disabled state styling */
.diff-toolbar label input:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.diff-toolbar label:has(input:disabled) {
  cursor: not-allowed;
  opacity: 0.6;
}

.legend {
  margin-left: 2rem;
  display: flex;
  gap: 1rem;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 0.3rem;
}
.legend-color {
  display: inline-block;
  width: 18px;
  height: 10px;
  border-radius: 2px;
  margin-right: 0.3em;
}
.legend-color.add {
  background: #2ecc40;
  border: 1px solid #1eae32;
}
.legend-color.remove {
  background: #ff4136;
  border: 1px solid #c22b1a;
}

svg { width: 100%; height: 100%; }
</style>
