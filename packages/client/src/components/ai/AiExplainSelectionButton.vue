<template>
  <div class="ai-ux">
    <div class="row">
      <button
        class="btn"
        :class="{ disabled: !!disabledReason, running: runState.state === 'running' }"
        :disabled="!!disabledReason || runState.state === 'running'"
        @click="onClick"
        :title="disabledReason || 'Request an explanation for the current selection'"
      >
        <span v-if="runState.state === 'running'" class="spinner" aria-hidden="true"></span>
        🧠 Explain selection
      </button>

      <button class="btn subtle" :disabled="runState.state === 'running'" @click="$emit('clear')">
        Clear
      </button>
    </div>

    <div class="status">
      <span class="sel">{{ selSummary }}</span>
      <span v-if="runState.state === 'success'" class="ok">
        Draft saved ({{ runState.advisoryId.slice(0, 8) }}…)
      </span>
      <span v-else-if="runState.state === 'error'" class="err">
        {{ runState.message }}
      </span>
      <span v-else class="hint">
        Draft advisory only — review required.
      </span>
    </div>

    <details class="why" v-if="disabledReason">
      <summary>Why disabled?</summary>
      <div class="why-body">{{ disabledReason }}</div>
    </details>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { ExplainButtonInputs, AiRunState } from "./types";
import { computeDisabledReason, selectionSummary } from "./helpers";

const props = defineProps<{
  inputs: ExplainButtonInputs;
  runState: AiRunState;
}>();

const emit = defineEmits<{
  (e: "run"): void;
  (e: "clear"): void;
}>();

const disabledReason = computed(() => computeDisabledReason(props.inputs));
const selSummary = computed(() => selectionSummary(props.inputs.selection));

function onClick() {
  if (disabledReason.value) return;
  emit("run");
}
</script>

<style scoped>
.ai-ux { display: grid; gap: 0.5rem; padding: 0.5rem; border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; }
.row { display: flex; gap: 0.5rem; align-items: center; }
.btn { padding: 0.5rem 0.75rem; border-radius: 10px; border: 1px solid rgba(255,255,255,0.14); background: rgba(255,255,255,0.06); color: inherit; cursor: pointer; }
.btn:hover { background: rgba(255,255,255,0.10); }
.btn.disabled { opacity: 0.55; cursor: not-allowed; }
.btn.subtle { background: rgba(255,255,255,0.03); }
.status { display: flex; gap: 0.75rem; flex-wrap: wrap; font-size: 0.85rem; opacity: 0.9; }
.sel { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; opacity: 0.85; }
.ok { color: #42b883; }
.err { color: #ff6b6b; }
.hint { opacity: 0.75; }
.why summary { cursor: pointer; opacity: 0.8; }
.why-body { margin-top: 0.25rem; opacity: 0.85; }
.spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  margin-right: 6px;
  border: 2px solid rgba(255,255,255,0.35);
  border-top-color: rgba(255,255,255,0.95);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  vertical-align: -2px;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
