<template>
  <SawLabShell>
    <div class="grid">
      <SawLabQueuePanel />
      <SawLabDiffPanel />
    </div>
  </SawLabShell>
</template>

<script setup lang="ts">
import SawLabShell from '@/components/saw_lab/SawLabShell.vue'
import SawLabQueuePanel from '@/components/saw_lab/SawLabQueuePanel.vue'
import SawLabDiffPanel from '@/components/saw_lab/SawLabDiffPanel.vue'
</script>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}
</style>
