<template>
  <div class="p-4 space-y-4">
    <h1 class="text-xl font-semibold">
      Full Rosette Manufacturing OS — Sandbox
    </h1>

    <div class="grid grid-cols-1 lg:grid-cols-[260px,1fr,320px] gap-4">
      <!-- Left: Pattern Library + JobLog -->
      <div class="space-y-4">
        <RosettePatternLibrary @pattern-selected="onPatternSelected" />
        <JobLogMiniList />
      </div>

      <!-- Center: RMOS workspace + Op Panel -->
      <div class="space-y-4">
        <RosetteTemplateLab
          v-if="selectedPattern"
          :pattern="selectedPattern"
          @update:pattern="updatePattern"
          @update:batch-op="updateBatchOp"
        />
        <div
          v-else
          class="border rounded-lg p-3 text-sm text-gray-600"
        >
          Select or create a pattern in the library.
        </div>

        <RosetteMultiRingOpPanel
          v-if="batchOp"
          :batch-op="batchOp"
          @update:batch-op="updateBatchOp"
        />
      </div>

      <!-- Right: Manufacturing Plan / Live Monitor -->
      <div class="space-y-3">
        <div class="flex items-center gap-2">
          <button
            class="px-3 py-1 rounded border text-sm"
            :class="rightPane==='plan' ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700 border-gray-300'"
            aria-label="Show Manufacturing Plan"
            @click="rightPane='plan'"
          >
            Plan
          </button>
          <button
            class="px-3 py-1 rounded border text-sm"
            :class="rightPane==='monitor' ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700 border-gray-300'"
            aria-label="Show Live Monitor"
            @click="rightPane='monitor'"
          >
            Live Monitor
          </button>
        </div>

        <div
          v-if="rightPane==='plan'"
          class="space-y-4"
        >
          <RosetteManufacturingPlanPanel :pattern-id="selectedPattern?.id ?? null" />
        </div>
        <div
          v-else
          class="min-h-[320px]"
        >
          <LiveMonitor />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import RosettePatternLibrary from '@/components/rmos/RosettePatternLibrary.vue';
import RosetteTemplateLab from '@/components/rmos/RosetteTemplateLab.vue';
import RosetteMultiRingOpPanel from '@/components/rmos/RosetteMultiRingOpPanel.vue';
import RosetteManufacturingPlanPanel from '@/components/rmos/RosetteManufacturingPlanPanel.vue';
import JobLogMiniList from '@/components/rmos/JobLogMiniList.vue';
import LiveMonitor from '@/components/rmos/LiveMonitor.vue';

import { useRosettePatternStore } from '@/stores/useRosettePatternStore';
import type { RosettePattern, SawSliceBatchOpCircle } from '@/models/rmos';

const patternStore = useRosettePatternStore();

const selectedPattern = computed<RosettePattern | null>(() => patternStore.selectedPattern);
const batchOp = ref<SawSliceBatchOpCircle | null>(null);
const rightPane = ref<'plan' | 'monitor'>('plan');

function onPatternSelected(_pattern: RosettePattern | null) {
  // patternStore already updated by the library; TemplateLab will sync via prop
}

function updatePattern(pattern: RosettePattern) {
  if (!pattern.id) return;
  patternStore.updatePattern(pattern.id, pattern);
}

function updateBatchOp(op: SawSliceBatchOpCircle) {
  batchOp.value = op;
}
</script>
