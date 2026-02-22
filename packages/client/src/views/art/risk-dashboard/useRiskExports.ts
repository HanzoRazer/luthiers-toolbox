/**
 * Composable for RiskDashboard export functions.
 */
import { type Ref } from 'vue'
import axios from 'axios'
import { csvEscape } from './riskFormatters'
import type { Bucket, BucketEntry } from '@/components/dashboard'

// ============================================================================
// Types
// ============================================================================

export interface RiskExportsState {
  exportCsv: () => void
  exportBucketCsv: () => Promise<void>
  exportBucketJson: () => Promise<void>
  downloadBucketJson: () => Promise<void>
  downloadSnapshotJson: () => Promise<void>
}

export interface UseRiskExportsOptions {
  filteredBuckets: Ref<Bucket[]>
  selectedBucket: Ref<Bucket | null>
  bucketEntries: Ref<BucketEntry[]>
  jobFilter: Ref<string>
  since: Ref<string>
  until: Ref<string>
  setError: (msg: string) => void
}

// ============================================================================
// Helpers
// ============================================================================

function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function buildFilenameTimestamp(): string {
  return new Date().toISOString().replace(/[:.]/g, '-')
}

// ============================================================================
// Composable
// ============================================================================

export function useRiskExports(options: UseRiskExportsOptions): RiskExportsState {
  const {
    filteredBuckets,
    selectedBucket,
    bucketEntries,
    jobFilter,
    since,
    until,
    setError
  } = options

  function buildWindowPart(): string {
    return (
      (since.value ? `_from-${since.value}` : '') +
      (until.value ? `_to-${until.value}` : '')
    )
  }

  function exportCsv(): void {
    if (!filteredBuckets.value.length) return

    const headers = [
      'lane',
      'preset',
      'count',
      'avg_added',
      'avg_removed',
      'avg_unchanged',
      'risk_score',
      'risk_label'
    ]

    const rows = filteredBuckets.value.map((b) =>
      [
        b.lane,
        b.preset,
        b.count,
        b.avgAdded,
        b.avgRemoved,
        b.avgUnchanged,
        b.riskScore,
        b.riskLabel
      ]
        .map((val) => csvEscape(val))
        .join(',')
    )

    const csvContent = [headers.join(','), ...rows].join('\r\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })

    const stamp = buildFilenameTimestamp()
    const windowPart = buildWindowPart()
    const filename = `crosslab_risk_aggregate${windowPart}_${stamp}.csv`

    downloadBlob(blob, filename)
  }

  async function exportBucketCsv(): Promise<void> {
    if (!selectedBucket.value) return

    try {
      const params: Record<string, string> = {
        lane: selectedBucket.value.lane,
        preset: selectedBucket.value.preset,
        format: 'csv'
      }

      const res = await axios.get('/api/compare/risk_bucket_export', {
        params,
        responseType: 'blob'
      })

      const filename = `risk_bucket_${selectedBucket.value.lane}_${selectedBucket.value.preset}.csv`
      downloadBlob(new Blob([res.data]), filename)
    } catch (err) {
      console.error('Failed to export bucket CSV', err)
    }
  }

  async function exportBucketJson(): Promise<void> {
    if (!selectedBucket.value) return

    try {
      const params: Record<string, string> = {
        lane: selectedBucket.value.lane,
        preset: selectedBucket.value.preset,
        format: 'json'
      }

      const res = await axios.get('/api/compare/risk_bucket_export', {
        params,
        responseType: 'blob'
      })

      const filename = `risk_bucket_${selectedBucket.value.lane}_${selectedBucket.value.preset}.json`
      downloadBlob(new Blob([res.data]), filename)
    } catch (err) {
      console.error('Failed to export bucket JSON', err)
    }
  }

  async function downloadBucketJson(): Promise<void> {
    if (!selectedBucket.value) return
    const b = selectedBucket.value

    try {
      const params: Record<string, string> = {
        lane: b.lane,
        preset: b.preset
      }
      if (jobFilter.value) {
        params.job_hint = jobFilter.value
      }

      const res = await axios.get('/api/compare/risk_bucket_report', {
        params,
        responseType: 'json'
      })

      const jsonData = res.data
      const blob = new Blob([JSON.stringify(jsonData, null, 2)], {
        type: 'application/json'
      })

      const hintPart = jobFilter.value ? `_hint-${jobFilter.value}` : ''
      const windowPart = buildWindowPart()
      const stamp = buildFilenameTimestamp()
      const filename = `bucket_report_${b.lane}_${b.preset}${hintPart}${windowPart}_${stamp}.json`

      downloadBlob(blob, filename)
    } catch (err) {
      console.error('Failed to download bucket JSON report', err)
      setError('Failed to download bucket JSON report.')
    }
  }

  async function downloadSnapshotJson(): Promise<void> {
    try {
      const params: Record<string, string> = {}
      if (since.value) params.since = since.value
      if (until.value) params.until = until.value

      const res = await axios.get('/api/compare/risk_snapshot', {
        params,
        responseType: 'json'
      })

      const jsonData = res.data
      const blob = new Blob([JSON.stringify(jsonData, null, 2)], {
        type: 'application/json'
      })

      const windowPart = buildWindowPart()
      const stamp = buildFilenameTimestamp()
      const filename = `risk_snapshot${windowPart}_${stamp}.json`

      downloadBlob(blob, filename)
    } catch (err) {
      console.error('Failed to download global risk snapshot', err)
    }
  }

  return {
    exportCsv,
    exportBucketCsv,
    exportBucketJson,
    downloadBucketJson,
    downloadSnapshotJson
  }
}
