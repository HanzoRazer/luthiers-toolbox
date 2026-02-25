/**
 * RmosRunViewer actions composable.
 */
import type { Ref, ComputedRef } from 'vue'
import type { Router } from 'vue-router'
import { downloadRun, type RunArtifactDetail } from '@/api/rmosRuns'
import { runs as rmosRuns } from '@/sdk/rmos'
import { downloadBlob } from '@/utils/downloadBlob'
import type { AssistantExplanation } from './rmosRunViewerTypes'

// ============================================================================
// Types
// ============================================================================

export interface RmosRunViewerActionsReturn {
  loadRun: () => Promise<void>
  generateAdvisoryExplanation: (force: boolean) => Promise<void>
  formatDate: (iso?: string | null) => string
  handleDownload: () => void
  goToDiff: () => void
  goToDiffWithParent: () => void
  goBack: () => void
  downloadOperatorPack: () => Promise<void>
  downloadAttachment: (att: any) => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useRmosRunViewerActions(
  router: Router,
  runId: ComputedRef<string>,
  parentRunId: ComputedRef<string | null>,
  run: Ref<RunArtifactDetail | null>,
  loading: Ref<boolean>,
  error: Ref<string | null>,
  isExplaining: Ref<boolean>,
  explainError: Ref<string | null>,
  assistantExplanation: Ref<AssistantExplanation | null>
): RmosRunViewerActionsReturn {
  /**
   * Load run artifact from API.
   */
  async function loadRun(): Promise<void> {
    if (!runId.value) return
    loading.value = true
    error.value = null
    try {
      run.value = (await rmosRuns.getRun(runId.value)) as RunArtifactDetail
    } catch (e: any) {
      error.value = e.message || 'Failed to load run'
      run.value = null
    } finally {
      loading.value = false
    }
  }

  /**
   * Generate advisory explanation (Phase 5).
   */
  async function generateAdvisoryExplanation(force: boolean): Promise<void> {
    const id = runId.value
    if (!id) return
    isExplaining.value = true
    explainError.value = null
    try {
      const result = await rmosRuns.explainRun(id, force)
      assistantExplanation.value = result.explanation ?? null
      // Refresh run to pick up new attachment
      await loadRun()
    } catch (e: any) {
      explainError.value = e?.message || 'Failed to generate advisory explanation.'
    } finally {
      isExplaining.value = false
    }
  }

  /**
   * Format ISO date string to locale string.
   */
  function formatDate(iso?: string | null): string {
    if (!iso) return '---'
    try {
      return new Date(iso).toLocaleString()
    } catch {
      return iso
    }
  }

  /**
   * Download run JSON.
   */
  function handleDownload(): void {
    if (runId.value) {
      downloadRun(runId.value)
    }
  }

  /**
   * Navigate to diff view.
   */
  function goToDiff(): void {
    router.push({ path: '/rmos/runs/diff', query: { a: runId.value } })
  }

  /**
   * Navigate to diff with parent run.
   */
  function goToDiffWithParent(): void {
    if (parentRunId.value) {
      router.push({
        path: '/rmos/runs/diff',
        query: { a: parentRunId.value, b: runId.value }
      })
    }
  }

  /**
   * Navigate back to runs list.
   */
  function goBack(): void {
    router.push('/rmos/runs')
  }

  /**
   * Download operator pack ZIP.
   */
  async function downloadOperatorPack(): Promise<void> {
    if (!runId.value) return
    error.value = null
    try {
      const { blob } = await rmosRuns.downloadOperatorPack(runId.value)
      downloadBlob(blob, `operator_pack_${runId.value}.zip`)
    } catch (e: any) {
      error.value = String(e?.message || e)
    }
  }

  /**
   * Download attachment by SHA.
   */
  async function downloadAttachment(att: any): Promise<void> {
    if (!att?.sha256) return
    error.value = null
    try {
      const { blob } = await rmosRuns.downloadAttachment(att.sha256)
      const safeName = (att.filename || `${att.sha256}`).replace(/[^\w.\-]+/g, '_')
      downloadBlob(blob, safeName)
    } catch (e: any) {
      error.value = String(e?.message || e)
    }
  }

  return {
    loadRun,
    generateAdvisoryExplanation,
    formatDate,
    handleDownload,
    goToDiff,
    goToDiffWithParent,
    goBack,
    downloadOperatorPack,
    downloadAttachment
  }
}
