/**
 * RmosRunViewer CSS class helper composable.
 */
import { badges } from '@/styles/shared'
import styles from '../../RmosRunViewerView.module.css'

// ============================================================================
// Types
// ============================================================================

export interface RmosRunViewerStylesReturn {
  statusBadgeClass: (status: string) => string
  gateBadgeClass: (gate: string) => string
  riskBadgeClass: (level: string) => string
  rulePillClass: (level: string) => string
}

// ============================================================================
// Composable
// ============================================================================

export function useRmosRunViewerStyles(): RmosRunViewerStylesReturn {
  /**
   * Get CSS class for status badge.
   */
  function statusBadgeClass(status: string): string {
    const s = status?.toLowerCase()
    if (s === 'completed' || s === 'success') return badges.badgeSuccess
    if (s === 'pending' || s === 'in_progress') return badges.badgeWarning
    if (s === 'failed' || s === 'error') return badges.badgeError
    return badges.badge
  }

  /**
   * Get CSS class for gate badge.
   */
  function gateBadgeClass(gate: string): string {
    const g = gate?.toLowerCase()
    if (g === 'approved' || g === 'green') return badges.badgeGreen
    if (g === 'blocked' || g === 'red') return badges.badgeRed
    if (g === 'pending' || g === 'yellow') return badges.badgeYellow
    return badges.badge
  }

  /**
   * Get CSS class for risk badge.
   */
  function riskBadgeClass(level: string): string {
    const l = level?.toLowerCase()
    if (l === 'green') return badges.badgeGreen
    if (l === 'yellow') return badges.badgeYellow
    if (l === 'red') return badges.badgeRed
    return badges.badge
  }

  /**
   * Get CSS class for rule pill.
   */
  function rulePillClass(level: string): string {
    const l = level?.toUpperCase()
    if (l === 'RED') return styles.rulePillRed
    if (l === 'YELLOW') return styles.rulePillYellow
    return styles.rulePill
  }

  return {
    statusBadgeClass,
    gateBadgeClass,
    riskBadgeClass,
    rulePillClass
  }
}
