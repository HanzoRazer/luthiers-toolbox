/**
 * JobIntHistory helper functions.
 */

// ============================================================================
// Types
// ============================================================================

export interface JobIntHistoryHelpersReturn {
  formatTime: (seconds: number | null) => string
}

// ============================================================================
// Composable
// ============================================================================

export function useJobIntHistoryHelpers(): JobIntHistoryHelpersReturn {
  function formatTime(seconds: number | null): string {
    if (seconds == null) return '—'
    if (seconds < 1) return `${(seconds * 1000).toFixed(0)} ms`
    if (seconds < 60) return `${seconds.toFixed(2)} s`
    const m = Math.floor(seconds / 60)
    const s = seconds - m * 60
    return `${m}m ${s.toFixed(0)}s`
  }

  return {
    formatTime
  }
}
