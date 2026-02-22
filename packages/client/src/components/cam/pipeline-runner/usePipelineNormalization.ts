/**
 * Composable for CAM intent normalization in pipeline specs.
 */
import { ref, type Ref } from 'vue'
import { normalizeCamIntent } from '@/services/rmosCamIntentApi'
import type { NormalizationEntry } from './pipelineTypes'

// ============================================================================
// Types
// ============================================================================

export interface PipelineNormalizationState {
  strictNormalize: Ref<boolean>
  normalizationIssues: Ref<NormalizationEntry[]>
  normalizePipelineSpec: (spec: any) => Promise<{ normalized: any; issues: NormalizationEntry[] }>
}

// ============================================================================
// Helpers
// ============================================================================

function isPlainObject(v: unknown): v is Record<string, any> {
  return !!v && typeof v === 'object' && !Array.isArray(v)
}

/**
 * Heuristic: identify "intent-like" objects without importing CamIntent types.
 */
function looksLikeCamIntent(obj: Record<string, any>): boolean {
  if ('operation' in obj) return true
  if ('operation_type' in obj) return true
  if ('op' in obj) return true
  if ('tool_id' in obj && ('material_id' in obj || 'stock' in obj)) return true
  if ('mode' in obj && (obj.mode === 'router_3axis' || obj.mode === 'saw')) return true
  return false
}

// ============================================================================
// Composable
// ============================================================================

export function usePipelineNormalization(): PipelineNormalizationState {
  const strictNormalize = ref(false)
  const normalizationIssues = ref<NormalizationEntry[]>([])

  /**
   * Deep-walk a pipeline spec and normalize any CamIntent-like objects.
   */
  async function normalizePipelineSpec(spec: any): Promise<{
    normalized: any
    issues: NormalizationEntry[]
  }> {
    const collected: NormalizationEntry[] = []

    async function walk(node: any, path: string): Promise<any> {
      if (node == null) return node

      if (Array.isArray(node)) {
        const out: any[] = []
        for (let i = 0; i < node.length; i++) {
          out.push(await walk(node[i], `${path}[${i}]`))
        }
        return out
      }

      if (isPlainObject(node)) {
        // Normalize directly if it looks like a CamIntent
        if (looksLikeCamIntent(node)) {
          try {
            const resp = await normalizeCamIntent(
              { intent: node as any, strict: false },
              { requestId: `CamPipelineRunner.normalizePipelineSpec.${Date.now()}` }
            )
            if (resp.issues?.length) {
              collected.push({ path, issues: resp.issues })
            }
            return resp.intent
          } catch {
            // If normalization fails, keep original
            return node
          }
        }

        // Otherwise deep-walk properties
        const out: Record<string, any> = { ...node }
        for (const key of Object.keys(out)) {
          out[key] = await walk(out[key], path ? `${path}.${key}` : key)
        }
        return out
      }

      // primitives
      return node
    }

    const normalized = await walk(spec, 'pipeline')
    return { normalized, issues: collected }
  }

  return {
    strictNormalize,
    normalizationIssues,
    normalizePipelineSpec
  }
}
