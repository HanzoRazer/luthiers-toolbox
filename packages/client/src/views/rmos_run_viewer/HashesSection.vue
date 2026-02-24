<template>
  <section :class="styles.infoSection">
    <h2>Hashes</h2>
    <div :class="styles.hashGrid">
      <div v-if="requestHash">
        <strong>Request:</strong>
        <code>{{ requestHash }}</code>
      </div>
      <div v-if="toolpathsHash">
        <strong>Toolpaths:</strong>
        <code>{{ toolpathsHash }}</code>
      </div>
      <div v-if="gcodeHash">
        <strong>G-code:</strong>
        <code>{{ gcodeHash }}</code>
      </div>
      <div v-if="geometryHash">
        <strong>Geometry:</strong>
        <code>{{ geometryHash }}</code>
      </div>
      <div v-if="configFingerprint">
        <strong>Config:</strong>
        <code>{{ configFingerprint }}</code>
      </div>
      <div
        v-if="!requestHash && !toolpathsHash && !gcodeHash && !geometryHash && !configFingerprint"
        :class="styles.emptyState"
      >
        No hashes recorded
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import styles from '../RmosRunViewerView.module.css'

defineProps<{
  requestHash?: string | null
  toolpathsHash?: string | null
  gcodeHash?: string | null
  geometryHash?: string | null
  configFingerprint?: string | null
}>()
</script>
