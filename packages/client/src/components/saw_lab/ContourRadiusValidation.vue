<template>
  <div :class="styles.radiusValidation">
    <h3>Radius Validation</h3>
    <div :class="[styles.validationBadge, styles[`validationBadge${status.charAt(0).toUpperCase()}${status.slice(1)}`]]">
      {{ status.toUpperCase() }}
    </div>
    <div :class="styles.validationDetails">
      <div :class="styles.detailRow">
        <span :class="styles.label">Minimum radius:</span>
        <span :class="styles.value">{{ minRadius?.toFixed(1) || 'N/A' }} mm</span>
      </div>
      <div :class="styles.detailRow">
        <span :class="styles.label">Requested radius:</span>
        <span :class="styles.value">{{ requestedRadius?.toFixed(1) || 'N/A' }} mm</span>
      </div>
      <div :class="styles.detailRow">
        <span :class="styles.label">Safety margin:</span>
        <span :class="styles.value">{{ safetyMargin?.toFixed(1) || 'N/A' }}%</span>
      </div>
    </div>
    <div :class="styles.validationMessage">
      {{ message }}
    </div>
  </div>
</template>

<script setup lang="ts">
import styles from './SawContourPanel.module.css'

defineProps<{
  status: string
  minRadius?: number
  requestedRadius?: number
  safetyMargin?: number
  message: string
}>()
</script>
