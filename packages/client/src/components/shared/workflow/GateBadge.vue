<script setup lang="ts">
import type { WorkflowGateLevel } from '@/types/workflow'
import styles from './workflow.module.css'

defineProps<{
  gate: WorkflowGateLevel
  label?: string
}>()
</script>

<template>
  <span :class="[styles.gateBadge, styles[gate]]">
    {{ label ?? gate }}
  </span>
</template>
