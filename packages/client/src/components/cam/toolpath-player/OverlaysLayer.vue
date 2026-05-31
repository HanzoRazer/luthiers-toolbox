<script setup lang="ts">
/**
 * OverlaysLayer — Consolidated overlay components for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Contains: LoadingOverlay, MemoryWarning, ValidationOverlay, EmptyState,
 * plus the fidelity-warnings banner + tool legend (F-Z1 / F-Z2).
 */

import { ref } from 'vue';
import { LoadingOverlay, ValidationOverlay, EmptyState } from './index';
import MemoryWarning from '../MemoryWarning.vue';
import { useToolpathPlayerStore, type MemoryInfo } from '@/stores/useToolpathPlayerStore';
import type { ValidationIssue } from '@/util/gcodeValidator';

interface ParseProgress {
  stage: 'uploading' | 'simulating' | 'idle' | 'complete';
  percent: number;
}

interface Props {
  loading: boolean;
  parseProgress: ParseProgress;
  showMemBanner: boolean;
  memoryInfo: MemoryInfo;
  hasErrors: boolean;
  validationErrors: ValidationIssue[];
  segmentCount: number;
  error: string | null;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  dismissMemory: [];
  optimizeMemory: [];
  loadAnyway: [];
}>();

// Fidelity warnings + multi-tool info come straight from the store (F-Z1/F-Z2).
const store = useToolpathPlayerStore();
const showWarnings = ref(true);
</script>

<template>
  <!-- Loading overlay with progress -->
  <LoadingOverlay
    v-if="props.loading"
    :progress="props.parseProgress"
  />

  <!-- Memory warning banner -->
  <MemoryWarning
    v-if="props.showMemBanner"
    :memory-info="props.memoryInfo"
    @close="emit('dismissMemory')"
    @optimize="emit('optimizeMemory')"
  />

  <!-- Limited-simulation banner: the backend told us it couldn't faithfully
       model part of the program. Show it instead of silently mis-rendering. (F-Z1) -->
  <div
    v-if="showWarnings && store.hasFidelityWarnings && !props.loading"
    class="tp-warning-banner"
  >
    <span class="tp-warning-icon">⚠️</span>
    <span class="tp-warning-text">
      Limited simulation —
      <template v-if="store.warnings?.unsupported_g?.length">
        unsupported G{{ store.warnings.unsupported_g.join(', G') }};
      </template>
      <template v-if="store.warnings?.unsupported_m?.length">
        unsupported M{{ store.warnings.unsupported_m.join(', M') }};
      </template>
      <template v-if="store.warnings?.approx_cycles?.length">
        approximated cycle(s) G{{ store.warnings.approx_cycles.join(', G') }};
      </template>
      <template v-if="store.warnings?.degenerate_arcs">
        {{ store.warnings.degenerate_arcs }} arc(s) drawn straight;
      </template>
      <template v-if="store.warnings?.non_xy_arcs">
        {{ store.warnings.non_xy_arcs }} non-XY arc(s);
      </template>
      <template v-if="store.warnings?.truncated">
        path truncated ({{ store.warnings.dropped_segments }} segments dropped);
      </template>
    </span>
    <button
      class="tp-warning-dismiss"
      title="Dismiss"
      @click="showWarnings = false"
    >
      ✕
    </button>
  </div>

  <!-- Tool legend for multi-tool programs (F-Z2) -->
  <div
    v-if="store.tools && store.tools.count > 1 && !props.loading"
    class="tp-tool-legend"
  >
    Tools: {{ store.tools.used.map((t) => 'T' + t).join(', ') }}
    <span class="tp-tool-changes">· {{ store.tools.changes.length }} change(s)</span>
  </div>

  <!-- Validation error overlay -->
  <ValidationOverlay
    v-if="props.hasErrors && !props.loading && props.segmentCount === 0"
    :errors="props.validationErrors"
    @load-anyway="emit('loadAnyway')"
  />

  <!-- Error / Empty state -->
  <EmptyState
    v-if="!props.loading && !props.hasErrors && props.segmentCount === 0"
    :error="props.error"
  />
</template>

<style scoped>
.tp-warning-banner {
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  max-width: 80%;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(92, 74, 26, 0.92);
  border: 1px solid #e6b800;
  border-radius: 6px;
  color: #ffe9a8;
  font-size: 11px;
  line-height: 1.4;
  z-index: 18;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.tp-warning-icon {
  flex: 0 0 auto;
}

.tp-warning-text {
  flex: 1 1 auto;
}

.tp-warning-dismiss {
  flex: 0 0 auto;
  background: transparent;
  border: none;
  color: #ffe9a8;
  cursor: pointer;
  font-size: 12px;
  padding: 0 2px;
}

.tp-warning-dismiss:hover {
  color: #fff;
}

.tp-tool-legend {
  position: absolute;
  top: 10px;
  left: 10px;
  padding: 4px 8px;
  background: rgba(30, 30, 46, 0.85);
  border: 1px solid #3a3a5c;
  border-radius: 4px;
  color: #aaa;
  font-size: 11px;
  z-index: 16;
}

.tp-tool-changes {
  color: #777;
}
</style>
