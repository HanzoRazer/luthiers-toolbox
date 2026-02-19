<template>
  <div class="wf-header">
    <div class="wf-title">Design-First Workflow</div>
    <div class="wf-pill" :data-state="state">
      {{ state || '—' }}
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  state: string | null | undefined
}>()
</script>

<style scoped>
.wf-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.wf-title {
  font-weight: 700;
  font-size: 14px;
}

.wf-pill {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 999px;
  border: 1px solid rgba(0, 0, 0, 0.15);
  text-transform: uppercase;
  font-weight: 600;
}

.wf-pill[data-state='draft'] {
  background: rgba(100, 100, 100, 0.08);
}
.wf-pill[data-state='in_review'] {
  background: rgba(200, 160, 0, 0.12);
  border-color: rgba(200, 160, 0, 0.35);
}
.wf-pill[data-state='approved'] {
  background: rgba(0, 180, 0, 0.12);
  border-color: rgba(0, 180, 0, 0.35);
}
.wf-pill[data-state='rejected'] {
  background: rgba(200, 0, 0, 0.12);
  border-color: rgba(200, 0, 0, 0.35);
}
</style>
