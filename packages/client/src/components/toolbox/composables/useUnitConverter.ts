/**
 * Composable for unit conversion.
 * Extracted from ScientificCalculator.vue
 */
import { ref, computed, watch } from 'vue'

export interface UnitDef {
  key: string
  label: string
  toBase: number  // multiply by this to convert to base unit
}

export const UNIT_CATEGORIES = ['Length', 'Area', 'Volume', 'Mass', 'Temperature', 'Speed', 'Time', 'Data'] as const
export type UnitCategory = typeof UNIT_CATEGORIES[number]

export const UNITS: Record<UnitCategory, UnitDef[]> = {
  Length: [
    { key: 'mm', label: 'Millimeters', toBase: 0.001 },
    { key: 'cm', label: 'Centimeters', toBase: 0.01 },
    { key: 'm', label: 'Meters', toBase: 1 },
    { key: 'km', label: 'Kilometers', toBase: 1000 },
    { key: 'in', label: 'Inches', toBase: 0.0254 },
    { key: 'ft', label: 'Feet', toBase: 0.3048 },
    { key: 'yd', label: 'Yards', toBase: 0.9144 },
    { key: 'mi', label: 'Miles', toBase: 1609.344 }
  ],
  Area: [
    { key: 'mm2', label: 'mm²', toBase: 0.000001 },
    { key: 'cm2', label: 'cm²', toBase: 0.0001 },
    { key: 'm2', label: 'm²', toBase: 1 },
    { key: 'in2', label: 'in²', toBase: 0.00064516 },
    { key: 'ft2', label: 'ft²', toBase: 0.092903 },
    { key: 'ac', label: 'Acres', toBase: 4046.86 }
  ],
  Volume: [
    { key: 'ml', label: 'Milliliters', toBase: 0.001 },
    { key: 'l', label: 'Liters', toBase: 1 },
    { key: 'gal', label: 'Gallons (US)', toBase: 3.78541 },
    { key: 'qt', label: 'Quarts', toBase: 0.946353 },
    { key: 'pt', label: 'Pints', toBase: 0.473176 },
    { key: 'floz', label: 'Fluid Oz', toBase: 0.0295735 },
    { key: 'cm3', label: 'cm³', toBase: 0.001 },
    { key: 'in3', label: 'in³', toBase: 0.0163871 }
  ],
  Mass: [
    { key: 'mg', label: 'Milligrams', toBase: 0.000001 },
    { key: 'g', label: 'Grams', toBase: 0.001 },
    { key: 'kg', label: 'Kilograms', toBase: 1 },
    { key: 'oz', label: 'Ounces', toBase: 0.0283495 },
    { key: 'lb', label: 'Pounds', toBase: 0.453592 },
    { key: 't', label: 'Metric Tons', toBase: 1000 }
  ],
  Temperature: [
    { key: 'c', label: 'Celsius', toBase: 1 },
    { key: 'f', label: 'Fahrenheit', toBase: 1 },
    { key: 'k', label: 'Kelvin', toBase: 1 }
  ],
  Speed: [
    { key: 'mps', label: 'm/s', toBase: 1 },
    { key: 'kph', label: 'km/h', toBase: 0.277778 },
    { key: 'mph', label: 'mph', toBase: 0.44704 },
    { key: 'fps', label: 'ft/s', toBase: 0.3048 },
    { key: 'knot', label: 'Knots', toBase: 0.514444 }
  ],
  Time: [
    { key: 'ms', label: 'Milliseconds', toBase: 0.001 },
    { key: 's', label: 'Seconds', toBase: 1 },
    { key: 'min', label: 'Minutes', toBase: 60 },
    { key: 'hr', label: 'Hours', toBase: 3600 },
    { key: 'day', label: 'Days', toBase: 86400 },
    { key: 'wk', label: 'Weeks', toBase: 604800 }
  ],
  Data: [
    { key: 'b', label: 'Bits (b)', toBase: 1 },
    { key: 'B', label: 'Bytes (B)', toBase: 8 },
    { key: 'KB', label: 'Kilobytes (KB)', toBase: 8000 },
    { key: 'KiB', label: 'Kibibytes (KiB)', toBase: 8192 },
    { key: 'MB', label: 'Megabytes (MB)', toBase: 8000000 },
    { key: 'MiB', label: 'Mebibytes (MiB)', toBase: 8388608 },
    { key: 'GB', label: 'Gigabytes (GB)', toBase: 8000000000 },
    { key: 'GiB', label: 'Gibibytes (GiB)', toBase: 8589934592 },
    { key: 'TB', label: 'Terabytes (TB)', toBase: 8000000000000 },
    { key: 'TiB', label: 'Tebibytes (TiB)', toBase: 8796093022208 },
    { key: 'PB', label: 'Petabytes (PB)', toBase: 8000000000000000 },
    { key: 'PiB', label: 'Pebibytes (PiB)', toBase: 9007199254740992 }
  ]
}

/**
 * Convert a value from one unit to another.
 */
export function convert(
  value: number,
  fromUnit: UnitDef,
  toUnit: UnitDef,
  category: UnitCategory
): number {
  // Special handling for temperature
  if (category === 'Temperature') {
    return convertTemperature(value, fromUnit.key, toUnit.key)
  }

  // Standard conversion via base unit
  const baseValue = value * fromUnit.toBase
  return baseValue / toUnit.toBase
}

function convertTemperature(value: number, from: string, to: string): number {
  // Convert to Celsius first
  let celsius: number
  if (from === 'c') celsius = value
  else if (from === 'f') celsius = (value - 32) * 5 / 9
  else if (from === 'k') celsius = value - 273.15
  else celsius = value

  // Convert from Celsius to target
  if (to === 'c') return celsius
  if (to === 'f') return celsius * 9 / 5 + 32
  if (to === 'k') return celsius + 273.15
  return celsius
}

export function useUnitConverter() {
  const category = ref<UnitCategory>('Length')
  const fromValue = ref(0)
  const fromUnit = ref('mm')
  const toUnit = ref('in')
  const toValue = ref(0)

  const availableUnits = computed(() => UNITS[category.value] || [])

  const fromUnitDef = computed(() =>
    availableUnits.value.find(u => u.key === fromUnit.value)
  )

  const toUnitDef = computed(() =>
    availableUnits.value.find(u => u.key === toUnit.value)
  )

  function updateConversion() {
    if (!fromUnitDef.value || !toUnitDef.value) {
      toValue.value = 0
      return
    }
    toValue.value = convert(fromValue.value, fromUnitDef.value, toUnitDef.value, category.value)
  }

  function swapUnits() {
    const tempUnit = fromUnit.value
    const tempValue = fromValue.value
    fromUnit.value = toUnit.value
    fromValue.value = toValue.value
    toUnit.value = tempUnit
    toValue.value = tempValue
  }

  // Reset when category changes
  watch(category, () => {
    const units = UNITS[category.value]
    if (units && units.length >= 2) {
      fromUnit.value = units[0].key
      toUnit.value = units[1].key
      fromValue.value = 0
      toValue.value = 0
    }
  })

  // Update conversion when inputs change
  watch([fromValue, fromUnit, toUnit], updateConversion)

  return {
    // State
    category,
    fromValue,
    fromUnit,
    toUnit,
    toValue,

    // Computed
    availableUnits,
    fromUnitDef,
    toUnitDef,

    // Methods
    updateConversion,
    swapUnits
  }
}
