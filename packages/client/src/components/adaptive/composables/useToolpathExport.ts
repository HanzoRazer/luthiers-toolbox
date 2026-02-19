/**
 * Composable for toolpath export functionality.
 * Handles G-code preview, export, and batch export.
 */
import { ref, watch, type Ref } from 'vue'
import { api } from '@/services/apiBase'

export interface ExportModes {
  comment: boolean
  inline_f: boolean
  mcode: boolean
}

export interface ExportState {
  ncOpen: Ref<boolean>
  ncText: Ref<string>
  jobName: Ref<string>
  exportModes: Ref<ExportModes>
  previewNc: (body: Record<string, unknown>) => Promise<void>
  exportProgram: (body: Record<string, unknown>, postId: string, strategy: string) => Promise<void>
  batchExport: (body: Record<string, unknown>, postId: string) => Promise<void>
  selectedModes: () => string[]
}

export function useToolpathExport(): ExportState {
  const ncOpen = ref(false)
  const ncText = ref('')

  // Job name for filename stem (localStorage persisted)
  const jobName = ref(localStorage.getItem('toolbox.job_name') || '')
  watch(jobName, (v: string) => {
    localStorage.setItem('toolbox.job_name', v || '')
  })

  // Batch export mode selection state (localStorage persisted)
  const exportModes = ref<ExportModes>(
    (() => {
      try {
        return JSON.parse(localStorage.getItem('toolbox.af.modes') || '')
      } catch {
        return { comment: true, inline_f: true, mcode: true }
      }
    })()
  )

  watch(
    exportModes,
    () => {
      localStorage.setItem('toolbox.af.modes', JSON.stringify(exportModes.value))
    },
    { deep: true }
  )

  function selectedModes(): string[] {
    const sel: string[] = []
    if (exportModes.value.comment) sel.push('comment')
    if (exportModes.value.inline_f) sel.push('inline_f')
    if (exportModes.value.mcode) sel.push('mcode')
    return sel
  }

  async function previewNc(body: Record<string, unknown>) {
    try {
      const r = await api('/api/cam/pocket/adaptive/gcode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      ncText.value = await r.text()
      ncOpen.value = true
    } catch (err) {
      console.error('Preview failed:', err)
      alert('Failed to preview NC: ' + err)
    }
  }

  async function exportProgram(body: Record<string, unknown>, postId: string, strategy: string) {
    try {
      const r = await api('/api/cam/pocket/adaptive/gcode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const blob = await r.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)

      // Use job_name if provided, else fallback to strategy_post pattern
      const stem =
        jobName.value && jobName.value.trim()
          ? jobName.value.trim().replace(/\s+/g, '_')
          : `pocket_${strategy.toLowerCase()}_${postId.toLowerCase()}`
      a.download = `${stem}.nc`

      a.click()
      URL.revokeObjectURL(a.href)
    } catch (err) {
      console.error('Export failed:', err)
      alert('Failed to export G-code: ' + err)
    }
  }

  async function batchExport(body: Record<string, unknown>, postId: string) {
    const exportBody: Record<string, unknown> = {
      ...body,
      post_id: postId,
      modes: selectedModes(),
      job_name: jobName.value || undefined,
    }

    try {
      const r = await api('/api/cam/pocket/adaptive/batch_export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(exportBody),
      })
      const blob = await r.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)

      // Use job_name if provided, else fallback to mode-based name
      const stem =
        jobName.value && jobName.value.trim()
          ? jobName.value.trim().replace(/\s+/g, '_')
          : `ToolBox_MultiMode_${selectedModes().join('-') || 'all'}`
      a.download = `${stem}.zip`

      a.click()
      URL.revokeObjectURL(a.href)
    } catch (err) {
      console.error('Batch export failed:', err)
      alert('Failed to batch export: ' + err)
    }
  }

  return {
    ncOpen,
    ncText,
    jobName,
    exportModes,
    previewNc,
    exportProgram,
    batchExport,
    selectedModes,
  }
}
