<script setup lang="ts">
/**
 * GcodePreviewPanel — G-code preview with line count, cycle time, download.
 * Empty state: "Generate G-code to preview".
 */
import { computed } from 'vue';

const props = defineProps<{
  gcode: string | null;
  filename: string;
  cycleTimeSeconds: number | null;
}>();

const lineCount = computed(() =>
  props.gcode ? props.gcode.trim().split(/\r?\n/).length : 0
);

const cycleTimeFormatted = computed(() => {
  if (props.cycleTimeSeconds == null) return '—';
  const m = Math.floor(props.cycleTimeSeconds / 60);
  const s = Math.round(props.cycleTimeSeconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
});

function download() {
  if (!props.gcode) return;
  const blob = new Blob([props.gcode], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = props.filename.endsWith('.nc') ? props.filename : `${props.filename}.nc`;
  a.click();
  URL.revokeObjectURL(url);
}
</script>

<template>
  <div class="gcode-panel">
    <div class="meta">
      <span>{{ lineCount }} lines</span>
      <span>Est. cycle: {{ cycleTimeFormatted }}</span>
    </div>
    <pre v-if="gcode" class="pre">{{ gcode }}</pre>
    <p v-else class="empty">Generate G-code to preview</p>
    <button
      type="button"
      class="download-btn"
      :disabled="!gcode"
      @click="download"
    >
      Download .nc
    </button>
  </div>
</template>

<style scoped>
.gcode-panel {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.75rem;
}
.meta {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
  color: #64748b;
  margin-bottom: 0.5rem;
}
.pre {
  margin: 0;
  padding: 0.5rem;
  background: #f8fafc;
  border-radius: 4px;
  overflow: auto;
  max-height: 240px;
  font-size: 0.8rem;
}
.empty {
  margin: 0.5rem 0;
  color: #94a3b8;
  font-size: 0.875rem;
}
.download-btn {
  margin-top: 0.5rem;
  padding: 0.35rem 0.75rem;
  font-size: 0.875rem;
  cursor: pointer;
}
.download-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
