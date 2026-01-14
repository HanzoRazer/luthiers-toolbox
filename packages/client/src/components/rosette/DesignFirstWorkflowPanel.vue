<template>
  <div class="wf-panel">
    <div class="wf-header">
      <div class="wf-title">Design-First Workflow</div>
      <div class="wf-pill" :data-state="state">{{ state || "—" }}</div>
    </div>

    <div class="wf-actions">
      <button :disabled="busy" @click="ensure" class="btn">
        {{ hasSession ? "Restart" : "Start" }}
      </button>
      <button :disabled="busy || !hasSession" @click="toReview" class="btn">
        Review
      </button>
      <button :disabled="busy || !hasSession" @click="approve" class="btn">
        Approve
      </button>
      <button :disabled="busy || !hasSession" @click="reject" class="btn ghost">
        Reject
      </button>
      <button :disabled="busy || !hasSession" @click="reopen" class="btn ghost">
        Reopen
      </button>
      <button
        :disabled="busy || !canIntent"
        @click="intent"
        class="btn primary"
      >
        Get CAM Handoff Intent
      </button>
    </div>

    <div v-if="err" class="wf-error">{{ err }}</div>

    <!-- History -->
    <div v-if="session?.history?.length" class="wf-history">
      <div class="wf-history-title">History ({{ session.history.length }})</div>
      <div
        v-for="(evt, idx) in session.history.slice().reverse().slice(0, 5)"
        :key="idx"
        class="wf-event"
      >
        <span class="wf-event-action">{{ evt.action }}</span>
        <span class="wf-event-transition">
          {{ evt.from_state }} → {{ evt.to_state }}
        </span>
        <span v-if="evt.note" class="wf-event-note">{{ evt.note }}</span>
      </div>
    </div>

    <!-- Last Intent Preview -->
    <div v-if="lastIntent" class="wf-intent-preview">
      <div class="wf-intent-title">Last Promotion Intent</div>
      <pre class="wf-intent-json">{{ JSON.stringify(lastIntent, null, 2) }}</pre>
      <div class="wf-intent-actions">
        <button class="btn ghost" @click="copyIntent">Copy JSON</button>
        <button class="btn ghost" @click="copySessionId">Copy Session ID</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * DesignFirstWorkflowPanel.vue (Bundle 32.7.0)
 *
 * UI panel for managing design-first workflow state.
 * Displays workflow state, history, and promotion intent.
 */
import { computed } from "vue";
import { useArtDesignFirstWorkflowStore } from "@/stores/artDesignFirstWorkflowStore";
import { useToastStore } from "@/stores/toastStore";

const wf = useArtDesignFirstWorkflowStore();
const toast = useToastStore();

const session = computed(() => wf.session);
const state = computed(() => wf.stateName);
const busy = computed(() => wf.loading);
const err = computed(() => wf.error);
const hasSession = computed(() => wf.hasSession);
const canIntent = computed(() => wf.canRequestIntent);
const lastIntent = computed(() => wf.lastPromotionIntent);

async function ensure() {
  if (wf.hasSession) {
    wf.clearSession();
  }
  await wf.ensureSessionDesignFirst();
}

async function toReview() {
  if (!wf.hasSession) {
    await wf.ensureSessionDesignFirst();
  }
  await wf.transition("in_review");
}

async function approve() {
  await wf.transition("approved");
}

async function reject() {
  await wf.transition("rejected", "Design needs revision");
}

async function reopen() {
  await wf.transition("draft");
}

async function intent() {
  const payload = await wf.requestPromotionIntent();
  if (payload) {
    toast.info("Intent payload ready. Use Log Viewer / CAM lane to consume.");
    console.log("[ArtStudio] CAM handoff intent:", payload);
  }
}

async function copyIntent() {
  if (!lastIntent.value) return;
  try {
    await navigator.clipboard.writeText(JSON.stringify(lastIntent.value, null, 2));
    toast.success("Intent JSON copied to clipboard");
  } catch {
    toast.error("Failed to copy to clipboard");
  }
}

async function copySessionId() {
  const sid = wf.sessionId;
  if (!sid) return;
  try {
    await navigator.clipboard.writeText(sid);
    toast.success("Session ID copied to clipboard");
  } catch {
    toast.error("Failed to copy to clipboard");
  }
}
</script>

<style scoped>
.wf-panel {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 12px;
  padding: 12px;
  margin: 10px 0;
  background: #fff;
}

.wf-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.wf-title {
  font-weight: 700;
  font-size: 14px;
}

.wf-pill {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 999px;
  border: 1px solid rgba(0, 0, 0, 0.15);
  text-transform: uppercase;
  font-weight: 600;
}

.wf-pill[data-state="draft"] {
  background: rgba(100, 100, 100, 0.08);
}
.wf-pill[data-state="in_review"] {
  background: rgba(200, 160, 0, 0.12);
  border-color: rgba(200, 160, 0, 0.35);
}
.wf-pill[data-state="approved"] {
  background: rgba(0, 180, 0, 0.12);
  border-color: rgba(0, 180, 0, 0.35);
}
.wf-pill[data-state="rejected"] {
  background: rgba(200, 0, 0, 0.12);
  border-color: rgba(200, 0, 0, 0.35);
}

.wf-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.btn {
  border: 1px solid rgba(0, 0, 0, 0.18);
  border-radius: 10px;
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
  background: #fff;
  transition: background 0.1s;
}

.btn:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.04);
}

.btn:disabled {
  opacity: 0.5;
  cursor: default;
}

.btn.primary {
  background: rgba(0, 0, 0, 0.06);
  font-weight: 600;
}

.btn.ghost {
  background: transparent;
}

.wf-error {
  color: #b00020;
  font-size: 12px;
  margin-top: 8px;
}

.wf-history {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.wf-history-title {
  font-size: 11px;
  font-weight: 600;
  opacity: 0.7;
  margin-bottom: 6px;
}

.wf-event {
  font-size: 11px;
  padding: 4px 0;
  display: flex;
  gap: 8px;
  align-items: center;
}

.wf-event-action {
  font-weight: 600;
}

.wf-event-transition {
  opacity: 0.7;
}

.wf-event-note {
  font-style: italic;
  opacity: 0.6;
}

.wf-intent-preview {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.wf-intent-title {
  font-size: 11px;
  font-weight: 600;
  opacity: 0.7;
  margin-bottom: 6px;
}

.wf-intent-json {
  background: rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 8px;
  padding: 8px;
  font-size: 10px;
  overflow-x: auto;
  max-height: 200px;
  overflow-y: auto;
}

.wf-intent-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}
</style>
