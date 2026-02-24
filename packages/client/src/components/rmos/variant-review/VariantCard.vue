<script setup lang="ts">
/**
 * VariantCard - Single advisory variant card for review
 * Extracted from VariantReviewPanel.vue
 */
import StarRating from "@/components/rmos/StarRating.vue";
import SvgPreview from "@/components/rmos/SvgPreview.vue";

export type Variant = {
  advisory_id: string;
  mime: string;
  filename: string;
  size_bytes: number;
  preview_blocked: boolean;
  preview_block_reason?: string | null;
  rating?: number | null;
  notes?: string | null;
  promoted: boolean;
};

const props = defineProps<{
  variant: Variant;
  runId: string;
  apiBase: string;
  saving: boolean;
  promoting: boolean;
}>();

const emit = defineEmits<{
  save: [];
  promote: [];
  'update:rating': [value: number | null];
  'update:notes': [value: string | null];
}>();

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  return `${Math.round(bytes / 1024)} KB`;
}
</script>

<template>
  <div class="variant-card">
    <div class="card-header">
      <code class="advisory-id">{{ variant.advisory_id.slice(0, 12) }}...</code>
      <span class="file-info">{{ variant.filename }} - {{ formatSize(variant.size_bytes) }}</span>
    </div>

    <!-- SVG Preview -->
    <SvgPreview
      v-if="variant.mime === 'image/svg+xml'"
      :run-id="runId"
      :advisory-id="variant.advisory_id"
      :api-base="apiBase"
    />
    <div
      v-else
      class="non-svg-blob"
    >
      <span class="subtle">Non-SVG blob: {{ variant.mime }}</span>
    </div>

    <!-- Review Controls -->
    <div class="review-controls">
      <div class="rating-row">
        <label>Rating:</label>
        <StarRating
          :model-value="variant.rating"
          @update:model-value="emit('update:rating', $event)"
        />
      </div>

      <textarea
        :value="variant.notes ?? ''"
        class="notes-input"
        placeholder="Review notes..."
        rows="3"
        @input="emit('update:notes', ($event.target as HTMLTextAreaElement).value || null)"
      />

      <div class="action-row">
        <button
          class="btn"
          :disabled="saving"
          @click="emit('save')"
        >
          {{ saving ? "Saving..." : "Save Review" }}
        </button>

        <button
          class="btn btn-primary"
          :disabled="variant.promoted || promoting"
          @click="emit('promote')"
        >
          {{ variant.promoted ? "Promoted" : (promoting ? "Promoting..." : "Promote") }}
        </button>
      </div>

      <div
        v-if="variant.preview_blocked"
        class="preview-warning"
      >
        Preview blocked: {{ variant.preview_block_reason }}
      </div>

      <div class="download-link">
        <a
          :href="`${apiBase}/rmos/runs/${encodeURIComponent(runId)}/advisory/blobs/${encodeURIComponent(variant.advisory_id)}/download`"
          target="_blank"
          rel="noreferrer"
        >Download</a>
      </div>
    </div>
  </div>
</template>

<style scoped>
.variant-card {
  border: 1px solid #dee2e6;
  border-radius: 10px;
  padding: 1rem;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.card-header {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.advisory-id {
  font-size: 0.8rem;
  background: #e9ecef;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  display: inline-block;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.file-info {
  font-size: 0.8rem;
  color: #6c757d;
}

.non-svg-blob {
  border: 1px dashed #dee2e6;
  border-radius: 8px;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.02);
  text-align: center;
}

.review-controls {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.rating-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.rating-row label {
  font-size: 0.85rem;
  font-weight: 500;
}

.notes-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-size: 0.9rem;
  resize: vertical;
}

.notes-input:focus {
  outline: none;
  border-color: #0066cc;
  box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.15);
}

.action-row {
  display: flex;
  gap: 0.5rem;
}

.btn {
  padding: 0.4rem 0.75rem;
  font-size: 0.85rem;
  border: 1px solid #dee2e6;
  border-radius: 6px;
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

.btn-primary {
  background: #0066cc;
  border-color: #0066cc;
  color: #fff;
  font-weight: 500;
}

.btn-primary:hover:not(:disabled) {
  background: #0052a3;
}

.btn-primary:disabled {
  background: #28a745;
  border-color: #28a745;
}

.preview-warning {
  font-size: 0.8rem;
  color: #8a5a00;
  padding: 0.25rem 0.5rem;
  background: #fff3cd;
  border-radius: 4px;
}

.download-link {
  text-align: right;
}

.download-link a {
  font-size: 0.8rem;
  color: #0066cc;
}

.subtle {
  opacity: 0.7;
}
</style>
