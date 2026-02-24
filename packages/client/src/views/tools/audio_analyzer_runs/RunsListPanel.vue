<template>
  <section class="runs-panel card">
    <h2>Recent Runs</h2>

    <!-- Filters -->
    <div class="filters">
      <label>
        <span>Session ID</span>
        <input
          :value="sessionIdFilter"
          type="text"
          placeholder="Filter..."
          @input="$emit('update:sessionIdFilter', ($event.target as HTMLInputElement).value)"
        >
      </label>
      <label>
        <span>Batch Label</span>
        <input
          :value="batchLabelFilter"
          type="text"
          placeholder="Filter..."
          @input="$emit('update:batchLabelFilter', ($event.target as HTMLInputElement).value)"
        >
      </label>
    </div>

    <div
      v-if="loading"
      class="muted"
    >
      Loading runs...
    </div>
    <div
      v-else-if="error"
      class="error-box"
    >
      {{ error }}
    </div>
    <div
      v-else-if="!runs?.length"
      class="muted"
    >
      No runs found. Import a viewer_pack in the Library.
    </div>
    <div
      v-else
      class="runs-list"
    >
      <div
        v-for="run in runs"
        :key="run.run_id"
        class="run-item"
        :class="{ selected: selectedRunId === run.run_id }"
        @click="$emit('select', run.run_id)"
      >
        <div class="run-header">
          <span class="run-date">{{ formatDate(run.created_at_utc) }}</span>
          <code
            class="run-status"
            :class="run.status.toLowerCase()"
          >{{ run.status }}</code>
        </div>
        <div class="run-meta">
          <span
            v-if="run.session_id"
            class="run-session"
          >{{ run.session_id }}</span>
          <span
            v-if="run.batch_label"
            class="run-batch"
          >{{ run.batch_label }}</span>
        </div>
        <div class="run-stats">
          <span>{{ run.attachment_count }} files</span>
          <span v-if="run.viewer_pack_count"> {{ run.viewer_pack_count }} viewer packs</span>
        </div>
        <div
          v-if="run.kinds_present.length"
          class="run-kinds"
        >
          <code
            v-for="k in run.kinds_present.slice(0, 4)"
            :key="k"
            class="kind-chip"
          >{{ k }}</code>
          <span
            v-if="run.kinds_present.length > 4"
            class="muted"
          >+{{ run.kinds_present.length - 4 }}</span>
        </div>
      </div>

      <button
        v-if="hasMore"
        class="btn load-more"
        @click="$emit('loadMore')"
      >
        Load More
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
interface Run {
  run_id: string
  created_at_utc: string
  status: string
  session_id?: string | null
  batch_label?: string | null
  event_type?: string | null
  attachment_count: number
  viewer_pack_count?: number
  kinds_present: string[]
  primary_viewer_pack_sha256?: string | null
}

defineProps<{
  runs: Run[] | null
  loading: boolean
  error: string
  selectedRunId: string | null
  sessionIdFilter: string
  batchLabelFilter: string
  hasMore: boolean
}>()

defineEmits<{
  select: [runId: string]
  loadMore: []
  'update:sessionIdFilter': [value: string]
  'update:batchLabelFilter': [value: string]
}>()

function formatDate(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleString()
  } catch {
    return iso
  }
}
</script>

<style scoped>
.runs-panel {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 12px;
}

.runs-panel h2 {
  margin: 0 0 12px 0;
  font-size: 1rem;
}

.filters {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.filters label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.8rem;
}

.filters label span {
  opacity: 0.7;
}

.filters input {
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.06);
  color: inherit;
  width: 140px;
}

.runs-list {
  display: grid;
  gap: 8px;
  max-height: 70vh;
  overflow-y: auto;
}

.run-item {
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  cursor: pointer;
  border: 1px solid transparent;
}

.run-item:hover {
  background: rgba(255, 255, 255, 0.06);
}

.run-item.selected {
  background: rgba(66, 184, 131, 0.12);
  border-color: rgba(66, 184, 131, 0.3);
}

.run-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.run-date {
  font-size: 0.85rem;
}

.run-status {
  font-size: 0.75rem;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.1);
}

.run-status.ok {
  background: rgba(66, 184, 131, 0.2);
  color: #42b883;
}

.run-status.error {
  background: rgba(255, 0, 0, 0.2);
  color: #ff6b6b;
}

.run-meta {
  display: flex;
  gap: 8px;
  margin-top: 4px;
  font-size: 0.8rem;
  opacity: 0.7;
}

.run-stats {
  font-size: 0.8rem;
  opacity: 0.6;
  margin-top: 4px;
}

.run-kinds {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}

.kind-chip {
  font-size: 0.7rem;
  padding: 2px 6px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 4px;
}

.load-more {
  margin-top: 8px;
}

.muted {
  opacity: 0.6;
}

.error-box {
  padding: 8px 12px;
  background: rgba(255, 0, 0, 0.12);
  border: 1px solid rgba(255, 0, 0, 0.25);
  border-radius: 8px;
  font-size: 0.9rem;
}

.btn {
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.08);
  color: inherit;
  cursor: pointer;
  font-size: 0.85rem;
}

.btn:hover {
  background: rgba(255, 255, 255, 0.12);
}
</style>
