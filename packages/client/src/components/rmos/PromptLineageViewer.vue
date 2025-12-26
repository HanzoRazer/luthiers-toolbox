<script setup lang="ts">
/**
 * PromptLineageViewer.vue
 *
 * Displays the AI prompt lineage for a variant - shows why this variant exists.
 * TODO: Connect to advisory provenance API when available.
 */
import { computed, onMounted, ref, watch } from "vue";

const props = defineProps<{
  runId: string;
  advisoryId: string;
  apiBase?: string;
}>();

const apiBase = computed(() => props.apiBase ?? "/api");
const loading = ref(false);
const error = ref<string | null>(null);
const lineage = ref<any>(null);

async function loadLineage() {
  if (!props.runId || !props.advisoryId) return;

  loading.value = true;
  error.value = null;

  try {
    // TODO: Replace with actual lineage API when available
    // For now, try to fetch from advisory metadata
    const res = await fetch(
      `${apiBase.value}/rmos/runs/${encodeURIComponent(props.runId)}/advisory/blobs/${encodeURIComponent(
        props.advisoryId
      )}/metadata`,
      { credentials: "include" }
    );

    if (res.status === 404) {
      // No lineage available - this is fine
      lineage.value = null;
      return;
    }

    if (!res.ok) throw new Error(`Load lineage failed (${res.status})`);
    lineage.value = await res.json();
  } catch (e: any) {
    // Silently handle - lineage is optional
    lineage.value = null;
  } finally {
    loading.value = false;
  }
}

onMounted(loadLineage);
watch(() => [props.runId, props.advisoryId], loadLineage);
</script>

<template>
  <div class="lineage-box">
    <div class="title">Prompt Lineage</div>

    <div v-if="loading" class="subtle">Loading lineage...</div>

    <div v-else-if="lineage" class="lineage-content">
      <div v-if="lineage.engine_id" class="row">
        <span class="label">Engine:</span>
        <code>{{ lineage.engine_id }}</code>
        <span v-if="lineage.engine_version" class="subtle">v{{ lineage.engine_version }}</span>
      </div>
      <div v-if="lineage.request_id" class="row">
        <span class="label">Request:</span>
        <code>{{ lineage.request_id }}</code>
      </div>
      <div v-if="lineage.prompt" class="prompt">
        <span class="label">Prompt:</span>
        <pre>{{ lineage.prompt }}</pre>
      </div>
    </div>

    <div v-else class="subtle">
      No lineage data available for this variant.
    </div>
  </div>
</template>

<style scoped>
.lineage-box {
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  padding: 12px;
}

.title {
  font-weight: 700;
  margin-bottom: 10px;
}

.lineage-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
}

.label {
  font-weight: 500;
  min-width: 70px;
}

.prompt {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.prompt pre {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 10px;
  font-size: 0.85rem;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}

.subtle {
  opacity: 0.7;
  font-size: 0.9rem;
}

code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.85em;
  background: #f4f4f4;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
}
</style>
