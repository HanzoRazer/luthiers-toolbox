/**
 * Lightweight verification harness for composable extraction.
 * Ensures extracted composables behave identically to inline code.
 *
 * Usage:
 *   import { verifyComposable } from '@/testing/ComposableVerifier'
 *
 *   verifyComposable({
 *     name: 'useCandidateFilters',
 *     composable: () => useCandidateFilters(() => 'run-123'),
 *     expectedState: { decisionFilter: 'ALL', statusFilter: 'ALL' },
 *     interactions: [
 *       { action: (c) => c.decisionFilter.value = 'GREEN', expect: { decisionFilter: 'GREEN' } },
 *       { action: (c) => c.clearFilters(), expect: { decisionFilter: 'ALL' } },
 *     ]
 *   })
 */

import { nextTick, isRef, type Ref } from 'vue'

export interface ComposableTest<T> {
  name: string
  composable: () => T
  expectedState?: Partial<Record<keyof T, unknown>>
  interactions?: Interaction<T>[]
}

export interface Interaction<T> {
  label?: string
  action: (instance: T) => void | Promise<void>
  expect?: Partial<Record<keyof T, unknown>>
}

export interface VerifyResult {
  name: string
  passed: boolean
  failures: string[]
  duration: number
}

/**
 * Extract current values from a composable instance.
 * Unwraps refs automatically.
 */
function captureState<T extends object>(instance: T): Record<string, unknown> {
  const state: Record<string, unknown> = {}
  for (const key of Object.keys(instance)) {
    const val = (instance as Record<string, unknown>)[key]
    if (isRef(val)) {
      state[key] = val.value
    } else if (typeof val === 'function') {
      // Skip functions
    } else {
      state[key] = val
    }
  }
  return state
}

/**
 * Compare expected vs actual state, return list of differences.
 */
function diffState(
  expected: Record<string, unknown>,
  actual: Record<string, unknown>
): string[] {
  const diffs: string[] = []
  for (const key of Object.keys(expected)) {
    const exp = expected[key]
    const act = actual[key]
    if (JSON.stringify(exp) !== JSON.stringify(act)) {
      diffs.push(`${key}: expected ${JSON.stringify(exp)}, got ${JSON.stringify(act)}`)
    }
  }
  return diffs
}

/**
 * Verify a composable behaves as expected.
 */
export async function verifyComposable<T extends object>(
  test: ComposableTest<T>
): Promise<VerifyResult> {
  const start = performance.now()
  const failures: string[] = []

  try {
    // Instantiate composable
    const instance = test.composable()

    // Check initial state
    if (test.expectedState) {
      const actual = captureState(instance)
      const diffs = diffState(test.expectedState as Record<string, unknown>, actual)
      if (diffs.length > 0) {
        failures.push(`Initial state mismatch:\n  ${diffs.join('\n  ')}`)
      }
    }

    // Run interactions
    if (test.interactions) {
      for (let i = 0; i < test.interactions.length; i++) {
        const interaction = test.interactions[i]
        const label = interaction.label || `Interaction ${i + 1}`

        try {
          await interaction.action(instance)
          await nextTick()

          if (interaction.expect) {
            const actual = captureState(instance)
            const diffs = diffState(interaction.expect as Record<string, unknown>, actual)
            if (diffs.length > 0) {
              failures.push(`${label} failed:\n  ${diffs.join('\n  ')}`)
            }
          }
        } catch (err) {
          failures.push(`${label} threw: ${err}`)
        }
      }
    }
  } catch (err) {
    failures.push(`Setup failed: ${err}`)
  }

  return {
    name: test.name,
    passed: failures.length === 0,
    failures,
    duration: performance.now() - start
  }
}

/**
 * Run multiple composable tests and report results.
 */
export async function runComposableTests(
  tests: ComposableTest<any>[]
): Promise<{ passed: number; failed: number; results: VerifyResult[] }> {
  const results: VerifyResult[] = []

  for (const test of tests) {
    const result = await verifyComposable(test)
    results.push(result)
  }

  const passed = results.filter(r => r.passed).length
  const failed = results.filter(r => !r.passed).length

  // Console output
  console.log('\n=== Composable Verification ===\n')
  for (const r of results) {
    const icon = r.passed ? '✓' : '✗'
    console.log(`${icon} ${r.name} (${r.duration.toFixed(1)}ms)`)
    if (!r.passed) {
      for (const f of r.failures) {
        console.log(`    ${f}`)
      }
    }
  }
  console.log(`\nTotal: ${passed} passed, ${failed} failed\n`)

  return { passed, failed, results }
}

/**
 * Quick smoke test - just verify composable instantiates without error.
 */
export function smokeTest<T>(name: string, composable: () => T): VerifyResult {
  const start = performance.now()
  const failures: string[] = []

  try {
    const instance = composable()
    if (!instance) {
      failures.push('Composable returned null/undefined')
    }
  } catch (err) {
    failures.push(`Failed to instantiate: ${err}`)
  }

  return {
    name,
    passed: failures.length === 0,
    failures,
    duration: performance.now() - start
  }
}
