<script setup lang="ts">
/**
 * RunArtifactRow.vue
 *
 * Single row in the run artifact list.
 * Emits 'select' when clicked.
 */
import type { RunIndexItem } from "@/api/rmosRuns";

const props = defineProps<{
  run: RunIndexItem;
  selected?: boolean;
}>();

const emit = defineEmits<{
  (e: "select"): void;
}>();

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function statusClass(status: string): string {
  switch (status?.toUpperCase()) {
    case "OK":
      return "status-ok";
    case "BLOCKED":
      return "status-blocked";
    case "ERROR":
      return "status-error";
    default:
      return "status-unknown";
  }
}
</script>

<template>
  <div
    class="run-row"
    :class="{ selected }"
    @click="emit('select')"
    role="button"
    tabindex="0"
    @keydown.enter="emit('select')"
  >
    <div class="run-id" :title="run.run_id">
      {{ run.run_id.slice(0, 12) }}…
    </div>
    <div class="run-status" :class="statusClass(run.status)">
      {{ run.status }}
    </div>
    <div class="run-event">{{ run.event_type }}</div>
    <div class="run-tool">{{ run.tool_id || "—" }}</div>
    <div class="run-date">{{ formatDate(run.created_at_utc) }}</div>
  </div>
</template>

<style scoped>
.run-row {
  display: grid;
  grid-template-columns: 140px 80px 120px 100px 1fr;
  gap: 0.75rem;
  padding: 0.6rem 0.8rem;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: background-color 0.15s ease;
  align-items: center;
}

.run-row:hover {
  background-color: #f8f9fa;
}

.run-row.selected {
  background-color: #e7f1ff;
  border-left: 3px solid #0066cc;
}

.run-id {
  font-family: monospace;
  font-size: 0.85rem;
  color: #333;
}

.run-status {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  text-align: center;
  text-transform: uppercase;
}

.status-ok {
  background-color: #d4edda;
  color: #155724;
}

.status-blocked {
  background-color: #fff3cd;
  color: #856404;
}

.status-error {
  background-color: #f8d7da;
  color: #721c24;
}

.status-unknown {
  background-color: #e9ecef;
  color: #6c757d;
}

.run-event {
  font-size: 0.85rem;
  color: #495057;
}

.run-tool {
  font-size: 0.85rem;
  color: #6c757d;
}

.run-date {
  font-size: 0.8rem;
  color: #868e96;
  text-align: right;
}
</style>
