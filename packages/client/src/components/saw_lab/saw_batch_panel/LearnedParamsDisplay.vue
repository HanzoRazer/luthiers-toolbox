<template>
  <div :class="styles.learnedParams">
    <h3 :class="styles.sectionTitle">Learned Parameters Applied</h3>
    <div :class="styles.paramGrid">
      <div :class="styles.paramItem">
        <span :class="styles.paramLabel">RPM:</span>
        <span :class="styles.paramValues">
          <span :class="styles.baseline">{{ baselineRpm }}</span>
          <span :class="styles.arrow">→</span>
          <span :class="styles.merged">{{ mergedParams.rpm?.toFixed(0) || baselineRpm }}</span>
        </span>
      </div>
      <div :class="styles.paramItem">
        <span :class="styles.paramLabel">Feed:</span>
        <span :class="styles.paramValues">
          <span :class="styles.baseline">{{ baselineFeedIpm }}</span>
          <span :class="styles.arrow">→</span>
          <span :class="styles.merged">{{ mergedParams.feed_ipm?.toFixed(1) || baselineFeedIpm }}</span>
        </span>
      </div>
      <div :class="styles.paramItem">
        <span :class="styles.paramLabel">DOC:</span>
        <span :class="styles.paramValues">
          <span :class="styles.baseline">{{ baselineDepthPerPass }}</span>
          <span :class="styles.arrow">→</span>
          <span :class="styles.merged">{{ mergedParams.doc_mm?.toFixed(1) || baselineDepthPerPass }}</span>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import styles from '../SawBatchPanel.module.css'

interface MergedParams {
  rpm?: number
  feed_ipm?: number
  doc_mm?: number
}

defineProps<{
  mergedParams: MergedParams
  baselineRpm: number
  baselineFeedIpm: number
  baselineDepthPerPass: number
}>()
</script>
