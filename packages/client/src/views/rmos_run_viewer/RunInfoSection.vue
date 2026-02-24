<template>
  <section :class="styles.infoSection">
    <h2>Run Info</h2>
    <div :class="styles.infoGrid">
      <div><strong>Created:</strong> {{ formatDate(createdAt) }}</div>
      <div><strong>Event Type:</strong> {{ eventType }}</div>
      <div><strong>Tool ID:</strong> {{ toolId || "---" }}</div>
      <div><strong>Material ID:</strong> {{ materialId || "---" }}</div>
      <div><strong>Machine ID:</strong> {{ machineId || "---" }}</div>
      <div><strong>Session:</strong> {{ sessionId?.slice(0, 16) || "---" }}</div>
      <div><strong>Parent Run:</strong> {{ parentRunId?.slice(0, 16) || "---" }}</div>
      <div><strong>Toolchain:</strong> {{ toolchainId || "---" }}</div>
      <div><strong>Post Processor:</strong> {{ postProcessorId || "---" }}</div>
      <div><strong>Engine Version:</strong> {{ engineVersion || "---" }}</div>
    </div>
  </section>
</template>

<script setup lang="ts">
import styles from '../RmosRunViewerView.module.css'

defineProps<{
  createdAt?: string | null
  eventType?: string | null
  toolId?: string | null
  materialId?: string | null
  machineId?: string | null
  sessionId?: string | null
  parentRunId?: string | null
  toolchainId?: string | null
  postProcessorId?: string | null
  engineVersion?: string | null
  formatDate: (date?: string | null) => string
}>()
</script>
