<script setup lang="ts">
/**
 * EvidenceReviewPanel
 *
 * Dev Order 76: Measurement Lab evidence review workspace
 *
 * Displays and captures observational evidence reviews for
 * Measurement Lab records. Reviews allow records to be grouped,
 * inspected, flagged, and comparatively reviewed.
 *
 * OBSERVATIONAL ONLY:
 * - Reviews are workflow annotations only
 * - Reviews do NOT establish authority
 * - Reviews do NOT validate or approve
 * - Reviews do NOT canonize or certify
 */

import { ref, computed } from 'vue'
import type {
  EvidenceReviewRecord,
  EvidenceReviewTargetType,
  EvidenceReviewState,
} from '@/types/acoustics/evidenceReview'
import {
  VALID_REVIEW_TARGET_TYPES,
  VALID_REVIEW_STATES,
  createEvidenceReview,
  filterReviewsByTarget,
  filterReviewsByState,
  summarizeReviewsByState,
  getTargetTypeLabel,
  getReviewStateLabel,
} from '@/utils/acoustics/evidenceReview'

const reviews = ref<EvidenceReviewRecord[]>([])

const selectedTargetTypeFilter = ref<EvidenceReviewTargetType | 'all'>('all')
const selectedStateFilter = ref<EvidenceReviewState | 'all'>('all')

const showAddForm = ref(false)
const newReviewTargetType = ref<EvidenceReviewTargetType>('archive')
const newReviewTargetId = ref('')
const newReviewState = ref<EvidenceReviewState>('reviewed')
const newReviewNotes = ref('')
const newReviewTags = ref('')
const addError = ref<string | null>(null)

const filteredReviews = computed<EvidenceReviewRecord[]>(() => {
  let result = reviews.value

  if (selectedTargetTypeFilter.value !== 'all') {
    result = filterReviewsByTarget(result, selectedTargetTypeFilter.value)
  }

  if (selectedStateFilter.value !== 'all') {
    result = filterReviewsByState(result, selectedStateFilter.value)
  }

  return result
})

const stateSummaries = computed(() => summarizeReviewsByState(reviews.value))

const isEmpty = computed(() => reviews.value.length === 0)

function handleAddReview() {
  addError.value = null

  try {
    const review = createEvidenceReview({
      targetType: newReviewTargetType.value,
      targetId: newReviewTargetId.value,
      reviewState: newReviewState.value,
      notes: newReviewNotes.value || undefined,
      tags: newReviewTags.value || undefined,
    })

    reviews.value = [review, ...reviews.value]

    newReviewTargetId.value = ''
    newReviewNotes.value = ''
    newReviewTags.value = ''
    showAddForm.value = false
  } catch (err) {
    addError.value = err instanceof Error ? err.message : 'Failed to create review'
  }
}

function handleCancelAdd() {
  showAddForm.value = false
  newReviewTargetId.value = ''
  newReviewNotes.value = ''
  newReviewTags.value = ''
  addError.value = null
}

function formatTimestamp(iso: string): string {
  try {
    const date = new Date(iso)
    return date.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}
</script>

<template>
  <div class="review-panel">
    <header class="review-header">
      <h3>Evidence Review Workspace</h3>
      <p class="review-subtitle">
        Observational workflow annotations for Measurement Lab records
      </p>
    </header>

    <!-- State summary badges -->
    <div v-if="stateSummaries.length > 0" class="review-summary">
      <span
        v-for="summary in stateSummaries"
        :key="summary.groupKey"
        class="summary-badge"
        :class="{ active: selectedStateFilter === summary.groupKey }"
        @click="selectedStateFilter = summary.groupKey as EvidenceReviewState"
      >
        {{ summary.groupLabel }}: {{ summary.reviewCount }}
      </span>
      <span
        class="summary-badge"
        :class="{ active: selectedStateFilter === 'all' }"
        @click="selectedStateFilter = 'all'"
      >
        All: {{ reviews.length }}
      </span>
    </div>

    <!-- Filters -->
    <div v-if="reviews.length > 0" class="review-filters">
      <label class="filter-label">
        Target Type
        <select v-model="selectedTargetTypeFilter" class="filter-select">
          <option value="all">All Types</option>
          <option v-for="tt in VALID_REVIEW_TARGET_TYPES" :key="tt" :value="tt">
            {{ getTargetTypeLabel(tt) }}
          </option>
        </select>
      </label>

      <label class="filter-label">
        Review State
        <select v-model="selectedStateFilter" class="filter-select">
          <option value="all">All States</option>
          <option v-for="state in VALID_REVIEW_STATES" :key="state" :value="state">
            {{ getReviewStateLabel(state) }}
          </option>
        </select>
      </label>
    </div>

    <!-- Add review form -->
    <div v-if="showAddForm" class="add-form">
      <div class="form-row">
        <label class="form-label">
          Target Type
          <select v-model="newReviewTargetType" class="form-select">
            <option v-for="tt in VALID_REVIEW_TARGET_TYPES" :key="tt" :value="tt">
              {{ getTargetTypeLabel(tt) }}
            </option>
          </select>
        </label>

        <label class="form-label">
          Target ID
          <input
            v-model="newReviewTargetId"
            type="text"
            class="form-input"
            placeholder="e.g., archive-001"
          />
        </label>
      </div>

      <div class="form-row">
        <label class="form-label">
          Review State
          <select v-model="newReviewState" class="form-select">
            <option v-for="state in VALID_REVIEW_STATES" :key="state" :value="state">
              {{ getReviewStateLabel(state) }}
            </option>
          </select>
        </label>
      </div>

      <label class="form-label">
        Notes (optional)
        <textarea
          v-model="newReviewNotes"
          class="form-textarea"
          placeholder="Enter review notes..."
          rows="2"
        />
      </label>

      <label class="form-label">
        Tags (comma-separated, optional)
        <input
          v-model="newReviewTags"
          type="text"
          class="form-input"
          placeholder="e.g., stable, consistent"
        />
      </label>

      <div v-if="addError" class="form-error">{{ addError }}</div>

      <div class="form-actions">
        <button class="btn-secondary" @click="handleCancelAdd">Cancel</button>
        <button class="btn-primary" @click="handleAddReview">Add Review</button>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else-if="isEmpty" class="review-empty">
      <span class="empty-icon">📋</span>
      <p>No evidence reviews yet.</p>
      <button class="btn-add" @click="showAddForm = true">Add Review</button>
    </div>

    <!-- Reviews list -->
    <template v-else>
      <button v-if="!showAddForm" class="btn-add-inline" @click="showAddForm = true">
        + Add Review
      </button>

      <div class="review-list">
        <div v-for="review in filteredReviews" :key="review.reviewId" class="review-card">
          <div class="review-card-header">
            <span class="review-state-badge">
              {{ getReviewStateLabel(review.reviewState) }}
            </span>
            <span class="review-target-type">
              {{ getTargetTypeLabel(review.targetType) }}
            </span>
            <span class="review-target-id">{{ review.targetId }}</span>
            <span class="review-timestamp">{{ formatTimestamp(review.createdAt) }}</span>
          </div>

          <p v-if="review.notes" class="review-notes">{{ review.notes }}</p>

          <div v-if="review.tags && review.tags.length > 0" class="review-tags">
            <span v-for="tag in review.tags" :key="tag" class="review-tag">{{ tag }}</span>
          </div>
        </div>
      </div>

      <div v-if="filteredReviews.length === 0" class="review-no-match">
        No reviews match the current filters.
      </div>
    </template>

    <footer class="review-footer">
      <p class="review-disclaimer">
        Evidence reviews are observational workflow annotations and do not establish acoustic authority, validation, or canonical status.
      </p>
    </footer>
  </div>
</template>

<style scoped>
.review-panel {
  padding: 1rem;
  background: var(--color-background-soft, #0d1117);
  border: 1px solid var(--color-border, #30363d);
  border-radius: 8px;
}

.review-header h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1.125rem;
  color: var(--color-text, #f9fafb);
}

.review-subtitle {
  margin: 0 0 1rem 0;
  color: var(--color-text-muted, #8b949e);
  font-size: 0.8125rem;
}

.review-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.summary-badge {
  padding: 0.25rem 0.5rem;
  background: var(--color-background, #1f2937);
  border: 1px solid var(--color-border, #30363d);
  border-radius: 12px;
  font-size: 0.75rem;
  color: var(--color-text-muted, #8b949e);
  cursor: pointer;
  transition: all 0.15s ease;
}

.summary-badge:hover {
  border-color: var(--color-text-muted, #8b949e);
  color: var(--color-text, #f9fafb);
}

.summary-badge.active {
  background: var(--color-background, #374151);
  border-color: var(--color-text-muted, #8b949e);
  color: var(--color-text, #f9fafb);
}

.review-filters {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.filter-label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: var(--color-text-muted, #8b949e);
}

.filter-select {
  padding: 0.375rem 0.5rem;
  background: var(--color-background, #1f2937);
  border: 1px solid var(--color-border, #30363d);
  border-radius: 4px;
  font-size: 0.8125rem;
  color: var(--color-text, #f9fafb);
}

.add-form {
  padding: 1rem;
  background: var(--color-background, #1f2937);
  border: 1px solid var(--color-border, #30363d);
  border-radius: 6px;
  margin-bottom: 1rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.form-label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: var(--color-text-muted, #8b949e);
  margin-bottom: 0.75rem;
}

.form-select,
.form-input,
.form-textarea {
  padding: 0.5rem;
  background: var(--color-background-soft, #0d1117);
  border: 1px solid var(--color-border, #30363d);
  border-radius: 4px;
  font-size: 0.875rem;
  color: var(--color-text, #f9fafb);
}

.form-select:focus,
.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: var(--color-text-muted, #8b949e);
}

.form-textarea {
  resize: vertical;
  min-height: 50px;
}

.form-error {
  padding: 0.5rem;
  background: var(--color-error-bg, rgba(248, 81, 73, 0.1));
  border: 1px solid var(--color-error, #f85149);
  border-radius: 4px;
  color: var(--color-error, #f85149);
  font-size: 0.8125rem;
  margin-bottom: 0.75rem;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.btn-primary,
.btn-secondary {
  padding: 0.5rem 1rem;
  border-radius: 4px;
  font-size: 0.8125rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-primary {
  background: var(--color-text-muted, #6b7280);
  border: none;
  color: white;
}

.btn-primary:hover {
  background: var(--color-text, #9ca3af);
}

.btn-secondary {
  background: transparent;
  border: 1px solid var(--color-border, #30363d);
  color: var(--color-text-muted, #8b949e);
}

.btn-secondary:hover {
  border-color: var(--color-text-muted, #8b949e);
  color: var(--color-text, #f9fafb);
}

.btn-add,
.btn-add-inline {
  padding: 0.5rem 1rem;
  background: transparent;
  border: 1px dashed var(--color-border, #30363d);
  border-radius: 4px;
  color: var(--color-text-muted, #8b949e);
  font-size: 0.8125rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-add:hover,
.btn-add-inline:hover {
  border-color: var(--color-text-muted, #8b949e);
  color: var(--color-text, #f9fafb);
  background: rgba(107, 114, 128, 0.08);
}

.btn-add-inline {
  margin-bottom: 0.75rem;
}

.review-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  text-align: center;
}

.empty-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.review-empty p {
  margin: 0 0 1rem 0;
  color: var(--color-text-muted, #8b949e);
  font-size: 0.875rem;
}

.review-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.review-card {
  padding: 0.75rem;
  background: var(--color-background, #1f2937);
  border: 1px solid var(--color-border, #30363d);
  border-radius: 4px;
}

.review-card-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;
}

.review-state-badge {
  padding: 0.125rem 0.375rem;
  background: var(--color-background-soft, #374151);
  border-radius: 4px;
  font-size: 0.6875rem;
  color: var(--color-text, #f9fafb);
  font-weight: 500;
}

.review-target-type {
  font-size: 0.75rem;
  color: var(--color-text-muted, #8b949e);
}

.review-target-id {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-text, #f9fafb);
}

.review-timestamp {
  margin-left: auto;
  font-size: 0.6875rem;
  color: var(--color-text-muted, #6b7280);
}

.review-notes {
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
  color: var(--color-text, #f9fafb);
  line-height: 1.5;
  white-space: pre-wrap;
}

.review-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.review-tag {
  padding: 0.125rem 0.375rem;
  background: var(--color-background-soft, #0d1117);
  border-radius: 4px;
  font-size: 0.6875rem;
  color: var(--color-text-muted, #8b949e);
}

.review-no-match {
  padding: 1rem;
  text-align: center;
  color: var(--color-text-muted, #8b949e);
  font-size: 0.875rem;
}

.review-footer {
  margin-top: 1rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--color-border, #30363d);
}

.review-disclaimer {
  margin: 0;
  font-size: 0.6875rem;
  color: var(--color-text-muted, #6b7280);
  font-style: italic;
  text-align: center;
}
</style>
