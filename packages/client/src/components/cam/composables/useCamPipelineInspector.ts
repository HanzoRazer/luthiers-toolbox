/**
 * CamPipeline inspector composable.
 */
import type { Ref } from 'vue'
import type { MachineProfile, PostProfile } from './camPipelineTypes'

// ============================================================================
// Types
// ============================================================================

export interface CamPipelineInspectorReturn {
  refreshInspector: () => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useCamPipelineInspector(
  machineId: Ref<string | null>,
  postId: Ref<string | null>,
  inspectorMachine: Ref<MachineProfile | null>,
  inspectorPost: Ref<PostProfile | null>
): CamPipelineInspectorReturn {
  /**
   * Fetch machine and post profiles for the inspector display.
   */
  async function refreshInspector(): Promise<void> {
    inspectorMachine.value = null
    inspectorPost.value = null

    try {
      if (machineId.value) {
        const resp = await fetch(`/cam/machines/${machineId.value}`)
        if (resp.ok) inspectorMachine.value = (await resp.json()) as MachineProfile
      }
    } catch {
      // ignore
    }

    try {
      if (postId.value) {
        const resp = await fetch(`/cam/posts/${postId.value}`)
        if (resp.ok) inspectorPost.value = (await resp.json()) as PostProfile
      }
    } catch {
      // ignore
    }
  }

  return {
    refreshInspector
  }
}
