/**
 * RmosRunViewer state composable.
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import type { RouteLocationNormalizedLoaded } from 'vue-router'
import type { RunArtifactDetail } from '@/api/rmosRuns'
import { explainRule } from '@/lib/feasibilityRuleRegistry'
import type { AssistantExplanation, RunAttachment, ExplainedRule } from './rmosRunViewerTypes'

// ============================================================================
// Types
// ============================================================================

export interface RmosRunViewerStateReturn {
  // Core state
  run: Ref<RunArtifactDetail | null>
  loading: Ref<boolean>
  error: Ref<string | null>
  showWhy: Ref<boolean>

  // Computed
  runId: ComputedRef<string>
  triggeredRuleIds: ComputedRef<string[]>
  triggeredRules: ComputedRef<ExplainedRule[]>
  hasExplainability: ComputedRef<boolean>
  riskLevel: ComputedRef<string>
  overrideAttachment: ComputedRef<RunAttachment | null>
  parentRunId: ComputedRef<string | null>

  // Phase 5: Advisory Explanation
  explainError: Ref<string | null>
  isExplaining: Ref<boolean>
  assistantExplanation: Ref<AssistantExplanation | null>
  assistantExplanationAttachment: ComputedRef<RunAttachment | null>
}

// ============================================================================
// Composable
// ============================================================================

export function useRmosRunViewerState(
  route: RouteLocationNormalizedLoaded
): RmosRunViewerStateReturn {
  // Core state
  const run = ref<RunArtifactDetail | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const showWhy = ref(false)

  // Phase 5: Advisory Explanation state
  const explainError = ref<string | null>(null)
  const isExplaining = ref(false)
  const assistantExplanation = ref<AssistantExplanation | null>(null)

  // Computed
  const runId = computed(() => route.params.id as string)

  // Phase 3.3: Explainability - triggered rules
  const triggeredRuleIds = computed<string[]>(() => {
    const ids = run.value?.feasibility?.rules_triggered
    if (!Array.isArray(ids)) return []
    return ids.map((x: any) => String(x).trim().toUpperCase()).filter(Boolean)
  })

  const triggeredRules = computed<ExplainedRule[]>(() => {
    return triggeredRuleIds.value.map((rid) => explainRule(rid))
  })

  const hasExplainability = computed(() => triggeredRuleIds.value.length > 0)

  const riskLevel = computed(() => {
    return String(
      run.value?.feasibility?.risk_level || run.value?.gate_decision || ''
    ).toUpperCase()
  })

  const overrideAttachment = computed<RunAttachment | null>(() => {
    const atts = run.value?.attachments || []
    if (!Array.isArray(atts)) return null
    return atts.find((a: any) => a?.kind === 'override') ?? null
  })

  // Parent run for "Compare with Parent" button
  const parentRunId = computed(() => run.value?.parent_run_id || null)

  const assistantExplanationAttachment = computed<RunAttachment | null>(() => {
    const atts = run.value?.attachments || []
    if (!Array.isArray(atts)) return null
    return atts.find((a: any) => a?.kind === 'assistant_explanation') ?? null
  })

  return {
    // Core state
    run,
    loading,
    error,
    showWhy,

    // Computed
    runId,
    triggeredRuleIds,
    triggeredRules,
    hasExplainability,
    riskLevel,
    overrideAttachment,
    parentRunId,

    // Phase 5
    explainError,
    isExplaining,
    assistantExplanation,
    assistantExplanationAttachment
  }
}
