/**
 * Styling utilities for SawLabDashboard risk visualization.
 */
import type { RiskBucketId } from '@/api/sawLab'

// ============================================================================
// Risk Styling
// ============================================================================

const RISK_BORDER_CLASSES: Record<RiskBucketId, string> = {
  unknown: 'border-gray-400',
  green: 'border-green-500',
  yellow: 'border-amber-500',
  orange: 'border-orange-500',
  red: 'border-rose-500'
}

const RISK_BADGE_CLASSES: Record<RiskBucketId, string> = {
  unknown: 'bg-gray-100 text-gray-700',
  green: 'bg-green-100 text-green-800',
  yellow: 'bg-amber-100 text-amber-800',
  orange: 'bg-orange-100 text-orange-800',
  red: 'bg-rose-100 text-rose-800'
}

const RISK_BAR_CLASSES: Record<RiskBucketId, string> = {
  unknown: 'bg-gray-400',
  green: 'bg-green-500',
  yellow: 'bg-amber-500',
  orange: 'bg-orange-500',
  red: 'bg-rose-500'
}

const STATUS_BADGE_CLASSES: Record<string, string> = {
  pending: 'bg-blue-100 text-blue-800',
  running: 'bg-purple-100 text-purple-800',
  completed: 'bg-green-100 text-green-800',
  error: 'bg-rose-100 text-rose-800'
}

export function riskBorderClass(bucketId: RiskBucketId): string {
  return RISK_BORDER_CLASSES[bucketId] || RISK_BORDER_CLASSES.unknown
}

export function riskBadgeClass(bucketId: RiskBucketId): string {
  return RISK_BADGE_CLASSES[bucketId] || RISK_BADGE_CLASSES.unknown
}

export function riskBarClass(bucketId: RiskBucketId): string {
  return RISK_BAR_CLASSES[bucketId] || RISK_BAR_CLASSES.unknown
}

export function riskScoreColor(score: number): string {
  if (score < 0.3) return 'text-green-700'
  if (score < 0.6) return 'text-amber-700'
  if (score < 0.85) return 'text-orange-700'
  return 'text-rose-700'
}

export function statusBadgeClass(status: string): string {
  return STATUS_BADGE_CLASSES[status] || 'bg-gray-100 text-gray-800'
}

// ============================================================================
// Formatting
// ============================================================================

export function formatDateTime(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

export function formatTime(date: Date): string {
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}
