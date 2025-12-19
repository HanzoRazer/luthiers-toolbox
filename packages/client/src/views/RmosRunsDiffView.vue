<script setup lang="ts">
/**
 * RmosRunsDiffView.vue
 *
 * Route wrapper for the Run Artifact Diff Viewer.
 * Includes URL-synced A/B inputs that write directly into URL query params.
 * The RunDiffViewer component auto-reloads when URL changes.
 */
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import RunDiffViewer from "@/components/rmos/RunDiffViewer.vue";

const route = useRoute();
const router = useRouter();

// Two-way binding with URL query params
const a = computed({
  get: () => (route.query.a as string) || "",
  set: (v: string) => router.replace({ query: { ...route.query, a: v || undefined } }),
});

const b = computed({
  get: () => (route.query.b as string) || "",
  set: (v: string) => router.replace({ query: { ...route.query, b: v || undefined } }),
});

function normalizeQuery() {
  // Push (not replace) so it creates a history entry
  router.push({ path: "/rmos/runs/diff", query: { a: a.value, b: b.value } });
}

function swapAB() {
  const tempA = a.value;
  const tempB = b.value;
  router.replace({ query: { a: tempB, b: tempA } });
}
</script>

<template>
  <div class="rmos-runs-diff-view">
    <div class="header">
      <div class="title-area">
        <h1>Run Artifact Comparison</h1>
        <p class="subtitle">
          Compare two run artifacts side-by-side.
          <router-link to="/rmos/runs">← Back to Run Artifacts</router-link>
        </p>
      </div>

      <div class="quick-inputs">
        <label>
          Run A
          <input
            v-model="a"
            type="text"
            placeholder="run_id A"
            spellcheck="false"
          />
        </label>
        <label>
          Run B
          <input
            v-model="b"
            type="text"
            placeholder="run_id B"
            spellcheck="false"
          />
        </label>
        <button class="btn-swap" @click="swapAB" title="Swap A and B">⇄</button>
        <button class="btn-compare" @click="normalizeQuery" :disabled="!a || !b">
          Compare
        </button>
      </div>
    </div>

    <RunDiffViewer />
  </div>
</template>

<style scoped>
.rmos-runs-diff-view {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1.5rem 2rem;
}

.header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.title-area h1 {
  margin: 0;
  font-size: 1.5rem;
}

.subtitle {
  color: #6c757d;
  margin: 0.5rem 0 0 0;
}

.subtitle a {
  color: #0066cc;
}

.quick-inputs {
  display: flex;
  gap: 0.75rem;
  align-items: flex-end;
}

.quick-inputs label {
  display: flex;
  flex-direction: column;
  font-size: 0.8rem;
  color: #6c757d;
}

.quick-inputs input {
  margin-top: 0.25rem;
  width: 220px;
  padding: 0.5rem 0.6rem;
  font-size: 0.9rem;
  font-family: monospace;
  border: 1px solid #dee2e6;
  border-radius: 4px;
}

.quick-inputs input:focus {
  outline: none;
  border-color: #0066cc;
  box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.15);
}

.btn-swap {
  padding: 0.5rem 0.6rem;
  font-size: 1rem;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
}

.btn-swap:hover {
  background: #e9ecef;
}

.btn-compare {
  padding: 0.55rem 1rem;
  font-size: 0.9rem;
  border: 1px solid #0066cc;
  border-radius: 4px;
  background: #0066cc;
  color: #fff;
  cursor: pointer;
}

.btn-compare:hover:not(:disabled) {
  background: #0052a3;
}

.btn-compare:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
