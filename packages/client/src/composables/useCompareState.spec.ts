// client/src/composables/useCompareState.spec.ts
// B22.8: Unit tests for Compare Lab State Machine
//
// Tests verify:
// 1. overlayDisabled behavior (guards overlay controls)
// 2. runWithCompareSkeleton behavior (loading states, error handling)
// 3. Double-click protection (prevents concurrent operations)
// 4. diffDisabledReason clearing on fresh runs

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { nextTick } from 'vue'
import { useCompareState } from './useCompareState'
import type { CanonicalGeometry } from '@/utils/geometry'

declare const global: typeof globalThis;

describe('useCompareState - B22.8 State Machine Guardrails', () => {
  describe('Initial State', () => {
    it('starts with idle, no reason, overlay enabled', () => {
      const state = useCompareState()

      expect(state.isComputingDiff.value).toBe(false)
      expect(state.diffDisabledReason.value).toBeNull()
      expect(state.currentMode.value).toBe('overlay')
      expect(state.compareResult.value).toBeNull()
      // Note: overlayDisabled is true initially because compareResult is null
      expect(state.overlayDisabled.value).toBe(true)
    })
  })

  describe('overlayDisabled computed property', () => {
    it('is disabled when diffDisabledReason is set', () => {
      const state = useCompareState()

      // Initially disabled because no result
      expect(state.overlayDisabled.value).toBe(true)

      // Set a result to enable
      state.compareResult.value = {
        baseline_id: 'test',
        baseline_name: 'Test Baseline',
        summary: {
          segments_baseline: 10,
          segments_current: 12,
          added: 2,
          removed: 0,
          unchanged: 10,
          overlap_ratio: 0.95,
        },
        segments: [],
      }

      expect(state.overlayDisabled.value).toBe(false)

      // Set disabled reason
      state.diffDisabledReason.value = 'Validation failed'
      expect(state.overlayDisabled.value).toBe(true)

      // Clear reason
      state.diffDisabledReason.value = null
      expect(state.overlayDisabled.value).toBe(false)
    })

    it('is disabled while computing diff', async () => {
      const state = useCompareState()

      // Set result so overlay would normally be enabled
      state.compareResult.value = {
        baseline_id: 'test',
        baseline_name: 'Test',
        summary: {
          segments_baseline: 5,
          segments_current: 5,
          added: 0,
          removed: 0,
          unchanged: 5,
          overlap_ratio: 1.0,
        },
        segments: [],
      }

      expect(state.overlayDisabled.value).toBe(false)

      const fn = vi.fn().mockResolvedValue('ok')
      const promise = state.runWithCompareSkeleton(fn)

      // Immediately after calling, overlay should be disabled
      expect(state.isComputingDiff.value).toBe(true)
      expect(state.overlayDisabled.value).toBe(true)

      const result = await promise
      await nextTick()

      expect(result).toBe('ok')
      expect(state.isComputingDiff.value).toBe(false)
      expect(state.overlayDisabled.value).toBe(false)
    })

    it('is disabled when compareResult is null', () => {
      const state = useCompareState()

      state.compareResult.value = null
      expect(state.overlayDisabled.value).toBe(true)

      state.compareResult.value = {
        baseline_id: 'test',
        baseline_name: 'Test',
        summary: {
          segments_baseline: 1,
          segments_current: 1,
          added: 0,
          removed: 0,
          unchanged: 1,
          overlap_ratio: 1.0,
        },
        segments: [],
      }
      expect(state.overlayDisabled.value).toBe(false)
    })
  })

  describe('runWithCompareSkeleton', () => {
    it('executes function and returns result on success', async () => {
      const state = useCompareState()
      const fn = vi.fn().mockResolvedValue('success')

      const result = await state.runWithCompareSkeleton(fn)
      await nextTick()

      expect(result).toBe('success')
      expect(fn).toHaveBeenCalledTimes(1)
      expect(state.isComputingDiff.value).toBe(false)
      expect(state.diffDisabledReason.value).toBeNull()
    })

    it('sets diffDisabledReason and returns undefined on error', async () => {
      const state = useCompareState()
      const error = new Error('Backend exploded')
      const fn = vi.fn().mockRejectedValue(error)

      const result = await state.runWithCompareSkeleton(fn)
      await nextTick()

      expect(result).toBeUndefined()
      expect(fn).toHaveBeenCalledTimes(1)
      expect(state.isComputingDiff.value).toBe(false)
      expect(state.diffDisabledReason.value).toContain('Backend exploded')
    })

    it('extracts error message from response.data.detail', async () => {
      const state = useCompareState()
      const error = {
        response: {
          data: {
            detail: 'API validation error: baseline not found',
          },
        },
      }
      const fn = vi.fn().mockRejectedValue(error)

      await state.runWithCompareSkeleton(fn)
      await nextTick()

      expect(state.diffDisabledReason.value).toBe('API validation error: baseline not found')
    })

    it('uses default message for unknown errors', async () => {
      const state = useCompareState()
      const fn = vi.fn().mockRejectedValue({})

      await state.runWithCompareSkeleton(fn)
      await nextTick()

      expect(state.diffDisabledReason.value).toBe('Compare operation failed. Overlay disabled.')
    })

    it('clears old diffDisabledReason on a fresh run', async () => {
      const state = useCompareState()

      // Seed an old error
      state.diffDisabledReason.value = 'Old error message'
      expect(state.diffDisabledReason.value).toBe('Old error message')

      const fn = vi.fn().mockResolvedValue('ok')
      const result = await state.runWithCompareSkeleton(fn)
      await nextTick()

      expect(result).toBe('ok')
      expect(state.diffDisabledReason.value).toBeNull()
    })
  })

  describe('Double-click protection', () => {
    it('does not start a second run while already computing', async () => {
      const state = useCompareState()

      // Create a deferred promise to hold computing state mid-flight
      let resolveFn: (value: string) => void
      const slowPromise = new Promise<string>((resolve) => {
        resolveFn = resolve
      })

      const slowFn = vi.fn().mockReturnValue(slowPromise)

      // Start first run
      const firstRun = state.runWithCompareSkeleton(slowFn)

      expect(state.isComputingDiff.value).toBe(true)
      expect(slowFn).toHaveBeenCalledTimes(1)

      // Try to start second run while still computing
      const secondFn = vi.fn().mockResolvedValue('second')
      const secondRun = state.runWithCompareSkeleton(secondFn)

      // Because we're mid-flight, secondFn should not be called
      expect(secondFn).not.toHaveBeenCalled()
      expect(state.isComputingDiff.value).toBe(true)

      // Resolve the first run
      resolveFn!('first-ok')
      const result1 = await firstRun
      const result2 = await secondRun // Should be undefined (ignored)
      await nextTick()

      expect(result1).toBe('first-ok')
      expect(result2).toBeUndefined()
      expect(state.isComputingDiff.value).toBe(false)
      expect(slowFn).toHaveBeenCalledTimes(1)
      expect(secondFn).not.toHaveBeenCalled()
    })

    it('allows a new run after the previous one completes', async () => {
      const state = useCompareState()

      const firstFn = vi.fn().mockResolvedValue('first')
      const result1 = await state.runWithCompareSkeleton(firstFn)
      await nextTick()

      expect(result1).toBe('first')
      expect(state.isComputingDiff.value).toBe(false)

      // Now start a second run
      const secondFn = vi.fn().mockResolvedValue('second')
      const result2 = await state.runWithCompareSkeleton(secondFn)
      await nextTick()

      expect(result2).toBe('second')
      expect(firstFn).toHaveBeenCalledTimes(1)
      expect(secondFn).toHaveBeenCalledTimes(1)
    })
  })

  describe('computeDiff action', () => {
    it('validates currentGeometry is present', async () => {
      const state = useCompareState()

      await state.computeDiff('baseline-123', null as any)

      expect(state.diffDisabledReason.value).toBe('No current geometry loaded')
      expect(state.compareResult.value).toBeNull()
    })

    it('validates baselineId is present', async () => {
      const state = useCompareState()
      const geometry: CanonicalGeometry = {
        units: 'mm',
        paths: [],
      }

      await state.computeDiff('', geometry)

      expect(state.diffDisabledReason.value).toBe('No baseline selected')
      expect(state.compareResult.value).toBeNull()
    })

    it('clears previous errors before computing', async () => {
      const state = useCompareState()

      // Seed an old error
      state.diffDisabledReason.value = 'Old validation error'

      const geometry: CanonicalGeometry = {
        units: 'mm',
        paths: [
          {
            segments: [
              { type: 'line', x1: 0, y1: 0, x2: 10, y2: 0 },
            ],
          },
        ],
      }

      // Mock fetch to succeed
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          baseline_id: 'baseline-123',
          baseline_name: 'Test Baseline',
          summary: {
            segments_baseline: 5,
            segments_current: 5,
            added: 0,
            removed: 0,
            unchanged: 5,
            overlap_ratio: 1.0,
          },
          segments: [],
        }),
      })

      await state.computeDiff('baseline-123', geometry)

      expect(state.diffDisabledReason.value).toBeNull()
      expect(state.compareResult.value).not.toBeNull()
    })
  })

  describe('setMode action', () => {
    it('changes mode when overlay is not disabled', () => {
      const state = useCompareState()

      // Set a result so overlay is not disabled
      state.compareResult.value = {
        baseline_id: 'test',
        baseline_name: 'Test',
        summary: {
          segments_baseline: 1,
          segments_current: 1,
          added: 0,
          removed: 0,
          unchanged: 1,
          overlap_ratio: 1.0,
        },
        segments: [],
      }

      expect(state.overlayDisabled.value).toBe(false)

      state.setMode('delta')
      expect(state.currentMode.value).toBe('delta')

      state.setMode('x-ray')
      expect(state.currentMode.value).toBe('x-ray')
    })

    it('warns and ignores mode change when overlay is disabled', () => {
      const state = useCompareState()
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      // Overlay is disabled because no result
      expect(state.overlayDisabled.value).toBe(true)

      state.setMode('delta')

      // Mode should not change
      expect(state.currentMode.value).toBe('overlay')
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        expect.stringContaining('Cannot set mode while overlay disabled'),
        null  // diffDisabledReason is null when no result
      )

      consoleWarnSpy.mockRestore()
    })
  })

  describe('reset action', () => {
    it('clears all state to initial values', () => {
      const state = useCompareState()

      // Set some state
      state.isComputingDiff.value = true
      state.diffDisabledReason.value = 'Some error'
      state.currentMode.value = 'delta'
      state.compareResult.value = {
        baseline_id: 'test',
        baseline_name: 'Test',
        summary: {
          segments_baseline: 1,
          segments_current: 1,
          added: 0,
          removed: 0,
          unchanged: 1,
          overlap_ratio: 1.0,
        },
        segments: [],
      }

      state.reset()

      expect(state.isComputingDiff.value).toBe(false)
      expect(state.diffDisabledReason.value).toBeNull()
      expect(state.currentMode.value).toBe('overlay')
      expect(state.compareResult.value).toBeNull()
    })
  })

  describe('Integration: State transitions', () => {
    it('follows correct state transitions during successful diff', async () => {
      const state = useCompareState()
      const geometry: CanonicalGeometry = {
        units: 'mm',
        paths: [],
      }

      // Mock successful API response
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          baseline_id: 'baseline-123',
          baseline_name: 'Test Baseline',
          summary: {
            segments_baseline: 10,
            segments_current: 12,
            added: 2,
            removed: 0,
            unchanged: 10,
            overlap_ratio: 0.95,
          },
          segments: [],
        }),
      })

      // Initial state: overlay disabled (no result)
      expect(state.overlayDisabled.value).toBe(true)
      expect(state.isComputingDiff.value).toBe(false)

      // Start diff computation
      const computePromise = state.computeDiff('baseline-123', geometry)

      // During computation: overlay disabled
      expect(state.isComputingDiff.value).toBe(true)
      expect(state.overlayDisabled.value).toBe(true)

      await computePromise
      await nextTick()

      // After completion: overlay enabled
      expect(state.isComputingDiff.value).toBe(false)
      expect(state.overlayDisabled.value).toBe(false)
      expect(state.compareResult.value).not.toBeNull()
      expect(state.diffDisabledReason.value).toBeNull()
    })

    it('follows correct state transitions during failed diff', async () => {
      const state = useCompareState()
      const geometry: CanonicalGeometry = {
        units: 'mm',
        paths: [],
      }

      // Mock failed API response
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        statusText: 'Not Found',
      })

      // Initial state
      expect(state.overlayDisabled.value).toBe(true)
      expect(state.isComputingDiff.value).toBe(false)

      // Start diff computation
      const computePromise = state.computeDiff('baseline-123', geometry)

      // During computation
      expect(state.isComputingDiff.value).toBe(true)
      expect(state.overlayDisabled.value).toBe(true)

      await computePromise
      await nextTick()

      // After failure: overlay still disabled, reason set
      expect(state.isComputingDiff.value).toBe(false)
      expect(state.overlayDisabled.value).toBe(true)
      expect(state.compareResult.value).toBeNull()
      expect(state.diffDisabledReason.value).not.toBeNull()
    })
  })
})
