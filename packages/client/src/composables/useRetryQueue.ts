/**
 * useRetryQueue - Manages retryable operations with exponential backoff
 *
 * Queues failed operations and retries them automatically when conditions improve
 * (e.g., network reconnection). Supports exponential backoff and max retries.
 *
 * Usage:
 *   const { enqueue, processQueue, queueSize } = useRetryQueue()
 *
 *   // Enqueue a failed operation
 *   enqueue({
 *     id: 'save-job-123',
 *     operation: () => saveJob(data),
 *     onSuccess: () => toast.success('Saved!'),
 *     onFailure: (e) => toast.error(e.message),
 *   })
 */
import { ref, computed, readonly, onMounted, onUnmounted } from 'vue'

export interface QueuedOperation {
  /** Unique identifier for deduplication */
  id: string
  /** The async operation to retry */
  operation: () => Promise<any>
  /** Called on successful completion */
  onSuccess?: (result: any) => void
  /** Called when all retries exhausted */
  onFailure?: (error: Error) => void
  /** Maximum retry attempts (default: 3) */
  maxRetries?: number
  /** Current retry count */
  retryCount?: number
  /** Timestamp when queued */
  queuedAt?: number
  /** Last error message */
  lastError?: string
  /** Operation category for grouping */
  category?: string
}

export interface UseRetryQueueOptions {
  /** Maximum concurrent operations (default: 3) */
  maxConcurrent?: number
  /** Base delay for exponential backoff in ms (default: 1000) */
  baseDelay?: number
  /** Maximum delay cap in ms (default: 30000) */
  maxDelay?: number
  /** Auto-process queue when online (default: true) */
  autoProcessOnReconnect?: boolean
  /** Persist queue to localStorage (default: false) */
  persist?: boolean
  /** Storage key for persistence */
  storageKey?: string
}

export function useRetryQueue(options: UseRetryQueueOptions = {}) {
  const {
    maxConcurrent = 3,
    baseDelay = 1000,
    maxDelay = 30000,
    autoProcessOnReconnect = true,
    persist = false,
    storageKey = 'retry-queue',
  } = options

  const queue = ref<QueuedOperation[]>([])
  const processing = ref<Set<string>>(new Set())
  const isProcessing = ref(false)

  const queueSize = computed(() => queue.value.length)
  const pendingCount = computed(() => queue.value.length - processing.value.size)
  const processingCount = computed(() => processing.value.size)

  /**
   * Calculate delay with exponential backoff
   */
  function getBackoffDelay(retryCount: number): number {
    const delay = baseDelay * Math.pow(2, retryCount)
    // Add jitter (10-20% randomization)
    const jitter = delay * (0.1 + Math.random() * 0.1)
    return Math.min(delay + jitter, maxDelay)
  }

  /**
   * Add operation to retry queue
   */
  function enqueue(op: QueuedOperation): void {
    // Deduplicate by ID
    const existingIndex = queue.value.findIndex((q) => q.id === op.id)
    if (existingIndex >= 0) {
      // Update existing entry
      queue.value[existingIndex] = {
        ...op,
        retryCount: queue.value[existingIndex].retryCount || 0,
        queuedAt: queue.value[existingIndex].queuedAt || Date.now(),
      }
    } else {
      // Add new entry
      queue.value.push({
        ...op,
        retryCount: 0,
        queuedAt: Date.now(),
      })
    }

    if (persist) {
      saveToStorage()
    }
  }

  /**
   * Remove operation from queue
   */
  function dequeue(id: string): void {
    queue.value = queue.value.filter((q) => q.id !== id)
    processing.value.delete(id)

    if (persist) {
      saveToStorage()
    }
  }

  /**
   * Clear all queued operations
   */
  function clearQueue(): void {
    queue.value = []
    processing.value.clear()

    if (persist) {
      localStorage.removeItem(storageKey)
    }
  }

  /**
   * Process a single operation
   */
  async function processOperation(op: QueuedOperation): Promise<boolean> {
    const maxRetries = op.maxRetries ?? 3

    if (processing.value.has(op.id)) {
      return false // Already processing
    }

    processing.value.add(op.id)

    try {
      const result = await op.operation()

      // Success - remove from queue
      dequeue(op.id)
      op.onSuccess?.(result)
      return true
    } catch (error: any) {
      const retryCount = (op.retryCount || 0) + 1

      if (retryCount >= maxRetries) {
        // Max retries reached - remove and report failure
        dequeue(op.id)
        op.onFailure?.(error)
        return false
      }

      // Update retry count and last error
      const index = queue.value.findIndex((q) => q.id === op.id)
      if (index >= 0) {
        queue.value[index] = {
          ...queue.value[index],
          retryCount,
          lastError: error.message,
        }
      }

      processing.value.delete(op.id)

      if (persist) {
        saveToStorage()
      }

      return false
    }
  }

  /**
   * Process all queued operations
   */
  async function processQueue(): Promise<{ success: number; failed: number }> {
    if (!navigator.onLine) {
      return { success: 0, failed: 0 }
    }

    isProcessing.value = true
    let success = 0
    let failed = 0

    // Process in batches respecting maxConcurrent
    const pending = queue.value.filter((op) => !processing.value.has(op.id))

    for (let i = 0; i < pending.length; i += maxConcurrent) {
      const batch = pending.slice(i, i + maxConcurrent)

      // Add delay based on retry count (exponential backoff)
      const maxRetryInBatch = Math.max(...batch.map((op) => op.retryCount || 0))
      if (maxRetryInBatch > 0) {
        await new Promise((resolve) => setTimeout(resolve, getBackoffDelay(maxRetryInBatch)))
      }

      const results = await Promise.all(batch.map(processOperation))

      success += results.filter(Boolean).length
      failed += results.filter((r) => !r).length
    }

    isProcessing.value = false
    return { success, failed }
  }

  /**
   * Get operations by category
   */
  function getByCategory(category: string): QueuedOperation[] {
    return queue.value.filter((op) => op.category === category)
  }

  /**
   * Save queue to localStorage (without functions)
   */
  function saveToStorage(): void {
    if (!persist) return

    const serializable = queue.value.map((op) => ({
      id: op.id,
      maxRetries: op.maxRetries,
      retryCount: op.retryCount,
      queuedAt: op.queuedAt,
      lastError: op.lastError,
      category: op.category,
    }))

    try {
      localStorage.setItem(storageKey, JSON.stringify(serializable))
    } catch {
      // Storage full or unavailable
    }
  }

  /**
   * Load queue metadata from localStorage
   */
  function loadFromStorage(): void {
    if (!persist) return

    try {
      const stored = localStorage.getItem(storageKey)
      if (stored) {
        const parsed = JSON.parse(stored)
        // Only load metadata - operations must be re-registered
        queue.value = parsed.map((item: any) => ({
          ...item,
          operation: () => Promise.reject(new Error('Operation not re-registered')),
        }))
      }
    } catch {
      // Invalid storage data
    }
  }

  // Auto-process on reconnection
  function handleOnline() {
    if (autoProcessOnReconnect && queue.value.length > 0) {
      processQueue()
    }
  }

  onMounted(() => {
    loadFromStorage()
    window.addEventListener('online', handleOnline)
  })

  onUnmounted(() => {
    window.removeEventListener('online', handleOnline)
  })

  return {
    // State
    queue: readonly(queue),
    queueSize,
    pendingCount,
    processingCount,
    isProcessing: readonly(isProcessing),

    // Actions
    enqueue,
    dequeue,
    clearQueue,
    processQueue,
    processOperation,
    getByCategory,
  }
}

/**
 * Create a global retry queue instance
 */
let globalQueue: ReturnType<typeof useRetryQueue> | null = null

export function useGlobalRetryQueue(options?: UseRetryQueueOptions) {
  if (!globalQueue) {
    globalQueue = useRetryQueue({
      persist: true,
      storageKey: 'global-retry-queue',
      ...options,
    })
  }
  return globalQueue
}
