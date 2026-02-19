<template>
  <div v-if="exportUrl" class="export-url-preview">
    <div class="export-url-label">Export URL</div>
    <input
      type="text"
      class="export-url-input"
      :value="exportUrl"
      readonly
      @click="($event.target as HTMLInputElement)?.select()"
    >
    <button class="btn ghost" title="Copy URL to clipboard" @click="$emit('copyUrl')">
      Copy URL
    </button>
    <button
      class="btn ghost"
      :disabled="!exportUrl"
      title="Copy PowerShell Invoke-WebRequest command (downloads JSON to a file)"
      @click="$emit('copyPowerShell')"
    >
      Copy PowerShell
    </button>
    <button
      class="btn ghost"
      :disabled="!exportUrl"
      title="Copy Python requests snippet (downloads JSON to a file)"
      @click="$emit('copyPython')"
    >
      Copy Python
    </button>
    <button
      class="btn ghost"
      :disabled="!exportUrl"
      title="Copy Node 18+ fetch snippet (downloads JSON to a file)"
      @click="$emit('copyNode')"
    >
      Copy Node
    </button>
    <button
      class="btn ghost"
      :disabled="!exportUrl"
      title="Copy GitHub Actions step YAML (curl + artifact upload)"
      @click="$emit('copyGHA')"
    >
      Copy GHA
    </button>
    <button
      class="btn ghost"
      :disabled="!exportUrl"
      title="Copy full GitHub Actions job YAML (checkout + auth + download + upload)"
      @click="$emit('copyGHAJob')"
    >
      Copy GHA Job
    </button>
    <button
      class="btn ghost"
      :disabled="!exportUrl"
      title="Copy complete GitHub Actions workflow file (.yml)"
      @click="$emit('copyGHAWorkflow')"
    >
      Copy GHA Workflow
    </button>
    <button
      class="btn ghost"
      :disabled="!exportUrl"
      title="Copy a complete GitHub Actions workflow with filename instructions"
      @click="$emit('copyGHAWorkflowFile')"
    >
      Copy GH Workflow (File-Ready)
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  exportUrl: string
}>()

defineEmits<{
  copyUrl: []
  copyPowerShell: []
  copyPython: []
  copyNode: []
  copyGHA: []
  copyGHAJob: []
  copyGHAWorkflow: []
  copyGHAWorkflowFile: []
}>()
</script>

<style scoped>
.export-url-preview {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.export-url-label {
  font-size: 12px;
  font-weight: 700;
  opacity: 0.85;
}

.export-url-input {
  flex: 1;
  min-width: 200px;
  border: 1px solid rgba(0, 0, 0, 0.16);
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 11px;
  font-family: monospace;
  background: rgba(0, 0, 0, 0.02);
  color: #333;
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

.btn:disabled {
  opacity: 0.5;
  cursor: default;
}

.btn.ghost {
  background: transparent;
}
</style>
