/**
 * Composable for candidate display helpers and summary computation.
 * Handles badge formatting, status text, summary counts, chip classes.
 */
import { computed, type Ref, type ComputedRef } from 'vue'
import type { ManufacturingCandidate, RiskLevel } from '@/sdk/rmos/runs'

export interface CandidateSummary {
  decisionCounts: Record<string, number>
  statusCounts: Record<string, number>
  total: number
}

export interface CandidateHelpersState {
  summary: ComputedRef<CandidateSummary>
  decidedByOptions: ComputedRef<string[]>
  decisionBadge: (decision: RiskLevel | null | undefined) => string
  statusText: (candidate: ManufacturingCandidate) => string
  notePreview: (note?: string | null) => string
  auditHover: (candidate: ManufacturingCandidate) => string
  chipClass: (active: boolean, kind?: 'neutral' | 'good' | 'warn' | 'bad' | 'muted') => Record<string, boolean>
}

type DecisionKey = 'NEEDS_DECISION' | 'GREEN' | 'YELLOW' | 'RED' | 'OTHER'
type StatusKey = 'PROPOSED' | 'ACCEPTED' | 'REJECTED' | 'OTHER'

function getDecisionKey(candidate: ManufacturingCandidate): DecisionKey {
  const d = candidate.decision ?? null
  if (d === null) return 'NEEDS_DECISION'
  if (d === 'GREEN' || d === 'YELLOW' || d === 'RED') return d
  return 'OTHER'
}

function getStatusKey(candidate: ManufacturingCandidate): StatusKey {
  const s = candidate.status ?? null
  if (s === 'PROPOSED' || s === 'ACCEPTED' || s === 'REJECTED') return s
  return 'OTHER'
}

function formatAuditLine(h: {
  decision?: string | null
  decided_by?: string | null
  decided_at_utc?: string | null
  note?: string | null
}): string {
  const d = h.decision ?? '—'
  const who = h.decided_by ?? '—'
  const when = h.decided_at_utc ?? '—'
  const note = h.note ? ` "${h.note.slice(0, 40)}${h.note.length > 40 ? '…' : ''}"` : ''
  return `${d} · ${who} · ${when}${note}`
}

export function useCandidateHelpers(candidates: Ref<ManufacturingCandidate[]>): CandidateHelpersState {
  const summary = computed<CandidateSummary>(() => {
    const decisionCounts: Record<string, number> = {
      NEEDS_DECISION: 0,
      GREEN: 0,
      YELLOW: 0,
      RED: 0,
      OTHER: 0,
    }
    const statusCounts: Record<string, number> = {
      PROPOSED: 0,
      ACCEPTED: 0,
      REJECTED: 0,
      OTHER: 0,
    }

    for (const c of candidates.value) {
      const dk = getDecisionKey(c)
      const sk = getStatusKey(c)
      decisionCounts[dk] = (decisionCounts[dk] || 0) + 1
      statusCounts[sk] = (statusCounts[sk] || 0) + 1
    }

    return {
      decisionCounts,
      statusCounts,
      total: candidates.value.length,
    }
  })

  const decidedByOptions = computed(() => {
    const set = new Set<string>()
    for (const c of candidates.value) {
      const v = (c.decided_by ?? '').trim()
      if (v) set.add(v)
    }
    return Array.from(set).sort((a, b) => a.localeCompare(b))
  })

  function decisionBadge(decision: RiskLevel | null | undefined): string {
    if (decision == null) return 'NEEDS_DECISION'
    return decision
  }

  function statusText(candidate: ManufacturingCandidate): string {
    if (candidate.decision == null) return 'Needs decision'
    if (candidate.decision === 'GREEN') return 'Accepted'
    if (candidate.decision === 'YELLOW') return 'Caution'
    if (candidate.decision === 'RED') return 'Rejected'
    return '—'
  }

  function notePreview(note?: string | null): string {
    const n = note ?? ''
    if (!n) return '—'
    return n.length > 120 ? n.slice(0, 120) + '…' : n
  }

  function auditHover(candidate: ManufacturingCandidate): string {
    const who = candidate.decided_by ?? '—'
    const when = candidate.decided_at_utc ?? '—'
    const note = candidate.decision_note ?? ''
    const preview = note ? (note.length > 80 ? note.slice(0, 80) + '…' : note) : '—'

    const lines = [
      `Decision: ${decisionBadge(candidate.decision)}`,
      `By: ${who}`,
      `At: ${when}`,
      `Note: ${preview}`,
    ]

    if (candidate.decision_history && candidate.decision_history.length > 0) {
      lines.push('History:')
      for (const h of candidate.decision_history.slice(-5)) {
        lines.push(`  ${formatAuditLine(h)}`)
      }
    }

    return lines.join('\n')
  }

  function chipClass(
    active: boolean,
    kind: 'neutral' | 'good' | 'warn' | 'bad' | 'muted' = 'neutral'
  ): Record<string, boolean> {
    return {
      chip: true,
      active,
      neutral: kind === 'neutral',
      good: kind === 'good',
      warn: kind === 'warn',
      bad: kind === 'bad',
      muted: kind === 'muted',
    }
  }

  return {
    summary,
    decidedByOptions,
    decisionBadge,
    statusText,
    notePreview,
    auditHover,
    chipClass,
  }
}
