<template>
  <div class="wf-panel">
    <!-- Header -->
    <WorkflowHeader :state="state" />

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
          {{ logDrawer.isPinned.value ? '📌' : '📍' }}
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

    <!-- Actions -->
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

    <!-- Download overrides -->
    <OverrideSelector
      v-model:tool-id="overrides.toolId.value"
      v-model:material-id="overrides.materialId.value"
      v-model:machine-profile-id="overrides.machineProfileId.value"
      v-model:cam-profile-id="overrides.camProfileId.value"
      v-model:risk-tolerance="overrides.riskTolerance.value"
      :tool-options="TOOL_OPTIONS"
      :material-options="MATERIAL_OPTIONS"
      :machine-options="MACHINE_OPTIONS"
      :cam-profile-options="CAM_PROFILE_OPTIONS"
      :risk-tolerance-options="RISK_TOLERANCE_OPTIONS"
      @clear="overrides.clearOverrides"
    />

    <!-- Export URL Preview -->
    <ExportUrlToolbar
      :export-url="exportUrlPreview"
      @copy-url="copyExportUrl"
      @copy-power-shell="copyExportPowerShell"
      @copy-python="copyExportPython"
      @copy-node="copyExportNode"
      @copy-g-h-a="copyExportGitHubActionsStep"
      @copy-g-h-a-job="copyExportGitHubActionsJob"
      @copy-g-h-a-workflow="copyExportGitHubActionsWorkflow"
      @copy-g-h-a-workflow-file="copyGitHubActionsWorkflowFile"
    />

    <!-- Error display -->
    <div v-if="err" class="wf-error">{{ err }}</div>

    <!-- History -->
    <WorkflowHistory :history="session?.history || []" />

    <!-- Last Intent Preview -->
    <IntentPreview
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
import { computed, onMounted } from 'vue'
import { useArtDesignFirstWorkflowStore } from '@/stores/artDesignFirstWorkflowStore'
import { useToastStore } from '@/stores/toastStore'
import SideDrawer from '@/components/ui/SideDrawer.vue'
import WorkflowSessionPicker from '@/components/rosette/WorkflowSessionPicker.vue'

// Child components
import {
  WorkflowHeader,
  WorkflowActionsBar,
  OverrideSelector,
  ExportUrlToolbar,
  WorkflowHistory,
  IntentPreview,
} from './workflow'

// Composables
import {
  useWorkflowOverrides,
  TOOL_OPTIONS,
  MATERIAL_OPTIONS,
  MACHINE_OPTIONS,
  CAM_PROFILE_OPTIONS,
  RISK_TOLERANCE_OPTIONS,
} from './composables/useWorkflowOverrides'
import { useLogDrawer } from './composables/useLogDrawer'
import {
  buildExportPowerShellIwr,
  buildExportPythonRequests,
  buildExportNodeFetch,
  buildExportGitHubActionsStep,
  buildExportGitHubActionsJob,
  buildExportGitHubActionsWorkflow,
  buildRepoReadyWorkflowBundle,
  buildPromotionIntentCurl,
} from './composables/useExportSnippets'

const wf = useArtDesignFirstWorkflowStore()
const toast = useToastStore()

// ==========================================================================
// Store bindings
// ==========================================================================

const session = computed(() => wf.session)
const state = computed(() => wf.stateName)
const busy = computed(() => wf.loading)
const err = computed(() => wf.error)
const hasSession = computed(() => wf.hasSession)
const canIntent = computed(() => wf.canRequestIntent)
const lastIntent = computed(() => wf.lastPromotionIntent)
const currentMode = computed(() => (wf.session?.mode as string) ?? 'design_first')

// ==========================================================================
// Composables
// ==========================================================================

const overrides = useWorkflowOverrides(
  () => currentMode.value,
  (newMode) => toast.info(`Loaded export overrides for mode: ${newMode}`)
)

const logDrawer = useLogDrawer(() => wf.sessionId || '')

// ==========================================================================
// Hydration
// ==========================================================================

onMounted(() => {
  wf.hydrateFromLocalStorage()
  overrides.hydrateOverrides()
})

// ==========================================================================
// Workflow actions
// ==========================================================================

async function ensure() {
  if (wf.hasSession) wf.clearSession()
  await wf.ensureSessionDesignFirst()
}

async function toReview() {
  if (!wf.hasSession) await wf.ensureSessionDesignFirst()
  await wf.transition('in_review')
}

async function approve() {
  await wf.transition('approved')
}

async function reject() {
  await wf.transition('rejected', 'Design needs revision')
}

async function reopen() {
  await wf.transition('draft')
}

async function intent() {
  const payload = await wf.requestPromotionIntent()
  if (payload) {
    toast.info('Intent payload ready. Use Log Viewer / CAM lane to consume.')
    console.log('[ArtStudio] CAM handoff intent:', payload)
  }
}

// ==========================================================================
// CAM Promotion (Phase 33.0)
// ==========================================================================

function _baseUrl(): string {
  const envBase = (import.meta as any).env?.VITE_API_URL
  const base = envBase && typeof envBase === 'string' ? envBase : '/api'
  const origin = window.location.origin
  if (base.startsWith('http://') || base.startsWith('https://')) return base
  return origin + base
}

async function promoteToCam() {
  const sid = wf.sessionId
  if (!sid) {
    toast.error('No session available')
    return
  }

  try {
    const base = _baseUrl()
    const camProfileId = overrides.camProfileId.value || undefined
    const params = new URLSearchParams()
    if (camProfileId) params.set('cam_profile_id', camProfileId)

    const url = `${base}/art/design-first-workflow/sessions/${encodeURIComponent(sid)}/promote_to_cam${params.toString() ? '?' + params.toString() : ''}`

    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })

    if (!resp.ok) {
      const errData = await resp.json().catch(() => ({}))
      toast.error(`Promotion failed: ${errData.detail || resp.statusText}`)
      return
    }

    const data = await resp.json()

    if (!data.ok) {
      toast.warning(`Promotion blocked: ${data.blocked_reason || 'unknown'}`)
      return
    }

    const requestId = data.request?.promotion_request_id
    toast.success(`CAM promotion request created: ${requestId?.slice(0, 8) || 'OK'}…`)
    console.log('[ArtStudio] CAM promotion request:', data.request)
  } catch (e: any) {
    toast.error(`Promotion error: ${e.message || e}`)
  }
}

// ==========================================================================
// Export URL
// ==========================================================================

function buildPromotionIntentExportUrl(sessionId: string): string {
  const base = _baseUrl()
  const url = new URL(
    `${base}/art/design-first-workflow/sessions/${encodeURIComponent(sessionId)}/promotion_intent.json`,
    window.location.origin
  )

  const ov = overrides.currentOverrides.value
  if (ov.tool_id) url.searchParams.set('tool_id', ov.tool_id)
  if (ov.material_id) url.searchParams.set('material_id', ov.material_id)
  if (ov.machine_profile_id) url.searchParams.set('machine_profile_id', ov.machine_profile_id)
  if (ov.requested_cam_profile_id) url.searchParams.set('requested_cam_profile_id', ov.requested_cam_profile_id)
  if (ov.risk_tolerance) url.searchParams.set('risk_tolerance', ov.risk_tolerance)

  return url.toString()
}

const exportUrlPreview = computed(() => {
  const sid = wf.sessionId
  if (!sid) return ''
  return buildPromotionIntentExportUrl(sid)
})

// ==========================================================================
// Clipboard helpers
// ==========================================================================

async function copyToClipboard(text: string, successMsg: string) {
  try {
    await navigator.clipboard.writeText(text)
    toast.success(successMsg)
  } catch {
    toast.error('Failed to copy to clipboard')
  }
}

async function copyExportUrl() {
  if (exportUrlPreview.value) {
    await copyToClipboard(exportUrlPreview.value, 'Export URL copied to clipboard')
  }
}

async function copyExportPowerShell() {
  const sid = wf.sessionId
  if (!sid || !exportUrlPreview.value) return
  const cmd = buildExportPowerShellIwr(exportUrlPreview.value, sid)
  const combined = `# Promotion intent export (PowerShell)\n${cmd}\n`
  await copyToClipboard(combined, 'Copied PowerShell command.')
}

async function copyExportPython() {
  const sid = wf.sessionId
  if (!sid || !exportUrlPreview.value) return
  const snippet = buildExportPythonRequests(exportUrlPreview.value, sid)
  await copyToClipboard(snippet, 'Copied Python requests snippet.')
}

async function copyExportNode() {
  const sid = wf.sessionId
  if (!sid || !exportUrlPreview.value) return
  const snippet = buildExportNodeFetch(exportUrlPreview.value, sid)
  await copyToClipboard(snippet, 'Copied Node fetch snippet.')
}

async function copyExportGitHubActionsStep() {
  const sid = wf.sessionId
  if (!sid || !exportUrlPreview.value) return
  const snippet = buildExportGitHubActionsStep(exportUrlPreview.value, sid)
  await copyToClipboard(snippet, 'Copied GitHub Actions step YAML.')
}

async function copyExportGitHubActionsJob() {
  const sid = wf.sessionId
  if (!sid || !exportUrlPreview.value) return
  const snippet = buildExportGitHubActionsJob(exportUrlPreview.value, sid)
  await copyToClipboard(snippet, 'Copied GitHub Actions job YAML.')
}

async function copyExportGitHubActionsWorkflow() {
  const sid = wf.sessionId
  if (!sid || !exportUrlPreview.value) return
  const workflow = buildExportGitHubActionsWorkflow(exportUrlPreview.value, sid)
  await copyToClipboard(workflow, 'Copied GitHub Actions workflow YAML.')
}

async function copyGitHubActionsWorkflowFile() {
  const sid = wf.sessionId
  if (!sid || !exportUrlPreview.value) return
  const bundle = buildRepoReadyWorkflowBundle(exportUrlPreview.value, sid)
  await copyToClipboard(bundle, 'Repo-ready GitHub Actions workflow copied')
}

// ==========================================================================
// Intent actions
// ==========================================================================

async function copyIntent() {
  if (!lastIntent.value) return
  await copyToClipboard(JSON.stringify(lastIntent.value, null, 2), 'Intent JSON copied to clipboard')
}

async function copySessionId() {
  const sid = wf.sessionId
  if (!sid) return
  await copyToClipboard(sid, 'Session ID copied to clipboard')
}

async function copyIntentCurl() {
  const sid = wf.sessionId
  if (!sid) return
  const curl = buildPromotionIntentCurl(_baseUrl(), sid)
  await copyToClipboard(curl, 'cURL copied to clipboard')
}

function clearIntent() {
  wf.clearSession()
  toast.info('Session cleared')
}

function openInLogViewer() {
  const sid = wf.sessionId
  if (!sid) return
  logDrawer.openDrawer(sid)
}

async function downloadIntent() {
  const sid = wf.sessionId
  if (!sid) return
  const url = buildPromotionIntentExportUrl(sid)
  try {
    const resp = await fetch(url, { method: 'GET' })
    if (!resp.ok) {
      const txt = await resp.text()
      throw new Error(`HTTP ${resp.status}: ${txt}`)
    }
    const blob = await resp.blob()
    const filename = `promotion_intent_${sid.slice(0, 8)}.json`
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(a.href)
    toast.success(`Downloaded ${filename}`)
  } catch (e: any) {
    toast.error(`Download failed: ${e.message || e}`)
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

.btn.active {
  background: rgba(0, 0, 0, 0.06);
}
</style>
