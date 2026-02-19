import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/services/apiBase'
import { runs as rmosRuns } from '@/sdk/rmos'

export interface CamParams {
  tool_d: number
  stepover: number
  stepdown: number
  z_rough: number
  feed_xy: number
  feed_z: number
  rapid: number
  safe_z: number
  strategy: string
  layer_name: string
  climb: boolean
  smoothing: number
  margin: number
}

export function useDxfToGcode() {
  const router = useRouter()

  // File state
  const dxfFile = ref<File | null>(null)
  const uploadError = ref<string | null>(null)

  // Generation state
  const isGenerating = ref(false)
  const result = ref<any>(null)
  const error = ref<string | null>(null)
  const abortController = ref<AbortController | null>(null)

  // Compare state
  const previousRunId = ref<string | null>(null)
  const isComparing = ref(false)
  const compareError = ref<string | null>(null)
  const compareResult = ref<any | null>(null)

  // Explainability state
  const showWhy = ref(false)

  // Override modal state
  const showOverrideModal = ref(false)
  const isSubmittingOverride = ref(false)
  const overrideError = ref<string | null>(null)

  // CAM parameters
  const params = ref<CamParams>({
    tool_d: 6.0,
    stepover: 0.45,
    stepdown: 1.5,
    z_rough: -3.0,
    feed_xy: 1200,
    feed_z: 300,
    rapid: 3000,
    safe_z: 5.0,
    strategy: 'Spiral',
    layer_name: 'GEOMETRY',
    climb: true,
    smoothing: 0.1,
    margin: 0.0
  })

  // Computed
  const canDownload = computed(() => result.value?.gcode?.inline && !!result.value?.gcode?.text)

  const canCompare = computed(() => {
    const runId = String(result.value?.run_id || '').trim()
    return !!runId && !!previousRunId.value && !isGenerating.value && !isComparing.value
  })

  const canDownloadOperatorPack = computed(() => {
    const runId = (result.value?.run_id || '').trim()
    return !!runId && !isGenerating.value
  })

  const riskLevel = computed(() => String(result.value?.decision?.risk_level || '').toUpperCase())

  const hasOverrideAttachment = computed(() => {
    const atts = result.value?.attachments || []
    return Array.isArray(atts) && atts.some((a: any) => a?.kind === 'override')
  })

  const triggeredRuleIds = computed<string[]>(() => {
    const ids = result.value?.feasibility?.rules_triggered
    if (!Array.isArray(ids)) return []
    return ids.map((x: any) => String(x).trim().toUpperCase()).filter(Boolean)
  })

  const hasExplainability = computed(() => triggeredRuleIds.value.length > 0)

  const canViewRun = computed(() => {
    const runId = String(result.value?.run_id || '').trim()
    return !!runId
  })

  const gcodeAttachment = computed(() => {
    if (!result.value?.attachments) return null
    return result.value.attachments.find((a: any) => a.kind === 'gcode_output')
  })

  const hasCompare = computed(() => !!compareResult.value && !compareError.value)

  const overrideReason = computed(() =>
    result.value?.override_reason ||
    result.value?.explanation?.override_reason ||
    result.value?.decision?.details?.override_reason
  )

  const compareTitle = computed(() =>
    previousRunId.value
      ? `Compare ${previousRunId.value} → ${result.value?.run_id}`
      : 'No previous run found yet'
  )

  // Auto-open Why on YELLOW/RED
  watch([riskLevel, hasExplainability], ([rl, hasExp]) => {
    if (!result.value) return
    if (!hasExp) return
    showWhy.value = rl === 'YELLOW' || rl === 'RED'
  }, { immediate: true })

  // Reset on file change
  watch(dxfFile, () => {
    if (abortController.value) {
      abortController.value.abort()
      abortController.value = null
    }
    result.value = null
    error.value = null
    isGenerating.value = false
  })

  // Functions
  function viewRunNewTab() {
    const runId = String(result.value?.run_id || '').trim()
    if (!runId) return
    const href = router.resolve(`/rmos/runs/${encodeURIComponent(runId)}`).href
    window.open(href, '_blank', 'noopener,noreferrer')
  }

  async function refreshPreviousRunId(currentRunId: string) {
    try {
      previousRunId.value = null
      const { items } = await rmosRuns.listRuns({ limit: 20 })
      const list = Array.isArray(items) ? items : []
      const mode = String(result.value?.mode || '').trim()

      let filtered = list
      if (mode) {
        filtered = list.filter((it: any) => String(it?.mode || '').trim() === mode)
      }

      const idx = filtered.findIndex((it: any) => String(it?.run_id || '').trim() === currentRunId)
      if (idx >= 0 && idx + 1 < filtered.length) {
        previousRunId.value = String(filtered[idx + 1]?.run_id || '').trim() || null
        return
      }

      const alt = filtered.find((it: any) =>
        String(it?.run_id || '').trim() && String(it?.run_id || '').trim() !== currentRunId
      )
      previousRunId.value = alt ? String(alt.run_id).trim() : null
    } catch {
      previousRunId.value = null
    }
  }

  async function refreshRunCanonical(runId: string) {
    try {
      const run = await rmosRuns.getRun(runId)
      result.value = {
        ...result.value,
        attachments: run.attachments ?? result.value?.attachments,
        hashes: run.hashes ?? result.value?.hashes,
        decision: run.decision ?? result.value?.decision,
        feasibility: run.feasibility ?? result.value?.feasibility,
        mode: run.mode ?? result.value?.mode,
      }
      await refreshPreviousRunId(runId)
    } catch {
      // Non-fatal
    }
  }

  async function compareWithPreviousRun() {
    const runId = String(result.value?.run_id || '').trim()
    const prev = String(previousRunId.value || '').trim()
    if (!runId || !prev) return

    isComparing.value = true
    compareError.value = null
    compareResult.value = null

    try {
      const diffResult = await rmosRuns.compareRuns(prev, runId)
      compareResult.value = diffResult
    } catch (e: any) {
      compareError.value = e?.message || 'Failed to compare runs.'
    } finally {
      isComparing.value = false
    }
  }

  function clearCompare() {
    compareResult.value = null
    compareError.value = null
  }

  async function parseErrorResponse(response: Response): Promise<string> {
    const status = response.status
    try {
      const data = await response.json()
      if (typeof data.detail === 'string') return data.detail
      if (Array.isArray(data.detail)) {
        return data.detail.map((d: any) => d.msg || JSON.stringify(d)).join('; ')
      }
      if (data.detail) return JSON.stringify(data.detail)
      return `HTTP ${status}`
    } catch {
      try {
        const text = await response.text()
        return text || `HTTP ${status}`
      } catch {
        return `HTTP ${status}`
      }
    }
  }

  async function generateGcode() {
    if (!dxfFile.value) return

    if (abortController.value) {
      abortController.value.abort()
    }
    abortController.value = new AbortController()

    isGenerating.value = true
    error.value = null
    result.value = null

    try {
      const fd = new FormData()
      fd.append('file', dxfFile.value)

      for (const [k, v] of Object.entries(params.value)) {
        if (typeof v === 'boolean') {
          fd.append(k, v ? 'true' : 'false')
        } else {
          fd.append(k, String(v))
        }
      }

      const response = await api('/api/rmos/wrap/mvp/dxf-to-grbl', {
        method: 'POST',
        body: fd,
        signal: abortController.value.signal
      })

      if (!response.ok) {
        const errMsg = await parseErrorResponse(response)
        throw new Error(errMsg)
      }

      result.value = await response.json()
      await refreshPreviousRunId(String(result.value?.run_id || '').trim())
    } catch (err: any) {
      if (err.name === 'AbortError') return
      error.value = err.message || 'Failed to generate G-code'
    } finally {
      isGenerating.value = false
      abortController.value = null
    }
  }

  function downloadGcode() {
    if (!canDownload.value) return

    const blob = new Blob([result.value.gcode.text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const baseName = (dxfFile.value?.name || 'output').replace(/\.dxf$/i, '')
    a.download = `${baseName}_GRBL.nc`
    a.click()
    URL.revokeObjectURL(url)
  }

  async function copyRunId() {
    if (!result.value?.run_id) return
    try {
      await navigator.clipboard.writeText(result.value.run_id)
    } catch {
      const input = document.createElement('input')
      input.value = result.value.run_id
      document.body.appendChild(input)
      input.select()
      document.execCommand('copy')
      document.body.removeChild(input)
    }
  }

  async function doDownloadOperatorPack() {
    const runId = (result.value?.run_id || '').trim()
    if (!runId) return

    try {
      const { blob } = await rmosRuns.downloadOperatorPack(runId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `operator_pack_${runId}.zip`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e: any) {
      if (e?.status === 403 && riskLevel.value === 'YELLOW' && !hasOverrideAttachment.value) {
        showOverrideModal.value = true
        return
      }
      error.value = String(e?.message || e)
    }
  }

  async function downloadOperatorPack() {
    const runId = (result.value?.run_id || '').trim()
    if (!runId) return

    if (riskLevel.value === 'YELLOW' && !hasOverrideAttachment.value) {
      showOverrideModal.value = true
      return
    }

    await doDownloadOperatorPack()
  }

  async function submitOverride(reason: string, operator: string) {
    const runId = String(result.value?.run_id || '').trim()
    if (!runId) return

    if (!reason) {
      overrideError.value = 'Please enter an override reason.'
      return
    }

    isSubmittingOverride.value = true
    overrideError.value = null

    try {
      await rmosRuns.addOverride(runId, {
        reason,
        operator: operator || undefined
      })
      await refreshRunCanonical(runId)
      showOverrideModal.value = false
      await doDownloadOperatorPack()
    } catch (e: any) {
      overrideError.value = e?.message || 'Override failed.'
    } finally {
      isSubmittingOverride.value = false
    }
  }

  function closeOverrideModal() {
    if (isSubmittingOverride.value) return
    showOverrideModal.value = false
  }

  return {
    // File
    dxfFile,
    uploadError,
    // Params
    params,
    // Generation
    isGenerating,
    result,
    error,
    generateGcode,
    // Download
    canDownload,
    downloadGcode,
    canDownloadOperatorPack,
    downloadOperatorPack,
    // Run
    canViewRun,
    viewRunNewTab,
    copyRunId,
    gcodeAttachment,
    // Risk/Explainability
    riskLevel,
    triggeredRuleIds,
    hasExplainability,
    showWhy,
    hasOverrideAttachment,
    overrideReason,
    // Compare
    previousRunId,
    isComparing,
    compareError,
    compareResult,
    hasCompare,
    canCompare,
    compareTitle,
    compareWithPreviousRun,
    clearCompare,
    // Override modal
    showOverrideModal,
    isSubmittingOverride,
    overrideError,
    submitOverride,
    closeOverrideModal,
  }
}
