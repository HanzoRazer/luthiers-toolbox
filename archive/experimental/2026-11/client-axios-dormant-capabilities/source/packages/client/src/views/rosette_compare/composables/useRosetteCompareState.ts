/**
 * RosetteCompare state composable.
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import type {
  RosetteJob,
  RosetteCompareResult,
  CompareSnapshot
} from './rosetteCompareTypes'

// ============================================================================
// Types
// ============================================================================

export interface RosetteCompareStateReturn {
  // Jobs
  jobs: Ref<RosetteJob[]>
  jobsLoading: Ref<boolean>
  jobsError: Ref<string | null>

  // Selection
  selectedJobIdA: Ref<string>
  selectedJobIdB: Ref<string>

  // Compare
  compareResult: Ref<RosetteCompareResult | null>
  compareLoading: Ref<boolean>

  // Status
  statusMessage: Ref<string>
  statusIsError: Ref<boolean>
  statusClass: ComputedRef<string>

  // Snapshot
  saveSnapshotLoading: Ref<boolean>

  // History
  showHistory: Ref<boolean>
  historySnapshots: Ref<CompareSnapshot[]>
  historyLoading: Ref<boolean>

  // Grouping
  groupByPreset: Ref<boolean>
  expandedGroups: Ref<Set<string>>
}

// ============================================================================
// Composable
// ============================================================================

export function useRosetteCompareState(): RosetteCompareStateReturn {
  // Jobs
  const jobs = ref<RosetteJob[]>([])
  const jobsLoading = ref(false)
  const jobsError = ref<string | null>(null)

  // Selection
  const selectedJobIdA = ref<string>('')
  const selectedJobIdB = ref<string>('')

  // Compare
  const compareResult = ref<RosetteCompareResult | null>(null)
  const compareLoading = ref(false)

  // Status
  const statusMessage = ref('')
  const statusIsError = ref(false)

  const statusClass = computed(() =>
    statusIsError.value ? 'text-[10px] text-rose-600' : 'text-[10px] text-emerald-700'
  )

  // Snapshot
  const saveSnapshotLoading = ref(false)

  // History
  const showHistory = ref(false)
  const historySnapshots = ref<CompareSnapshot[]>([])
  const historyLoading = ref(false)

  // Grouping
  const groupByPreset = ref(false)
  const expandedGroups = ref<Set<string>>(new Set())

  return {
    // Jobs
    jobs,
    jobsLoading,
    jobsError,

    // Selection
    selectedJobIdA,
    selectedJobIdB,

    // Compare
    compareResult,
    compareLoading,

    // Status
    statusMessage,
    statusIsError,
    statusClass,

    // Snapshot
    saveSnapshotLoading,

    // History
    showHistory,
    historySnapshots,
    historyLoading,

    // Grouping
    groupByPreset,
    expandedGroups
  }
}
