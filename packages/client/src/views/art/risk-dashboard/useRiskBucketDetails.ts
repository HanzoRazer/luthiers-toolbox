/**
 * Composable for RiskDashboard bucket details panel.
 */
import { ref, type Ref } from 'vue'
import axios from 'axios'
import type { Bucket, BucketEntry } from '@/components/dashboard'

// ============================================================================
// Types
// ============================================================================

export interface RiskBucketDetailsState {
  selectedBucket: Ref<Bucket | null>
  bucketEntries: Ref<BucketEntry[]>
  bucketEntriesLoading: Ref<boolean>
  bucketEntriesError: Ref<string | null>
  loadBucketDetails: (bucket: Bucket) => Promise<void>
  clearBucketDetails: () => void
}

export interface UseRiskBucketDetailsOptions {
  jobFilter: Ref<string>
}

// ============================================================================
// Composable
// ============================================================================

export function useRiskBucketDetails(
  options: UseRiskBucketDetailsOptions
): RiskBucketDetailsState {
  const { jobFilter } = options

  const selectedBucket = ref<Bucket | null>(null)
  const bucketEntries = ref<BucketEntry[]>([])
  const bucketEntriesLoading = ref(false)
  const bucketEntriesError = ref<string | null>(null)

  async function loadBucketDetails(bucket: Bucket): Promise<void> {
    selectedBucket.value = bucket
    bucketEntriesLoading.value = true
    bucketEntriesError.value = null
    bucketEntries.value = []

    try {
      const params: Record<string, string> = {
        lane: bucket.lane,
        preset: bucket.preset
      }
      if (jobFilter.value) {
        params.job_hint = jobFilter.value
      }

      const res = await axios.get<BucketEntry[]>(
        '/api/compare/risk_bucket_detail',
        { params }
      )
      bucketEntries.value = res.data || []
    } catch (err) {
      console.error('Failed to load bucket entries', err)
      bucketEntriesError.value = 'Failed to load bucket entries.'
    } finally {
      bucketEntriesLoading.value = false
    }
  }

  function clearBucketDetails(): void {
    selectedBucket.value = null
    bucketEntries.value = []
    bucketEntriesError.value = null
    bucketEntriesLoading.value = false
  }

  return {
    selectedBucket,
    bucketEntries,
    bucketEntriesLoading,
    bucketEntriesError,
    loadBucketDetails,
    clearBucketDetails
  }
}
