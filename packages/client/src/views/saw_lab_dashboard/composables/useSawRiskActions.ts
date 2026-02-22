/**
 * Composable for SawLabDashboard risk actions computation and override handling.
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import type { RunSummaryItem } from '@/api/sawLab'

// ============================================================================
// Types
// ============================================================================

export type ActionSeverity = 'critical' | 'warning' | 'info'
export type ActionType = 'apply_override' | 'manual_check'

export interface RiskAction {
  title: string
  description: string
  severity: ActionSeverity
  action_type: ActionType
  suggested_override: string | null
}

export interface PendingOverride {
  title: string
  suggested_override: string
  action_type: string
}

export interface SawRiskActionsState {
  pendingOverride: Ref<PendingOverride | null>
  computedActions: ComputedRef<RiskAction[]>
  applyOverride: (action: RiskAction) => void
  confirmApplyOverride: (run: RunSummaryItem, onSuccess: () => Promise<void>) => Promise<void>
  cancelOverride: () => void
}

// ============================================================================
// Composable
// ============================================================================

export function useSawRiskActions(
  riskActionsRun: Ref<RunSummaryItem | null>,
  setError: (msg: string) => void
): SawRiskActionsState {
  const pendingOverride = ref<PendingOverride | null>(null)

  const computedActions = computed<RiskAction[]>(() => {
    if (!riskActionsRun.value || !riskActionsRun.value.metrics) return []

    const actions: RiskAction[] = []
    const metrics = riskActionsRun.value.metrics
    const avgLoad = metrics.avg_spindle_load_pct || 0
    const maxLoad = metrics.max_spindle_load_pct || 0
    const avgVibration = metrics.avg_vibration_rms || 0

    // High load detection
    if (avgLoad > 80) {
      actions.push({
        title: 'High Average Spindle Load Detected',
        description: `Average load of ${avgLoad.toFixed(1)}% exceeds safe threshold (80%). Reduce feed rate to prevent blade damage.`,
        severity: 'critical',
        action_type: 'apply_override',
        suggested_override: 'Feed rate -20%'
      })
    } else if (avgLoad > 70) {
      actions.push({
        title: 'Elevated Spindle Load',
        description: `Average load of ${avgLoad.toFixed(1)}% is approaching limits. Consider reducing feed rate.`,
        severity: 'warning',
        action_type: 'apply_override',
        suggested_override: 'Feed rate -10%'
      })
    }

    // Peak load detection
    if (maxLoad > 90) {
      actions.push({
        title: 'Critical Peak Load',
        description: `Peak load of ${maxLoad.toFixed(1)}% indicates potential stall conditions. Immediate feed reduction required.`,
        severity: 'critical',
        action_type: 'apply_override',
        suggested_override: 'Feed rate -30%'
      })
    }

    // Low load - can speed up
    if (avgLoad < 40 && maxLoad < 50) {
      actions.push({
        title: 'Low Spindle Load - Optimization Opportunity',
        description: `Average load of ${avgLoad.toFixed(1)}% suggests feed rate can be safely increased for faster cycle times.`,
        severity: 'info',
        action_type: 'apply_override',
        suggested_override: 'Feed rate +15%'
      })
    }

    // Vibration detection
    if (avgVibration > 10) {
      actions.push({
        title: 'Excessive Vibration Detected',
        description: `Average vibration of ${avgVibration.toFixed(2)} mm/s RMS indicates blade imbalance or looseness. Inspect blade mounting.`,
        severity: 'critical',
        action_type: 'manual_check',
        suggested_override: null
      })
    } else if (avgVibration > 5) {
      actions.push({
        title: 'Elevated Vibration',
        description: `Vibration of ${avgVibration.toFixed(2)} mm/s RMS is above normal. Check blade condition and mounting.`,
        severity: 'warning',
        action_type: 'manual_check',
        suggested_override: null
      })
    }

    return actions
  })

  function applyOverride(action: RiskAction): void {
    if (action.suggested_override) {
      pendingOverride.value = {
        title: action.title,
        suggested_override: action.suggested_override,
        action_type: action.action_type
      }
    }
  }

  async function confirmApplyOverride(
    run: RunSummaryItem,
    onSuccess: () => Promise<void>
  ): Promise<void> {
    if (!pendingOverride.value) return

    try {
      // TODO: Call backend API to apply override
      console.log('Applying override:', {
        run_id: run.run_id,
        override: pendingOverride.value.suggested_override,
        action: pendingOverride.value.title
      })

      // Show success message (placeholder)
      alert(`✓ Override applied: ${pendingOverride.value.suggested_override}`)

      // Reload dashboard
      await onSuccess()

      // Clear pending
      pendingOverride.value = null
    } catch (err: unknown) {
      const error = err as { message?: string }
      setError(error.message || 'Failed to apply override')
      console.error('Override apply error:', err)
    }
  }

  function cancelOverride(): void {
    pendingOverride.value = null
  }

  return {
    pendingOverride,
    computedActions,
    applyOverride,
    confirmApplyOverride,
    cancelOverride
  }
}
