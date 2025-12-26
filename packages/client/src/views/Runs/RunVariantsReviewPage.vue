<script setup lang="ts">
/**
 * RunVariantsReviewPage.vue
 *
 * Product surface for variant review workflow.
 * Provides: variant browser, review/rating, promotion, comparison, and manufacturing queue.
 */
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import VariantNotes from "@/components/rmos/VariantNotes.vue";
import PromoteToManufacturingButton from "@/components/rmos/PromoteToManufacturingButton.vue";
import ManufacturingCandidatesPanel from "@/components/rmos/ManufacturingCandidatesPanel.vue";
import PromptLineageViewer from "@/components/rmos/PromptLineageViewer.vue";
import SvgPathDiffViewer from "@/components/rmos/SvgPathDiffViewer.vue";
import SvgPreview from "@/components/rmos/SvgPreview.vue";

const route = useRoute();
const apiBase = "/api";

// Run ID from route params
const runId = computed(() => String(route.params.run_id ?? route.params.id ?? ""));

// Variant list
type VariantRow = {
  advisory_id: string;
  mime?: string | null;
  filename?: string | null;
  rating?: number | null;
  notes?: string | null;
  promoted?: boolean;
};

const variants = ref<VariantRow[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

// Selection and comparison state
const selected = ref<string | null>(null);
const compareLeft = ref<string | null>(null);
const compareRight = ref<string | null>(null);

async function loadVariants() {
  if (!runId.value) return;
  loading.value = true;
  error.value = null;

  try {
    const res = await fetch(
      `${apiBase}/rmos/runs/${encodeURIComponent(runId.value)}/advisory/variants`,
      { credentials: "include" }
    );
    if (!res.ok) throw new Error(`Load variants failed (${res.status})`);
    const data = await res.json();

    // Handle both { items: [...] } and raw array responses
    const items = Array.isArray(data)
      ? data
      : Array.isArray(data?.items)
        ? data.items
        : [];

    variants.value = items
      .map((x: any) => ({
        advisory_id: String(x.advisory_id ?? x.advisoryId ?? x.sha256 ?? ""),
        mime: x.mime ?? null,
        filename: x.filename ?? null,
        rating: x.rating ?? null,
        notes: x.notes ?? null,
        promoted: x.promoted ?? false,
      }))
      .filter((x: VariantRow) => !!x.advisory_id);

    // Auto-select first if nothing selected
    if (!selected.value && variants.value.length) {
      selected.value = variants.value[0].advisory_id;
    }
  } catch (e: any) {
    error.value = e?.message ?? String(e);
    variants.value = [];
    selected.value = null;
  } finally {
    loading.value = false;
  }
}

function selectVariant(id: string) {
  selected.value = id;
}

function pickCompare(id: string) {
  if (!compareLeft.value) {
    compareLeft.value = id;
    return;
  }
  if (!compareRight.value && compareLeft.value !== id) {
    compareRight.value = id;
    return;
  }
  // Toggle off if clicked again
  if (compareLeft.value === id) {
    compareLeft.value = null;
    return;
  }
  if (compareRight.value === id) {
    compareRight.value = null;
    return;
  }
}

function clearCompare() {
  compareLeft.value = null;
  compareRight.value = null;
}

const compareReady = computed(() => !!compareLeft.value && !!compareRight.value);

const selectedVariant = computed(() =>
  variants.value.find((v) => v.advisory_id === selected.value)
);

onMounted(loadVariants);

watch(runId, () => {
  selected.value = null;
  compareLeft.value = null;
  compareRight.value = null;
  loadVariants();
});
</script>

<template>
  <div class="page">
    <div class="header">
      <div>
        <h1 class="title">Variants & Review</h1>
        <div class="subtitle">
          Run: <code>{{ runId }}</code>
        </div>
      </div>
      <div class="actions">
        <button class="btn secondary" @click="loadVariants" :disabled="loading">
          {{ loading ? "Loading..." : "Refresh" }}
        </button>
        <router-link class="btn secondary" :to="`/rmos/runs`">
          Back to Runs
        </router-link>
      </div>
    </div>

    <div v-if="error" class="error-banner">
      {{ error }}
      <button @click="error = null">&times;</button>
    </div>

    <div v-if="loading && !variants.length" class="loading">Loading variants...</div>

    <div v-else class="grid">
      <!-- LEFT: Variant list -->
      <div class="panel">
        <div class="panel-title">Variants</div>

        <div v-if="!variants.length" class="empty">
          No advisory variants linked to this run.
        </div>

        <div v-else class="variant-list">
          <button
            v-for="v in variants"
            :key="v.advisory_id"
            class="variant-row"
            :class="{ selected: selected === v.advisory_id }"
            @click="selectVariant(v.advisory_id)"
          >
            <div class="variant-main">
              <code class="variant-id">{{ v.advisory_id.slice(0, 12) }}...</code>
              <div class="variant-meta">
                <span v-if="v.mime" class="mime">{{ v.mime }}</span>
                <span v-if="v.rating" class="rating">{{ v.rating }}/5</span>
                <span v-if="v.promoted" class="promoted-badge">Promoted</span>
              </div>
            </div>
            <div class="variant-actions">
              <button
                class="btn tiny"
                :class="{ active: compareLeft === v.advisory_id || compareRight === v.advisory_id }"
                @click.stop="pickCompare(v.advisory_id)"
              >
                {{ compareLeft === v.advisory_id || compareRight === v.advisory_id ? "Picked" : "Compare" }}
              </button>
            </div>
          </button>
        </div>

        <div class="compare-hint">
          <span class="label">Compare:</span>
          <code>{{ compareLeft ? compareLeft.slice(0, 8) + "..." : "—" }}</code>
          <span>vs</span>
          <code>{{ compareRight ? compareRight.slice(0, 8) + "..." : "—" }}</code>
          <button v-if="compareLeft || compareRight" class="btn tiny" @click="clearCompare">
            Clear
          </button>
        </div>
      </div>

      <!-- RIGHT: Selected variant details -->
      <div class="panel" v-if="selected">
        <div class="panel-title">Selected Variant</div>

        <!-- SVG Preview -->
        <SvgPreview :runId="runId" :advisoryId="selected" :apiBase="apiBase" />

        <!-- Promote Button -->
        <div class="section">
          <PromoteToManufacturingButton
            :runId="runId"
            :advisoryId="selected"
            :apiBase="apiBase"
          />
        </div>

        <!-- Rating + Notes -->
        <div class="section">
          <VariantNotes :runId="runId" :advisoryId="selected" :apiBase="apiBase" />
        </div>

        <!-- Prompt Lineage -->
        <div class="section">
          <PromptLineageViewer :runId="runId" :advisoryId="selected" :apiBase="apiBase" />
        </div>
      </div>

      <div v-else class="panel empty-state">
        <p>Select a variant from the list to view details.</p>
      </div>

      <!-- BOTTOM: SVG Comparison -->
      <div class="panel wide" v-if="compareReady">
        <SvgPathDiffViewer
          :runId="runId"
          :leftAdvisoryId="compareLeft!"
          :rightAdvisoryId="compareRight!"
          :apiBase="apiBase"
        />
      </div>

      <!-- Manufacturing Candidates -->
      <div class="panel wide">
        <ManufacturingCandidatesPanel :runId="runId" :apiBase="apiBase" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  padding: 16px;
  max-width: 1600px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  gap: 16px;
  flex-wrap: wrap;
}

.title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
}

.subtitle {
  font-size: 0.9rem;
  color: #6c757d;
  margin-top: 4px;
}

.actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.error-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8d7da;
  color: #721c24;
  border-radius: 8px;
  margin-bottom: 16px;
}

.error-banner button {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: inherit;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #6c757d;
}

.grid {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 16px;
  align-items: start;
}

.panel {
  border: 1px solid #dee2e6;
  border-radius: 12px;
  padding: 16px;
  background: #fff;
}

.panel.wide {
  grid-column: 1 / -1;
}

.panel-title {
  font-weight: 700;
  font-size: 1.1rem;
  margin-bottom: 12px;
}

.empty,
.empty-state {
  color: #6c757d;
  text-align: center;
  padding: 20px;
}

.variant-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 400px;
  overflow-y: auto;
}

.variant-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border: 1px solid #e9ecef;
  border-radius: 10px;
  background: #fff;
  cursor: pointer;
  text-align: left;
  width: 100%;
}

.variant-row:hover {
  border-color: #adb5bd;
}

.variant-row.selected {
  border-color: #0066cc;
  background: #f0f7ff;
}

.variant-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.variant-id {
  font-size: 0.85rem;
}

.variant-meta {
  display: flex;
  gap: 8px;
  font-size: 0.75rem;
  color: #6c757d;
}

.promoted-badge {
  background: #d4edda;
  color: #155724;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.variant-actions {
  flex-shrink: 0;
}

.compare-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e9ecef;
  font-size: 0.85rem;
  flex-wrap: wrap;
}

.compare-hint .label {
  font-weight: 500;
}

.section {
  margin-top: 16px;
}

.btn {
  padding: 8px 14px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  text-decoration: none;
  color: inherit;
  font-size: 0.9rem;
}

.btn:hover:not(:disabled) {
  background: #f0f0f0;
}

.btn.secondary {
  opacity: 0.9;
}

.btn.tiny {
  padding: 4px 10px;
  font-size: 0.8rem;
}

.btn.active {
  background: #0066cc;
  color: #fff;
  border-color: #0066cc;
}

code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.85em;
  background: #f4f4f4;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
}

@media (max-width: 1100px) {
  .grid {
    grid-template-columns: 1fr;
  }

  .panel.wide {
    grid-column: auto;
  }
}
</style>
