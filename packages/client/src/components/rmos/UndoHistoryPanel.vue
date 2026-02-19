<script setup lang="ts">
/**
 * UndoHistoryPanel - Displays recent undo history items
 *
 * Extracted from ManufacturingCandidateList.vue
 */

export interface UndoHistoryItem {
  ts_utc: string;
  label: string;
}

defineProps<{
  history: UndoHistoryItem[];
  maxItems?: number;
}>();

const emit = defineEmits<{
  (e: "hover", item: UndoHistoryItem): string;
}>();

function getHoverText(item: UndoHistoryItem): string {
  return `${item.ts_utc}: ${item.label}`;
}
</script>

<template>
  <div class="undolist">
    <div class="undotitle muted">
      Undo history (most recent first)
    </div>
    <div
      v-for="(u, idx) in history.slice(0, maxItems ?? 5)"
      :key="u.ts_utc + ':' + idx"
      class="undoitem"
      :title="getHoverText(u)"
    >
      <span class="mono">{{ u.ts_utc }}</span>
      <span>—</span>
      <span>{{ u.label }}</span>
    </div>
  </div>
</template>

<style scoped>
.undolist {
  padding: 8px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.02);
}

.undotitle {
  font-size: 12px;
  margin-bottom: 6px;
}

.undoitem {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  padding: 2px 0;
}

.muted {
  opacity: 0.75;
}

.mono {
  font-family: "SF Mono", Monaco, Consolas, monospace;
  font-size: 11px;
}
</style>
