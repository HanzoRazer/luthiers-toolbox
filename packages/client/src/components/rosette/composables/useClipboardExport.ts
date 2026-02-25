/**
 * Composable for clipboard copy operations and export URL building.
 * Extracted from DesignFirstWorkflowPanel.vue
 */
import { computed, type Ref, type ComputedRef } from 'vue'
import {
  buildExportPowerShellIwr,
  buildExportPythonRequests,
  buildExportNodeFetch,
  buildExportGitHubActionsStep,
  buildExportGitHubActionsJob,
  buildExportGitHubActionsWorkflow,
  buildRepoReadyWorkflowBundle,
  buildPromotionIntentCurl,
  safeFilenameFromSession,
} from './useExportSnippets'
import { downloadBlob } from '@/utils/downloadBlob'
import type { WorkflowOverridesState } from './useWorkflowOverrides'

// ==========================================================================
// Types
// ==========================================================================

/**
 * Subset of WorkflowOverridesState needed for export URL building.
 * @deprecated Import WorkflowOverridesState from useWorkflowOverrides instead.
 */
export type WorkflowOverrides = Pick<
  WorkflowOverridesState,
  'toolId' | 'materialId' | 'machineProfileId' | 'camProfileId' | 'riskTolerance'
>

export interface ClipboardExportState {
  /** Full export URL with overrides applied */
  exportUrlPreview: ComputedRef<string>
  /** Build export URL for a session */
  buildPromotionIntentExportUrl: (sessionId: string) => string
  /** Get API base URL */
  getApiBaseUrl: () => string
  /** Copy intent JSON to clipboard */
  copyIntent: () => Promise<void>
  /** Copy session ID to clipboard */
  copySessionId: () => Promise<void>
  /** Copy cURL command for promotion intent */
  copyIntentCurl: () => Promise<void>
  /** Copy export URL to clipboard */
  copyExportUrl: () => Promise<void>
  /** Copy PowerShell command */
  copyExportPowerShell: () => Promise<void>
  /** Copy Python snippet */
  copyExportPython: () => Promise<void>
  /** Copy Node.js snippet */
  copyExportNode: () => Promise<void>
  /** Copy GitHub Actions step YAML */
  copyExportGitHubActionsStep: () => Promise<void>
  /** Copy GitHub Actions job YAML */
  copyExportGitHubActionsJob: () => Promise<void>
  /** Copy GitHub Actions workflow YAML */
  copyExportGitHubActionsWorkflow: () => Promise<void>
  /** Copy repo-ready workflow file */
  copyGitHubActionsWorkflowFile: () => Promise<void>
  /** Download intent as JSON file */
  downloadIntent: () => Promise<void>
}

export interface ToastService {
  success: (msg: string) => void
  error: (msg: string) => void
  info: (msg: string) => void
}

// ==========================================================================
// Composable
// ==========================================================================

export function useClipboardExport(
  getSessionId: () => string | null | undefined,
  getLastIntent: () => unknown | null | undefined,
  overrides: WorkflowOverrides,
  toast: ToastService
): ClipboardExportState {
  // ==========================================================================
  // URL Building
  // ==========================================================================

  function getApiBaseUrl(): string {
    const envBase = (import.meta as any).env?.VITE_API_URL
    const base = envBase && typeof envBase === 'string' ? envBase : '/api'
    const origin = window.location.origin
    if (base.startsWith('http://') || base.startsWith('https://')) return base
    return origin + base
  }

  function buildPromotionIntentExportUrl(sessionId: string): string {
    const base = getApiBaseUrl()
    const url = new URL(
      `${base}/art/design-first-workflow/sessions/${encodeURIComponent(sessionId)}/promotion_intent.json`,
      window.location.origin
    )

    if (overrides.toolId.value) url.searchParams.set('tool_id', overrides.toolId.value)
    if (overrides.materialId.value) url.searchParams.set('material_id', overrides.materialId.value)
    if (overrides.machineProfileId.value)
      url.searchParams.set('machine_profile_id', overrides.machineProfileId.value)
    if (overrides.camProfileId.value)
      url.searchParams.set('requested_cam_profile_id', overrides.camProfileId.value)
    if (overrides.riskTolerance.value)
      url.searchParams.set('risk_tolerance', overrides.riskTolerance.value)

    return url.toString()
  }

  const exportUrlPreview = computed(() => {
    const sid = getSessionId()
    if (!sid) return ''
    return buildPromotionIntentExportUrl(sid)
  })

  // ==========================================================================
  // Clipboard Helpers
  // ==========================================================================

  async function copyToClipboard(text: string, successMsg: string, errorMsg = 'Failed to copy to clipboard') {
    try {
      await navigator.clipboard.writeText(text)
      toast.success(successMsg)
    } catch {
      toast.error(errorMsg)
    }
  }

  // ==========================================================================
  // Copy Actions — table-driven to eliminate 9x session-guard duplication
  // ==========================================================================

  /** Guard: returns [sessionId, exportUrl] or null if either is missing. */
  function getSessionAndUrl(): [string, string] | null {
    const sid = getSessionId()
    const url = exportUrlPreview.value
    if (!sid || !url) return null
    return [sid, url]
  }

  async function copyIntent() {
    const intent = getLastIntent()
    if (!intent) return
    await copyToClipboard(JSON.stringify(intent, null, 2), 'Intent JSON copied to clipboard')
  }

  async function copySessionId() {
    const sid = getSessionId()
    if (!sid) return
    await copyToClipboard(sid, 'Session ID copied to clipboard')
  }

  async function copyIntentCurl() {
    const sid = getSessionId()
    if (!sid) return
    const curl = buildPromotionIntentCurl(getApiBaseUrl(), sid)
    await copyToClipboard(curl, 'cURL copied to clipboard', 'Failed to copy cURL')
  }

  async function copyExportUrl() {
    const url = exportUrlPreview.value
    if (!url) return
    await copyToClipboard(url, 'Export URL copied to clipboard', 'Failed to copy URL')
  }

  // Snippet copy actions — all require [sid, url] guard
  type SnippetBuilder = (url: string, sid: string) => string

  const snippetCopiers: Record<string, { build: SnippetBuilder; toast: string }> = {
    powerShell: {
      build: (url, sid) =>
        ['# Promotion intent export (PowerShell)', buildExportPowerShellIwr(url, sid), ''].join('\n'),
      toast: 'Copied PowerShell command.',
    },
    python: { build: buildExportPythonRequests, toast: 'Copied Python requests snippet.' },
    node: { build: buildExportNodeFetch, toast: 'Copied Node fetch snippet.' },
    gitHubActionsStep: { build: buildExportGitHubActionsStep, toast: 'Copied GitHub Actions step YAML.' },
    gitHubActionsJob: { build: buildExportGitHubActionsJob, toast: 'Copied GitHub Actions job YAML.' },
    gitHubActionsWorkflow: {
      build: buildExportGitHubActionsWorkflow,
      toast: 'Copied GitHub Actions workflow YAML.',
    },
    repoReadyWorkflow: {
      build: buildRepoReadyWorkflowBundle,
      toast: 'Repo-ready GitHub Actions workflow copied',
    },
  }

  function makeSnippetCopier(key: string): () => Promise<void> {
    return async () => {
      const pair = getSessionAndUrl()
      if (!pair) return
      const [sid, url] = pair
      const { build, toast: successMsg } = snippetCopiers[key]
      await copyToClipboard(build(url, sid), successMsg, 'Copy failed.')
    }
  }

  const copyExportPowerShell = makeSnippetCopier('powerShell')
  const copyExportPython = makeSnippetCopier('python')
  const copyExportNode = makeSnippetCopier('node')
  const copyExportGitHubActionsStep = makeSnippetCopier('gitHubActionsStep')
  const copyExportGitHubActionsJob = makeSnippetCopier('gitHubActionsJob')
  const copyExportGitHubActionsWorkflow = makeSnippetCopier('gitHubActionsWorkflow')
  const copyGitHubActionsWorkflowFile = makeSnippetCopier('repoReadyWorkflow')

  async function downloadIntent() {
    const sid = getSessionId()
    if (!sid) return
    const url = buildPromotionIntentExportUrl(sid)
    try {
      const resp = await fetch(url, { method: 'GET' })
      if (!resp.ok) {
        const txt = await resp.text()
        throw new Error(`HTTP ${resp.status}: ${txt}`)
      }
      const blob = await resp.blob()
      const filename = safeFilenameFromSession(sid)
      downloadBlob(blob, filename)
      toast.success(`Downloaded ${filename}`)
    } catch (e: any) {
      toast.error(`Download failed: ${e.message || e}`)
    }
  }

  return {
    exportUrlPreview,
    buildPromotionIntentExportUrl,
    getApiBaseUrl,
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
    downloadIntent,
  }
}
