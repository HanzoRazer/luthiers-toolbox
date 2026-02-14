/**
 * Generic composables test suite.
 *
 * Covers all 7 domain-agnostic composables in packages/client/src/composables/.
 * Each test mirrors the assertions from the original domain-specific tests
 * but validates against the genericized API surface.
 *
 * Run: npm run test (or npx vitest run src/composables/__tests__)
 */
import { describe, it, expect } from 'vitest'

import {
  useListFilters,
  type FilterableRow,
} from '../useListFilters'

import {
  useListSelection,
} from '../useListSelection'

import {
  useParametricSettings,
  type FieldSpec,
} from '../useParametricSettings'

import {
  useDimensionEditor,
  type DimensionPreset,
} from '../useDimensionEditor'

import {
  useMaterialCalculator,
  calculateBoardFeet,
  calculateWeight,
  calculateAngle,
  calculateComplementaryAngle,
  type MaterialSpec,
  type VolumeInput,
} from '../useMaterialCalculator'

import {
  useFormulaCalculator,
} from '../useFormulaCalculator'

import {
  useUnitConverter,
  convert,
  UNITS,
} from '../useUnitConverter'

// =============================================================================
// useListFilters
// =============================================================================
describe('useListFilters', () => {
  const makeFilters = () =>
    useListFilters<FilterableRow & { category?: string; status?: string; note?: string; author?: string }>({
      persistenceKey: () => 'test-run',
      categoryValues: ['ALL', 'UNDECIDED', 'GREEN', 'YELLOW', 'RED'],
      statusValues: ['ALL', 'PROPOSED', 'ACCEPTED', 'REJECTED'],
      searchableFields: ['id', 'note', 'author'],
    })

  it('initializes with default state', () => {
    const f = makeFilters()
    expect(f.categoryFilter.value).toBe('ALL')
    expect(f.statusFilter.value).toBe('ALL')
    expect(f.searchText.value).toBe('')
    expect(f.showSelectedOnly.value).toBe(false)
    expect(f.compact.value).toBe(false)
    expect(f.sortKey.value).toBe('id')
  })

  it('clearFilters resets all filters', () => {
    const f = makeFilters()
    f.categoryFilter.value = 'GREEN'
    f.statusFilter.value = 'ACCEPTED'
    f.searchText.value = 'test search'

    f.clearFilters()

    expect(f.categoryFilter.value).toBe('ALL')
    expect(f.statusFilter.value).toBe('ALL')
    expect(f.searchText.value).toBe('')
  })

  it('filterRows filters by category', () => {
    const f = makeFilters()
    const rows = [
      { id: 'r1', category: 'GREEN' },
      { id: 'r2', category: 'RED' },
      { id: 'r3', category: 'GREEN' },
      { id: 'r4', category: undefined },
    ]

    f.categoryFilter.value = 'GREEN'
    const result = f.filterRows(rows, new Set(), 'category' as keyof typeof rows[0])
    expect(result.length).toBe(2)
    expect(result.every((r) => r.category === 'GREEN')).toBe(true)
  })

  it('sortRows sorts by key ascending and descending', () => {
    const f = makeFilters()
    const rows = [
      { id: 'c-zebra' },
      { id: 'c-alpha' },
      { id: 'c-beta' },
    ]

    const asc = f.sortRows(rows, 'id')
    expect(asc[0].id).toBe('c-alpha')

    const desc = f.sortRows(rows, 'id_desc')
    expect(desc[0].id).toBe('c-zebra')
  })

  it('matchesSearch finds text in searchable fields', () => {
    const f = makeFilters()
    const row = {
      id: 'item-123',
      note: 'Important note here',
      author: 'operator_jane',
    }

    expect(f.matchesSearch(row, 'item-123')).toBe(true)
    expect(f.matchesSearch(row, 'important')).toBe(true)
    expect(f.matchesSearch(row, 'jane')).toBe(true)
    expect(f.matchesSearch(row, 'nonexistent')).toBe(false)
  })
})

// =============================================================================
// useListSelection
// =============================================================================
describe('useListSelection', () => {
  it('initializes with empty selection', () => {
    const sel = useListSelection()
    expect(sel.selectedCount.value).toBe(0)
    expect(sel.lastClickedId.value).toBe(null)
  })

  it('toggleSelection adds and removes items', () => {
    const sel = useListSelection()

    sel.toggleSelection('item-1')
    expect(sel.selectedCount.value).toBe(1)
    expect(sel.isSelected('item-1')).toBe(true)

    sel.toggleSelection('item-2')
    expect(sel.selectedCount.value).toBe(2)

    sel.toggleSelection('item-1')
    expect(sel.selectedCount.value).toBe(1)
    expect(sel.isSelected('item-1')).toBe(false)
  })

  it('clearSelection removes all selections', () => {
    const sel = useListSelection()

    sel.toggleSelection('a')
    sel.toggleSelection('b')
    sel.toggleSelection('c')
    expect(sel.selectedCount.value).toBe(3)

    sel.clearSelection()
    expect(sel.selectedCount.value).toBe(0)
    expect(sel.lastClickedId.value).toBe(null)
  })

  it('selectAll selects all items', () => {
    const sel = useListSelection()
    const items = [{ id: 'a' }, { id: 'b' }, { id: 'c' }]

    sel.selectAll(items)
    expect(sel.selectedCount.value).toBe(3)
    expect(sel.isSelected('a')).toBe(true)
    expect(sel.isSelected('b')).toBe(true)
    expect(sel.isSelected('c')).toBe(true)
  })

  it('selectRange selects contiguous items', () => {
    const sel = useListSelection()
    const items = [
      { id: 'a' }, { id: 'b' }, { id: 'c' },
      { id: 'd' }, { id: 'e' },
    ]

    sel.toggleSelection('b')
    sel.selectRange(items, 'd')

    expect(sel.selectedCount.value).toBe(3) // b, c, d
    expect(sel.isSelected('b')).toBe(true)
    expect(sel.isSelected('c')).toBe(true)
    expect(sel.isSelected('d')).toBe(true)
    expect(sel.isSelected('a')).toBe(false)
    expect(sel.isSelected('e')).toBe(false)
  })

  it('getSelected returns selected items', () => {
    const sel = useListSelection()
    const items = [
      { id: 'a', name: 'Alpha' },
      { id: 'b', name: 'Beta' },
      { id: 'c', name: 'Gamma' },
    ]

    sel.toggleSelection('a')
    sel.toggleSelection('c')

    const selected = sel.getSelected(items)
    expect(selected.length).toBe(2)
    expect(selected.map((i) => i.id)).toEqual(['a', 'c'])
  })
})

// =============================================================================
// useParametricSettings
// =============================================================================
describe('useParametricSettings', () => {
  const makeFields = (): FieldSpec[] => [
    { key: 'diameter', label: 'Diameter', type: 'number', defaultValue: 6, min: 0.1 },
    { key: 'overlapPct', label: 'Overlap %', type: 'number', defaultValue: 45, min: 5, max: 95 },
    { key: 'stepDepth', label: 'Step Depth', type: 'number', defaultValue: 1.5, min: 0.01 },
    { key: 'clearance', label: 'Clearance', type: 'number', defaultValue: 0.5 },
    { key: 'mode', label: 'Mode', type: 'select', defaultValue: 'Spiral', options: ['Spiral', 'Lanes'] },
    { key: 'enabled', label: 'Enabled', type: 'boolean', defaultValue: true },
    { key: 'feedRate', label: 'Feed Rate', type: 'number', defaultValue: 1200, min: 1 },
    { key: 'totalDepth', label: 'Total Depth', type: 'number', defaultValue: 10, min: 0.1 },
    { key: 'speed', label: 'Speed', type: 'number', defaultValue: 18000, min: 1 },
  ]

  it('initializes with expected defaults', () => {
    const s = useParametricSettings({ fields: makeFields() })

    expect(s.settings.value.diameter).toBe(6)
    expect(s.settings.value.overlapPct).toBe(45)
    expect(s.settings.value.stepDepth).toBe(1.5)
    expect(s.settings.value.clearance).toBe(0.5)
    expect(s.settings.value.mode).toBe('Spiral')
    expect(s.settings.value.enabled).toBe(true)
  })

  it('validates min/max constraints', () => {
    const s = useParametricSettings({ fields: makeFields() })
    expect(s.isValid.value).toBe(true)
    expect(s.validationErrors.value.length).toBe(0)

    // Break min constraint
    s.settings.value.diameter = -1
    expect(s.isValid.value).toBe(false)

    // Fix diameter, break max constraint on overlapPct
    s.settings.value.diameter = 6
    s.settings.value.overlapPct = 100
    expect(s.isValid.value).toBe(false)
    expect(s.validationErrors.value.some((e) => e.field === 'overlapPct')).toBe(true)
  })

  it('loadSettings applies partial updates', () => {
    const s = useParametricSettings({ fields: makeFields() })

    s.loadSettings({ diameter: 12, feedRate: 2000 })

    expect(s.settings.value.diameter).toBe(12)
    expect(s.settings.value.feedRate).toBe(2000)
    // Untouched values remain
    expect(s.settings.value.overlapPct).toBe(45)
    expect(s.settings.value.mode).toBe('Spiral')
  })

  it('resetToDefaults restores all values', () => {
    const s = useParametricSettings({ fields: makeFields() })

    s.settings.value.diameter = 99
    s.settings.value.overlapPct = 99
    s.settings.value.mode = 'Lanes'
    s.settings.value.enabled = false

    s.resetToDefaults()

    expect(s.settings.value.diameter).toBe(6)
    expect(s.settings.value.overlapPct).toBe(45)
    expect(s.settings.value.mode).toBe('Spiral')
    expect(s.settings.value.enabled).toBe(true)
  })

  it('settingsSnapshot exports current state', () => {
    const s = useParametricSettings({ fields: makeFields() })
    s.settings.value.diameter = 42
    const snap = s.settingsSnapshot.value
    expect(snap.diameter).toBe(42)
    expect(snap.overlapPct).toBe(45)
  })
})

// =============================================================================
// useDimensionEditor
// =============================================================================
describe('useDimensionEditor', () => {
  const FIELDS = [
    { key: 'length', label: 'Length' },
    { key: 'widthUpper', label: 'Width Upper' },
    { key: 'widthLower', label: 'Width Lower' },
    { key: 'waist', label: 'Waist' },
    { key: 'depth', label: 'Depth' },
    { key: 'slotLength', label: 'Slot Length', required: false },
    { key: 'slotWidth', label: 'Slot Width', required: false },
    { key: 'span', label: 'Span' },
  ]

  const DEFAULTS: Record<string, number> = {
    length: 400, widthUpper: 290, widthLower: 340,
    waist: 260, depth: 45, slotLength: 76,
    slotWidth: 56, span: 648,
  }

  const PRESETS: DimensionPreset[] = [
    {
      id: 'compact',
      label: 'Compact',
      values: { length: 440, widthUpper: 290, widthLower: 330, waist: 260, depth: 50, slotLength: 80, slotWidth: 60, span: 629 },
    },
    {
      id: 'standard',
      label: 'Standard',
      values: { length: 400, widthUpper: 280, widthLower: 330, waist: 280, depth: 45, slotLength: 76, slotWidth: 56, span: 648 },
    },
  ]

  const makeDims = () => useDimensionEditor({ fields: FIELDS, presets: PRESETS, defaults: DEFAULTS })

  it('initializes with mm units and defaults', () => {
    const d = makeDims()
    expect(d.units.value).toBe('mm')
    expect(d.values.value.length).toBe(400)
  })

  it('hasValidDimensions validates required fields', () => {
    const d = makeDims()
    expect(d.hasValidDimensions.value).toBe(true)

    d.values.value.length = 0
    expect(d.hasValidDimensions.value).toBe(false)

    d.values.value.length = 400
    expect(d.hasValidDimensions.value).toBe(true)
  })

  it('toggleUnits converts mm to inches', () => {
    const d = makeDims()
    expect(d.values.value.length).toBe(400)

    d.toggleUnits('inch')
    // 400mm ≈ 15.75 in
    expect(d.values.value.length).toBeCloseTo(15.75, 1)
    expect(d.units.value).toBe('inch')
  })

  it('toggleUnits round-trips mm → inch → mm', () => {
    const d = makeDims()
    d.toggleUnits('inch')
    d.toggleUnits('mm')
    expect(d.values.value.length).toBeCloseTo(400, 0)
  })

  it('loadPreset applies preset values', () => {
    const d = makeDims()
    d.loadPreset('compact')
    expect(d.values.value.length).toBe(440)
    expect(d.values.value.span).toBe(629)
  })

  it('loadPreset converts to current units', () => {
    const d = makeDims()
    d.toggleUnits('inch')
    d.loadPreset('standard')
    // 400mm ≈ 15.75 in
    expect(d.values.value.length).toBeCloseTo(15.75, 1)
  })

  it('exportAsObject returns correct structure', () => {
    const d = makeDims()
    d.selectedPreset.value = 'compact'
    const exported = d.exportAsObject()

    expect(exported.preset).toBe('compact')
    expect(exported.units).toBe('mm')
    expect(exported.dimensions.length).toBe(400)
  })

  it('exportAsCSV returns valid CSV', () => {
    const d = makeDims()
    const csv = d.exportAsCSV()
    const lines = csv.split('\n')

    expect(lines[0]).toBe('Dimension,Value,Unit')
    expect(lines.length).toBeGreaterThan(5)
    expect(lines.some((l) => l.includes('length'))).toBe(true)
  })

  it('reset restores all defaults', () => {
    const d = makeDims()
    d.toggleUnits('inch')
    d.loadPreset('compact')

    d.reset()

    expect(d.units.value).toBe('mm')
    expect(d.values.value.length).toBe(400)
    expect(d.selectedPreset.value).toBe(null)
  })
})

// =============================================================================
// useMaterialCalculator
// =============================================================================
describe('useMaterialCalculator', () => {
  const MATERIALS: Record<string, MaterialSpec> = {
    softwood: { name: 'Softwood', density: 0.43 },
    hardwood: { name: 'Hardwood', density: 0.71 },
    dense: { name: 'Dense Hardwood', density: 1.12 },
    light: { name: 'Lightweight', density: 0.37 },
  }

  it('calculates board feet correctly', () => {
    // 48" × 6" × 1" = 288 / 144 = 2 BF
    expect(calculateBoardFeet({ length: 48, width: 6, thickness: 1 })).toBe(2)
    // 96" × 12" × 2" = 2304 / 144 = 16 BF
    expect(calculateBoardFeet({ length: 96, width: 12, thickness: 2 })).toBe(16)
  })

  it('calculates board cost', () => {
    const calc = useMaterialCalculator(MATERIALS)
    calc.boardFeet.value = { length: 48, width: 6, thickness: 1, pricePerBF: 10 }
    // 2 BF × $10 = $20
    expect(calc.boardCostResult.value).toBe(20)
  })

  it('calculates weight using material density', () => {
    // 100×100×10 mm = 100 cm³ × 0.43 g/cm³ = 43 g
    const w = calculateWeight(
      { length: 100, width: 100, thickness: 10, materialKey: 'softwood' },
      MATERIALS,
    )
    expect(w).toBeCloseTo(43, 0)
  })

  it('denser material weighs more', () => {
    const base: VolumeInput = { length: 100, width: 100, thickness: 10, materialKey: '' }
    const heavy = calculateWeight({ ...base, materialKey: 'dense' }, MATERIALS)
    const light = calculateWeight({ ...base, materialKey: 'light' }, MATERIALS)
    expect(heavy).toBeGreaterThan(light * 2)
  })

  it('calculates angle correctly', () => {
    // 12/12 = 45°
    expect(calculateAngle({ rise: 12, run: 12 })).toBeCloseTo(45, 1)
    // 6/12 ≈ 26.57°
    expect(calculateAngle({ rise: 6, run: 12 })).toBeCloseTo(26.57, 1)
    // 0/12 = 0°
    expect(calculateAngle({ rise: 0, run: 12 })).toBe(0)
  })

  it('calculates complementary angle', () => {
    expect(calculateComplementaryAngle({ rise: 12, run: 12 })).toBeCloseTo(45, 1)
    expect(calculateComplementaryAngle({ rise: 6, run: 12 })).toBeCloseTo(63.43, 1)
  })

  it('resetAll restores defaults', () => {
    const calc = useMaterialCalculator(MATERIALS)
    calc.boardFeet.value.length = 999
    calc.angle.value.rise = 99

    calc.resetAll()

    expect(calc.boardFeet.value.length).toBe(48)
    expect(calc.angle.value.rise).toBe(12)
  })
})

// =============================================================================
// useFormulaCalculator
// =============================================================================
describe('useFormulaCalculator', () => {
  const makeCalc = () =>
    useFormulaCalculator({
      params: [
        { key: 'base', label: 'Base', defaultValue: 10 },
        { key: 'height', label: 'Height', defaultValue: 5 },
      ],
      presets: [
        { id: 'small', label: 'Small', values: { base: 4, height: 3 } },
        { id: 'large', label: 'Large', values: { base: 20, height: 15 } },
      ],
      formula: (v) => (v.base * v.height) / 2, // triangle area
      thresholds: [
        { label: 'small', min: 0, max: 10 },
        { label: 'medium', min: 10.01, max: 50 },
        { label: 'large', min: 50.01, max: Infinity },
      ],
    })

  it('initializes with defaults', () => {
    const c = makeCalc()
    expect(c.values.value.base).toBe(10)
    expect(c.values.value.height).toBe(5)
  })

  it('computes result via formula', () => {
    const c = makeCalc()
    // (10 × 5) / 2 = 25
    expect(c.result.value).toBe(25)
  })

  it('classifies result against thresholds', () => {
    const c = makeCalc()
    // 25 is in medium range
    expect(c.classification.value).toBe('medium')

    c.values.value.base = 2
    c.values.value.height = 2
    // (2×2)/2 = 2 → small
    expect(c.result.value).toBe(2)
    expect(c.classification.value).toBe('small')
  })

  it('applyPreset overrides values', () => {
    const c = makeCalc()
    c.applyPreset('large')
    expect(c.values.value.base).toBe(20)
    expect(c.values.value.height).toBe(15)
  })

  it('reset restores defaults', () => {
    const c = makeCalc()
    c.applyPreset('large')
    c.reset()
    expect(c.values.value.base).toBe(10)
    expect(c.values.value.height).toBe(5)
  })

  it('setValue updates a single param', () => {
    const c = makeCalc()
    c.setValue('base', 42)
    expect(c.values.value.base).toBe(42)
    expect(c.values.value.height).toBe(5) // unchanged
  })

  it('paramEntries exposes labelled values', () => {
    const c = makeCalc()
    const entries = c.paramEntries.value
    expect(entries.length).toBe(2)
    expect(entries[0].key).toBe('base')
    expect(entries[0].value).toBe(10)
  })
})

// =============================================================================
// useUnitConverter
// =============================================================================
describe('useUnitConverter', () => {
  it('initializes with Length category', () => {
    const uc = useUnitConverter()
    expect(uc.category.value).toBe('Length')
    expect(uc.fromUnit.value).toBe('mm')
    expect(uc.toUnit.value).toBe('in')
  })

  it('converts mm to inches', () => {
    const mm = UNITS.Length.find((u) => u.key === 'mm')!
    const inch = UNITS.Length.find((u) => u.key === 'in')!
    expect(convert(25.4, mm, inch, 'Length')).toBeCloseTo(1, 4)
  })

  it('converts meters to feet', () => {
    const m = UNITS.Length.find((u) => u.key === 'm')!
    const ft = UNITS.Length.find((u) => u.key === 'ft')!
    expect(convert(1, m, ft, 'Length')).toBeCloseTo(3.281, 2)
  })

  it('converts temperature C → F', () => {
    const c = UNITS.Temperature.find((u) => u.key === 'c')!
    const f = UNITS.Temperature.find((u) => u.key === 'f')!
    expect(convert(0, c, f, 'Temperature')).toBeCloseTo(32, 1)
    expect(convert(100, c, f, 'Temperature')).toBeCloseTo(212, 1)
    expect(convert(-40, c, f, 'Temperature')).toBeCloseTo(-40, 1)
  })

  it('converts temperature F → C', () => {
    const c = UNITS.Temperature.find((u) => u.key === 'c')!
    const f = UNITS.Temperature.find((u) => u.key === 'f')!
    expect(convert(32, f, c, 'Temperature')).toBeCloseTo(0, 1)
    expect(convert(212, f, c, 'Temperature')).toBeCloseTo(100, 1)
  })

  it('converts Kelvin correctly', () => {
    const c = UNITS.Temperature.find((u) => u.key === 'c')!
    const k = UNITS.Temperature.find((u) => u.key === 'k')!
    expect(convert(0, c, k, 'Temperature')).toBeCloseTo(273.15, 1)
    expect(convert(273.15, k, c, 'Temperature')).toBeCloseTo(0, 1)
  })

  it('swapUnits exchanges from/to', () => {
    const uc = useUnitConverter()
    uc.fromUnit.value = 'mm'
    uc.toUnit.value = 'in'
    uc.fromValue.value = 25.4

    uc.swapUnits()

    expect(uc.fromUnit.value).toBe('in')
    expect(uc.toUnit.value).toBe('mm')
  })

  it('availableUnits changes with category', () => {
    const uc = useUnitConverter()
    expect(uc.availableUnits.value.some((u) => u.key === 'mm')).toBe(true)

    uc.category.value = 'Mass'
    expect(uc.availableUnits.value.some((u) => u.key === 'kg')).toBe(true)
    expect(uc.availableUnits.value.some((u) => u.key === 'mm')).toBe(false)
  })

  it('converts Data units (decimal)', () => {
    const B = UNITS.Data.find((u) => u.key === 'B')!
    const KB = UNITS.Data.find((u) => u.key === 'KB')!
    expect(convert(1000, B, KB, 'Data')).toBeCloseTo(1, 2)
  })

  it('converts Data units (binary)', () => {
    const B = UNITS.Data.find((u) => u.key === 'B')!
    const KiB = UNITS.Data.find((u) => u.key === 'KiB')!
    expect(convert(1024, B, KiB, 'Data')).toBeCloseTo(1, 2)
  })
})
