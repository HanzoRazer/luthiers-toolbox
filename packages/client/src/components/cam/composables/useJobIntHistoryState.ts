/**
 * JobIntHistory state composable.
 */
import { ref, reactive } from 'vue'
import type { Ref, UnwrapNestedRefs } from 'vue'
import type { JobIntLogEntry, JobIntFilters, CloneForm } from './jobIntHistoryTypes'

// ============================================================================
// Types
// ============================================================================

export interface JobIntHistoryStateReturn {
  // List state
  items: Ref<JobIntLogEntry[]>
  total: Ref<number>
  loading: Ref<boolean>
  errorMessage: Ref<string | null>

  // Filters
  filters: UnwrapNestedRefs<JobIntFilters>

  // Pagination
  limit: Ref<number>
  offset: Ref<number>

  // Clone modal state
  showCloneModal: Ref<boolean>
  selectedEntry: Ref<JobIntLogEntry | null>
  cloning: Ref<boolean>
  cloneSuccess: Ref<boolean>
  cloneError: Ref<string | null>
  cloneForm: UnwrapNestedRefs<CloneForm>
}

// ============================================================================
// Composable
// ============================================================================

export function useJobIntHistoryState(): JobIntHistoryStateReturn {
  // List state
  const items = ref<JobIntLogEntry[]>([])
  const total = ref(0)
  const loading = ref(false)
  const errorMessage = ref<string | null>(null)

  // Filters
  const filters = reactive<JobIntFilters>({
    machine_id: '',
    post_id: '',
    helical_only: false,
    favorites_only: false
  })

  // Pagination
  const limit = ref(50)
  const offset = ref(0)

  // Clone modal state
  const showCloneModal = ref(false)
  const selectedEntry = ref<JobIntLogEntry | null>(null)
  const cloning = ref(false)
  const cloneSuccess = ref(false)
  const cloneError = ref<string | null>(null)
  const cloneForm = reactive<CloneForm>({
    name: '',
    description: '',
    kind: 'cam',
    tagsInput: '',
    cam_params: {}
  })

  return {
    items,
    total,
    loading,
    errorMessage,
    filters,
    limit,
    offset,
    showCloneModal,
    selectedEntry,
    cloning,
    cloneSuccess,
    cloneError,
    cloneForm
  }
}
