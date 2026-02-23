<template>
  <div class="wf-panel">
    <!-- Header -->
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

    <!-- Log Viewer split pane drawer -->
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

    <!-- Workflow Actions -->
    <WorkflowActionsBar
      :busy="busy"
      :has-session="hasSession"
      :can-intent="canIntent"
      @ensure="ensure"
      @to-review="toReview"
      @approve="approve"
      @reject="reject"
      @reopen="reopen"
      @intent="intent"
      @promote-to-cam="promoteToCam"
    />

    <!-- Download Overrides -->
    <DownloadOverridesPanel
      :tool-id="overrides.toolId.value"
      :material-id="overrides.materialId.value"
      :machine-profile-id="overrides.machineProfileId.value"
      :cam-profile-id="overrides.camProfileId.value"
      :risk-tolerance="overrides.riskTolerance.value"
      @update:tool-id="overrides.toolId.value = $event"
      @update:material-id="overrides.materialId.value = $event"
      @update:machine-profile-id="overrides.machineProfileId.value = $event"
      @update:cam-profile-id="overrides.camProfileId.value = $event"
      @update:risk-tolerance="overrides.riskTolerance.value = $event"
      @clear="handleClearOverrides"
    />

    <!-- Export URL Preview -->
    <ExportUrlPreview
      v-if="hasSession"
      :export-url="exportUrlPreview"
      @copy-url="copyExportUrl"
      @copy-powershell="copyExportPowerShell"
      @copy-python="copyExportPython"
      @copy-node="copyExportNode"
      @copy-gha-step="copyExportGitHubActionsStep"
      @copy-gha-job="copyExportGitHubActionsJob"
      @copy-gha-workflow="copyExportGitHubActionsWorkflow"
      @copy-gha-workflow-file="copyGitHubActionsWorkflowFile"
    />

    <!-- Error -->
    <div
      v-if="err"
      class="wf-error"
    >
      {{ err }}
    </div>

    <!-- History -->
    <WorkflowHistoryPanel :history="session?.history" />

    <!-- Intent Preview -->
    <IntentPreviewPanel
      :intent="lastIntent"
      @copy-json="copyIntent"
      @copy-session-id="copySessionId"
      @copy-curl="copyIntentCurl"
      @open-logs="openInLogViewer"
      @download="downloadIntent"
      @clear="clearIntent"
    />

    <!-- Session Picker -->
    <WorkflowSessionPicker />
  </div>
</template>

<script setup lang="ts">
/**
 * DesignFirstWorkflowPanel.vue
 *
 * Orchestrator component for design-first workflow management.
 * Delegates to child components and composables for specific concerns.
 *
 * Child Components:
 * - WorkflowActionsBar: Workflow state transition buttons
 * - DownloadOverridesPanel: Export override dropdowns
 * - ExportUrlPreview: Export URL with copy buttons
 * - WorkflowHistoryPanel: State transition history
 * - IntentPreviewPanel: Last intent JSON preview
 *
 * Composables:
 * - useWorkflowActions: Workflow state and transitions
 * - useLogDrawer: Log viewer drawer state
 * - useWorkflowOverrides: Override state with localStorage
 * - useClipboardExport: Code snippet builders
 * - useCamPromotion: CAM promotion request
 */
import { onMounted } from 'vue'
import { useToastStore } from '@/stores/toastStore'

// Child components
import SideDrawer from '@/components/ui/SideDrawer.vue'
import WorkflowSessionPicker from '@/components/rosette/WorkflowSessionPicker.vue'
import WorkflowActionsBar from './WorkflowActionsBar.vue'
import DownloadOverridesPanel from './DownloadOverridesPanel.vue'
import ExportUrlPreview from './ExportUrlPreview.vue'
import WorkflowHistoryPanel from './WorkflowHistoryPanel.vue'
import IntentPreviewPanel from './IntentPreviewPanel.vue'

// Composables
import {
  useWorkflowActions,
  useLogDrawer,
  useWorkflowOverrides,
  useClipboardExport,
  useCamPromotion
} from './composables'

const toast = useToastStore()

// Workflow state and actions
const {
  session,
  state,
  busy,
  err,
  hasSession,
  canIntent,
  lastIntent,
  sessionId,
  ensure,
  toReview,
  approve,
  reject,
  reopen,
  intent,
  clearIntent,
  hydrateFromLocalStorage
} = useWorkflowActions()

// Log drawer
const logDrawer = useLogDrawer(() => sessionId.value || '')

// Workflow overrides with localStorage persistence
const overrides = useWorkflowOverrides(
  () => (session.value?.mode as string) ?? 'design_first',
  (mode) => toast.info(`Loaded export overrides for mode: ${mode}`)
)

// Clipboard export with URL building
const clipboard = useClipboardExport(
  () => sessionId.value,
  () => lastIntent.value,
  overrides,
  toast
)

// CAM promotion
const { promoteToCam } = useCamPromotion(
  () => sessionId.value,
  clipboard.getApiBaseUrl,
  () => overrides.camProfileId.value
)

// Convenience aliases
const exportUrlPreview = clipboard.exportUrlPreview
const {
  copyIntent,
  copySessionId,
  copyIntentCurl,
  copyExportUrl,
  copyExportPowerShell,
  copyExportPython,
  copyExportNode,
  copyExportGitHubActionsStep,
  copyExportGitHubActionsJob,
  copyExportGitHubActionsWorkflow,
  copyGitHubActionsWorkflowFile,
  downloadIntent
} = clipboard

// Lifecycle
onMounted(() => {
  hydrateFromLocalStorage()
  overrides.hydrateOverrides()
})

// Handlers
function handleClearOverrides(): void {
  overrides.clearOverrides()
  toast.info('Download overrides cleared')
}

function openInLogViewer(): void {
  const sid = sessionId.value
  if (!sid) return
  logDrawer.openDrawer(sid)
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

.wf-error {
  color: #b00020;
  font-size: 12px;
  margin-top: 8px;
}

.log-iframe {
  flex: 1;
  width: 100%;
  border: none;
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

.btn.ghost {
  background: transparent;
}

.btn.ghost.active {
  background: rgba(0, 0, 0, 0.08);
}
</style>
