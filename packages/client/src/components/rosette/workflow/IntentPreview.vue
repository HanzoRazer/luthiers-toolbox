<template>
  <div v-if="intent" class="wf-intent-preview">
    <div class="wf-intent-title">Last Promotion Intent</div>
    <pre class="wf-intent-json">{{ JSON.stringify(intent, null, 2) }}</pre>
    <div class="wf-intent-actions">
      <button class="btn ghost" @click="$emit('copyJson')">
        Copy JSON
      </button>
      <button class="btn ghost" @click="$emit('copySessionId')">
        Copy Session ID
      </button>
      <button
        class="btn ghost"
        title="Copy cURL for promotion intent"
        @click="$emit('copyCurl')"
      >
        Copy cURL
      </button>
      <button
        class="btn ghost"
        title="Open Log Viewer filtered to this run"
        @click="$emit('openLogs')"
      >
        Open logs
      </button>
      <button
        class="btn ghost"
        title="Download intent as JSON file"
        @click="$emit('download')"
      >
        Download intent
      </button>
      <button class="btn ghost" @click="$emit('clear')">
        Clear
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  intent: Record<string, unknown> | null
}>()

defineEmits<{
  copyJson: []
  copySessionId: []
  copyCurl: []
  openLogs: []
  download: []
  clear: []
}>()
</script>

<style scoped>
.wf-intent-preview {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.wf-intent-title {
  font-size: 11px;
  font-weight: 600;
  opacity: 0.7;
  margin-bottom: 6px;
}

.wf-intent-json {
  background: rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 8px;
  padding: 8px;
  font-size: 10px;
  overflow-x: auto;
  max-height: 200px;
  overflow-y: auto;
}

.wf-intent-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.wf-intent-actions .btn {
  font-size: 11px;
  padding: 4px 8px;
}

.btn {
  border: 1px solid rgba(0, 0, 0, 0.18);
  border-radius: 10px;
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
  background: #fff;
  transition: background 0.1s;
}

.btn:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.04);
}

.btn.ghost {
  background: transparent;
}
</style>
