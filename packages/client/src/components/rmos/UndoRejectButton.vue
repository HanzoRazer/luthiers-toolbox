<script setup lang="ts">
import { ref } from "vue";
import { unrejectAdvisoryVariant } from "@/api/rmosRuns";

const props = defineProps<{
  runId: string;
  advisoryId: string;
  disabled?: boolean;
}>();

const emit = defineEmits<{ (e: "cleared"): void }>();

const busy = ref(false);
const error = ref<string | null>(null);

async function doClear() {
  busy.value = true;
  error.value = null;
  try {
    await unrejectAdvisoryVariant(props.runId, props.advisoryId);
    emit("cleared");
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <div class="wrap">
    <button class="btn tiny" :disabled="disabled || busy" @click="doClear">
      {{ busy ? "Undo…" : "Undo Reject" }}
    </button>
    <div v-if="error" class="err">{{ error }}</div>
  </div>
</template>

<style scoped>
.btn {
  padding: 8px 10px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 10px;
  background: white;
  cursor: pointer;
}
.btn.tiny {
  padding: 4px 8px;
  font-size: 0.9em;
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.err {
  color: #b00020;
  font-size: 12px;
  margin-top: 4px;
}
.wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
</style>
