<script setup lang="ts">
/**
 * RingNudgePanel - Ring width adjustment controls
 * Extracted from RosetteEditorView.vue (Bundle 32.4.0)
 */
import { useRosetteStore } from '@/stores/rosetteStore'

defineProps<{
  styles: Record<string, string>
}>()

const store = useRosetteStore()
</script>

<template>
  <div
    v-if="store.currentParams?.ring_params?.length"
    :class="styles.ringNudgeSection"
  >
    <div :class="styles.nudgeTitle">
      Ring Widths
    </div>
    <div
      v-for="(ring, idx) in store.currentParams.ring_params"
      :key="idx"
      :class="[styles.ringRow, { [styles.ringRowFocused]: store.focusedRingIndex === idx }]"
      :data-ring-index="idx"
    >
      <span :class="styles.ringLabel">Ring {{ idx + 1 }}</span>
      <span :class="styles.ringWidth">{{ Number(ring.width_mm || 0).toFixed(2) }} mm</span>
      <div :class="styles.ringActions">
        <button
          :class="styles.mini"
          type="button"
          title="Shrink width by 0.10 mm"
          :disabled="store.isRedBlocked"
          @click="store.nudgeRingWidth(idx, -0.1)"
        >
          −0.10
        </button>
        <button
          :class="styles.mini"
          type="button"
          title="Grow width by 0.10 mm"
          :disabled="store.isRedBlocked"
          @click="store.nudgeRingWidth(idx, 0.1)"
        >
          +0.10
        </button>
        <button
          :class="[styles.mini, styles.miniDist]"
          type="button"
          title="Shrink width, distribute to neighbors"
          :disabled="store.isRedBlocked"
          @click="store.nudgeRingWidthDistribute(idx, -0.1)"
        >
          −0.10↔
        </button>
        <button
          :class="[styles.mini, styles.miniDist]"
          type="button"
          title="Grow width, distribute to neighbors"
          :disabled="store.isRedBlocked"
          @click="store.nudgeRingWidthDistribute(idx, 0.1)"
        >
          +0.10↔
        </button>
      </div>
    </div>
  </div>
</template>
