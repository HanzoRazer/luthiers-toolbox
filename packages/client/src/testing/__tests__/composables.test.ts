/**
 * Vitest tests for extracted composables.
 * Run with: npm run test:composables
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { useCandidateFilters } from '../../components/rmos/composables/useCandidateFilters'
import { useCandidateSelection } from '../../components/rmos/composables/useCandidateSelection'
import { usePocketSettings } from '../../components/adaptive/composables/usePocketSettings'

describe('useCandidateFilters', () => {
  it('initializes with default state', () => {
    const filters = useCandidateFilters(() => 'test-run')

    expect(filters.decisionFilter.value).toBe('ALL')
    expect(filters.statusFilter.value).toBe('ALL')
    expect(filters.searchText.value).toBe('')
    expect(filters.showSelectedOnly.value).toBe(false)
    expect(filters.filterOnlyMine.value).toBe(false)
    expect(filters.compact.value).toBe(false)
    expect(filters.sortKey.value).toBe('id')
  })

  it('clearFilters resets all filters', () => {
    const filters = useCandidateFilters(() => 'test-run')

    // Set some filters
    filters.decisionFilter.value = 'GREEN'
    filters.statusFilter.value = 'ACCEPTED'
    filters.searchText.value = 'test search'

    // Clear
    filters.clearFilters()

    expect(filters.decisionFilter.value).toBe('ALL')
    expect(filters.statusFilter.value).toBe('ALL')
    expect(filters.searchText.value).toBe('')
  })

  it('quickUndecided sets correct filter', () => {
    const filters = useCandidateFilters(() => 'test-run')

    filters.quickUndecided()

    expect(filters.decisionFilter.value).toBe('UNDECIDED')
    expect(filters.statusFilter.value).toBe('ALL')
  })

  it('filterCandidates filters by decision', () => {
    const filters = useCandidateFilters(() => 'test-run')
    const candidates = [
      { candidate_id: 'c1', decision: 'GREEN' },
      { candidate_id: 'c2', decision: 'RED' },
      { candidate_id: 'c3', decision: 'GREEN' },
      { candidate_id: 'c4', decision: null }
    ]

    // Filter GREEN
    filters.decisionFilter.value = 'GREEN'
    let result = filters.filterCandidates(candidates, new Set(), '')
    expect(result.length).toBe(2)
    expect(result.every(c => c.decision === 'GREEN')).toBe(true)

    // Filter UNDECIDED
    filters.decisionFilter.value = 'UNDECIDED'
    result = filters.filterCandidates(candidates, new Set(), '')
    expect(result.length).toBe(1)
    expect(result[0].candidate_id).toBe('c4')
  })

  it('sortCandidates sorts by various keys', () => {
    const filters = useCandidateFilters(() => 'test-run')
    const candidates = [
      { candidate_id: 'c-zebra', decided_at_utc: '2024-01-03' },
      { candidate_id: 'c-alpha', decided_at_utc: '2024-01-01' },
      { candidate_id: 'c-beta', decided_at_utc: '2024-01-02' }
    ]

    // Sort by id ascending
    filters.sortKey.value = 'id'
    let result = filters.sortCandidates(candidates)
    expect(result[0].candidate_id).toBe('c-alpha')

    // Sort by id descending
    filters.sortKey.value = 'id_desc'
    result = filters.sortCandidates(candidates)
    expect(result[0].candidate_id).toBe('c-zebra')
  })

  it('matchesSearch finds text in candidate fields', () => {
    const filters = useCandidateFilters(() => 'test-run')

    const candidate = {
      candidate_id: 'cand-123',
      advisory_id: 'adv-456',
      decision_note: 'Important note here',
      decided_by: 'operator_jane'
    }

    expect(filters.matchesSearch(candidate, 'cand-123')).toBe(true)
    expect(filters.matchesSearch(candidate, 'adv-456')).toBe(true)
    expect(filters.matchesSearch(candidate, 'important')).toBe(true)
    expect(filters.matchesSearch(candidate, 'jane')).toBe(true)
    expect(filters.matchesSearch(candidate, 'nonexistent')).toBe(false)
  })
})

describe('useCandidateSelection', () => {
  it('initializes with empty selection', () => {
    const selection = useCandidateSelection()

    expect(selection.selectedCount.value).toBe(0)
    expect(selection.lastClickedId.value).toBe(null)
  })

  it('toggleSelection adds and removes items', () => {
    const selection = useCandidateSelection()

    selection.toggleSelection('item-1')
    expect(selection.selectedCount.value).toBe(1)
    expect(selection.isSelected('item-1')).toBe(true)

    selection.toggleSelection('item-2')
    expect(selection.selectedCount.value).toBe(2)

    selection.toggleSelection('item-1')
    expect(selection.selectedCount.value).toBe(1)
    expect(selection.isSelected('item-1')).toBe(false)
  })

  it('clearSelection removes all selections', () => {
    const selection = useCandidateSelection()

    selection.toggleSelection('a')
    selection.toggleSelection('b')
    selection.toggleSelection('c')
    expect(selection.selectedCount.value).toBe(3)

    selection.clearSelection()
    expect(selection.selectedCount.value).toBe(0)
    expect(selection.lastClickedId.value).toBe(null)
  })

  it('selectAll selects all candidates', () => {
    const selection = useCandidateSelection()
    const candidates = [
      { candidate_id: 'a' },
      { candidate_id: 'b' },
      { candidate_id: 'c' }
    ]

    selection.selectAll(candidates)
    expect(selection.selectedCount.value).toBe(3)
    expect(selection.isSelected('a')).toBe(true)
    expect(selection.isSelected('b')).toBe(true)
    expect(selection.isSelected('c')).toBe(true)
  })

  it('selectRange selects contiguous items', () => {
    const selection = useCandidateSelection()
    const candidates = [
      { candidate_id: 'a' },
      { candidate_id: 'b' },
      { candidate_id: 'c' },
      { candidate_id: 'd' },
      { candidate_id: 'e' }
    ]

    // Click first item
    selection.toggleSelection('b')
    // Shift-click to select range
    selection.selectRange(candidates, 'd')

    expect(selection.selectedCount.value).toBe(3) // b, c, d
    expect(selection.isSelected('b')).toBe(true)
    expect(selection.isSelected('c')).toBe(true)
    expect(selection.isSelected('d')).toBe(true)
    expect(selection.isSelected('a')).toBe(false)
    expect(selection.isSelected('e')).toBe(false)
  })

  it('getSelectedCandidates returns selected items', () => {
    const selection = useCandidateSelection()
    const candidates = [
      { candidate_id: 'a', name: 'Alpha' },
      { candidate_id: 'b', name: 'Beta' },
      { candidate_id: 'c', name: 'Gamma' }
    ]

    selection.toggleSelection('a')
    selection.toggleSelection('c')

    const selected = selection.getSelectedCandidates(candidates)
    expect(selected.length).toBe(2)
    expect(selected.map(c => c.name)).toEqual(['Alpha', 'Gamma'])
  })
})

describe('usePocketSettings', () => {
  it('initializes with expected defaults', () => {
    const settings = usePocketSettings()

    expect(settings.toolD.value).toBe(6)
    expect(settings.stepoverPct.value).toBe(45)
    expect(settings.stepdown.value).toBe(1.5)
    expect(settings.margin.value).toBe(0.5)
    expect(settings.strategy.value).toBe('Spiral')
    expect(settings.climb.value).toBe(true)
    expect(settings.units.value).toBe('mm')
  })

  it('stepoverMm computes correctly', () => {
    const settings = usePocketSettings()

    // toolD=6, stepoverPct=45 => 6 * 0.45 = 2.7
    expect(settings.stepoverMm.value).toBeCloseTo(2.7, 2)

    settings.toolD.value = 10
    expect(settings.stepoverMm.value).toBeCloseTo(4.5, 2)

    settings.stepoverPct.value = 50
    expect(settings.stepoverMm.value).toBeCloseTo(5.0, 2)
  })

  it('chipload computes correctly', () => {
    const settings = usePocketSettings()

    // chipload = feedXY / (rpm * flutes)
    // feedXY=1200, rpm=18000, flutes=2 => 1200 / 36000 = 0.0333
    expect(settings.chipload.value).toBeCloseTo(0.0333, 3)

    settings.feedXY.value = 2400
    expect(settings.chipload.value).toBeCloseTo(0.0667, 3)
  })

  it('mrr computes correctly', () => {
    const settings = usePocketSettings()

    // mrr = stepoverMm * stepdown * feedXY
    // 2.7 * 1.5 * 1200 = 4860
    expect(settings.mrr.value).toBeCloseTo(4860, 0)
  })

  it('validates settings correctly', () => {
    const settings = usePocketSettings()

    // Default settings should be valid
    expect(settings.isValid.value).toBe(true)
    expect(settings.validationErrors.value.length).toBe(0)

    // Invalid toolD
    settings.toolD.value = -1
    expect(settings.isValid.value).toBe(false)
    expect(settings.validationErrors.value).toContain('Tool diameter must be positive')

    // Fix toolD, break stepover
    settings.toolD.value = 6
    settings.stepoverPct.value = 100 // Out of 5-95 range
    expect(settings.isValid.value).toBe(false)
    expect(settings.validationErrors.value.some(e => e.includes('Step-over'))).toBe(true)
  })

  it('loadSettings applies partial updates', () => {
    const settings = usePocketSettings()

    settings.loadSettings({
      toolD: 12,
      feedXY: 2000
    })

    expect(settings.toolD.value).toBe(12)
    expect(settings.feedXY.value).toBe(2000)
    // Other values unchanged
    expect(settings.stepoverPct.value).toBe(45)
    expect(settings.strategy.value).toBe('Spiral')
  })

  it('resetToDefaults restores all values', () => {
    const settings = usePocketSettings()

    // Modify everything
    settings.toolD.value = 99
    settings.stepoverPct.value = 99
    settings.strategy.value = 'Lanes'
    settings.climb.value = false

    settings.resetToDefaults()

    expect(settings.toolD.value).toBe(6)
    expect(settings.stepoverPct.value).toBe(45)
    expect(settings.strategy.value).toBe('Spiral')
    expect(settings.climb.value).toBe(true)
  })
})
