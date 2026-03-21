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
    const expr = expression.value + (display.value !== '0' ? display.value : '')
    if (!expr.trim()) return

    fetch('/api/ltb/calculator/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ expression: expr, angle_mode: angleMode.value })
    })
      .then(res => {
        if (!res.ok) return res.json().then(err => { throw new Error(err.detail || 'Evaluation failed') })
        return res.json()
      })
      .then((data: { result: number; expression: string }) => {
        const result = data.result
        display.value = Number.isFinite(result)
          ? (Math.abs(result) < 0.00001 && result !== 0
              ? result.toExponential(4)
              : parseFloat(result.toFixed(8)).toString())
          : 'Error'

        // Add to history
        history.value.unshift(`${expr} = ${display.value}`)
        if (history.value.length > 20) history.value.pop()

        expression.value = ''
      })
      .catch(() => {
        display.value = 'Error'
        expression.value = ''
      })
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
