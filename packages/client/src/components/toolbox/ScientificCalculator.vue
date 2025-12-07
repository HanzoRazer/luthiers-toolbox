<template>
  <div class="calculator">
    <!-- Tab Navigation -->
    <div class="tabs">
      <div 
        v-for="tabName in tabs" 
        :key="tabName"
        class="tab" 
        :class="{ active: activeTab === tabName }"
        @click="activeTab = tabName"
      >
        {{ tabName }}
      </div>
    </div>

    <!-- Display (shared across all tabs) -->
    <div class="display-container">
      <div class="expression">{{ expression || '\u00A0' }}</div>
      <div class="display">{{ display }}</div>
    </div>

    <!-- Tab Content -->
    <div class="tab-content">
      <!-- BASIC TAB -->
      <div v-if="activeTab === 'Basic'" class="calculator-grid basic-grid">
        <button class="btn btn-clear" @click="clear">C</button>
        <button class="btn btn-operator" @click="backspace">⌫</button>
        <button class="btn btn-operator" @click="appendOperator('%')">%</button>
        <button class="btn btn-operator" @click="appendOperator('÷')">÷</button>
        
        <button class="btn btn-number" @click="appendNumber('7')">7</button>
        <button class="btn btn-number" @click="appendNumber('8')">8</button>
        <button class="btn btn-number" @click="appendNumber('9')">9</button>
        <button class="btn btn-operator" @click="appendOperator('×')">×</button>
        
        <button class="btn btn-number" @click="appendNumber('4')">4</button>
        <button class="btn btn-number" @click="appendNumber('5')">5</button>
        <button class="btn btn-number" @click="appendNumber('6')">6</button>
        <button class="btn btn-operator" @click="appendOperator('−')">−</button>
        
        <button class="btn btn-number" @click="appendNumber('1')">1</button>
        <button class="btn btn-number" @click="appendNumber('2')">2</button>
        <button class="btn btn-number" @click="appendNumber('3')">3</button>
        <button class="btn btn-operator" @click="appendOperator('+')">+</button>
        
        <button class="btn btn-number" @click="toggleSign">±</button>
        <button class="btn btn-number" @click="appendNumber('0')">0</button>
        <button class="btn btn-number" @click="appendNumber('.')">.</button>
        <button class="btn btn-equals" @click="calculate">=</button>
      </div>

      <!-- SCIENTIFIC TAB -->
      <div v-else-if="activeTab === 'Scientific'" class="calculator-grid scientific-grid">
        <div class="mode-toggles">
          <label class="toggle">
            <input type="radio" v-model="angleMode" value="deg" />
            <span>DEG</span>
          </label>
          <label class="toggle">
            <input type="radio" v-model="angleMode" value="rad" />
            <span>RAD</span>
          </label>
          <button class="btn-small" @click="showHistory = !showHistory">History</button>
        </div>

        <button class="btn btn-function" @click="appendFunction('sin(')">sin</button>
        <button class="btn btn-function" @click="appendFunction('cos(')">cos</button>
        <button class="btn btn-function" @click="appendFunction('tan(')">tan</button>
        <button class="btn btn-function" @click="appendFunction('ln(')">ln</button>
        <button class="btn btn-function" @click="appendFunction('log(')">log</button>
        <button class="btn btn-function" @click="appendFunction('sqrt(')">√</button>

        <button class="btn btn-operator" @click="appendOperator('^')">^</button>
        <button class="btn btn-operator" @click="appendOperator('(')">(</button>
        <button class="btn btn-operator" @click="appendOperator(')')">)</button>
        <button class="btn btn-function" @click="appendNumber('π')">π</button>
        <button class="btn btn-function" @click="appendNumber('e')">e</button>
        <button class="btn btn-function" @click="appendFunction('!')">!</button>

        <button class="btn btn-clear" @click="clear">C</button>
        <button class="btn btn-operator" @click="backspace">⌫</button>
        <button class="btn btn-operator" @click="appendOperator('%')">%</button>
        <button class="btn btn-operator" @click="appendOperator('÷')">÷</button>
        <button class="btn btn-number" @click="appendNumber('7')">7</button>
        <button class="btn btn-number" @click="appendNumber('8')">8</button>

        <button class="btn btn-number" @click="appendNumber('9')">9</button>
        <button class="btn btn-operator" @click="appendOperator('×')">×</button>
        <button class="btn btn-number" @click="appendNumber('4')">4</button>
        <button class="btn btn-number" @click="appendNumber('5')">5</button>
        <button class="btn btn-number" @click="appendNumber('6')">6</button>
        <button class="btn btn-operator" @click="appendOperator('−')">−</button>

        <button class="btn btn-number" @click="appendNumber('1')">1</button>
        <button class="btn btn-number" @click="appendNumber('2')">2</button>
        <button class="btn btn-number" @click="appendNumber('3')">3</button>
        <button class="btn btn-operator" @click="appendOperator('+')">+</button>
        <button class="btn btn-number" @click="toggleSign">±</button>
        <button class="btn btn-number" @click="appendNumber('0')">0</button>

        <button class="btn btn-number" @click="appendNumber('.')">.</button>
        <button class="btn btn-equals" @click="calculate">=</button>

        <div v-if="showHistory" class="history-dropdown">
          <div class="history-title">History</div>
          <div v-for="(item, i) in history" :key="i" class="history-item" @click="loadHistory(item)">
            {{ item }}
          </div>
          <div v-if="history.length === 0" class="history-empty">No history yet</div>
        </div>
      </div>

      <!-- CONVERTER TAB -->
      <div v-else-if="activeTab === 'Converter'" class="converter-content">
        <div class="converter-tabs">
          <button 
            v-for="cat in converterCategories" 
            :key="cat"
            class="converter-tab"
            :class="{ active: converterType === cat }"
            @click="converterType = cat"
          >
            {{ cat }}
          </button>
        </div>

        <div class="converter-main">
          <div class="converter-input-group">
            <input 
              type="number" 
              v-model.number="convertFrom.value" 
              @input="updateConversion"
              class="converter-input"
              placeholder="0"
            />
            <select v-model="convertFrom.unit" @change="updateConversion" class="converter-select">
              <option v-for="unit in getUnitsForType(converterType)" :key="unit.key" :value="unit.key">
                {{ unit.label }}
              </option>
            </select>
          </div>

          <div class="converter-swap">
            <button @click="swapUnits" class="btn-swap">↕</button>
          </div>

          <div class="converter-input-group">
            <input 
              type="number" 
              v-model.number="convertTo.value" 
              readonly
              class="converter-input"
            />
            <select v-model="convertTo.unit" @change="updateConversion" class="converter-select">
              <option v-for="unit in getUnitsForType(converterType)" :key="unit.key" :value="unit.key">
                {{ unit.label }}
              </option>
            </select>
          </div>

          <!-- Fraction Input (for Length only) -->
          <div v-if="converterType === 'Length'" class="fraction-input">
            <div class="fraction-label">Fraction Input:</div>
            <div class="fraction-fields">
              <input type="number" v-model.number="fraction.whole" @input="updateFromFraction" class="fraction-field" placeholder="2" />
              <span class="fraction-sep">+</span>
              <input type="number" v-model.number="fraction.num" @input="updateFromFraction" class="fraction-field" placeholder="7" />
              <span class="fraction-sep">/</span>
              <input type="number" v-model.number="fraction.denom" @input="updateFromFraction" class="fraction-field" placeholder="16" />
              <span class="fraction-unit">inches</span>
            </div>
            <div class="fraction-result">= {{ fractionToDecimal() }}" = {{ fractionToMM() }} mm</div>
          </div>

          <!-- Quick Presets -->
          <div class="quick-presets">
            <div class="preset-label">Common Measurements:</div>
            <div class="preset-buttons">
              <button @click="applyPreset('1/16', 'in')" class="btn-preset">1/16"</button>
              <button @click="applyPreset('1/32', 'in')" class="btn-preset">1/32"</button>
              <button @click="applyPreset('1/64', 'in')" class="btn-preset">1/64"</button>
              <button @click="applyPreset('0.010', 'in')" class="btn-preset">.010" (String)</button>
              <button @click="applyPreset('0.046', 'in')" class="btn-preset">.046" (String)</button>
              <button @click="applyPreset('25.5', 'in')" class="btn-preset">25.5"</button>
              <button @click="applyPreset('24.75', 'in')" class="btn-preset">24.75"</button>
            </div>
          </div>
        </div>
      </div>

      <!-- WOODWORK TAB -->
      <div v-else-if="activeTab === 'Woodwork'" class="woodwork-content">
        <div class="woodwork-tabs">
          <button 
            v-for="cat in woodworkCategories" 
            :key="cat"
            class="woodwork-tab"
            :class="{ active: woodworkType === cat }"
            @click="woodworkType = cat"
          >
            {{ cat }}
          </button>
        </div>

        <!-- Board Feet Calculator -->
        <div v-if="woodworkType === 'Board Feet'" class="woodwork-panel">
          <h3>📏 Board Feet Calculator</h3>
          <div class="input-row">
            <label>Length (in):</label>
            <input type="number" v-model.number="boardFeet.length" @input="calculateBoardFeet" />
          </div>
          <div class="input-row">
            <label>Width (in):</label>
            <input type="number" v-model.number="boardFeet.width" @input="calculateBoardFeet" />
          </div>
          <div class="input-row">
            <label>Thickness (in):</label>
            <input type="number" v-model.number="boardFeet.thickness" @input="calculateBoardFeet" />
          </div>
          <div class="result-box">
            <div class="result-label">Board Feet:</div>
            <div class="result-value">{{ boardFeetResult.toFixed(2) }} BF</div>
          </div>
          <div class="input-row">
            <label>Price ($/BF):</label>
            <input type="number" v-model.number="boardFeet.pricePerBF" @input="calculateBoardFeet" />
          </div>
          <div class="result-box">
            <div class="result-label">Total Cost:</div>
            <div class="result-value">${{ (boardFeetResult * boardFeet.pricePerBF).toFixed(2) }}</div>
          </div>
        </div>

        <!-- Wood Volume/Weight -->
        <div v-if="woodworkType === 'Volume'" class="woodwork-panel">
          <h3>🌲 Wood Volume & Weight</h3>
          <div class="input-row">
            <label>Length (mm):</label>
            <input type="number" v-model.number="woodVolume.length" @input="calculateWoodWeight" />
          </div>
          <div class="input-row">
            <label>Width (mm):</label>
            <input type="number" v-model.number="woodVolume.width" @input="calculateWoodWeight" />
          </div>
          <div class="input-row">
            <label>Thickness (mm):</label>
            <input type="number" v-model.number="woodVolume.thickness" @input="calculateWoodWeight" />
          </div>
          <div class="input-row">
            <label>Species:</label>
            <select v-model="woodVolume.species" @change="calculateWoodWeight">
              <option v-for="(density, name) in woodSpecies" :key="name" :value="name">
                {{ name }} (ρ={{ density }} g/cm³)
              </option>
            </select>
          </div>
          <div class="result-box">
            <div class="result-label">Volume:</div>
            <div class="result-value">{{ woodVolumeResult.toFixed(1) }} cm³</div>
          </div>
          <div class="result-box">
            <div class="result-label">Weight:</div>
            <div class="result-value">{{ woodWeightResult.toFixed(1) }} g</div>
          </div>
        </div>

        <!-- Miter Angles -->
        <div v-if="woodworkType === 'Angles'" class="woodwork-panel">
          <h3>📐 Miter/Bevel Angle Calculator</h3>
          <div class="input-row">
            <label>Rise (mm):</label>
            <input type="number" v-model.number="miterAngle.rise" @input="calculateMiterAngle" />
          </div>
          <div class="input-row">
            <label>Run (mm):</label>
            <input type="number" v-model.number="miterAngle.run" @input="calculateMiterAngle" />
          </div>
          <div class="result-box">
            <div class="result-label">Angle:</div>
            <div class="result-value">{{ miterAngleResult.toFixed(2) }}°</div>
          </div>
          <div class="helper-text">
            Common uses: Neck angle (0.5-3°), Headstock angle (12-17°), Bridge ramp
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// ============================================================================
// STATE MANAGEMENT
// ============================================================================

const tabs = ['Basic', 'Scientific', 'Converter', 'Woodwork']
const activeTab = ref('Basic')
const display = ref('0')
const expression = ref('')
const angleMode = ref<'deg' | 'rad'>('deg')
const showHistory = ref(false)
const history = ref<string[]>([])

// ============================================================================
// CONVERTER STATE
// ============================================================================

const converterCategories = ['Length', 'Area', 'Temperature', 'Volume', 'Mass', 'Data', 'Speed', 'Time']
const converterType = ref('Length')
const convertFrom = ref({ value: 0, unit: 'mm' })
const convertTo = ref({ value: 0, unit: 'in' })

// Fraction input (for length conversions)
const fraction = ref({ whole: 0, num: 0, denom: 1 })

// Unit definitions
const units = {
  Length: [
    { key: 'mm', label: 'Millimeters (mm)', toMM: 1 },
    { key: 'cm', label: 'Centimeters (cm)', toMM: 10 },
    { key: 'm', label: 'Meters (m)', toMM: 1000 },
    { key: 'km', label: 'Kilometers (km)', toMM: 1000000 },
    { key: 'in', label: 'Inches (in)', toMM: 25.4 },
    { key: 'ft', label: 'Feet (ft)', toMM: 304.8 },
    { key: 'yd', label: 'Yards (yd)', toMM: 914.4 },
    { key: 'mi', label: 'Miles (mi)', toMM: 1609344 },
    { key: 'thou', label: 'Thousandths (mil)', toMM: 0.0254 },
    { key: 'nm', label: 'Nanometers (nm)', toMM: 0.000001 },
    { key: 'μm', label: 'Micrometers (μm)', toMM: 0.001 }
  ],
  Area: [
    { key: 'mm2', label: 'Square Millimeters (mm²)', toMM2: 1 },
    { key: 'cm2', label: 'Square Centimeters (cm²)', toMM2: 100 },
    { key: 'm2', label: 'Square Meters (m²)', toMM2: 1000000 },
    { key: 'km2', label: 'Square Kilometers (km²)', toMM2: 1000000000000 },
    { key: 'ha', label: 'Hectares (ha)', toMM2: 10000000000 },
    { key: 'in2', label: 'Square Inches (in²)', toMM2: 645.16 },
    { key: 'ft2', label: 'Square Feet (ft²)', toMM2: 92903.04 },
    { key: 'yd2', label: 'Square Yards (yd²)', toMM2: 836127.36 },
    { key: 'ac', label: 'Acres (ac)', toMM2: 4046856422.4 },
    { key: 'mi2', label: 'Square Miles (mi²)', toMM2: 2589988110336 }
  ],
  Temperature: [
    { key: 'c', label: 'Celsius (°C)', type: 'temp' },
    { key: 'f', label: 'Fahrenheit (°F)', type: 'temp' },
    { key: 'k', label: 'Kelvin (K)', type: 'temp' }
  ],
  Volume: [
    { key: 'ml', label: 'Milliliters (mL)', toML: 1 },
    { key: 'l', label: 'Liters (L)', toML: 1000 },
    { key: 'cm3', label: 'Cubic Centimeters (cm³)', toML: 1 },
    { key: 'm3', label: 'Cubic Meters (m³)', toML: 1000000 },
    { key: 'in3', label: 'Cubic Inches (in³)', toML: 16.387064 },
    { key: 'ft3', label: 'Cubic Feet (ft³)', toML: 28316.846592 },
    { key: 'floz_us', label: 'Fluid Ounces US (fl oz)', toML: 29.5735 },
    { key: 'floz_uk', label: 'Fluid Ounces UK (fl oz)', toML: 28.4131 },
    { key: 'cup_us', label: 'Cups US', toML: 236.588 },
    { key: 'pt_us', label: 'Pints US (pt)', toML: 473.176 },
    { key: 'qt_us', label: 'Quarts US (qt)', toML: 946.353 },
    { key: 'gal_us', label: 'Gallons US (gal)', toML: 3785.41 },
    { key: 'gal_uk', label: 'Gallons UK (gal)', toML: 4546.09 },
    { key: 'bf', label: 'Board Feet (bf)', toML: 2359737.216 },
    { key: 'tbsp', label: 'Tablespoons (tbsp)', toML: 14.7868 },
    { key: 'tsp', label: 'Teaspoons (tsp)', toML: 4.92892 }
  ],
  Mass: [
    { key: 'mg', label: 'Milligrams (mg)', toG: 0.001 },
    { key: 'g', label: 'Grams (g)', toG: 1 },
    { key: 'kg', label: 'Kilograms (kg)', toG: 1000 },
    { key: 't', label: 'Metric Tons (t)', toG: 1000000 },
    { key: 'oz', label: 'Ounces (oz)', toG: 28.3495 },
    { key: 'lb', label: 'Pounds (lb)', toG: 453.592 },
    { key: 'st', label: 'Stones (st)', toG: 6350.29 },
    { key: 'ton_us', label: 'US Tons', toG: 907184.74 },
    { key: 'ton_uk', label: 'UK Tons', toG: 1016046.91 }
  ],
  Data: [
    { key: 'b', label: 'Bits (b)', toBits: 1 },
    { key: 'B', label: 'Bytes (B)', toBits: 8 },
    { key: 'KB', label: 'Kilobytes (KB)', toBits: 8000 },
    { key: 'KiB', label: 'Kibibytes (KiB)', toBits: 8192 },
    { key: 'MB', label: 'Megabytes (MB)', toBits: 8000000 },
    { key: 'MiB', label: 'Mebibytes (MiB)', toBits: 8388608 },
    { key: 'GB', label: 'Gigabytes (GB)', toBits: 8000000000 },
    { key: 'GiB', label: 'Gibibytes (GiB)', toBits: 8589934592 },
    { key: 'TB', label: 'Terabytes (TB)', toBits: 8000000000000 },
    { key: 'TiB', label: 'Tebibytes (TiB)', toBits: 8796093022208 },
    { key: 'PB', label: 'Petabytes (PB)', toBits: 8000000000000000 },
    { key: 'PiB', label: 'Pebibytes (PiB)', toBits: 9007199254740992 }
  ],
  Speed: [
    { key: 'mps', label: 'Meters/second (m/s)', toMPS: 1 },
    { key: 'kph', label: 'Kilometers/hour (km/h)', toMPS: 0.277778 },
    { key: 'mph', label: 'Miles/hour (mph)', toMPS: 0.44704 },
    { key: 'fps', label: 'Feet/second (ft/s)', toMPS: 0.3048 },
    { key: 'knot', label: 'Knots (kn)', toMPS: 0.514444 },
    { key: 'mach', label: 'Mach (Ma)', toMPS: 343 }
  ],
  Time: [
    { key: 'ns', label: 'Nanoseconds (ns)', toMS: 0.000001 },
    { key: 'μs', label: 'Microseconds (μs)', toMS: 0.001 },
    { key: 'ms', label: 'Milliseconds (ms)', toMS: 1 },
    { key: 's', label: 'Seconds (s)', toMS: 1000 },
    { key: 'min', label: 'Minutes (min)', toMS: 60000 },
    { key: 'hr', label: 'Hours (hr)', toMS: 3600000 },
    { key: 'day', label: 'Days', toMS: 86400000 },
    { key: 'wk', label: 'Weeks', toMS: 604800000 },
    { key: 'mo', label: 'Months (30 days)', toMS: 2592000000 },
    { key: 'yr', label: 'Years (365 days)', toMS: 31536000000 }
  ]
}

// ============================================================================
// WOODWORK STATE
// ============================================================================

const woodworkCategories = ['Board Feet', 'Volume', 'Angles']
const woodworkType = ref('Board Feet')

// Board Feet
const boardFeet = ref({ length: 48, width: 6, thickness: 1, pricePerBF: 8.5 })
const boardFeetResult = ref(0)

// Wood Volume/Weight
const woodVolume = ref({ length: 650, width: 200, thickness: 3, species: 'Spruce' })
const woodVolumeResult = ref(0)
const woodWeightResult = ref(0)

const woodSpecies = {
  'Spruce': 0.42,
  'Cedar': 0.38,
  'Mahogany': 0.56,
  'Maple': 0.63,
  'Rosewood': 0.85,
  'Ebony': 1.05,
  'Walnut': 0.65,
  'MDF': 0.70
}

// Miter Angles
const miterAngle = ref({ rise: 12, run: 100 })
const miterAngleResult = ref(0)

// ============================================================================
// BASIC CALCULATOR FUNCTIONS
// ============================================================================

function clear() {
  display.value = '0'
  expression.value = ''
}

function backspace() {
  if (display.value.length > 1) {
    display.value = display.value.slice(0, -1)
  } else {
    display.value = '0'
  }
}

function appendNumber(num: string) {
  if (display.value === '0' && num !== '.') {
    display.value = num
  } else if (num === '.' && display.value.includes('.')) {
    return // Prevent multiple decimals
  } else {
    display.value += num
  }
  // Don't overwrite expression - it should build up with operators
}

function appendOperator(op: string) {
  if (display.value !== '0') {
    // Append current display number to expression, then add operator
    expression.value += display.value + ` ${op} `
    display.value = '0'
  } else if (expression.value && !['+', '−', '×', '÷', '^', '%', '(', ')'].some(o => expression.value.endsWith(o))) {
    // Replace last operator if display is still 0
    expression.value = expression.value.trim().slice(0, -1) + ` ${op} `
  }
}

function appendFunction(func: string) {
  expression.value += func
  display.value = '0'
}

function toggleSign() {
  if (display.value !== '0') {
    if (display.value.startsWith('-')) {
      display.value = display.value.slice(1)
    } else {
      display.value = '-' + display.value
    }
    // Don't overwrite expression
  }
}

function calculate() {
  try {
    let expr = expression.value + (display.value !== '0' ? display.value : '')
    
    // Replace visual symbols with math operators
    expr = expr.replace(/×/g, '*')
               .replace(/÷/g, '/')
               .replace(/−/g, '-')
               .replace(/\^/g, '**')
               .replace(/√\(/g, 'Math.sqrt(')
               .replace(/π/g, String(Math.PI))
               .replace(/e/g, String(Math.E))
    
    // Handle trig functions (degree/radian conversion)
    if (angleMode.value === 'deg') {
      expr = expr.replace(/sin\(/g, 'Math.sin((Math.PI/180)*')
                 .replace(/cos\(/g, 'Math.cos((Math.PI/180)*')
                 .replace(/tan\(/g, 'Math.tan((Math.PI/180)*')
    } else {
      expr = expr.replace(/sin\(/g, 'Math.sin(')
                 .replace(/cos\(/g, 'Math.cos(')
                 .replace(/tan\(/g, 'Math.tan(')
    }
    
    // Handle log functions
    expr = expr.replace(/log\(/g, 'Math.log10(')
               .replace(/ln\(/g, 'Math.log(')
    
    // Handle factorial (simple implementation for small numbers)
    expr = expr.replace(/(\d+)!/g, (_, n) => {
      const num = parseInt(n)
      if (num > 20) return 'Infinity'
      let result = 1
      for (let i = 2; i <= num; i++) result *= i
      return String(result)
    })
    
    // Evaluate expression
    const result = eval(expr)
    
    // Format result
    display.value = Number.isFinite(result) ? 
      (Math.abs(result) < 0.00001 && result !== 0 ? result.toExponential(4) : result.toFixed(8).replace(/\.?0+$/, '')) :
      'Error'
    
    // Add to history
    history.value.unshift(`${expression.value}${display.value === '0' ? '' : display.value} = ${display.value}`)
    if (history.value.length > 20) history.value.pop()
    
    expression.value = ''
  } catch (e) {
    display.value = 'Error'
    expression.value = ''
  }
}

function loadHistory(item: string) {
  const [expr] = item.split(' = ')
  expression.value = expr
  display.value = '0'
  showHistory.value = false
}

// ============================================================================
// CONVERTER FUNCTIONS
// ============================================================================

function getUnitsForType(type: string) {
  return units[type as keyof typeof units] || []
}

function updateConversion() {
  const fromUnit = getUnitsForType(converterType.value).find(u => u.key === convertFrom.value.unit)
  const toUnit = getUnitsForType(converterType.value).find(u => u.key === convertTo.value.unit)
  
  if (!fromUnit || !toUnit) return
  
  // Conversion logic based on type
  let baseValue = 0
  const type = converterType.value
  
  if (type === 'Length') {
    baseValue = convertFrom.value.value * (fromUnit as any).toMM
    convertTo.value.value = baseValue / (toUnit as any).toMM
  } else if (type === 'Area') {
    baseValue = convertFrom.value.value * (fromUnit as any).toMM2
    convertTo.value.value = baseValue / (toUnit as any).toMM2
  } else if (type === 'Temperature') {
    // Temperature requires special conversion formulas
    const fromKey = fromUnit.key
    const toKey = toUnit.key
    const val = convertFrom.value.value
    
    // Convert to Celsius first
    let celsius = 0
    if (fromKey === 'c') celsius = val
    else if (fromKey === 'f') celsius = (val - 32) * 5 / 9
    else if (fromKey === 'k') celsius = val - 273.15
    
    // Convert from Celsius to target
    if (toKey === 'c') convertTo.value.value = celsius
    else if (toKey === 'f') convertTo.value.value = celsius * 9 / 5 + 32
    else if (toKey === 'k') convertTo.value.value = celsius + 273.15
  } else if (type === 'Volume') {
    baseValue = convertFrom.value.value * (fromUnit as any).toML
    convertTo.value.value = baseValue / (toUnit as any).toML
  } else if (type === 'Mass') {
    baseValue = convertFrom.value.value * (fromUnit as any).toG
    convertTo.value.value = baseValue / (toUnit as any).toG
  } else if (type === 'Data') {
    baseValue = convertFrom.value.value * (fromUnit as any).toBits
    convertTo.value.value = baseValue / (toUnit as any).toBits
  } else if (type === 'Speed') {
    baseValue = convertFrom.value.value * (fromUnit as any).toMPS
    convertTo.value.value = baseValue / (toUnit as any).toMPS
  } else if (type === 'Time') {
    baseValue = convertFrom.value.value * (fromUnit as any).toMS
    convertTo.value.value = baseValue / (toUnit as any).toMS
  }
}

function swapUnits() {
  const temp = { ...convertFrom.value }
  convertFrom.value = { ...convertTo.value }
  convertTo.value = temp
  updateConversion()
}

function updateFromFraction() {
  const decimal = fraction.value.whole + (fraction.value.num / fraction.value.denom)
  convertFrom.value = { value: decimal, unit: 'in' }
  convertTo.value.unit = 'mm'
  updateConversion()
}

function fractionToDecimal() {
  const { whole, num, denom } = fraction.value
  return (whole + (num / denom)).toFixed(4)
}

function fractionToMM() {
  const decimal = parseFloat(fractionToDecimal())
  return (decimal * 25.4).toFixed(3)
}

function applyPreset(value: string, unit: string) {
  const numValue = value.includes('/') ? 
    eval(value.replace('/', ' / ')) : // Safely evaluate simple fractions like "1/16"
    parseFloat(value)
  
  convertFrom.value = { value: numValue, unit }
  convertTo.value.unit = unit === 'in' ? 'mm' : 'in'
  updateConversion()
}

// ============================================================================
// WOODWORK FUNCTIONS
// ============================================================================

function calculateBoardFeet() {
  const { length, width, thickness } = boardFeet.value
  boardFeetResult.value = (length * width * thickness) / 144
}

function calculateWoodWeight() {
  const { length, width, thickness, species } = woodVolume.value
  const volumeCM3 = (length * width * thickness) / 1000 // mm³ to cm³
  const density = woodSpecies[species as keyof typeof woodSpecies] || 0.5
  
  woodVolumeResult.value = volumeCM3
  woodWeightResult.value = volumeCM3 * density
}

function calculateMiterAngle() {
  const { rise, run } = miterAngle.value
  miterAngleResult.value = Math.atan(rise / run) * (180 / Math.PI)
}

// ============================================================================
// LIFECYCLE - Initialize calculations
// ============================================================================

calculateBoardFeet()
calculateWoodWeight()
calculateMiterAngle()

</script>

<style scoped>
.calculator {
  max-width: 800px;
  margin: 0 auto;
  background: #202124;
  border-radius: 12px;
  padding: 20px;
  color: #e8eaed;
  font-family: 'Roboto', sans-serif;
}

/* Tab Navigation */
.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  border-bottom: 1px solid #3c4043;
  padding-bottom: 8px;
}

.tab {
  padding: 8px 16px;
  cursor: pointer;
  border-radius: 8px 8px 0 0;
  transition: all 0.2s;
  color: #9aa0a6;
  font-size: 14px;
  font-weight: 500;
}

.tab:hover {
  background: #3c4043;
  color: #e8eaed;
}

.tab.active {
  background: #8ab4f8;
  color: #202124;
}

/* Display */
.display-container {
  background: #292a2d;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  min-height: 80px;
}

.expression {
  font-size: 14px;
  color: #9aa0a6;
  min-height: 20px;
  text-align: right;
  margin-bottom: 8px;
}

.display {
  font-size: 32px;
  font-weight: 300;
  text-align: right;
  color: #e8eaed;
  word-break: break-all;
}

/* Basic Calculator Grid */
.basic-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

/* Scientific Calculator Grid */
.scientific-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 8px;
  position: relative;
}

.mode-toggles {
  grid-column: 1 / -1;
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 8px;
  background: #292a2d;
  border-radius: 8px;
  margin-bottom: 8px;
}

.toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  font-size: 12px;
}

.toggle input[type="radio"] {
  accent-color: #8ab4f8;
}

.btn-small {
  padding: 4px 12px;
  background: #3c4043;
  border: none;
  border-radius: 4px;
  color: #e8eaed;
  cursor: pointer;
  font-size: 12px;
}

.btn-small:hover {
  background: #5f6368;
}

/* Calculator Buttons */
.btn {
  padding: 16px;
  border: none;
  border-radius: 50%;
  font-size: 18px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  background: #3c4043;
  color: #e8eaed;
}

.btn:hover {
  background: #5f6368;
  transform: scale(1.05);
}

.btn:active {
  transform: scale(0.95);
}

.btn-number {
  background: #3c4043;
}

.btn-operator {
  background: #5f6368;
}

.btn-function {
  background: #1a73e8;
  color: white;
}

.btn-clear {
  background: #ea4335;
  color: white;
}

.btn-equals {
  background: #34a853;
  color: white;
}

/* History Dropdown */
.history-dropdown {
  position: absolute;
  top: 60px;
  right: 0;
  background: #292a2d;
  border: 1px solid #3c4043;
  border-radius: 8px;
  padding: 8px;
  max-height: 300px;
  overflow-y: auto;
  z-index: 10;
  min-width: 300px;
}

.history-title {
  font-weight: 500;
  margin-bottom: 8px;
  color: #8ab4f8;
}

.history-item {
  padding: 8px;
  cursor: pointer;
  border-radius: 4px;
  font-size: 12px;
  margin-bottom: 4px;
}

.history-item:hover {
  background: #3c4043;
}

.history-empty {
  color: #9aa0a6;
  font-size: 12px;
  padding: 8px;
}

/* Converter Content */
.converter-content, .woodwork-content {
  background: #292a2d;
  border-radius: 8px;
  padding: 20px;
}

.converter-tabs, .woodwork-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.converter-tab, .woodwork-tab {
  padding: 8px 16px;
  background: #3c4043;
  border: none;
  border-radius: 8px;
  color: #e8eaed;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.converter-tab:hover, .woodwork-tab:hover {
  background: #5f6368;
}

.converter-tab.active, .woodwork-tab.active {
  background: #8ab4f8;
  color: #202124;
}

.converter-main {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.converter-input-group {
  display: flex;
  gap: 12px;
  align-items: center;
}

.converter-input {
  flex: 1;
  padding: 12px;
  background: #3c4043;
  border: 1px solid #5f6368;
  border-radius: 8px;
  color: #e8eaed;
  font-size: 18px;
}

.converter-select {
  flex: 1;
  padding: 12px;
  background: #3c4043;
  border: 1px solid #5f6368;
  border-radius: 8px;
  color: #e8eaed;
  font-size: 14px;
}

.converter-swap {
  display: flex;
  justify-content: center;
}

.btn-swap {
  padding: 12px 24px;
  background: #1a73e8;
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  font-size: 20px;
}

.btn-swap:hover {
  background: #2b7de9;
}

/* Fraction Input */
.fraction-input {
  background: #3c4043;
  padding: 16px;
  border-radius: 8px;
}

.fraction-label {
  font-size: 14px;
  color: #9aa0a6;
  margin-bottom: 8px;
}

.fraction-fields {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.fraction-field {
  width: 60px;
  padding: 8px;
  background: #292a2d;
  border: 1px solid #5f6368;
  border-radius: 4px;
  color: #e8eaed;
  text-align: center;
}

.fraction-sep {
  color: #9aa0a6;
  font-size: 18px;
}

.fraction-unit {
  color: #9aa0a6;
  font-size: 14px;
}

.fraction-result {
  color: #8ab4f8;
  font-size: 14px;
}

/* Quick Presets */
.quick-presets {
  background: #3c4043;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.preset-label {
  font-size: 14px;
  color: #9aa0a6;
  margin-bottom: 8px;
}

.preset-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-preset {
  padding: 8px 12px;
  background: #1a73e8;
  border: none;
  border-radius: 4px;
  color: white;
  cursor: pointer;
  font-size: 12px;
}

.btn-preset:hover {
  background: #2b7de9;
}

/* Woodwork Panels */
.woodwork-panel {
  background: #3c4043;
  padding: 20px;
  border-radius: 8px;
}

.woodwork-panel h3 {
  margin: 0 0 16px 0;
  color: #8ab4f8;
  font-size: 18px;
}

.input-row {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
}

.input-row label {
  flex: 0 0 150px;
  color: #9aa0a6;
  font-size: 14px;
}

.input-row input, .input-row select {
  flex: 1;
  padding: 10px;
  background: #292a2d;
  border: 1px solid #5f6368;
  border-radius: 4px;
  color: #e8eaed;
  font-size: 14px;
}

.result-box {
  background: #292a2d;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-label {
  color: #9aa0a6;
  font-size: 14px;
}

.result-value {
  color: #34a853;
  font-size: 24px;
  font-weight: 500;
}

.helper-text {
  color: #9aa0a6;
  font-size: 12px;
  font-style: italic;
  margin-top: 12px;
}

/* Responsive */
@media (max-width: 768px) {
  .calculator {
    padding: 12px;
  }
  
  .tabs {
    overflow-x: auto;
    flex-wrap: nowrap;
  }
  
  .basic-grid {
    grid-template-columns: repeat(4, 1fr);
  }
  
  .scientific-grid {
    grid-template-columns: repeat(4, 1fr);
  }
  
  .converter-input-group {
    flex-direction: column;
  }
  
  .input-row {
    flex-direction: column;
    align-items: stretch;
  }
  
  .input-row label {
    flex: 0 0 auto;
  }
}
</style>
