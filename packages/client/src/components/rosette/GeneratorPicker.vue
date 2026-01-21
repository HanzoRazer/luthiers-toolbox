<template>
  <div class="card">
    <div class="row">
      <h3>Generator</h3>
      <button
        class="btn"
        :disabled="store.generatorsLoading"
        @click="store.loadGenerators()"
      >
        Refresh
      </button>
    </div>
    <div
      v-if="store.generatorsError"
      class="err"
    >
      {{ store.generatorsError }}
    </div>
    <label class="lbl">Generator Key</label>
    <select
      v-model="store.selectedGeneratorKey"
      class="input"
    >
      <option
        v-for="g in store.generators"
        :key="g.generator_key"
        :value="g.generator_key"
      >
        {{ g.name }} - {{ g.generator_key }}
      </option>
    </select>
    <div
      v-if="selectedDesc"
      class="hint"
    >
      <div class="small">
        {{ selectedDesc.description }}
      </div>
    </div>
    <label class="lbl">Generator Params (JSON)</label>
    <textarea
      v-model="paramsJson"
      class="input mono"
      rows="6"
    />
    <div class="row">
      <button
        class="btn primary"
        @click="applyParamsJson"
      >
        Apply Params
      </button>
      <button
        class="btn"
        @click="store.generateSpecFromGenerator()"
      >
        Generate Spec
      </button>
      <button
        class="btn"
        @click="store.refreshPreview()"
      >
        Preview
      </button>
    </div>
    <div
      v-if="store.generatorWarnings?.length"
      class="warn"
    >
      <div><strong>Generator warnings:</strong></div>
      <ul>
        <li
          v-for="(w, i) in store.generatorWarnings"
          :key="i"
        >
          {{ w }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRosetteStore } from "@/stores/rosetteStore";
import { useToastStore } from "@/stores/toastStore";

const store = useRosetteStore();
const toast = useToastStore();

const selectedDesc = computed(() =>
  store.generators.find((g) => g.generator_key === store.selectedGeneratorKey) || null
);

const paramsJson = ref(JSON.stringify(store.generatorParams || {}, null, 2));

watch(
  () => store.generatorParams,
  (v) => {
    paramsJson.value = JSON.stringify(v || {}, null, 2);
  },
  { deep: true }
);

function applyParamsJson() {
  try {
    const parsed = JSON.parse(paramsJson.value || "{}");
    store.generatorParams = parsed;
    toast.success( "Generator params applied.");
  } catch (e: any) {
    toast.error( e?.message || "Invalid JSON.");
  }
}
</script>

<style scoped>
.card {
  border: 1px solid #ddd;
  border-radius: 12px;
  padding: 12px;
  background: #fff;
}
.row {
  display: flex;
  gap: 10px;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.btn {
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid #ccc;
  background: #f7f7f7;
  cursor: pointer;
}
.btn.primary {
  background: #111;
  color: #fff;
  border-color: #111;
}
.lbl {
  display: block;
  margin-top: 10px;
  margin-bottom: 6px;
  font-size: 12px;
  color: #333;
}
.input {
  width: 100%;
  border: 1px solid #ccc;
  border-radius: 10px;
  padding: 8px;
}
.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}
.err {
  color: #a00;
  margin: 8px 0;
}
.warn {
  margin-top: 10px;
  padding: 10px;
  border-radius: 10px;
  background: #fff7e6;
  border: 1px solid #f1d199;
}
.small {
  font-size: 12px;
  color: #333;
}
.hint {
  margin-top: 8px;
  padding: 8px;
  border-radius: 10px;
  background: #fafafa;
  border: 1px solid #eee;
}
</style>
