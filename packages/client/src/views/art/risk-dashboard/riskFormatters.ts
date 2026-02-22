/**
 * Formatting utilities for RiskDashboardCrossLab.
 */

// ============================================================================
// Date/Time Formatting
// ============================================================================

export function toIsoDate(d: Date): string {
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function formatMetaTime(ts?: string | null): string {
  if (!ts) return '—'
  try {
    const d = new Date(ts)
    return d.toLocaleString()
  } catch {
    return ts
  }
}

export function formatRelativeMetaTime(ts?: string | null): string {
  if (!ts) return 'unknown'
  const t = Date.parse(ts)
  if (isNaN(t)) return ts
  const now = Date.now()
  const diffMs = now - t
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHr = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHr / 24)

  if (diffDay > 0) return `${diffDay}d ago`
  if (diffHr > 0) return `${diffHr}h ago`
  if (diffMin > 0) return `${diffMin}m ago`
  return 'just now'
}

// ============================================================================
// CSV Utilities
// ============================================================================

export function csvEscape(val: unknown): string {
  if (val === null || val === undefined) return ''
  const s = String(val)
  if (s.includes(',') || s.includes('"') || s.includes('\n')) {
    return `"${s.replace(/"/g, '""')}"`
  }
  return s
}

// ============================================================================
// Risk Score
// ============================================================================

export function computeRiskScoreLabel(score: number): string {
  if (score < 1) return 'Low'
  if (score < 3) return 'Medium'
  if (score < 6) return 'High'
  return 'Extreme'
}

// ============================================================================
// Sparkline
// ============================================================================

export function buildSparklineFromSeries(
  values: number[],
  width: number,
  height: number
): string {
  if (!values.length) return ''

  const maxVal = Math.max(...values, 1)
  const n = values.length

  if (n === 1) {
    const y = height / 2
    return `0,${y} ${width},${y}`
  }

  const stepX = width / (n - 1)
  const points: string[] = []

  for (let i = 0; i < n; i++) {
    const x = stepX * i
    const v = values[i] ?? 0
    const norm = maxVal > 0 ? v / maxVal : 0
    const y = height - norm * (height - 2) - 1
    points.push(`${x.toFixed(1)},${y.toFixed(1)}`)
  }

  return points.join(' ')
}
