/**
 * Composable for vision provider loading and selection.
 * Extracted from VisionAttachToRunWidget.vue
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import {
  getProviders,
  type VisionProvider,
  type ProviderName,
} from '../api/visionApi'

// =============================================================================
// Types
// =============================================================================

export interface VisionProvidersState {
  /** Available providers */
  providers: Ref<VisionProvider[]>
  /** Currently selected provider */
  provider: Ref<ProviderName>
  /** Providers that are configured and available */
  configuredProviders: ComputedRef<VisionProvider[]>
  /** Load providers from API */
  loadProviders: () => Promise<void>
}

// =============================================================================
// Composable
// =============================================================================

export function useVisionProviders(): VisionProvidersState {
  const providers = ref<VisionProvider[]>([])
  const provider = ref<ProviderName>('openai')

  // ===========================================================================
  // Computed
  // ===========================================================================

  const configuredProviders = computed(() => {
    return providers.value.filter((p) => p.configured)
  })

  // ===========================================================================
  // Methods
  // ===========================================================================

  async function loadProviders() {
    try {
      const res = await getProviders()
      providers.value = res.providers

      // Default to first configured provider
      const configured = res.providers.find((p) => p.configured)
      if (configured) {
        provider.value = configured.name as ProviderName
      }
    } catch (e: any) {
      console.warn('Failed to load providers:', e)
    }
  }

  return {
    providers,
    provider,
    configuredProviders,
    loadProviders,
  }
}
