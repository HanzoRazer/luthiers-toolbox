import { ref, computed, type Ref, type ComputedRef } from 'vue'
import JSZip from 'jszip'
import { downloadManufacturingCandidateZip, type ManufacturingCandidate } from '@/sdk/rmos/runs'

export interface BulkExportState {
  exporting: Ref<boolean>
  exportError: Ref<string | null>
  bulkPackaging: Ref<boolean>
  bulkPackageName: Ref<string>
  greenCandidates: ComputedRef<ManufacturingCandidate[]>
  undecidedCount: ComputedRef<number>
  yellowCount: ComputedRef<number>
  redCount: ComputedRef<number>
  runReadyStatus: ComputedRef<'READY' | 'BLOCKED' | 'EMPTY'>
  runReadyLabel: ComputedRef<string>
  runReadyHover: ComputedRef<string>
  exportBlockedReason: ComputedRef<string | null>
  exportPackageDisabledReason: ComputedRef<string | null>
  canExportGreenOnly: ComputedRef<boolean>
  runReadyBadgeClass: () => string
  exportGreenOnlyZips: () => Promise<void>
  exportGreenOnlyPackageZip: () => Promise<void>
}

export function useBulkExport(
  runId: () => string,
  candidates: Ref<ManufacturingCandidate[]>,
  loading: Ref<boolean>,
  showToast: (msg: string, variant?: 'ok' | 'err') => void
): BulkExportState {
  const exporting = ref(false)
  const exportError = ref<string | null>(null)
  const bulkPackaging = ref(false)
  const bulkPackageName = ref('')
  const requestId = ref('')

  // Computed counts
  const greenCandidates = computed(() =>
    candidates.value.filter((c) => c.decision === 'GREEN')
  )
  const undecidedCount = computed(() =>
    candidates.value.filter((c) => c.decision == null).length
  )
  const yellowCount = computed(() =>
    candidates.value.filter((c) => c.decision === 'YELLOW').length
  )
  const redCount = computed(() =>
    candidates.value.filter((c) => c.decision === 'RED').length
  )

  // Run ready status
  const runReadyStatus = computed<'READY' | 'BLOCKED' | 'EMPTY'>(() => {
    if (loading.value) return 'BLOCKED'
    if (!candidates.value.length) return 'EMPTY'
    if (greenCandidates.value.length > 0 && undecidedCount.value === 0) return 'READY'
    return 'BLOCKED'
  })

  const runReadyLabel = computed(() => {
    if (runReadyStatus.value === 'READY') return 'RUN READY'
    if (runReadyStatus.value === 'EMPTY') return 'NO CANDIDATES'
    return 'RUN BLOCKED'
  })

  const runReadyHover = computed(() => {
    if (loading.value) return 'Loading candidates…'
    if (!candidates.value.length) return 'No manufacturing candidates yet. Promote variants to create candidates.'

    if (greenCandidates.value.length === 0) {
      if (undecidedCount.value > 0) {
        return `No GREEN candidates yet.\n${undecidedCount.value} candidate(s) are undecided.\nDecide GREEN/YELLOW/RED to proceed.`
      }
      if (yellowCount.value > 0 || redCount.value > 0) {
        return `No GREEN candidates.\nYELLOW: ${yellowCount.value}, RED: ${redCount.value}.\nSet at least one candidate to GREEN to enable export.`
      }
      return 'No GREEN candidates. Decide at least one candidate as GREEN to proceed.'
    }

    if (undecidedCount.value > 0) {
      return `Export is gated by undecided candidates.\n${greenCandidates.value.length} GREEN candidate(s) available,\nbut ${undecidedCount.value} candidate(s) still need an explicit decision.`
    }

    return `Ready:\nGREEN: ${greenCandidates.value.length}\nYELLOW: ${yellowCount.value}\nRED: ${redCount.value}\nNo undecided candidates.`
  })

  const exportBlockedReason = computed(() => {
    if (candidates.value.length === 0) return 'No candidates to export.'
    if (undecidedCount.value > 0) {
      return `Export blocked: ${undecidedCount.value} candidate(s) still NEED DECISION. Decide all candidates before exporting.`
    }
    if (greenCandidates.value.length === 0) {
      return 'Export blocked: there are no GREEN candidates to export.'
    }
    return null
  })

  const exportPackageDisabledReason = computed(() => {
    if (loading.value) return 'Still loading candidates.'
    if (bulkPackaging.value) return 'Package export already in progress.'
    if (!candidates.value.length) return 'No candidates available for this run.'
    if (undecidedCount.value > 0) {
      return `Export blocked: ${undecidedCount.value} candidate(s) are undecided. Decide GREEN/YELLOW/RED to proceed.`
    }
    if (!greenCandidates.value.length) {
      return 'Export blocked: no GREEN candidates.'
    }
    return null
  })

  const canExportGreenOnly = computed(() =>
    exportBlockedReason.value == null && !exporting.value
  )

  function runReadyBadgeClass() {
    if (runReadyStatus.value === 'READY') return 'badgeReady'
    if (runReadyStatus.value === 'EMPTY') return 'badgeEmpty'
    return 'badgeBlocked'
  }

  function downloadBlob(blob: Blob, filename: string) {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    setTimeout(() => URL.revokeObjectURL(url), 2500)
  }

  async function exportGreenOnlyZips() {
    const rid = runId()
    if (!rid) return
    exportError.value = null

    const reason = exportBlockedReason.value
    if (reason) {
      exportError.value = reason
      return
    }

    exporting.value = true
    try {
      for (const c of greenCandidates.value) {
        const res = await downloadManufacturingCandidateZip(rid, c.candidate_id)
        requestId.value = res.requestId ?? requestId.value
        const fname = `rmos_${rid}_candidate_${c.candidate_id}_GREEN.zip`
        downloadBlob(res.blob, fname)
        await new Promise((r) => setTimeout(r, 250))
      }
    } catch (e: any) {
      exportError.value = e?.message ?? String(e)
    } finally {
      exporting.value = false
    }
  }

  async function exportGreenOnlyPackageZip() {
    const deny = exportPackageDisabledReason.value
    if (deny) {
      showToast(deny, 'err')
      return
    }

    const rid = runId()
    bulkPackaging.value = true
    exportError.value = null

    try {
      const zip = new JSZip()
      const exportedAtUtc = new Date().toISOString()

      const safeRun = (rid || 'run').replace(/[^a-zA-Z0-9._-]/g, '_')
      const baseName =
        bulkPackageName.value.trim() ||
        `${safeRun}_GREEN_candidates_${exportedAtUtc.slice(0, 19).replace(/[:T]/g, '-')}`

      const manifest = {
        run_id: rid,
        exported_at_utc: exportedAtUtc,
        count: greenCandidates.value.length,
        items: greenCandidates.value.map((c) => ({
          candidate_id: c.candidate_id,
          advisory_id: (c as any).advisory_id ?? null,
          decision: c.decision ?? null,
          decided_by: c.decided_by ?? null,
          decided_at_utc: c.decided_at_utc ?? null,
          decision_note: c.decision_note ?? null,
        })),
      }
      zip.file('manifest.json', JSON.stringify(manifest, null, 2))

      for (const c of greenCandidates.value) {
        try {
          const res = await downloadManufacturingCandidateZip(rid, c.candidate_id)
          requestId.value = res.requestId ?? requestId.value
          zip.file(`candidates/${c.candidate_id}.zip`, res.blob)
        } catch (e: any) {
          zip.file(
            `errors/${c.candidate_id}.error.txt`,
            String(e?.message || e || 'download failed')
          )
        }
      }

      const out = await zip.generateAsync({ type: 'blob' })
      downloadBlob(out, `${baseName}.zip`)
      showToast(`Exported ${greenCandidates.value.length} GREEN candidate(s) as package`, 'ok')
    } catch (e: any) {
      exportError.value = e?.message ?? String(e)
    } finally {
      bulkPackaging.value = false
    }
  }

  return {
    exporting,
    exportError,
    bulkPackaging,
    bulkPackageName,
    greenCandidates,
    undecidedCount,
    yellowCount,
    redCount,
    runReadyStatus,
    runReadyLabel,
    runReadyHover,
    exportBlockedReason,
    exportPackageDisabledReason,
    canExportGreenOnly,
    runReadyBadgeClass,
    exportGreenOnlyZips,
    exportGreenOnlyPackageZip,
  }
}
