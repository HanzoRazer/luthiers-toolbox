<script setup lang="ts">
import styles from './workflow.module.css'

defineProps<{
  text: string
}>()
</script>

<template>
  <div :class="styles.sectionLabel">{{ text }}</div>
</template>
