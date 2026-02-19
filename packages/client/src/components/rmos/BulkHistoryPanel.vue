<script setup lang="ts">
/**
 * BulkHistoryPanel - Displays bulk decision history
 *
 * Extracted from ManufacturingCandidateList.vue
 */

export interface BulkHistoryRecord {
  id: string;
  at_utc: string;
  decision: string;
  selected_count: number;
  note?: string;
}

defineProps<{
  history: BulkHistoryRecord[];
}>();
</script>

<template>
  <div class="bulkHistory">
    <div class="bulkHistoryHeader muted">
      Bulk history (newest first)
    </div>
    <div class="bulkHistoryList">
      <div
        v-for="rec in history"
        :key="rec.id"
        class="bulkHistoryRow"
      >
        <span class="mono small">{{ rec.at_utc }}</span>
        <span
          class="badge"
          :class="'b' + rec.decision"
        >{{ rec.decision }}</span>
        <span>{{ rec.selected_count }} items</span>
        <span
          v-if="rec.note"
          class="muted"
        >— {{ rec.note }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bulkHistory {
  padding: 8px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.5);
}

.bulkHistoryHeader {
  font-size: 12px;
  margin-bottom: 6px;
}

.bulkHistoryList {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.bulkHistoryRow {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.muted {
  opacity: 0.75;
}

.mono {
  font-family: "SF Mono", Monaco, Consolas, monospace;
}

.small {
  font-size: 11px;
}

.badge {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.bGREEN {
  background: rgba(0, 180, 0, 0.15);
  color: #006600;
}

.bYELLOW {
  background: rgba(255, 200, 0, 0.2);
  color: #886600;
}

.bRED {
  background: rgba(200, 0, 0, 0.1);
  color: #880000;
}
</style>
