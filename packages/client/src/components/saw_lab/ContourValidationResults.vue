<template>
  <div :class="styles.validationResults">
    <h3>Full Validation Results</h3>
    <div :class="[styles.validationBadge, styles[`validationBadge${overallResult.charAt(0).toUpperCase()}${overallResult.slice(1).toLowerCase()}`]]">
      {{ overallResult }}
    </div>
    <div :class="styles.validationChecks">
      <div
        v-for="(check, key) in checks"
        :key="key"
        :class="[styles.checkItem, styles[`checkItem${check.result.charAt(0).toUpperCase()}${check.result.slice(1).toLowerCase()}`]]"
      >
        <span :class="styles.checkIcon">{{ check.result === 'OK' ? '✓' : check.result === 'WARN' ? '⚠' : '✗' }}</span>
        <span :class="styles.checkName">{{ formatCheckName(String(key)) }}</span>
        <span :class="styles.checkMessage">{{ check.message }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import styles from './SawContourPanel.module.css'

interface ValidationCheck {
  result: string
  message: string
}

defineProps<{
  overallResult: string
  checks: Record<string, ValidationCheck>
}>()

function formatCheckName(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
}
</script>
