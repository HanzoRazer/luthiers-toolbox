/**
 * Verification tests for extracted composables.
 * Run with: npx vite-node src/testing/composable-tests.ts
 */

import { runComposableTests, smokeTest, type ComposableTest } from './ComposableVerifier'
import { useCandidateFilters } from '../components/rmos/composables/useCandidateFilters'
import { useCandidateSelection } from '../components/rmos/composables/useCandidateSelection'
import { usePocketSettings } from '../components/adaptive/composables/usePocketSettings'

// Mock localStorage for Node environment
if (typeof localStorage === 'undefined') {
  (globalThis as any).localStorage = {
    _data: {} as Record<string, string>,
    getItem(key: string) { return this._data[key] ?? null },
    setItem(key: string, value: string) { this._data[key] = value },
    removeItem(key: string) { delete this._data[key] },
    clear() { this._data = {} }
  }
}

const tests: ComposableTest<any>[] = [
  // useCandidateFilters tests
  {
    name: 'useCandidateFilters - initial state',
    composable: () => useCandidateFilters(() => 'test-run-123'),
    expectedState: {
      decisionFilter: 'ALL',
      statusFilter: 'ALL',
      searchText: '',
      showSelectedOnly: false,
      filterOnlyMine: false,
      compact: false,
      sortKey: 'id'
    }
  },
  {
    name: 'useCandidateFilters - filter interactions',
    composable: () => useCandidateFilters(() => 'test-run-456'),
    interactions: [
      {
        label: 'Set decision filter to GREEN',
        action: (c) => { c.decisionFilter.value = 'GREEN' },
        expect: { decisionFilter: 'GREEN' }
      },
      {
        label: 'Set status filter to ACCEPTED',
        action: (c) => { c.statusFilter.value = 'ACCEPTED' },
        expect: { statusFilter: 'ACCEPTED', decisionFilter: 'GREEN' }
      },
      {
        label: 'Clear filters',
        action: (c) => { c.clearFilters() },
        expect: { decisionFilter: 'ALL', statusFilter: 'ALL', searchText: '' }
      },
      {
        label: 'Quick undecided',
        action: (c) => { c.quickUndecided() },
        expect: { decisionFilter: 'UNDECIDED', statusFilter: 'ALL' }
      }
    ]
  },
  {
    name: 'useCandidateFilters - filterCandidates',
    composable: () => useCandidateFilters(() => 'test-run'),
    interactions: [
      {
        label: 'Filter GREEN candidates',
        action: (c) => {
          c.decisionFilter.value = 'GREEN'
          const candidates = [
            { candidate_id: 'c1', decision: 'GREEN' },
            { candidate_id: 'c2', decision: 'RED' },
            { candidate_id: 'c3', decision: 'GREEN' }
          ]
          const filtered = c.filterCandidates(candidates, new Set(), '')
          if (filtered.length !== 2) {
            throw new Error(`Expected 2 GREEN candidates, got ${filtered.length}`)
          }
        }
      }
    ]
  },

  // useCandidateSelection tests
  {
    name: 'useCandidateSelection - initial state',
    composable: () => useCandidateSelection(),
    expectedState: {
      selectedCount: 0,
      lastClickedId: null
    }
  },
  {
    name: 'useCandidateSelection - toggle and select',
    composable: () => useCandidateSelection(),
    interactions: [
      {
        label: 'Toggle selection',
        action: (c) => { c.toggleSelection('item-1') },
        expect: { selectedCount: 1, lastClickedId: 'item-1' }
      },
      {
        label: 'Toggle another',
        action: (c) => { c.toggleSelection('item-2') },
        expect: { selectedCount: 2 }
      },
      {
        label: 'Deselect first',
        action: (c) => { c.toggleSelection('item-1') },
        expect: { selectedCount: 1 }
      },
      {
        label: 'Clear all',
        action: (c) => { c.clearSelection() },
        expect: { selectedCount: 0, lastClickedId: null }
      }
    ]
  },
  {
    name: 'useCandidateSelection - selectAll',
    composable: () => useCandidateSelection(),
    interactions: [
      {
        label: 'Select all candidates',
        action: (c) => {
          const candidates = [
            { candidate_id: 'a' },
            { candidate_id: 'b' },
            { candidate_id: 'c' }
          ]
          c.selectAll(candidates)
        },
        expect: { selectedCount: 3 }
      }
    ]
  },

  // usePocketSettings tests
  {
    name: 'usePocketSettings - initial defaults',
    composable: () => usePocketSettings(),
    expectedState: {
      toolD: 6,
      stepoverPct: 45,
      stepdown: 1.5,
      margin: 0.5,
      strategy: 'Spiral',
      climb: true,
      units: 'mm'
    }
  },
  {
    name: 'usePocketSettings - computed values',
    composable: () => usePocketSettings(),
    interactions: [
      {
        label: 'Verify stepoverMm calculation',
        action: (c) => {
          // toolD=6, stepoverPct=45 => stepoverMm = 6 * 0.45 = 2.7
          const expected = 2.7
          const actual = c.stepoverMm.value
          if (Math.abs(actual - expected) > 0.01) {
            throw new Error(`stepoverMm: expected ${expected}, got ${actual}`)
          }
        }
      },
      {
        label: 'Change toolD, verify stepoverMm updates',
        action: (c) => {
          c.toolD.value = 10
          // stepoverMm = 10 * 0.45 = 4.5
          const expected = 4.5
          const actual = c.stepoverMm.value
          if (Math.abs(actual - expected) > 0.01) {
            throw new Error(`stepoverMm after toolD change: expected ${expected}, got ${actual}`)
          }
        }
      }
    ]
  },
  {
    name: 'usePocketSettings - validation',
    composable: () => usePocketSettings(),
    interactions: [
      {
        label: 'Valid settings pass',
        action: (c) => {
          if (!c.isValid.value) {
            throw new Error(`Expected valid, got errors: ${c.validationErrors.value.join(', ')}`)
          }
        }
      },
      {
        label: 'Invalid toolD triggers error',
        action: (c) => {
          c.toolD.value = -1
          if (c.isValid.value) {
            throw new Error('Expected invalid due to negative toolD')
          }
          if (!c.validationErrors.value.some(e => e.includes('Tool diameter'))) {
            throw new Error('Expected tool diameter error')
          }
        }
      }
    ]
  },
  {
    name: 'usePocketSettings - loadSettings',
    composable: () => usePocketSettings(),
    interactions: [
      {
        label: 'Load partial settings',
        action: (c) => {
          c.loadSettings({ toolD: 8, stepoverPct: 50 })
        },
        expect: { toolD: 8, stepoverPct: 50, stepdown: 1.5 } // stepdown unchanged
      }
    ]
  },
  {
    name: 'usePocketSettings - resetToDefaults',
    composable: () => usePocketSettings(),
    interactions: [
      {
        label: 'Modify then reset',
        action: (c) => {
          c.toolD.value = 99
          c.stepoverPct.value = 99
          c.resetToDefaults()
        },
        expect: { toolD: 6, stepoverPct: 45 }
      }
    ]
  }
]

// Run tests
async function main() {
  console.log('Running composable verification tests...\n')

  // Quick smoke tests first
  console.log('=== Smoke Tests ===')
  const smokes = [
    smokeTest('useCandidateFilters', () => useCandidateFilters(() => 'x')),
    smokeTest('useCandidateSelection', () => useCandidateSelection()),
    smokeTest('usePocketSettings', () => usePocketSettings())
  ]
  for (const s of smokes) {
    console.log(`${s.passed ? '✓' : '✗'} ${s.name}`)
  }

  // Full tests
  const results = await runComposableTests(tests)

  // Exit with error code if any failed
  if (results.failed > 0) {
    process.exit(1)
  }
}

main().catch(err => {
  console.error('Test runner error:', err)
  process.exit(1)
})
