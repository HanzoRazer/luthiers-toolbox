/**
 * RiskTimelineRelief actions composable.
 */
import { onMounted, type Ref, type ComputedRef } from 'vue'
import { api } from '@/services/apiBase'
import { csvEscape, downloadCsvFile } from '@/utils/downloadBlob'
import type { RiskJob, PresetFilter } from './riskTimelineTypes'

export interface RiskTimelineActionsReturn {
  fetchJobs: () => Promise<void>
  reload: () => void
  exportCompareCsv: () => Promise<void>
}

/**
 * Build CSV rows from jobs with window label.
 */
function buildCsvFromJobsWithWindow(jobsList: RiskJob[], windowLabel: string): string[] {
  const rows: string[] = []
  for (const job of jobsList) {
    const pipelineId = job.pipeline_id || job.pipelineId || ''
    const opId = job.op_id || job.opId || ''
    const created = job.created_at || job.timestamp || ''

    const preset = job.meta?.preset
    const presetName = preset?.name || ''
    const presetSource = preset?.source || ''

    const riskScore = job.analytics?.risk_score ?? ''
    const totalIssues = job.analytics?.total_issues ?? ''

    const criticalCount =
      job.analytics?.severity_counts?.critical != null
        ? job.analytics.severity_counts.critical
        : ''

    const stats = job.meta?.relief_sim_bridge || job.meta?.sim_stats || null

    const avgFloor =
      stats && typeof stats.avg_floor_thickness === 'number'
        ? stats.avg_floor_thickness
        : ''
    const minFloor =
      stats && typeof stats.min_floor_thickness === 'number'
        ? stats.min_floor_thickness
        : ''
    const maxLoad =
      stats && typeof stats.max_load_index === 'number' ? stats.max_load_index : ''
    const avgLoad =
      stats && typeof stats.avg_load_index === 'number' ? stats.avg_load_index : ''
    const totalVol =
      stats && typeof stats.total_removed_volume === 'number'
        ? stats.total_removed_volume
        : ''

    const stockThickness =
      job.meta && typeof job.meta.stock_thickness === 'number'
        ? job.meta.stock_thickness
        : ''

    const row = [
      csvEscape(windowLabel),
      csvEscape(job.id),
      csvEscape(pipelineId),
      csvEscape(opId),
      csvEscape(created),
      csvEscape(presetName),
      csvEscape(presetSource),
      csvEscape(riskScore),
      csvEscape(totalIssues),
      csvEscape(criticalCount),
      csvEscape(avgFloor),
      csvEscape(minFloor),
      csvEscape(maxLoad),
      csvEscape(avgLoad),
      csvEscape(totalVol),
      csvEscape(stockThickness)
    ].join(',')
    rows.push(row)
  }
  return rows
}

export function useRiskTimelineActions(
  jobs: Ref<RiskJob[]>,
  loading: Ref<boolean>,
  exporting: Ref<boolean>,
  presetFilter: Ref<PresetFilter>,
  pipelineFilter: Ref<string>,
  filteredJobs: ComputedRef<RiskJob[]>,
  filteredJobsPrev: ComputedRef<RiskJob[]>
): RiskTimelineActionsReturn {
  async function fetchJobs(): Promise<void> {
    loading.value = true
    try {
      const res = await api('/api/cam/jobs/risk_report')
      if (!res.ok) {
        console.error('Failed to fetch risk jobs:', await res.text())
        jobs.value = []
        return
      }
      const data = await res.json()
      jobs.value = Array.isArray(data) ? data : []
    } catch (err) {
      console.error('Risk jobs fetch error:', err)
      jobs.value = []
    } finally {
      loading.value = false
    }
  }

  function reload(): void {
    fetchJobs()
  }

  async function exportCompareCsv(): Promise<void> {
    exporting.value = true
    try {
      const header = [
        'window_label',
        'job_id',
        'pipeline_id',
        'op_id',
        'created_at',
        'preset_name',
        'preset_source',
        'risk_score',
        'total_issues',
        'critical_count',
        'avg_floor_thickness',
        'min_floor_thickness',
        'max_load_index',
        'avg_load_index',
        'total_removed_volume',
        'stock_thickness'
      ].join(',')

      const currentRows = buildCsvFromJobsWithWindow(filteredJobs.value, 'current')
      const prevRows = buildCsvFromJobsWithWindow(filteredJobsPrev.value, 'previous')

      const csv = [header, ...currentRows, ...prevRows].join('\r\n')

      const presetLabel =
        presetFilter.value === 'Any' ? 'mixed' : presetFilter.value.toLowerCase()
      const pipeLabel =
        pipelineFilter.value === 'Any' ? 'all' : pipelineFilter.value.toLowerCase()
      const ts = new Date().toISOString().replace(/[:.]/g, '-')
      const filename = `relief_risk_compare_${presetLabel}_${pipeLabel}_${ts}.csv`

      downloadCsvFile(csv, filename)
    } catch (err) {
      console.error('Compare CSV export failed:', err)
      alert('Compare CSV export failed. See console for details.')
    } finally {
      exporting.value = false
    }
  }

  onMounted(() => {
    fetchJobs()
  })

  return {
    fetchJobs,
    reload,
    exportCompareCsv
  }
}
