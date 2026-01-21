<script setup lang="ts">
/**
 * ManufacturingCandidatesPanel.vue
 *
 * Simplified wrapper that mounts the canonical ManufacturingCandidateList.vue.
 */
import ManufacturingCandidateList from "@/components/rmos/ManufacturingCandidateList.vue";

const props = defineProps<{
  runId: string;
}>();
</script>

<template>
  <ManufacturingCandidateList :run-id="props.runId" />
</template>
