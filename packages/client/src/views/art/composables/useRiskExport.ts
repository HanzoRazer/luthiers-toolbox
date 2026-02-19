/**
 * Composable for risk dashboard export functionality.
 * Handles CSV and JSON exports for buckets and snapshots.
 */
import axios from 'axios'
import type { Bucket, BucketEntry } from './useRiskBuckets'

export interface RiskExportState {
  exportCsv: (buckets: Bucket[], since: string, until: string) => void
  exportBucketCsv: (bucket: Bucket | null) => Promise<void>
  exportBucketJson: (bucket: Bucket | null) => Promise<void>
  downloadBucketJson: (bucket: Bucket | null, entries: BucketEntry[], jobFilter: string, since: string, until: string) => Promise<void>
  downloadSnapshotJson: (since: string, until: string) => Promise<void>
}

function csvEscape(val: unknown): string {
  if (val === null || val === undefined) return ''
  const s = String(val)
  if (s.includes(',') || s.includes('"') || s.includes('\n')) {
    return `"${s.replace(/"/g, '""')}"`
  }
  return s
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function buildWindowPart(since: string, until: string): string {
  return (since ? `_from-${since}` : '') + (until ? `_to-${until}` : '')
}

function buildTimestamp(): string {
  return new Date().toISOString().replace(/[:.]/g, '-')
}

export function useRiskExport(): RiskExportState {
  function exportCsv(buckets: Bucket[], since: string, until: string) {
    if (!buckets.length) return

    const headers = ['lane', 'preset', 'count', 'avg_added', 'avg_removed', 'avg_unchanged', 'risk_score', 'risk_label']

    const rows = buckets.map((b) =>
      [b.lane, b.preset, b.count, b.avgAdded, b.avgRemoved, b.avgUnchanged, b.riskScore, b.riskLabel]
        .map((val) => csvEscape(val))
        .join(',')
    )

    const csvContent = [headers.join(','), ...rows].join('\r\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const filename = `crosslab_risk_aggregate${buildWindowPart(since, until)}_${buildTimestamp()}.csv`
    downloadBlob(blob, filename)
  }

  async function exportBucketCsv(bucket: Bucket | null) {
    if (!bucket) return

    try {
      const params: Record<string, string> = {
        lane: bucket.lane,
        preset: bucket.preset,
        format: 'csv',
      }
      const res = await axios.get('/api/compare/risk_bucket_export', {
        params,
        responseType: 'blob',
      })

      const filename = `risk_bucket_${bucket.lane}_${bucket.preset}.csv`
      downloadBlob(new Blob([res.data]), filename)
    } catch (err) {
      console.error('Failed to export bucket CSV', err)
    }
  }

  async function exportBucketJson(bucket: Bucket | null) {
    if (!bucket) return

    try {
      const params: Record<string, string> = {
        lane: bucket.lane,
        preset: bucket.preset,
        format: 'json',
      }
      const res = await axios.get('/api/compare/risk_bucket_export', {
        params,
        responseType: 'blob',
      })

      const filename = `risk_bucket_${bucket.lane}_${bucket.preset}.json`
      downloadBlob(new Blob([res.data]), filename)
    } catch (err) {
      console.error('Failed to export bucket JSON', err)
    }
  }

  async function downloadBucketJson(
    bucket: Bucket | null,
    _entries: BucketEntry[],
    jobFilter: string,
    since: string,
    until: string
  ) {
    if (!bucket) return

    try {
      const params: Record<string, string> = {
        lane: bucket.lane,
        preset: bucket.preset,
      }
      if (jobFilter) params.job_hint = jobFilter

      const res = await axios.get('/api/compare/risk_bucket_report', {
        params,
        responseType: 'json',
      })

      const jsonData = res.data
      const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: 'application/json' })
      const hintPart = jobFilter ? `_hint-${jobFilter}` : ''
      const filename = `bucket_report_${bucket.lane}_${bucket.preset}${hintPart}${buildWindowPart(since, until)}_${buildTimestamp()}.json`
      downloadBlob(blob, filename)
    } catch (err) {
      console.error('Failed to download bucket JSON report', err)
    }
  }

  async function downloadSnapshotJson(since: string, until: string) {
    try {
      const params: Record<string, string> = {}
      if (since) params.since = since
      if (until) params.until = until

      const res = await axios.get('/api/compare/risk_snapshot', {
        params,
        responseType: 'json',
      })

      const jsonData = res.data
      const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: 'application/json' })
      const filename = `risk_snapshot${buildWindowPart(since, until)}_${buildTimestamp()}.json`
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
    downloadSnapshotJson,
  }
}
