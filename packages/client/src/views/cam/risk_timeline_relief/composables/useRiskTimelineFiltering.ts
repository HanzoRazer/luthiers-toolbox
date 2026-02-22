/**
 * RiskTimelineRelief filtering composable.
 */
import { computed, type Ref, type ComputedRef } from 'vue'
import type { RiskJob, PresetFilter, RiskSummary, DateWindow } from './riskTimelineTypes'

export interface RiskTimelineFilteringReturn {
  filteredJobs: ComputedRef<RiskJob[]>
  filteredJobsPrev: ComputedRef<RiskJob[]>
  summary: ComputedRef<RiskSummary>
  summaryPrev: ComputedRef<RiskSummary>
  prevWindow: ComputedRef<DateWindow>
  classifyPresetName: (name: string | undefined) => PresetFilter
}

/**
 * Classify preset name into canonical bucket.
 */
function classifyPresetName(name: string | undefined): PresetFilter {
  if (!name) return 'Custom'
  const n = name.toLowerCase()
  if (n.includes('safe')) return 'Safe'
  if (n.includes('standard') || n.includes('std')) return 'Standard'
  if (n.includes('agg') || n.includes('aggressive')) return 'Aggressive'
  return 'Custom'
}

/**
 * Get job date.
 */
function jobDate(job: RiskJob): Date | null {
  const ts = job.created_at || job.timestamp
  if (!ts) return null
  return new Date(ts)
}

/**
 * Compute previous window based on from/to dates.
 */
function computePrevWindow(fromStr: string, toStr: string): DateWindow {
  if (fromStr && toStr) {
    const from = new Date(fromStr + 'T00:00:00')
    const to = new Date(toStr + 'T23:59:59.999')
    const spanMs = to.getTime() - from.getTime() + 1
    const prevTo = new Date(from.getTime() - 1)
    const prevFrom = new Date(prevTo.getTime() - spanMs + 1)
    return { from: prevFrom, to: prevTo }
  }

  if (!fromStr && toStr) {
    const to = new Date(toStr + 'T23:59:59.999')
    const prevTo = new Date(to.getTime() - 24 * 3600 * 1000)
    const prevFrom = new Date(prevTo.getTime() - 29 * 24 * 3600 * 1000)
    return { from: prevFrom, to: prevTo }
  }

  if (fromStr && !toStr) {
    const from = new Date(fromStr + 'T00:00:00')
    const prevTo = new Date(from.getTime() - 1)
    const prevFrom = new Date(prevTo.getTime() - 29 * 24 * 3600 * 1000)
    return { from: prevFrom, to: prevTo }
  }

  return { from: null, to: null }
}

/**
 * Check if job is in date range.
 */
function jobInDateRange(job: RiskJob, from: Date | null, to: Date | null): boolean {
  if (!from && !to) return true
  const d = jobDate(job)
  if (!d) return false
  if (from && d < from) return false
  if (to && d > to) return false
  return true
}

/**
 * Compute summary from jobs list.
 */
function computeSummary(list: RiskJob[]): RiskSummary {
  const jobsCount = list.length
  if (!jobsCount) {
    return { jobsCount: 0, avgRisk: 0, totalCritical: 0 }
  }

  let riskSum = 0
  let criticalSum = 0

  for (const job of list) {
    const risk = job.analytics?.risk_score ?? 0
    riskSum += risk

    const crit =
      job.analytics?.severity_counts?.critical != null
        ? job.analytics.severity_counts.critical
        : 0
    criticalSum += crit || 0
  }

  return {
    jobsCount,
    avgRisk: riskSum / jobsCount,
    totalCritical: criticalSum
  }
}

export function useRiskTimelineFiltering(
  jobs: Ref<RiskJob[]>,
  presetFilter: Ref<PresetFilter>,
  pipelineFilter: Ref<string>
): RiskTimelineFilteringReturn {
  /**
   * Jobs filtered by pipeline and preset.
   */
  const filteredJobs = computed(() => {
    return jobs.value.filter((job) => {
      const pipelineId = job.pipeline_id || job.pipelineId || ''
      if (pipelineFilter.value !== 'Any' && pipelineId !== pipelineFilter.value) {
        return false
      }

      if (presetFilter.value === 'Any') return true

      const preset = job.meta?.preset
      const category = classifyPresetName(preset?.name)
      return category === presetFilter.value
    })
  })

  /**
   * Previous window dates.
   */
  const prevWindow = computed(() => computePrevWindow('', ''))

  /**
   * Jobs filtered for previous window.
   */
  const filteredJobsPrev = computed(() => {
    const from = prevWindow.value.from
    const to = prevWindow.value.to

    return jobs.value.filter((job) => {
      const pipelineId = job.pipeline_id || job.pipelineId || ''
      if (pipelineFilter.value !== 'Any' && pipelineId !== pipelineFilter.value) {
        return false
      }

      if (presetFilter.value !== 'Any') {
        const preset = job.meta?.preset
        const category = classifyPresetName(preset?.name)
        if (category !== presetFilter.value) {
          return false
        }
      }

      return jobInDateRange(job, from, to)
    })
  })

  /**
   * Summary over filtered jobs.
   */
  const summary = computed(() => computeSummary(filteredJobs.value))

  /**
   * Summary over previous window jobs.
   */
  const summaryPrev = computed(() => computeSummary(filteredJobsPrev.value))

  return {
    filteredJobs,
    filteredJobsPrev,
    summary,
    summaryPrev,
    prevWindow,
    classifyPresetName
  }
}
