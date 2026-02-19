/**
 * Core calculator state and functions.
 * Extracted from ScientificCalculator.vue
 */
import { ref, type Ref } from 'vue'

export type AngleMode = 'deg' | 'rad'

export interface CalculatorCoreState {
  display: Ref<string>
  expression: Ref<string>
  angleMode: Ref<AngleMode>
  history: Ref<string[]>
  showHistory: Ref<boolean>
  clear: () => void
  backspace: () => void
  appendNumber: (num: string) => void
  appendOperator: (op: string) => void
  appendFunction: (func: string) => void
  toggleSign: () => void
  calculate: () => void
  loadHistory: (item: string) => void
}

export function useCalculatorCore(): CalculatorCoreState {
  const display = ref('0')
  const expression = ref('')
  const angleMode = ref<AngleMode>('deg')
  const history = ref<string[]>([])
  const showHistory = ref(false)

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
  }

  function appendOperator(op: string) {
    if (display.value !== '0') {
      expression.value += display.value + ` ${op} `
      display.value = '0'
    } else if (expression.value && !['+', '−', '×', '÷', '^', '%', '(', ')'].some(o => expression.value.endsWith(o))) {
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

      // Evaluate expression (using Function for safer eval)
      const result = new Function('return ' + expr)()

      // Format result
      display.value = Number.isFinite(result)
        ? (Math.abs(result) < 0.00001 && result !== 0
            ? result.toExponential(4)
            : result.toFixed(8).replace(/\.?0+$/, ''))
        : 'Error'

      // Add to history
      history.value.unshift(`${expression.value}${display.value === '0' ? '' : display.value} = ${display.value}`)
      if (history.value.length > 20) history.value.pop()

      expression.value = ''
    } catch {
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

  return {
    display,
    expression,
    angleMode,
    history,
    showHistory,
    clear,
    backspace,
    appendNumber,
    appendOperator,
    appendFunction,
    toggleSign,
    calculate,
    loadHistory
  }
}
