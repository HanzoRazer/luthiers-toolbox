<template>
  <div :class="styles.learnedParams">
    <h3>Learned Parameters Applied</h3>
    <div :class="styles.paramComparison">
      <div :class="styles.paramRow">
        <span :class="styles.label">RPM:</span>
        <span :class="styles.baseline">{{ baselineRpm }}</span>
        <span :class="styles.arrow">→</span>
        <span :class="styles.merged">{{ mergedRpm?.toFixed(0) || baselineRpm }}</span>
      </div>
      <div :class="styles.paramRow">
        <span :class="styles.label">Feed:</span>
        <span :class="styles.baseline">{{ baselineFeedIpm }}</span>
        <span :class="styles.arrow">→</span>
        <span :class="styles.merged">{{ mergedFeedIpm?.toFixed(1) || baselineFeedIpm }}</span>
      </div>
      <div :class="styles.paramRow">
        <span :class="styles.label">DOC:</span>
        <span :class="styles.baseline">{{ baselineDepthPerPass }}</span>
        <span :class="styles.arrow">→</span>
        <span :class="styles.merged">{{ mergedDocMm?.toFixed(1) || baselineDepthPerPass }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import styles from './SawContourPanel.module.css'

defineProps<{
  baselineRpm: number
  baselineFeedIpm: number
  baselineDepthPerPass: number
  mergedRpm?: number
  mergedFeedIpm?: number
  mergedDocMm?: number
}>()
</script>
