<template>
  <div :class="styles.pathStats">
    <h3>Path Statistics</h3>
    <div :class="styles.statsGrid">
      <div :class="styles.statItem">
        <span :class="styles.statLabel">Path Length:</span>
        <span :class="styles.statValue">{{ pathLengthMm.toFixed(1) }} mm</span>
      </div>
      <div :class="styles.statItem">
        <span :class="styles.statLabel">Depth Passes:</span>
        <span :class="styles.statValue">{{ depthPasses }}</span>
      </div>
      <div :class="styles.statItem">
        <span :class="styles.statLabel">Total Length:</span>
        <span :class="styles.statValue">{{ totalLengthMm.toFixed(1) }} mm</span>
      </div>
      <div :class="styles.statItem">
        <span :class="styles.statLabel">Est. Time:</span>
        <span :class="styles.statValue">{{ estimatedTimeSec.toFixed(0) }}s</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import styles from './SawContourPanel.module.css'

defineProps<{
  pathLengthMm: number
  depthPasses: number
  totalLengthMm: number
  estimatedTimeSec: number
}>()
</script>
