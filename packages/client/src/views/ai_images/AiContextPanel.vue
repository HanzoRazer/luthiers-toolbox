<template>
  <div class="context-panel">
    <h2>Generate AI Context</h2>
    <p class="context-description">
      Build a bounded context envelope for AI consumption.
      Manufacturing secrets (toolpaths, G-code) are excluded by design.
    </p>

    <div class="context-form">
      <label>
        Run ID (optional)
        <input
          :value="runId"
          type="text"
          placeholder="run_abc123..."
          class="context-input"
          @input="$emit('update:runId', ($event.target as HTMLInputElement).value)"
        >
      </label>

      <button
        class="btn-build-context"
        :disabled="loading"
        @click="$emit('build')"
      >
        {{ loading ? 'Building...' : 'Build AI Context' }}
      </button>
    </div>

    <div
      v-if="error"
      class="context-error"
    >
      <strong>Error:</strong> {{ error }}
    </div>

    <div
      v-if="result"
      class="context-result"
    >
      <div class="context-result-header">
        <span class="context-id">{{ result.context_id }}</span>
        <button
          class="btn-copy"
          @click="$emit('copy')"
        >
          Copy JSON
        </button>
      </div>

      <div
        v-if="result.warnings?.length"
        class="context-warnings"
      >
        <strong>Warnings:</strong>
        <ul>
          <li
            v-for="(w, i) in result.warnings"
            :key="i"
          >
            {{ w }}
          </li>
        </ul>
      </div>

      <pre class="context-json">{{ JSON.stringify(result, null, 2) }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  runId: string
  loading: boolean
  error: string | null
  result: { context_id: string; warnings?: string[] } | null
}>()

defineEmits<{
  'update:runId': [value: string]
  build: []
  copy: []
}>()
</script>

<style scoped>
.context-panel {
  background: var(--bg-panel, #16213e);
  border: 1px solid var(--border, #2a3f5f);
  border-radius: 12px;
  padding: 24px;
}

.context-panel h2 {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 600;
  color: var(--text, #fff);
}

.context-description {
  margin: 0 0 20px;
  font-size: 14px;
  color: var(--text-dim, #8892a0);
}

.context-form {
  display: flex;
  gap: 16px;
  align-items: flex-end;
  margin-bottom: 20px;
}

.context-form label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 14px;
  color: var(--text-dim, #8892a0);
}

.context-input {
  padding: 10px 14px;
  background: var(--bg-input, #0f1629);
  border: 1px solid var(--border, #2a3f5f);
  border-radius: 8px;
  color: var(--text, #e0e0e0);
  font-size: 14px;
  width: 280px;
}

.context-input:focus {
  outline: none;
  border-color: var(--accent, #4fc3f7);
}

.btn-build-context {
  padding: 10px 20px;
  background: var(--accent, #4fc3f7);
  border: none;
  border-radius: 8px;
  color: #000;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-build-context:hover:not(:disabled) {
  background: #29b6f6;
}

.btn-build-context:disabled {
  background: var(--bg-input, #0f1629);
  color: var(--text-dim, #8892a0);
  cursor: not-allowed;
}

.context-error {
  background: rgba(244, 67, 54, 0.15);
  border: 1px solid #f44336;
  border-radius: 8px;
  padding: 12px 16px;
  color: #f44336;
  margin-bottom: 16px;
  font-size: 14px;
}

.context-result {
  background: var(--bg-input, #0f1629);
  border: 1px solid var(--border, #2a3f5f);
  border-radius: 8px;
  overflow: hidden;
}

.context-result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border, #2a3f5f);
}

.context-id {
  font-family: monospace;
  font-size: 13px;
  color: var(--accent, #4fc3f7);
}

.btn-copy {
  padding: 6px 12px;
  background: var(--bg-panel, #16213e);
  border: 1px solid var(--border, #2a3f5f);
  border-radius: 6px;
  color: var(--text, #e0e0e0);
  font-size: 12px;
  cursor: pointer;
}

.btn-copy:hover {
  background: var(--accent, #4fc3f7);
  color: #000;
}

.context-warnings {
  padding: 12px 16px;
  background: rgba(255, 193, 7, 0.1);
  border-bottom: 1px solid var(--border, #2a3f5f);
  font-size: 13px;
  color: #ffc107;
}

.context-warnings ul {
  margin: 8px 0 0 20px;
  padding: 0;
}

.context-warnings li {
  margin-bottom: 4px;
}

.context-json {
  margin: 0;
  padding: 16px;
  font-family: monospace;
  font-size: 12px;
  color: var(--text, #e0e0e0);
  overflow-x: auto;
  max-height: 500px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
