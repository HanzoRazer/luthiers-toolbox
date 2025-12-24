<script setup lang="ts">
/**
 * VariantReviewPanel.vue
 *
 * Panel for reviewing, rating, and promoting advisory variants.
 * Integrates with the /api/rmos/runs/{run_id}/advisory/variants API.
 */
import { ref, computed, onMounted, watch } from "vue";
import SvgPreview from "./SvgPreview.vue";
import StarRating from "./StarRating.vue";

interface AdvisoryVariant {
  advisory_id: string;
  mime: string;
  filename: string;
  kind: string;
  rating: number | null;
  notes: string | null;
  reviewed_at: string | null;
  reviewed_by: string | null;
  promoted: boolean;
  promoted_run_id: string | null;
}

const props = defineProps<{
  /** Run artifact ID */
  runId: string;
  /** API base URL (default: "") */
  apiBase?: string;
  /** Current operator identity */
  operatorId?: string;
}>();

const emit = defineEmits<{
  (e: "variant-reviewed", advisoryId: string): void;
  (e: "variant-promoted", advisoryId: string, newRunId: string): void;
  (e: "error", msg: string): void;
}>();

const variants = ref<AdvisoryVariant[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const selectedVariant = ref<AdvisoryVariant | null>(null);
const svgContent = ref<string>("");
const loadingSvg = ref(false);

// Review form state
const reviewRating = ref<number | null>(null);
const reviewNotes = ref("");
const saving = ref(false);
const promoting = ref(false);

const apiUrl = computed(() => props.apiBase || "");

async function fetchVariants() {
  loading.value = true;
  error.value = null;
  try {
    const res = await fetch(
      `${apiUrl.value}/api/rmos/runs/${props.runId}/advisory/variants`
    );
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Failed to load variants: ${res.status} ${text}`);
    }
    variants.value = await res.json();
  } catch (err) {
    error.value = String(err);
    emit("error", String(err));
  } finally {
    loading.value = false;
  }
}

async function fetchSvgContent(advisoryId: string) {
  loadingSvg.value = true;
  svgContent.value = "";
  try {
    const res = await fetch(
      `${apiUrl.value}/api/rmos/runs/${props.runId}/advisory/${advisoryId}/blob`
    );
    if (!res.ok) {
      throw new Error(`Failed to load SVG: ${res.status}`);
    }
    const text = await res.text();
    svgContent.value = text;
  } catch (err) {
    console.warn("Could not load SVG:", err);
  } finally {
    loadingSvg.value = false;
  }
}

function selectVariant(variant: AdvisoryVariant) {
  selectedVariant.value = variant;
  reviewRating.value = variant.rating;
  reviewNotes.value = variant.notes || "";

  // Load SVG if it's an SVG type
  if (variant.mime === "image/svg+xml") {
    fetchSvgContent(variant.advisory_id);
  } else {
    svgContent.value = "";
  }
}

async function saveReview() {
  if (!selectedVariant.value || reviewRating.value === null) return;

  saving.value = true;
  try {
    const res = await fetch(
      `${apiUrl.value}/api/rmos/runs/${props.runId}/advisory/${selectedVariant.value.advisory_id}/review`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          rating: reviewRating.value,
          notes: reviewNotes.value,
          reviewed_by: props.operatorId || null,
        }),
      }
    );
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Failed to save review: ${res.status} ${text}`);
    }

    // Update local state
    const idx = variants.value.findIndex(
      (v) => v.advisory_id === selectedVariant.value!.advisory_id
    );
    if (idx >= 0) {
      variants.value[idx] = {
        ...variants.value[idx],
        rating: reviewRating.value,
        notes: reviewNotes.value,
        reviewed_at: new Date().toISOString(),
        reviewed_by: props.operatorId || null,
      };
    }

    emit("variant-reviewed", selectedVariant.value.advisory_id);
  } catch (err) {
    error.value = String(err);
    emit("error", String(err));
  } finally {
    saving.value = false;
  }
}

async function promoteVariant() {
  if (!selectedVariant.value) return;
  if (selectedVariant.value.promoted) return;

  promoting.value = true;
  try {
    const res = await fetch(
      `${apiUrl.value}/api/rmos/runs/${props.runId}/advisory/${selectedVariant.value.advisory_id}/promote`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          promoted_by: props.operatorId || null,
        }),
      }
    );
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Failed to promote: ${res.status} ${text}`);
    }

    const result = await res.json();

    // Update local state
    const idx = variants.value.findIndex(
      (v) => v.advisory_id === selectedVariant.value!.advisory_id
    );
    if (idx >= 0) {
      variants.value[idx] = {
        ...variants.value[idx],
        promoted: true,
        promoted_run_id: result.manufacturing_run_id,
      };
      selectedVariant.value = variants.value[idx];
    }

    emit("variant-promoted", selectedVariant.value!.advisory_id, result.manufacturing_run_id);
  } catch (err) {
    error.value = String(err);
    emit("error", String(err));
  } finally {
    promoting.value = false;
  }
}

function formatDate(iso: string | null): string {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function kindLabel(kind: string): string {
  const labels: Record<string, string> = {
    explanation: "Explanation",
    advisory: "Advisory",
    note: "Note",
    unknown: "Unknown",
  };
  return labels[kind] || kind;
}

onMounted(fetchVariants);

watch(() => props.runId, fetchVariants);
</script>

<template>
  <div class="variant-review-panel">
    <div class="panel-header">
      <h3>Variant Review</h3>
      <button class="btn btn-sm" @click="fetchVariants" :disabled="loading">
        Refresh
      </button>
    </div>

    <!-- Error -->
    <div v-if="error" class="error-banner">
      {{ error }}
      <button @click="error = null">&times;</button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading">Loading variants...</div>

    <!-- Empty -->
    <div v-else-if="variants.length === 0" class="empty">
      No advisory variants found for this run.
    </div>

    <!-- Content -->
    <div v-else class="panel-content">
      <!-- Variant List -->
      <div class="variant-list">
        <div
          v-for="v in variants"
          :key="v.advisory_id"
          class="variant-item"
          :class="{
            selected: selectedVariant?.advisory_id === v.advisory_id,
            promoted: v.promoted,
          }"
          @click="selectVariant(v)"
        >
          <div class="variant-header">
            <span class="kind-badge">{{ kindLabel(v.kind) }}</span>
            <span class="filename">{{ v.filename }}</span>
          </div>
          <div class="variant-meta">
            <StarRating
              :modelValue="v.rating"
              :disabled="true"
              :size="14"
            />
            <span v-if="v.promoted" class="promoted-badge">Promoted</span>
          </div>
        </div>
      </div>

      <!-- Detail Panel -->
      <div v-if="selectedVariant" class="variant-detail">
        <div class="detail-header">
          <h4>{{ selectedVariant.filename }}</h4>
          <span class="advisory-id">{{ selectedVariant.advisory_id.slice(0, 16) }}...</span>
        </div>

        <!-- SVG Preview -->
        <div v-if="selectedVariant.mime === 'image/svg+xml'" class="preview-section">
          <div v-if="loadingSvg" class="loading-svg">Loading preview...</div>
          <SvgPreview
            v-else-if="svgContent"
            :svg="svgContent"
            :maxHeight="250"
            :expandable="true"
          />
        </div>

        <!-- Review Form -->
        <div class="review-form">
          <div class="form-group">
            <label>Rating</label>
            <StarRating
              v-model="reviewRating"
              :disabled="saving"
              :size="28"
            />
          </div>

          <div class="form-group">
            <label>Notes</label>
            <textarea
              v-model="reviewNotes"
              rows="3"
              placeholder="Add review notes..."
              :disabled="saving"
            />
          </div>

          <!-- Previous Review Info -->
          <div v-if="selectedVariant.reviewed_at" class="previous-review">
            <span>Last reviewed: {{ formatDate(selectedVariant.reviewed_at) }}</span>
            <span v-if="selectedVariant.reviewed_by">
              by {{ selectedVariant.reviewed_by }}
            </span>
          </div>

          <div class="form-actions">
            <button
              class="btn btn-primary"
              @click="saveReview"
              :disabled="saving || reviewRating === null"
            >
              {{ saving ? "Saving..." : "Save Review" }}
            </button>

            <button
              v-if="!selectedVariant.promoted"
              class="btn btn-success"
              @click="promoteVariant"
              :disabled="promoting || reviewRating === null"
              title="Promote to manufacturing candidate"
            >
              {{ promoting ? "Promoting..." : "Promote" }}
            </button>

            <div v-else class="promoted-info">
              <span class="promoted-label">Promoted to:</span>
              <code>{{ selectedVariant.promoted_run_id?.slice(0, 16) }}...</code>
            </div>
          </div>
        </div>
      </div>

      <!-- No Selection -->
      <div v-else class="no-selection">
        Select a variant to review
      </div>
    </div>
  </div>
</template>

<style scoped>
.variant-review-panel {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  background: #fff;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.panel-header h3 {
  margin: 0;
  font-size: 1rem;
}

.error-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  background: #f8d7da;
  color: #721c24;
  font-size: 0.85rem;
}

.error-banner button {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: #721c24;
}

.loading,
.empty {
  padding: 2rem;
  text-align: center;
  color: #6c757d;
}

.panel-content {
  display: grid;
  grid-template-columns: 280px 1fr;
  min-height: 400px;
}

.variant-list {
  border-right: 1px solid #dee2e6;
  overflow-y: auto;
  max-height: 500px;
}

.variant-item {
  padding: 0.75rem;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: background 0.15s;
}

.variant-item:hover {
  background: #f8f9fa;
}

.variant-item.selected {
  background: #e7f1ff;
  border-left: 3px solid #0066cc;
}

.variant-item.promoted {
  background: #d4edda;
}

.variant-item.promoted.selected {
  background: #c3e6cb;
  border-left-color: #28a745;
}

.variant-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.kind-badge {
  font-size: 0.7rem;
  padding: 0.1rem 0.35rem;
  background: #e9ecef;
  border-radius: 3px;
  text-transform: uppercase;
}

.filename {
  font-size: 0.85rem;
  font-family: monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.variant-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.promoted-badge {
  font-size: 0.7rem;
  padding: 0.1rem 0.35rem;
  background: #28a745;
  color: #fff;
  border-radius: 3px;
}

.variant-detail {
  padding: 1rem;
  overflow-y: auto;
}

.detail-header {
  margin-bottom: 1rem;
}

.detail-header h4 {
  margin: 0 0 0.25rem 0;
  font-size: 1rem;
}

.advisory-id {
  font-size: 0.75rem;
  color: #6c757d;
  font-family: monospace;
}

.preview-section {
  margin-bottom: 1rem;
}

.loading-svg {
  padding: 2rem;
  text-align: center;
  color: #6c757d;
  background: #f8f9fa;
  border-radius: 6px;
}

.review-form {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 6px;
}

.form-group {
  margin-bottom: 0.75rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.25rem;
  font-size: 0.85rem;
  font-weight: 500;
  color: #495057;
}

.form-group textarea {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.9rem;
  resize: vertical;
}

.form-group textarea:focus {
  outline: none;
  border-color: #0066cc;
  box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.15);
}

.previous-review {
  margin-bottom: 0.75rem;
  font-size: 0.8rem;
  color: #6c757d;
}

.form-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.btn {
  padding: 0.4rem 0.75rem;
  font-size: 0.85rem;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
}

.btn:hover:not(:disabled) {
  background: #e9ecef;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
}

.btn-primary {
  background: #0066cc;
  border-color: #0066cc;
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: #0052a3;
}

.btn-success {
  background: #28a745;
  border-color: #28a745;
  color: #fff;
}

.btn-success:hover:not(:disabled) {
  background: #218838;
}

.promoted-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: #155724;
}

.promoted-label {
  font-weight: 500;
}

.promoted-info code {
  background: #d4edda;
  padding: 0.15rem 0.4rem;
  border-radius: 3px;
  font-size: 0.8rem;
}

.no-selection {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6c757d;
  font-size: 0.9rem;
}
</style>
