<template>
  <div class="session-panel">
    <header class="session-header">
      <h2>Experimental Sessions</h2>
      <button
        class="btn-create"
        @click="showCreateForm = !showCreateForm"
      >
        {{ showCreateForm ? 'Cancel' : '+ New Session' }}
      </button>
    </header>

    <form
      v-if="showCreateForm"
      class="create-form"
      @submit.prevent="handleCreateSession"
    >
      <div class="form-group">
        <label for="title">Title</label>
        <input
          id="title"
          v-model="newSession.title"
          type="text"
          required
          placeholder="e.g., Spruce vs Cedar Tap Comparison"
        />
      </div>
      <div class="form-group">
        <label for="objective">Objective (optional)</label>
        <textarea
          id="objective"
          v-model="newSession.objective"
          rows="2"
          placeholder="What are you exploring?"
        />
      </div>
      <div class="form-group">
        <label for="constraints">Constraints (optional)</label>
        <textarea
          id="constraints"
          v-model="newSession.constraints"
          rows="2"
          placeholder="e.g., Same humidity, same mallet"
        />
      </div>
      <div class="form-group">
        <label for="notes">Notes (optional)</label>
        <textarea
          id="notes"
          v-model="newSession.notes"
          rows="2"
          placeholder="Any additional context"
        />
      </div>
      <button
        type="submit"
        class="btn-submit"
        :disabled="!newSession.title.trim()"
      >
        Create Session
      </button>
    </form>

    <div
      v-if="sessions.length === 0 && !showCreateForm"
      class="empty-state"
    >
      <p>No sessions yet. Create one to group your measurement archives.</p>
    </div>

    <ul
      v-else
      class="session-list"
    >
      <li
        v-for="session in sessions"
        :key="session.sessionId"
        class="session-card"
        :class="{ selected: selectedSessionId === session.sessionId }"
        @click="selectSession(session.sessionId)"
      >
        <div class="session-card-header">
          <span class="session-title">{{ session.title }}</span>
          <span class="session-id">{{ formatSessionId(session.sessionId) }}</span>
        </div>

        <div
          v-if="session.objective"
          class="session-objective"
        >
          {{ session.objective }}
        </div>

        <div class="session-meta">
          <span class="meta-item">
            {{ session.archiveIds.length }} archive{{ session.archiveIds.length !== 1 ? 's' : '' }}
          </span>
          <span class="meta-item">
            {{ session.variantIds.length }} variant{{ session.variantIds.length !== 1 ? 's' : '' }}
          </span>
          <span class="meta-item">
            Started {{ formatDate(session.startedAt) }}
          </span>
        </div>

        <div
          v-if="selectedSessionId === session.sessionId"
          class="session-detail"
        >
          <div
            v-if="session.constraints"
            class="detail-section"
          >
            <strong>Constraints:</strong>
            {{ session.constraints }}
          </div>
          <div
            v-if="session.notes"
            class="detail-section"
          >
            <strong>Notes:</strong>
            {{ session.notes }}
          </div>

          <div
            v-if="session.archiveIds.length > 0"
            class="archive-list"
          >
            <strong>Archives (iteration order):</strong>
            <ol class="iteration-list">
              <li
                v-for="(archiveId, index) in session.archiveIds"
                :key="archiveId"
              >
                <span class="iteration-num">{{ index + 1 }}.</span>
                <span class="archive-id">{{ archiveId }}</span>
              </li>
            </ol>
          </div>

          <div
            v-if="selectedSummary"
            class="summary-section"
          >
            <strong>Date range:</strong>
            <span v-if="selectedSummary.dateRange.earliest">
              {{ formatDate(selectedSummary.dateRange.earliest) }}
              to
              {{ formatDate(selectedSummary.dateRange.latest!) }}
              ({{ selectedSummary.durationDays }} day{{ selectedSummary.durationDays !== 1 ? 's' : '' }})
            </span>
            <span v-else>No timestamps available</span>
          </div>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue';
import type {
  ExperimentalSessionRecord,
  ExperimentalSessionSummary,
} from '@/types/acoustics/experimentalSession';
import {
  createExperimentalSession,
  buildSessionSummary,
} from '@/utils/acoustics/experimentalSession';
import type { MeasurementArchiveRecord } from '@/types/acoustics/measurementArchive';

const props = defineProps<{
  archives?: Map<string, MeasurementArchiveRecord>;
}>();

const emit = defineEmits<{
  (e: 'session-created', session: ExperimentalSessionRecord): void;
  (e: 'session-selected', sessionId: string): void;
}>();

const sessions = ref<ExperimentalSessionRecord[]>([]);
const selectedSessionId = ref<string | null>(null);
const showCreateForm = ref(false);

const newSession = reactive({
  title: '',
  objective: '',
  constraints: '',
  notes: '',
});

const selectedSummary = computed<ExperimentalSessionSummary | null>(() => {
  if (!selectedSessionId.value) return null;
  const session = sessions.value.find((s) => s.sessionId === selectedSessionId.value);
  if (!session) return null;
  return buildSessionSummary(session, props.archives ?? new Map());
});

function handleCreateSession(): void {
  if (!newSession.title.trim()) return;

  const session = createExperimentalSession(newSession.title.trim(), {
    objective: newSession.objective.trim() || undefined,
    constraints: newSession.constraints.trim() || undefined,
    notes: newSession.notes.trim() || undefined,
  });

  sessions.value.unshift(session);
  selectedSessionId.value = session.sessionId;
  showCreateForm.value = false;

  newSession.title = '';
  newSession.objective = '';
  newSession.constraints = '';
  newSession.notes = '';

  emit('session-created', session);
}

function selectSession(sessionId: string): void {
  selectedSessionId.value = selectedSessionId.value === sessionId ? null : sessionId;
  if (selectedSessionId.value) {
    emit('session-selected', sessionId);
  }
}

function formatSessionId(sessionId: string): string {
  const match = sessionId.match(/experimental-session-(\d{8})-(\d{6})/);
  if (!match) return sessionId;
  return `${match[1].slice(0, 4)}-${match[1].slice(4, 6)}-${match[1].slice(6)} ${match[2].slice(0, 2)}:${match[2].slice(2, 4)}`;
}

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

defineExpose({
  sessions,
  selectedSessionId,
});
</script>

<style scoped>
.session-panel {
  padding: 1rem;
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.session-header h2 {
  margin: 0;
  font-size: 1.25rem;
}

.btn-create {
  padding: 0.5rem 1rem;
  background: var(--color-primary, #0d6efd);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.btn-create:hover {
  background: var(--color-primary-hover, #0b5ed7);
}

.create-form {
  background: var(--color-bg-secondary, #f8f9fa);
  border: 1px solid var(--color-border, #dee2e6);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.form-group {
  margin-bottom: 0.75rem;
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid var(--color-border, #dee2e6);
  border-radius: 4px;
  font-size: 0.875rem;
  font-family: inherit;
}

.form-group textarea {
  resize: vertical;
}

.btn-submit {
  padding: 0.5rem 1rem;
  background: var(--color-success, #198754);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.btn-submit:hover:not(:disabled) {
  background: var(--color-success-hover, #157347);
}

.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--color-text-muted, #6c757d);
}

.session-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.session-card {
  background: var(--color-bg-secondary, #f8f9fa);
  border: 1px solid var(--color-border, #dee2e6);
  border-radius: 8px;
  padding: 1rem;
  cursor: pointer;
  transition: border-color 0.15s;
}

.session-card:hover {
  border-color: var(--color-primary, #0d6efd);
}

.session-card.selected {
  border-color: var(--color-primary, #0d6efd);
  border-width: 2px;
}

.session-card-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.25rem;
}

.session-title {
  font-weight: 600;
  font-size: 1rem;
}

.session-id {
  font-size: 0.75rem;
  color: var(--color-text-muted, #6c757d);
  font-family: monospace;
}

.session-objective {
  font-size: 0.875rem;
  color: var(--color-text-muted, #6c757d);
  margin-bottom: 0.5rem;
}

.session-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.75rem;
  color: var(--color-text-muted, #6c757d);
}

.meta-item::before {
  content: '\2022';
  margin-right: 0.5rem;
}

.meta-item:first-child::before {
  content: '';
  margin-right: 0;
}

.session-detail {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border, #dee2e6);
}

.detail-section {
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
}

.detail-section strong {
  display: block;
  margin-bottom: 0.25rem;
}

.archive-list {
  margin-top: 0.75rem;
}

.archive-list strong {
  display: block;
  font-size: 0.875rem;
  margin-bottom: 0.25rem;
}

.iteration-list {
  margin: 0;
  padding-left: 1.25rem;
  font-size: 0.875rem;
}

.iteration-list li {
  margin-bottom: 0.125rem;
}

.iteration-num {
  color: var(--color-text-muted, #6c757d);
}

.archive-id {
  font-family: monospace;
  font-size: 0.8rem;
}

.summary-section {
  margin-top: 0.75rem;
  font-size: 0.875rem;
}

.summary-section strong {
  margin-right: 0.5rem;
}
</style>
