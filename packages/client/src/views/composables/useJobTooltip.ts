/**
 * Composable for job source tooltip with details caching.
 * Extracted from PresetHubView.vue (B20 feature)
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import { api } from '@/services/apiBase'
import type { Preset } from './usePresetFilters'

// ==========================================================================
// Types
// ==========================================================================

export interface JobDetails {
  run_id: string
  job_name?: string
  machine_id?: string
  post_id?: string
  use_helical?: boolean
  sim_time_s?: number
  sim_energy_j?: number
  sim_issue_count?: number
  sim_max_dev_pct?: number
  created_at?: string
}

export interface TooltipPosition {
  x: number
  y: number
}

export interface JobTooltipState {
  /** ID of preset currently being hovered */
  hoveredPresetId: Ref<string | null>
  /** Tooltip position on screen */
  tooltipPosition: Ref<TooltipPosition>
  /** Cached job details by run_id */
  jobDetailsCache: Ref<Record<string, JobDetails>>
  /** Current job details for hovered preset */
  currentJobDetails: ComputedRef<JobDetails | null>
  /** Show tooltip for a preset */
  showJobTooltip: (preset: Preset, event: MouseEvent) => void
  /** Hide tooltip */
  hideJobTooltip: () => void
  /** Navigate to job history */
  viewJobInHistory: (runId: string) => void
  /** Format seconds to human-readable time */
  formatTime: (seconds: number) => string
  /** Format joules to human-readable energy */
  formatEnergy: (joules: number) => string
  /** Format ISO date to locale string */
  formatDate: (isoString: string | undefined) => string
}

// ==========================================================================
// Composable
// ==========================================================================

export function useJobTooltip(
  getPresets: () => Preset[],
  onViewJob?: (runId: string) => void
): JobTooltipState {
  const hoveredPresetId = ref<string | null>(null)
  const tooltipPosition = ref<TooltipPosition>({ x: 0, y: 0 })
  const jobDetailsCache = ref<Record<string, JobDetails>>({})

  // ========================================================================
  // Computed
  // ========================================================================

  const currentJobDetails = computed<JobDetails | null>(() => {
    if (!hoveredPresetId.value) return null
    const preset = getPresets().find((p) => p.id === hoveredPresetId.value)
    if (!preset?.job_source_id) return null
    return jobDetailsCache.value[preset.job_source_id] || null
  })

  // ========================================================================
  // Methods
  // ========================================================================

  async function fetchJobDetails(runId: string) {
    if (jobDetailsCache.value[runId]) return

    try {
      const response = await api(
        `/api/cam/job-int/log/${encodeURIComponent(runId)}`
      )
      if (response.ok) {
        jobDetailsCache.value[runId] = await response.json()
      }
    } catch (error) {
      console.error('Failed to fetch job details:', error)
    }
  }

  function showJobTooltip(preset: Preset, event: MouseEvent) {
    if (!preset.job_source_id) return

    hoveredPresetId.value = preset.id
    tooltipPosition.value = {
      x: event.clientX + 15,
      y: event.clientY + 15,
    }

    fetchJobDetails(preset.job_source_id)
  }

  function hideJobTooltip() {
    hoveredPresetId.value = null
  }

  function viewJobInHistory(runId: string) {
    // Allow custom handler or default console log
    if (onViewJob) {
      onViewJob(runId)
    } else {
      console.log('View job:', runId)
    }
    hideJobTooltip()
  }

  // ========================================================================
  // Formatters
  // ========================================================================

  function formatTime(seconds: number): string {
    if (seconds < 1) return `${(seconds * 1000).toFixed(0)} ms`
    if (seconds < 60) return `${seconds.toFixed(2)} s`
    const m = Math.floor(seconds / 60)
    const s = seconds - m * 60
    return `${m}m ${s.toFixed(0)}s`
  }

  function formatEnergy(joules: number): string {
    if (joules < 1000) return `${joules.toFixed(0)} J`
    return `${(joules / 1000).toFixed(2)} kJ`
  }

  function formatDate(isoString: string | undefined): string {
    if (!isoString) return '—'
    try {
      const date = new Date(isoString)
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
    } catch {
      return isoString
    }
  }

  return {
    hoveredPresetId,
    tooltipPosition,
    jobDetailsCache,
    currentJobDetails,
    showJobTooltip,
    hideJobTooltip,
    viewJobInHistory,
    formatTime,
    formatEnergy,
    formatDate,
  }
}
