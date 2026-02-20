<template>
  <div class="wf-panel">
    <div class="wf-header">
      <div class="wf-title">
        Design-First Workflow
      </div>
      <div
        class="wf-pill"
        :data-state="state"
      >
        {{ state || "—" }}
      </div>
    </div>

    <!-- Log Viewer split pane drawer (Bundle 32.7.4 + 32.7.5) -->
    <SideDrawer
      :open="logDrawer.isOpen.value"
      :title="logDrawer.drawerTitle.value"
      @close="logDrawer.closeDrawer"
    >
      <template #actions>
        <button
          class="btn ghost"
          :class="{ active: logDrawer.isPinned.value }"
          title="Pin to this run (keep logs stable)"
          @click="logDrawer.togglePin"
        >
          {{ logDrawer.isPinned.value ? "📌" : "📍" }}
        </button>
        <button
          class="btn ghost"
          title="Open in new tab"
          @click="logDrawer.openLogsNewTab"
        >
          ↗
        </button>
      </template>
      <iframe
        v-if="logDrawer.isOpen.value && logDrawer.logsUrl.value"
        :src="logDrawer.logsUrl.value"
        class="log-iframe"
      />
    </SideDrawer>

    <div class="wf-actions">
      <button
        :disabled="busy"
        class="btn"
        @click="ensure"
      >
        {{ hasSession ? "Restart" : "Start" }}
      </button>
      <button
        :disabled="busy || !hasSession"
        class="btn"
        @click="toReview"
      >
        Review
      </button>
      <button
        :disabled="busy || !hasSession"
        class="btn"
        @click="approve"
      >
        Approve
      </button>
      <button
        :disabled="busy || !hasSession"
        class="btn ghost"
        @click="reject"
      >
        Reject
      </button>
      <button
        :disabled="busy || !hasSession"
        class="btn ghost"
        @click="reopen"
      >
        Reopen
      </button>
      <button
        :disabled="busy || !canIntent"
        class="btn primary"
        @click="intent"
      >
        Get CAM Handoff Intent
      </button>
      <button
        :disabled="busy || !canIntent"
        class="btn"
        title="Phase 33.0: Promote to downstream CAM request (does NOT execute)"
        @click="promoteToCam"
      >
        Promote to CAM Request
      </button>
    </div>

    <!-- Download overrides (Bundle 32.8.4.2) -->
    <div class="overrides">
      <div class="ovTitle">
        Download overrides
      </div>

      <select
        v-model="overrides.toolId.value"
        class="sel"
        title="Override tool_id"
      >
        <option
          v-for="o in TOOL_OPTIONS"
          :key="o.id"
          :value="o.id"
        >
          {{ o.label }}
        </option>
      </select>

      <select
        v-model="overrides.materialId.value"
        class="sel"
        title="Override material_id"
      >
        <option
          v-for="o in MATERIAL_OPTIONS"
          :key="o.id"
          :value="o.id"
        >
          {{ o.label }}
        </option>
      </select>

      <select
        v-model="overrides.machineProfileId.value"
        class="sel"
        title="Override machine_profile_id"
      >
        <option
          v-for="o in MACHINE_OPTIONS"
          :key="o.id"
          :value="o.id"
        >
          {{ o.label }}
        </option>
      </select>

      <select
        v-model="overrides.camProfileId.value"
        class="sel"
        title="Override requested_cam_profile_id"
      >
        <option
          v-for="o in CAM_PROFILE_OPTIONS"
          :key="o.id"
          :value="o.id"
        >
          {{ o.label }}
        </option>
      </select>

      <select
        v-model="overrides.riskTolerance.value"
        class="sel"
        title="Override risk_tolerance"
      >
        <option
          v-for="o in RISK_TOLERANCE_OPTIONS"
          :key="o.id"
          :value="o.id"
        >
          {{ o.label }}
        </option>
      </select>

      <button
        class="btn ghost"
        title="Clear overrides"
        @click="handleClearOverrides"
      >
        Clear
      </button>
    </div>

    <!-- Export URL Preview (Bundle 32.8.4.5 + 32.8.4.8) -->
    <div
      v-if="hasSession"
      class="export-url-preview"
    >
      <div class="export-url-label">
        Export URL
      </div>
      <input
        type="text"
        class="export-url-input"
        :value="exportUrlPreview"
        readonly
        @click="($event.target as HTMLInputElement)?.select()"
      >
      <button
        class="btn ghost"
        title="Copy URL to clipboard"
        @click="copyExportUrl"
      >
        Copy URL
      </button>
      <button
        class="btn ghost"
        :disabled="!exportUrlPreview"
        title="Copy PowerShell Invoke-WebRequest command (downloads JSON to a file)"
        @click="copyExportPowerShell"
      >
        Copy PowerShell
      </button>
      <button
        class="btn ghost"
        :disabled="!exportUrlPreview"
        title="Copy Python requests snippet (downloads JSON to a file)"
        @click="copyExportPython"
      >
        Copy Python
      </button>
      <button
        class="btn ghost"
        :disabled="!exportUrlPreview"
        title="Copy Node 18+ fetch snippet (downloads JSON to a file)"
        @click="copyExportNode"
      >
        Copy Node
      </button>
      <button
        class="btn ghost"
        :disabled="!exportUrlPreview"
        title="Copy GitHub Actions step YAML (curl + artifact upload)"
        @click="copyExportGitHubActionsStep"
      >
        Copy GHA
      </button>
      <button
        class="btn ghost"
        :disabled="!exportUrlPreview"
        title="Copy full GitHub Actions job YAML (checkout + auth + download + upload)"
        @click="copyExportGitHubActionsJob"
      >
        Copy GHA Job
      </button>
      <button
        class="btn ghost"
        :disabled="!exportUrlPreview"
        title="Copy complete GitHub Actions workflow file (.yml)"
        @click="copyExportGitHubActionsWorkflow"
      >
        Copy GHA Workflow
      </button>
      <button
        class="btn ghost"
        :disabled="!exportUrlPreview"
        title="Copy a complete GitHub Actions workflow with filename instructions"
        @click="copyGitHubActionsWorkflowFile"
      >
        Copy GH Workflow (File-Ready)
      </button>
    </div>

    <div
      v-if="err"
      class="wf-error"
    >
      {{ err }}
    </div>

    <!-- History -->
    <div
      v-if="session?.history?.length"
      class="wf-history"
    >
      <div class="wf-history-title">
        History ({{ session.history.length }})
      </div>
      <div
        v-for="(evt, idx) in session.history.slice().reverse().slice(0, 5)"
        :key="idx"
        class="wf-event"
      >
        <span class="wf-event-action">{{ evt.action }}</span>
        <span class="wf-event-transition">
          {{ evt.from_state }} → {{ evt.to_state }}
        </span>
        <span
          v-if="evt.note"
          class="wf-event-note"
        >{{ evt.note }}</span>
      </div>
    </div>

    <!-- Last Intent Preview -->
    <div
      v-if="lastIntent"
      class="wf-intent-preview"
    >
      <div class="wf-intent-title">
        Last Promotion Intent
      </div>
      <pre class="wf-intent-json">{{ JSON.stringify(lastIntent, null, 2) }}</pre>
      <div class="wf-intent-actions">
        <button
          class="btn ghost"
          @click="copyIntent"
        >
          Copy JSON
        </button>
        <button
          class="btn ghost"
          @click="copySessionId"
        >
          Copy Session ID
        </button>
        <button
          class="btn ghost"
          title="Copy cURL for promotion intent"
          @click="copyIntentCurl"
        >
          Copy cURL
        </button>
        <button
          class="btn ghost"
          title="Open Log Viewer filtered to this run"
          @click="openInLogViewer"
        >
          Open logs
        </button>
        <button
          class="btn ghost"
          title="Download intent as JSON file"
          @click="downloadIntent"
        >
          Download intent
        </button>
        <button
          class="btn ghost"
          @click="clearIntent"
        >
          Clear
        </button>
      </div>
    </div>

    <!-- Session Picker (Bundle 32.7.7) -->
    <WorkflowSessionPicker />
  </div>
</template>

<script setup lang="ts">
/**
 * DesignFirstWorkflowPanel.vue (Phase 32.0 — Promotion Intent Export Contract)
 *
 * UI panel for managing design-first workflow state.
 * Displays workflow state, history, and promotion intent.
 *
 * REFACTORED: Now uses composables for cleaner separation of concerns:
 * - useLogDrawer: Log viewer drawer state and actions
 * - useWorkflowOverrides: Override state with localStorage persistence
 * - useExportSnippets: Code snippet builders (PowerShell, Python, Node, GHA)
 */
import { computed, onMounted } from "vue";
import { useArtDesignFirstWorkflowStore } from "@/stores/artDesignFirstWorkflowStore";
import { useToastStore } from "@/stores/toastStore";
import SideDrawer from "@/components/ui/SideDrawer.vue";
import WorkflowSessionPicker from "@/components/rosette/WorkflowSessionPicker.vue";

// Composables
import { useLogDrawer } from "./composables/useLogDrawer";
import {
  useWorkflowOverrides,
  TOOL_OPTIONS,
  MATERIAL_OPTIONS,
  MACHINE_OPTIONS,
  CAM_PROFILE_OPTIONS,
  RISK_TOLERANCE_OPTIONS,
} from "./composables/useWorkflowOverrides";
import { useClipboardExport } from "./composables/useClipboardExport";

// ==========================================================================
// Store + Toast
// ==========================================================================

const wf = useArtDesignFirstWorkflowStore();
const toast = useToastStore();

// ==========================================================================
// Computed state from store
// ==========================================================================

const session = computed(() => wf.session);
const state = computed(() => wf.stateName);
const busy = computed(() => wf.loading);
const err = computed(() => wf.error);
const hasSession = computed(() => wf.hasSession);
const canIntent = computed(() => wf.canRequestIntent);
const lastIntent = computed(() => wf.lastPromotionIntent);

// ==========================================================================
// Composables
// ==========================================================================

// Log drawer
const logDrawer = useLogDrawer(() => wf.sessionId || "");

// Workflow overrides with localStorage persistence
const overrides = useWorkflowOverrides(
  () => (wf.session?.mode as string) ?? "design_first",
  (mode) => toast.info(`Loaded export overrides for mode: ${mode}`)
);

// Clipboard export with URL building
const clipboard = useClipboardExport(
  () => wf.sessionId,
  () => wf.lastPromotionIntent,
  overrides,
  toast
);

// Convenience aliases
const exportUrlPreview = clipboard.exportUrlPreview;
const getApiBaseUrl = clipboard.getApiBaseUrl;

// ==========================================================================
// Lifecycle
// ==========================================================================

onMounted(() => {
  wf.hydrateFromLocalStorage();
  overrides.hydrateOverrides();
});

// ==========================================================================
// Workflow actions
// ==========================================================================

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

// ==========================================================================
// Phase 33.0: Promote to CAM Request
// ==========================================================================

async function promoteToCam() {
  const sid = wf.sessionId;
  if (!sid) {
    toast.error("No session available");
    return;
  }

  try {
    const base = getApiBaseUrl();
    const camProfileId = overrides.camProfileId.value || undefined;
    const params = new URLSearchParams();
    if (camProfileId) params.set("cam_profile_id", camProfileId);

    const url = `${base}/art/design-first-workflow/sessions/${encodeURIComponent(sid)}/promote_to_cam${params.toString() ? "?" + params.toString() : ""}`;

    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    if (!resp.ok) {
      const errData = await resp.json().catch(() => ({}));
      toast.error(`Promotion failed: ${errData.detail || resp.statusText}`);
      return;
    }

    const data = await resp.json();

    if (!data.ok) {
      toast.warning(`Promotion blocked: ${data.blocked_reason || "unknown"}`);
      return;
    }

    const requestId = data.request?.promotion_request_id;
    toast.success(`CAM promotion request created: ${requestId?.slice(0, 8) || "OK"}…`);
    console.log("[ArtStudio] CAM promotion request:", data.request);
  } catch (e: any) {
    toast.error(`Promotion error: ${e.message || e}`);
  }
}

// ==========================================================================
// Clipboard actions (delegated to composable)
// ==========================================================================

const copyIntent = clipboard.copyIntent;
const copySessionId = clipboard.copySessionId;
const copyIntentCurl = clipboard.copyIntentCurl;
const copyExportUrl = clipboard.copyExportUrl;
const copyExportPowerShell = clipboard.copyExportPowerShell;
const copyExportPython = clipboard.copyExportPython;
const copyExportNode = clipboard.copyExportNode;
const copyExportGitHubActionsStep = clipboard.copyExportGitHubActionsStep;
const copyExportGitHubActionsJob = clipboard.copyExportGitHubActionsJob;
const copyExportGitHubActionsWorkflow = clipboard.copyExportGitHubActionsWorkflow;
const copyGitHubActionsWorkflowFile = clipboard.copyGitHubActionsWorkflowFile;

// ==========================================================================
// Override + Intent actions
// ==========================================================================

function handleClearOverrides() {
  overrides.clearOverrides();
  toast.info("Download overrides cleared");
}

function clearIntent() {
  wf.clearSession();
  toast.info("Session cleared");
}

function openInLogViewer() {
  const sid = wf.sessionId;
  if (!sid) return;
  logDrawer.openDrawer(sid);
}

const downloadIntent = clipboard.downloadIntent;
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
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.wf-intent-actions .btn {
  font-size: 11px;
  padding: 4px 8px;
}

.log-iframe {
  flex: 1;
  width: 100%;
  border: none;
}

.overrides {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.export-url-preview {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.export-url-label {
  font-size: 12px;
  font-weight: 700;
  opacity: 0.85;
}

.export-url-input {
  flex: 1;
  min-width: 200px;
  border: 1px solid rgba(0, 0, 0, 0.16);
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 11px;
  font-family: monospace;
  background: rgba(0, 0, 0, 0.02);
  color: #333;
}

.ovTitle {
  font-size: 12px;
  font-weight: 800;
  opacity: 0.85;
  margin-right: 4px;
}

.sel {
  border: 1px solid rgba(0, 0, 0, 0.16);
  border-radius: 10px;
  padding: 6px 8px;
  font-size: 12px;
  background: white;
}
</style>
