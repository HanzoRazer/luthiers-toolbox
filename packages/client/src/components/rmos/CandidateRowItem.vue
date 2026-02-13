<script setup lang="ts">
/**
 * Single row for ManufacturingCandidateList.
 * Extracted from ManufacturingCandidateList.vue to reduce god file size.
 */
import CandidateDecisionHistoryPopover from "@/components/rmos/CandidateDecisionHistoryPopover.vue";
import type { ManufacturingCandidate, RiskLevel } from "@/sdk/rmos/runs";

type CandidateRow = ManufacturingCandidate & { candidate_id: string };

const props = defineProps<{
  candidate: CandidateRow;
  isSelected: boolean;
  disabled: boolean;
  isHistoryOpen: boolean;
  isEditing: boolean;
  editValue: string;
}>();

const emit = defineEmits<{
  toggle: [id: string, event: MouseEvent];
  openHistory: [id: string];
  decide: [candidate: CandidateRow, decision: RiskLevel];
  startEdit: [candidate: CandidateRow];
  saveEdit: [candidate: CandidateRow];
  cancelEdit: [];
  copy: [field: string, value: string];
  "update:editValue": [value: string];
}>();

// Helper functions
function decisionBadge(decision: RiskLevel | null | undefined) {
  if (decision == null) return "NEEDS_DECISION";
  return decision;
}

function statusText(c: CandidateRow) {
  if (c.decision == null) return "Needs decision";
  if (c.decision === "GREEN") return "Accepted";
  if (c.decision === "YELLOW") return "Caution";
  if (c.decision === "RED") return "Rejected";
  return "—";
}

function notePreview(note?: string | null) {
  const n = note ?? "";
  if (!n) return "—";
  return n.length > 120 ? n.slice(0, 120) + "…" : n;
}

function auditHover(c: CandidateRow) {
  const who = c.decided_by ?? "—";
  const when = c.decided_at_utc ?? "—";
  const note = c.decision_note ?? "";
  const preview = note ? (note.length > 80 ? note.slice(0, 80) + "…" : note) : "—";
  return `Decided by: ${who}\nDecided at: ${when}\nNote: ${preview}`;
}
</script>

<template>
  <div
    class="row clickable"
    :title="auditHover(candidate)"
    @click="emit('toggle', candidate.candidate_id, $event)"
  >
    <div class="sel">
      <input
        type="checkbox"
        :checked="isSelected"
        :disabled="disabled"
        :title="isSelected ? 'Selected' : 'Select'"
        @click.stop="emit('toggle', candidate.candidate_id, $event)"
      >
    </div>
    <div class="mono">
      {{ candidate.candidate_id }}
    </div>
    <div class="mono">
      {{ candidate.advisory_id ?? "—" }}
    </div>

    <div class="decision-cell">
      <span
        class="badge"
        :data-badge="decisionBadge(candidate.decision)"
      >
        {{ decisionBadge(candidate.decision) }}
      </span>
      <span
        v-if="candidate.decision_history && candidate.decision_history.length > 0"
        class="history-count"
        :title="`${candidate.decision_history.length} history entries`"
        @click.stop="emit('openHistory', candidate.candidate_id)"
      >
        ({{ candidate.decision_history.length }})
      </span>
    </div>

    <!-- Audit column -->
    <div
      class="audit"
      :title="(candidate.decided_by || candidate.decided_at_utc)
        ? `Decided by: ${candidate.decided_by || '—'}\nDecided at: ${candidate.decided_at_utc || '—'}\nLatest note: ${notePreview(candidate.decision_note)}`
        : 'No decision yet (decision=null) — export is blocked until explicit operator decision.'"
    >
      <div class="auditBy">
        {{ candidate.decided_by || "—" }}
      </div>
      <div class="auditAt mono">
        {{ candidate.decided_at_utc ? candidate.decided_at_utc.slice(0, 19).replace('T', ' ') : '—' }}
      </div>
    </div>

    <div class="history">
      <button
        class="btn ghost smallbtn"
        :disabled="disabled"
        @click.stop="emit('openHistory', candidate.candidate_id)"
      >
        {{ isHistoryOpen ? "Hide" : "View" }}
      </button>
      <div
        v-if="isHistoryOpen"
        class="popover"
      >
        <CandidateDecisionHistoryPopover
          :items="candidate.decision_history ?? null"
          :current-decision="candidate.decision ?? null"
          :current-note="candidate.decision_note ?? null"
          :current-by="candidate.decided_by ?? null"
          :current-at="candidate.decided_at_utc ?? null"
        />
      </div>
    </div>

    <div class="muted">
      {{ statusText(candidate) }}
    </div>

    <div class="note">
      <div
        v-if="isEditing"
        class="editor"
      >
        <textarea
          :value="editValue"
          rows="2"
          @input="emit('update:editValue', ($event.target as HTMLTextAreaElement).value)"
        />
        <div class="editor-actions">
          <button
            class="btn"
            :disabled="disabled"
            @click="emit('saveEdit', candidate)"
          >
            Save
          </button>
          <button
            class="btn ghost"
            :disabled="disabled"
            @click="emit('cancelEdit')"
          >
            Cancel
          </button>
        </div>
      </div>
      <div
        v-else
        class="note-display"
      >
        <span
          v-if="!candidate.decision_note"
          class="muted"
        >—</span>
        <span v-else>{{ notePreview(candidate.decision_note) }}</span>
      </div>
    </div>

    <div class="copyCol">
      <button
        class="btn ghost smallbtn"
        title="Copy candidate_id"
        @click.stop="emit('copy', 'candidate_id', candidate.candidate_id)"
      >
        Copy ID
      </button>
      <button
        class="btn ghost smallbtn"
        title="Copy advisory_id"
        @click.stop="emit('copy', 'advisory_id', candidate.advisory_id || '')"
      >
        Copy Adv
      </button>
    </div>

    <div class="actions">
      <button
        class="btn"
        :disabled="disabled"
        @click.stop="emit('decide', candidate, 'GREEN')"
      >
        GREEN
      </button>
      <button
        class="btn"
        :disabled="disabled"
        @click.stop="emit('decide', candidate, 'YELLOW')"
      >
        YELLOW
      </button>
      <button
        class="btn danger"
        :disabled="disabled"
        @click.stop="emit('decide', candidate, 'RED')"
      >
        RED
      </button>

      <button
        class="btn ghost"
        :disabled="disabled || candidate.decision == null"
        :title="candidate.decision == null ? 'Decide first to enable note editing' : 'Edit decision note'"
        @click.stop="emit('startEdit', candidate)"
      >
        Edit Note
      </button>
    </div>
  </div>
</template>
