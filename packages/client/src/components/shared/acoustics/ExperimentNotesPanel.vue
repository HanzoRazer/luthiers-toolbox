<script setup lang="ts">
/**
 * ExperimentNotesPanel
 *
 * Dev Order 74: Measurement Lab experiment notes layer
 *
 * Displays and captures human-entered observational notes for
 * Measurement Lab records. Notes can attach to archives, topology
 * variants, drift records, correlations, and synthesis records.
 *
 * OBSERVATIONAL ONLY:
 * - Notes are local annotations only
 * - Notes do NOT modify measurements
 * - Notes do NOT establish acoustic conclusions
 * - Notes do NOT imply calibration or recommendation
 */

import { ref, computed } from 'vue'
import type {
  ExperimentNote,
  ExperimentNoteTargetType,
} from '@/types/acoustics/experimentNote'
import {
  VALID_TARGET_TYPES,
  createExperimentNote,
  filterNotesByTarget,
  summarizeExperimentNotes,
  getTargetTypeLabel,
} from '@/utils/acoustics/experimentNote'

const notes = ref<ExperimentNote[]>([])

const selectedTargetTypeFilter = ref<ExperimentNoteTargetType | 'all'>('all')

const showAddForm = ref(false)
const newNoteTargetType = ref<ExperimentNoteTargetType>('archive')
const newNoteTargetId = ref('')
const newNoteText = ref('')
const newNoteTags = ref('')
const addError = ref<string | null>(null)

const filteredNotes = computed<ExperimentNote[]>(() => {
  if (selectedTargetTypeFilter.value === 'all') {
    return notes.value
  }
  return filterNotesByTarget(notes.value, selectedTargetTypeFilter.value)
})

const summaries = computed(() => summarizeExperimentNotes(notes.value))

const isEmpty = computed(() => notes.value.length === 0)

function handleAddNote() {
  addError.value = null

  try {
    const note = createExperimentNote({
      targetType: newNoteTargetType.value,
      targetId: newNoteTargetId.value,
      text: newNoteText.value,
      tags: newNoteTags.value || undefined,
    })

    notes.value = [note, ...notes.value]

    newNoteTargetId.value = ''
    newNoteText.value = ''
    newNoteTags.value = ''
    showAddForm.value = false
  } catch (err) {
    addError.value = err instanceof Error ? err.message : 'Failed to create note'
  }
}

function handleCancelAdd() {
  showAddForm.value = false
  newNoteTargetId.value = ''
  newNoteText.value = ''
  newNoteTags.value = ''
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
  <div class="notes-panel">
    <header class="notes-header">
      <h3>Experiment Notes</h3>
      <p class="notes-subtitle">
        Local observational annotations for Measurement Lab records
      </p>
    </header>

    <!-- Summary badges -->
    <div v-if="summaries.length > 0" class="notes-summary">
      <span
        v-for="summary in summaries"
        :key="summary.targetType"
        class="summary-badge"
        :class="{ active: selectedTargetTypeFilter === summary.targetType }"
        @click="selectedTargetTypeFilter = summary.targetType"
      >
        {{ getTargetTypeLabel(summary.targetType) }}: {{ summary.noteCount }}
      </span>
      <span
        class="summary-badge"
        :class="{ active: selectedTargetTypeFilter === 'all' }"
        @click="selectedTargetTypeFilter = 'all'"
      >
        All: {{ notes.length }}
      </span>
    </div>

    <!-- Add note form -->
    <div v-if="showAddForm" class="add-form">
      <div class="form-row">
        <label class="form-label">
          Target Type
          <select v-model="newNoteTargetType" class="form-select">
            <option v-for="tt in VALID_TARGET_TYPES" :key="tt" :value="tt">
              {{ getTargetTypeLabel(tt) }}
            </option>
          </select>
        </label>

        <label class="form-label">
          Target ID
          <input
            v-model="newNoteTargetId"
            type="text"
            class="form-input"
            placeholder="e.g., archive-001"
          />
        </label>
      </div>

      <label class="form-label">
        Note
        <textarea
          v-model="newNoteText"
          class="form-textarea"
          placeholder="Enter observation..."
          rows="3"
        />
      </label>

      <label class="form-label">
        Tags (comma-separated, optional)
        <input
          v-model="newNoteTags"
          type="text"
          class="form-input"
          placeholder="e.g., helmholtz, stable"
        />
      </label>

      <div v-if="addError" class="form-error">{{ addError }}</div>

      <div class="form-actions">
        <button class="btn-secondary" @click="handleCancelAdd">Cancel</button>
        <button class="btn-primary" @click="handleAddNote">Add Note</button>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else-if="isEmpty" class="notes-empty">
      <span class="empty-icon">📝</span>
      <p>No experiment notes yet.</p>
      <button class="btn-add" @click="showAddForm = true">Add Note</button>
    </div>

    <!-- Notes list -->
    <template v-else>
      <button v-if="!showAddForm" class="btn-add-inline" @click="showAddForm = true">
        + Add Note
      </button>

      <div class="notes-list">
        <div v-for="note in filteredNotes" :key="note.noteId" class="note-card">
          <div class="note-header">
            <span class="note-target-badge">
              {{ getTargetTypeLabel(note.targetType) }}
            </span>
            <span class="note-target-id">{{ note.targetId }}</span>
            <span class="note-timestamp">{{ formatTimestamp(note.createdAt) }}</span>
          </div>

          <p class="note-text">{{ note.text }}</p>

          <div v-if="note.tags && note.tags.length > 0" class="note-tags">
            <span v-for="tag in note.tags" :key="tag" class="note-tag">{{ tag }}</span>
          </div>
        </div>
      </div>

      <div v-if="filteredNotes.length === 0" class="notes-no-match">
        No notes for {{ getTargetTypeLabel(selectedTargetTypeFilter as ExperimentNoteTargetType) }}.
      </div>
    </template>

    <footer class="notes-footer">
      <p class="notes-disclaimer">
        Notes are local observational annotations and do not modify measurements or establish acoustic conclusions.
      </p>
    </footer>
  </div>
</template>

<style scoped>
.notes-panel {
  padding: 1rem;
  background: var(--color-background-soft, #0d1117);
  border: 1px solid var(--color-border, #30363d);
  border-radius: 8px;
}

.notes-header h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1.125rem;
  color: var(--color-text, #f9fafb);
}

.notes-subtitle {
  margin: 0 0 1rem 0;
  color: var(--color-text-muted, #8b949e);
  font-size: 0.8125rem;
}

.notes-summary {
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
  border-color: var(--color-primary, #6366f1);
  color: var(--color-text, #f9fafb);
}

.summary-badge.active {
  background: var(--color-primary, #6366f1);
  border-color: var(--color-primary, #6366f1);
  color: white;
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
  border-color: var(--color-primary, #6366f1);
}

.form-textarea {
  resize: vertical;
  min-height: 60px;
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
  background: var(--color-primary, #6366f1);
  border: none;
  color: white;
}

.btn-primary:hover {
  background: var(--color-primary-hover, #4f46e5);
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
  border-color: var(--color-primary, #6366f1);
  color: var(--color-text, #f9fafb);
  background: rgba(99, 102, 241, 0.08);
}

.btn-add-inline {
  margin-bottom: 0.75rem;
}

.notes-empty {
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

.notes-empty p {
  margin: 0 0 1rem 0;
  color: var(--color-text-muted, #8b949e);
  font-size: 0.875rem;
}

.notes-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.note-card {
  padding: 0.75rem;
  background: var(--color-background, #1f2937);
  border: 1px solid var(--color-border, #30363d);
  border-radius: 4px;
}

.note-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;
}

.note-target-badge {
  padding: 0.125rem 0.375rem;
  background: var(--color-primary, #6366f1);
  border-radius: 4px;
  font-size: 0.6875rem;
  color: white;
  font-weight: 500;
}

.note-target-id {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-text, #f9fafb);
}

.note-timestamp {
  margin-left: auto;
  font-size: 0.6875rem;
  color: var(--color-text-muted, #6b7280);
}

.note-text {
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
  color: var(--color-text, #f9fafb);
  line-height: 1.5;
  white-space: pre-wrap;
}

.note-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.note-tag {
  padding: 0.125rem 0.375rem;
  background: var(--color-background-soft, #0d1117);
  border-radius: 4px;
  font-size: 0.6875rem;
  color: var(--color-text-muted, #8b949e);
}

.notes-no-match {
  padding: 1rem;
  text-align: center;
  color: var(--color-text-muted, #8b949e);
  font-size: 0.875rem;
}

.notes-footer {
  margin-top: 1rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--color-border, #30363d);
}

.notes-disclaimer {
  margin: 0;
  font-size: 0.6875rem;
  color: var(--color-text-muted, #6b7280);
  font-style: italic;
  text-align: center;
}
</style>
