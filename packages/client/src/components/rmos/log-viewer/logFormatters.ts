/**
 * Formatting utilities for RMOS log viewer.
 */

// ============================================================================
// Time Formatting
// ============================================================================

export function formatTime(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleString()
  } catch {
    return iso
  }
}

export function formatTimeShort(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return iso
  }
}

// ============================================================================
// ID Formatting
// ============================================================================

export function truncateRunId(runId: string, length = 16): string {
  if (runId.length <= length) return runId
  return `${runId.slice(0, length)}...`
}

// ============================================================================
// Risk Level Styling
// ============================================================================

export function riskLevelClass(level: string): string {
  switch (level) {
    case 'GREEN':
      return 'risk-green'
    case 'YELLOW':
      return 'risk-yellow'
    case 'RED':
    case 'ERROR':
      return 'risk-red'
    default:
      return ''
  }
}

export function riskLevelColor(level: string): string {
  switch (level) {
    case 'GREEN':
      return '#16a34a'
    case 'YELLOW':
      return '#ca8a04'
    case 'RED':
    case 'ERROR':
      return '#dc2626'
    default:
      return '#666666'
  }
}
