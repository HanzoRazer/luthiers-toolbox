/**
 * JobIntHistory clone modal composable.
 */
import type { Ref, UnwrapNestedRefs } from 'vue'
import { api } from '@/services/apiBase'
import type { JobIntLogEntry, CloneForm } from './jobIntHistoryTypes'

// ============================================================================
// Types
// ============================================================================

export interface JobIntHistoryCloneReturn {
  openCloneModal: (entry: JobIntLogEntry) => void
  closeCloneModal: () => void
  executeClone: () => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useJobIntHistoryClone(
  showCloneModal: Ref<boolean>,
  selectedEntry: Ref<JobIntLogEntry | null>,
  cloning: Ref<boolean>,
  cloneSuccess: Ref<boolean>,
  cloneError: Ref<string | null>,
  cloneForm: UnwrapNestedRefs<CloneForm>
): JobIntHistoryCloneReturn {
  function openCloneModal(entry: JobIntLogEntry): void {
    selectedEntry.value = entry
    cloneForm.name = `${entry.job_name || 'Job'} - ${entry.machine_id || 'Machine'}`
    cloneForm.description = `Cloned from job run ${entry.run_id.slice(0, 8)} on ${new Date().toLocaleDateString()}`
    cloneForm.kind = 'cam'
    cloneForm.tagsInput = entry.use_helical ? 'helical, cloned' : 'cloned'
    cloneSuccess.value = false
    cloneError.value = null
    showCloneModal.value = true
  }

  function closeCloneModal(): void {
    showCloneModal.value = false
    selectedEntry.value = null
    cloneForm.name = ''
    cloneForm.description = ''
    cloneForm.tagsInput = ''
    cloneSuccess.value = false
    cloneError.value = null
  }

  async function executeClone(): Promise<void> {
    if (!selectedEntry.value || !cloneForm.name) return

    cloning.value = true
    cloneError.value = null
    cloneSuccess.value = false

    try {
      // First fetch detailed job data
      const detailResponse = await api(
        `/api/cam/job-int/log/${encodeURIComponent(selectedEntry.value.run_id)}`
      )
      if (!detailResponse.ok) {
        throw new Error(`Failed to fetch job details: ${detailResponse.statusText}`)
      }
      const jobDetail = await detailResponse.json()

      // Build preset payload
      const tags = cloneForm.tagsInput
        .split(',')
        .map((t) => t.trim())
        .filter((t) => t.length > 0)

      const presetPayload = {
        name: cloneForm.name,
        kind: cloneForm.kind,
        description: cloneForm.description,
        tags: tags,
        machine_id: selectedEntry.value.machine_id || null,
        post_id: selectedEntry.value.post_id || null,
        units: 'mm', // Default, could be extracted from job if available
        job_source_id: selectedEntry.value.run_id,
        cam_params: {
          strategy: 'Spiral', // Default, could be extracted from job
          use_helical: selectedEntry.value.use_helical,
          // Add more params from jobDetail.sim_stats if available
          ...(jobDetail.sim_stats || {})
        }
      }

      // Create preset via API
      const createResponse = await api('/api/presets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(presetPayload)
      })

      if (!createResponse.ok) {
        const errorData = await createResponse.json().catch(() => ({}))
        throw new Error(
          errorData.detail || `Failed to create preset: ${createResponse.statusText}`
        )
      }

      cloneSuccess.value = true

      // Auto-close after 2 seconds on success
      setTimeout(() => {
        closeCloneModal()
      }, 2000)
    } catch (err: any) {
      console.error('Clone preset error:', err)
      cloneError.value = err?.message || 'Failed to clone job as preset'
    } finally {
      cloning.value = false
    }
  }

  return {
    openCloneModal,
    closeCloneModal,
    executeClone
  }
}
