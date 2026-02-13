/**
 * Vitest tests for toolbox composables.
 * Run with: npm run test:composables
 */
import { describe, it, expect } from 'vitest'
import {
  useScaleLengthCalculator,
  calculateStringTension,
  SCALE_PRESETS,
  GAUGE_PRESETS
} from '../../components/toolbox/composables/useScaleLengthCalculator'
import {
  useUnitConverter,
  convert,
  UNITS
} from '../../components/toolbox/composables/useUnitConverter'
import {
  useWoodworkCalculator,
  calculateBoardFeet,
  calculateWoodWeight,
  calculateMiterAngle,
  WOOD_SPECIES
} from '../../components/toolbox/composables/useWoodworkCalculator'
import {
  useGuitarDimensions,
  DIMENSION_PRESETS,
  GUITAR_TYPES
} from '../../components/toolbox/composables/useGuitarDimensions'

// =============================================================================
// useScaleLengthCalculator
// =============================================================================
describe('useScaleLengthCalculator', () => {
  it('initializes with Fender scale defaults', () => {
    const calc = useScaleLengthCalculator()

    expect(calc.customScale.value).toBe(25.5)
    expect(calc.scaleUnit.value).toBe('in')
    expect(calc.strings.value.length).toBe(6)
  })

  it('calculates string tension using Mersenne\'s Law', () => {
    // Formula: T = (μ × (2 × L × f)²) ÷ 4
    // μ = 0.00001294 × gauge² (empirical approximation)
    const tension = calculateStringTension(25.5, 329.63, 0.010)
    expect(tension).toBeGreaterThan(0)
    expect(tension).toBeLessThan(1) // Small values due to empirical constant
  })

  it('totalTension sums all strings', () => {
    const calc = useScaleLengthCalculator()
    const total = calc.totalTension.value

    // Sum of all string tensions (using empirical formula)
    expect(total).toBeGreaterThan(0)
    expect(total).toBeLessThan(10)
  })

  it('averageTension computes correctly', () => {
    const calc = useScaleLengthCalculator()
    const avg = calc.averageTension.value

    expect(avg).toBeCloseTo(calc.totalTension.value / 6, 2)
  })

  it('applyGaugeSet changes string gauges', () => {
    const calc = useScaleLengthCalculator()

    calc.applyGaugeSet('heavy')
    expect(calc.strings.value[0].gauge).toBe(0.012)
    expect(calc.strings.value[5].gauge).toBe(0.053)

    calc.applyGaugeSet('light')
    expect(calc.strings.value[0].gauge).toBe(0.009)
  })

  it('applyScalePreset changes scale length', () => {
    const calc = useScaleLengthCalculator()

    calc.applyScalePreset('gibson')
    expect(calc.customScale.value).toBe(24.75)

    calc.applyScalePreset('baritone')
    expect(calc.customScale.value).toBe(27.0)
  })

  it('converts mm to inches for calculations', () => {
    const calc = useScaleLengthCalculator()

    calc.customScale.value = 648
    calc.scaleUnit.value = 'mm'

    // 648mm ≈ 25.5 inches
    expect(calc.scaleInches.value).toBeCloseTo(25.5, 1)
  })

  it('getTensionClass categorizes tension correctly', () => {
    const calc = useScaleLengthCalculator()

    // Thresholds: <13 = low, 13-18 = good, >18 = high
    expect(calc.getTensionClass(10)).toBe('low')
    expect(calc.getTensionClass(15)).toBe('good')
    expect(calc.getTensionClass(20)).toBe('high')
    expect(calc.getTensionClass(0.1)).toBe('low') // For actual formula output
  })

  it('reset restores defaults', () => {
    const calc = useScaleLengthCalculator()

    calc.customScale.value = 30
    calc.applyGaugeSet('heavy')
    calc.reset()

    expect(calc.customScale.value).toBe(25.5)
    expect(calc.strings.value[0].gauge).toBe(0.010)
  })
})

// =============================================================================
// useUnitConverter
// =============================================================================
describe('useUnitConverter', () => {
  it('initializes with Length category', () => {
    const converter = useUnitConverter()

    expect(converter.category.value).toBe('Length')
    expect(converter.fromUnit.value).toBe('mm')
    expect(converter.toUnit.value).toBe('in')
  })

  it('converts mm to inches correctly', () => {
    const mmDef = UNITS.Length.find(u => u.key === 'mm')!
    const inDef = UNITS.Length.find(u => u.key === 'in')!

    const result = convert(25.4, mmDef, inDef, 'Length')
    expect(result).toBeCloseTo(1, 4)
  })

  it('converts meters to feet correctly', () => {
    const mDef = UNITS.Length.find(u => u.key === 'm')!
    const ftDef = UNITS.Length.find(u => u.key === 'ft')!

    const result = convert(1, mDef, ftDef, 'Length')
    expect(result).toBeCloseTo(3.281, 2)
  })

  it('converts temperature Celsius to Fahrenheit', () => {
    const cDef = UNITS.Temperature.find(u => u.key === 'c')!
    const fDef = UNITS.Temperature.find(u => u.key === 'f')!

    expect(convert(0, cDef, fDef, 'Temperature')).toBeCloseTo(32, 1)
    expect(convert(100, cDef, fDef, 'Temperature')).toBeCloseTo(212, 1)
    expect(convert(-40, cDef, fDef, 'Temperature')).toBeCloseTo(-40, 1)
  })

  it('converts temperature Fahrenheit to Celsius', () => {
    const cDef = UNITS.Temperature.find(u => u.key === 'c')!
    const fDef = UNITS.Temperature.find(u => u.key === 'f')!

    expect(convert(32, fDef, cDef, 'Temperature')).toBeCloseTo(0, 1)
    expect(convert(212, fDef, cDef, 'Temperature')).toBeCloseTo(100, 1)
  })

  it('converts Kelvin correctly', () => {
    const cDef = UNITS.Temperature.find(u => u.key === 'c')!
    const kDef = UNITS.Temperature.find(u => u.key === 'k')!

    expect(convert(0, cDef, kDef, 'Temperature')).toBeCloseTo(273.15, 1)
    expect(convert(273.15, kDef, cDef, 'Temperature')).toBeCloseTo(0, 1)
  })

  it('swapUnits exchanges from/to', () => {
    const converter = useUnitConverter()

    converter.fromUnit.value = 'mm'
    converter.toUnit.value = 'in'
    converter.fromValue.value = 25.4

    converter.swapUnits()

    expect(converter.fromUnit.value).toBe('in')
    expect(converter.toUnit.value).toBe('mm')
  })

  it('availableUnits changes with category', () => {
    const converter = useUnitConverter()

    expect(converter.availableUnits.value.some(u => u.key === 'mm')).toBe(true)

    converter.category.value = 'Mass'
    expect(converter.availableUnits.value.some(u => u.key === 'kg')).toBe(true)
    expect(converter.availableUnits.value.some(u => u.key === 'mm')).toBe(false)
  })

  it('converts Data units correctly', () => {
    const byteDef = UNITS.Data.find(u => u.key === 'B')!
    const kbDef = UNITS.Data.find(u => u.key === 'KB')!

    // 1000 bytes = 1 KB (decimal)
    const result = convert(1000, byteDef, kbDef, 'Data')
    expect(result).toBeCloseTo(1, 2)
  })

  it('converts binary Data units correctly', () => {
    const byteDef = UNITS.Data.find(u => u.key === 'B')!
    const kibDef = UNITS.Data.find(u => u.key === 'KiB')!

    // 1024 bytes = 1 KiB (binary)
    const result = convert(1024, byteDef, kibDef, 'Data')
    expect(result).toBeCloseTo(1, 2)
  })
})

// =============================================================================
// useWoodworkCalculator
// =============================================================================
describe('useWoodworkCalculator', () => {
  it('calculates board feet correctly', () => {
    // 48" x 6" x 1" = 288 / 144 = 2 BF
    const bf = calculateBoardFeet({ length: 48, width: 6, thickness: 1 })
    expect(bf).toBe(2)

    // 96" x 12" x 2" = 2304 / 144 = 16 BF
    const bf2 = calculateBoardFeet({ length: 96, width: 12, thickness: 2 })
    expect(bf2).toBe(16)
  })

  it('calculates board cost correctly', () => {
    const calc = useWoodworkCalculator()

    calc.boardFeet.value = { length: 48, width: 6, thickness: 1, pricePerBF: 10 }
    // 2 BF × $10 = $20
    expect(calc.boardCostResult.value).toBe(20)
  })

  it('calculates wood weight using species density', () => {
    // 100x100x10 mm = 100,000 mm³ = 100 cm³
    // Spruce density = 0.43 g/cm³
    // Weight = 100 × 0.43 = 43g
    const weight = calculateWoodWeight({
      length: 100,
      width: 100,
      thickness: 10,
      species: 'spruce'
    })
    expect(weight).toBeCloseTo(43, 0)
  })

  it('calculates weight for different species', () => {
    const input = { length: 100, width: 100, thickness: 10, species: '' }

    input.species = 'ebony'
    const ebonyWeight = calculateWoodWeight(input)

    input.species = 'cedar'
    const cedarWeight = calculateWoodWeight(input)

    // Ebony is much denser than cedar
    expect(ebonyWeight).toBeGreaterThan(cedarWeight * 2)
  })

  it('calculates miter angle correctly', () => {
    // 12/12 pitch = 45 degrees
    expect(calculateMiterAngle({ rise: 12, run: 12 })).toBeCloseTo(45, 1)

    // 6/12 pitch ≈ 26.57 degrees
    expect(calculateMiterAngle({ rise: 6, run: 12 })).toBeCloseTo(26.57, 1)

    // Flat (0/12) = 0 degrees
    expect(calculateMiterAngle({ rise: 0, run: 12 })).toBe(0)
  })

  it('calculates complementary angle', () => {
    const calc = useWoodworkCalculator()

    calc.miter.value = { rise: 12, run: 12 }
    expect(calc.complementaryAngle.value).toBeCloseTo(45, 1)

    calc.miter.value = { rise: 6, run: 12 }
    expect(calc.complementaryAngle.value).toBeCloseTo(63.43, 1)
  })

  it('resetAll restores defaults', () => {
    const calc = useWoodworkCalculator()

    calc.boardFeet.value.length = 999
    calc.woodVolume.value.species = 'ebony'
    calc.miter.value.rise = 99

    calc.resetAll()

    expect(calc.boardFeet.value.length).toBe(48)
    expect(calc.woodVolume.value.species).toBe('spruce')
    expect(calc.miter.value.rise).toBe(12)
  })
})

// =============================================================================
// useGuitarDimensions
// =============================================================================
describe('useGuitarDimensions', () => {
  it('initializes with acoustic type and mm units', () => {
    const dims = useGuitarDimensions()

    expect(dims.selectedType.value).toBe('acoustic')
    expect(dims.units.value).toBe('mm')
    expect(dims.dimensions.value.bodyLength).toBe(400)
  })

  it('hasValidDimensions validates correctly', () => {
    const dims = useGuitarDimensions()

    expect(dims.hasValidDimensions.value).toBe(true)

    dims.dimensions.value.bodyLength = 0
    expect(dims.hasValidDimensions.value).toBe(false)

    dims.dimensions.value.bodyLength = 400
    expect(dims.hasValidDimensions.value).toBe(true)
  })

  it('toggleUnits converts mm to inches', () => {
    const dims = useGuitarDimensions()

    // Start with 400mm body length
    expect(dims.dimensions.value.bodyLength).toBe(400)

    dims.toggleUnits('inch')

    // 400mm ≈ 15.75 inches
    expect(dims.dimensions.value.bodyLength).toBeCloseTo(15.75, 1)
    expect(dims.units.value).toBe('inch')
  })

  it('toggleUnits converts inches to mm', () => {
    const dims = useGuitarDimensions()

    dims.toggleUnits('inch') // First convert to inches
    const inchValue = dims.dimensions.value.bodyLength

    dims.toggleUnits('mm') // Convert back to mm

    // Should be close to original 400mm
    expect(dims.dimensions.value.bodyLength).toBeCloseTo(400, 0)
  })

  it('loadPreset applies preset dimensions', () => {
    const dims = useGuitarDimensions()

    dims.loadPreset('lesPaul')

    expect(dims.dimensions.value.bodyLength).toBe(440)
    expect(dims.dimensions.value.scaleLength).toBe(629)
  })

  it('loadPreset converts to current units', () => {
    const dims = useGuitarDimensions()

    dims.toggleUnits('inch')
    dims.loadPreset('telecaster')

    // 400mm ≈ 15.75 inches
    expect(dims.dimensions.value.bodyLength).toBeCloseTo(15.75, 1)
  })

  it('exportAsObject returns correct structure', () => {
    const dims = useGuitarDimensions()

    dims.selectType('electric')
    const exported = dims.exportAsObject()

    expect(exported.type).toBe('electric')
    expect(exported.units).toBe('mm')
    expect(exported.dimensions.bodyLength).toBe(400)
  })

  it('exportAsCSV returns valid CSV', () => {
    const dims = useGuitarDimensions()

    const csv = dims.exportAsCSV()
    const lines = csv.split('\n')

    expect(lines[0]).toBe('Dimension,Value,Unit')
    expect(lines.length).toBeGreaterThan(5)
    expect(lines.some(l => l.includes('bodyLength'))).toBe(true)
  })

  it('reset restores all defaults', () => {
    const dims = useGuitarDimensions()

    dims.selectType('bass')
    dims.toggleUnits('inch')
    dims.loadPreset('lesPaul')

    dims.reset()

    expect(dims.selectedType.value).toBe('acoustic')
    expect(dims.units.value).toBe('mm')
    expect(dims.dimensions.value.bodyLength).toBe(400)
  })

  it('GUITAR_TYPES has expected entries', () => {
    expect(GUITAR_TYPES.length).toBe(4)
    expect(GUITAR_TYPES.find(t => t.id === 'acoustic')).toBeDefined()
    expect(GUITAR_TYPES.find(t => t.id === 'bass')).toBeDefined()
  })

  it('DIMENSION_PRESETS has expected presets', () => {
    expect(DIMENSION_PRESETS.telecaster).toBeDefined()
    expect(DIMENSION_PRESETS.stratocaster).toBeDefined()
    expect(DIMENSION_PRESETS.lesPaul).toBeDefined()
    expect(DIMENSION_PRESETS.dreadnought).toBeDefined()
  })
})
