<template>
  <button class="compare-mode-btn" @click="goToCompareLab">
    <slot>Compare in Lab</slot>
  </button>
</template>
<script setup lang="ts">
import { useRouter } from 'vue-router'
import { defineProps } from 'vue'
const props = defineProps<{ baselineId: string, candidateId: string }>()
const router = useRouter()
function goToCompareLab() {
  router.push({
    path: '/lab/compare',
    query: { baseline_id: props.baselineId, candidate_id: props.candidateId }
  })
}
</script>
<style scoped>
.compare-mode-btn {
  background: #2b6cb0;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 0.5rem 1.2rem;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}
.compare-mode-btn:hover {
  background: #22577a;
}
</style>
