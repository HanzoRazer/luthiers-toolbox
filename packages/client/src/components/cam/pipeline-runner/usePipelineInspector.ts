/**
 * Composable for machine/post profile inspection.
 */
import { ref, type Ref } from 'vue'
import type { MachineProfile, PostProfile } from './pipelineTypes'

// ============================================================================
// Types
// ============================================================================

export interface PipelineInspectorState {
  inspectorMachine: Ref<MachineProfile | null>
  inspectorPost: Ref<PostProfile | null>
  refreshInspector: (machineId: string | null, postId: string | null) => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function usePipelineInspector(): PipelineInspectorState {
  const inspectorMachine = ref<MachineProfile | null>(null)
  const inspectorPost = ref<PostProfile | null>(null)

  async function refreshInspector(
    machineId: string | null,
    postId: string | null
  ): Promise<void> {
    inspectorMachine.value = null
    inspectorPost.value = null

    try {
      if (machineId) {
        const resp = await fetch(`/cam/machines/${machineId}`)
        if (resp.ok) {
          inspectorMachine.value = await resp.json() as MachineProfile
        }
      }
    } catch {
      // ignore
    }

    try {
      if (postId) {
        const resp = await fetch(`/cam/posts/${postId}`)
        if (resp.ok) {
          inspectorPost.value = await resp.json() as PostProfile
        }
      }
    } catch {
      // ignore
    }
  }

  return {
    inspectorMachine,
    inspectorPost,
    refreshInspector
  }
}
